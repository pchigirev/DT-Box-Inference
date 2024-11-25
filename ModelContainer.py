"""
DT-Box-Inference
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

import numpy as np
from keras.api.models import load_model
import socket
import threading
import queue
import struct
from collections import deque
import time
from sklearn.preprocessing import StandardScaler

cmd_new_connection = "cmd_nc"
cmd_init_data = "cmd_id"
cmd_next_data_point = "cmd_ndp"
cmd_close_connection = "cmd_cc"
cmd_heartbeat = "cmd_hb"

class SessionContainer:
    def __init__(self, session_id, model_container, dataset_len, client_socket, client_address):
        self.session_id = session_id
        self.model_container = model_container

        self.is_socket_open = True
        self.client_socket = client_socket
        self.client_address = client_address
        self.default_buflen = 1024
        self.q_recv = queue.Queue()

        self.dataset_len = dataset_len
        self.data_queue = deque(maxlen = self.dataset_len)

        self.scaler = StandardScaler()

    def normalize_standard(self, np_array):
        np_array_reshaped = np_array.reshape(-1, 1)
        normalized_array = self.scaler.fit_transform(np_array_reshaped).flatten()
        return normalized_array.reshape(1, -1)

    def create_sliding_windows(self, data, window_size):
        num_windows = len(data) - window_size + 1
        windows = []
        for i in range(num_windows):
            window = data[i:i+window_size]
            window_normalized = self.scaler.fit_transform(window.reshape(-1, 1)).flatten()
            windows.append(window_normalized)
    
        return np.array(windows)

    def send_data(self, msg):
        msg_size = struct.pack('<q', len(msg))
        data = msg_size + msg.encode()

        try:
            self.client_socket.send(data)
        except:
            self.close_remove_session()
            return

    def decode_data(self, data:bytearray):
        data_len = len(data)
        if (data_len >= 8):
            size_buf = data[0:8]
            [msg_size,] = struct.unpack('<q', size_buf)
            if (data_len >= msg_size + 8):
                msg = (data[7 : (7 + msg_size)]).decode().replace('\x00', '')
                self.q_recv.put(msg)
                del data[:(7 + msg_size + 1)]
                self.decode_data(data)

    def run_session(self):
        data = bytearray()  
        while self.is_socket_open:
            try:
                buffer = self.client_socket.recv(self.default_buflen)
            except:
                self.close_remove_session()
                return
            
            data.extend(buffer)
            self.decode_data(data)

            if len(data) == 0:
                self.run_model()
        
    def run_model(self):
        while not self.q_recv.empty():
            start_time = time.time()
            request_data = self.q_recv.get()
            request_flds =  request_data.split(';')

            if len(request_flds) != 2: 
                self.close_remove_session()
                return

            request_cmd = request_flds[0]
            request = request_flds[1]

            if request_cmd == cmd_heartbeat:
                self.send_data(cmd_heartbeat)
                continue

            if request_cmd == cmd_close_connection:
                self.close_remove_session()
                return

            if request_cmd == cmd_init_data:
                req_data = np.fromstring(request, dtype=float, sep=',')
                req_data_len = len(req_data)
                self.model_container.q_log_messages.put(f'{self.model_container.port}:{self.session_id} Indicator initialization with {req_data_len} bars')
                
                if (req_data_len < self.dataset_len):
                    self.data_queue.append(req_data)

                req_data_n = self.create_sliding_windows(req_data, self.dataset_len)
                prediction = self.model_container.predict(req_data_n)

                flattened_array = prediction.flatten()
                zeros_list = [0.0] * (self.dataset_len - 1) 
                response_list = zeros_list + flattened_array.tolist()
                response_str = ",".join(map(lambda x: "{:.5f}".format(x), response_list))

                self.send_data(response_str)

                end_time = time.time()
                self.model_container.q_log_messages.put(f'{self.model_container.port}:{self.session_id} Indicator initialization completed in {end_time - start_time:.6f} seconds')

                for item in req_data[-self.dataset_len:]:
                    self.data_queue.append(item)
                
                return

            if request_cmd == cmd_next_data_point:
                self.data_queue.append(float(request))
                if len(self.data_queue) < self.dataset_len:
                    self.send_data('0.0')
                    return

                req_data = np.array(self.data_queue)
                req_data_n = self.normalize_standard(req_data)
                prediction = self.model_container.predict(req_data_n)
                self.send_data("{:.5f}".format(prediction[0][0]))
                end_time = time.time()
                if self.model_container.allow_log_latencies():
                    self.model_container.q_log_messages.put(f'{self.model_container.port}:{self.session_id} Single prediciton {end_time - start_time:.6f} seconds')

    def close_remove_session(self):
        if self.is_socket_open:
            self.is_socket_open = False
            self.client_socket.close()
            self.model_container.remove_stopped_sessions(self.session_id)

    def on_stop(self):
        self.is_socket_open = False
        self.send_data(cmd_close_connection)
        self.client_socket.close()

class ModelContainer:
    def __init__(self, port, model_path, model_full_name, q_state, q_log_messages, allow_log_latencies):
        self.is_active = True

        self.server_socket = None
        self.host = '127.0.0.1'
        self.port = port
        self.model_path = model_path
        self.model_full_name = model_full_name

        self.lock = threading.Lock()
        self.q_state = q_state
        self.q_log_messages = q_log_messages
        self.allow_log_latencies = allow_log_latencies

        self.session_id = 0
        self.sessions = {}
        self.add_remove_session_lock = threading.Lock()

        self.q_log_messages.put(f'Model container for {model_full_name} model has been created on {port} port')
        
    def predict(self, input_data):
        with self.lock:
            return self.model.predict(input_data, verbose=0)

    def run_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.q_state.put(f"{self.port},Model loaded. Waiting connection...")
        self.q_log_messages.put(f"{self.port} Socket server started. Waiting connection...")

        try:
            while self.is_active:
                client_socket, client_address = self.server_socket.accept()
                with self.add_remove_session_lock:
                    self.sessions[self.session_id] = SessionContainer(self.session_id, self, self.dataset_len, client_socket, client_address)
                client_thread = threading.Thread(target=self.sessions[self.session_id].run_session, args=())
                client_thread.daemon = True
                client_thread.start()

                self.session_id += 1
                self.q_state.put(f"{self.port},Model loaded. Indicators connected: {len(self.sessions)}")
                self.q_log_messages.put(f"{self.port} New session initialized. Indicators connected: {len(self.sessions)}")
        except:
            self.stop_container() 

    def start_container(self):
        self.q_state.put(f"{self.port},Loading model...")
        self.q_log_messages.put(f"{self.port} Loading model...")

        self.model = load_model(self.model_path)
        self.dataset_len:int = self.model.input_shape[1]
        self.scaler = StandardScaler()
        self.data_queue = deque(maxlen = self.dataset_len)
        
        self.q_state.put(f"{self.port},Model loaded. Starting socket server...")
        self.q_log_messages.put(f"{self.port} Model loaded. Starting socket server...")
        self.th_read = threading.Thread(target=self.run_server, args=())
        self.th_read.start()
    
    def stop_container(self):
        if self.is_active:
            self.is_active = False
            for s_id in self.sessions:
                self.q_log_messages.put(f"{self.port} Disconnecting session {s_id}")
                self.sessions[s_id].on_stop()
            self.sessions.clear()

            if self.server_socket != None: 
                self.server_socket.close()
                self.q_log_messages.put(f"{self.port} Closing connection")

            self.q_log_messages.put(f"{self.port} Model container has been stopped and deleted")
            self.q_state.put(f"{self.port},Stopped")

    def remove_stopped_sessions(self, s_id):
        with self.add_remove_session_lock:
            if s_id in self.sessions: 
                    self.sessions.pop(s_id)
                    self.q_state.put(f"{self.port},Model loaded. Indicators connected: {len(self.sessions)}")
                    self.q_log_messages.put(f"{self.port} Session deleted. Indicators connected: {len(self.sessions)}")

    def on_closing(self):
        self.stop_container() 
