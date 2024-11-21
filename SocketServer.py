"""
DT-Box
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

from socket import *
import struct
from time import sleep
import threading
from queue import Queue

default_buflen = 1024

class SocketSrv:
    def send_data(self, msg):
        msg_size = struct.pack('<q', len(msg))
        data = msg_size + msg.encode()

        try:
            self.client.send(data)
        except:
            self.is_client_set = False
            self.serv.close()
            return

    def process_q_recv_sync(self, q_recv:Queue, cmd_proc_func):
        data = bytearray()  
        while (self.is_client_set):
            try:
                buffer = self.client.recv(default_buflen)
            except:
                self.is_client_set = False
                self.serv.close()
                return
            
            data.extend(buffer)
            self.decode_data(data, q_recv)

            if len(data) == 0:
                cmd_proc_func()

    def process_q_recv(self, q_recv:Queue):
        data = bytearray()  
	    
        while (self.is_client_set):
            try:
                buffer = self.client.recv(default_buflen)
            except:
                self.is_client_set = False
                self.serv.close()
                return
            
            data.extend(buffer)
            self.decode_data(data, q_recv)
    
    def decode_data(self, data:bytearray, q_recv:Queue):
        data_len = len(data)
        if (data_len >= 8):
            size_buf = data[0:8]
            [msg_size,] = struct.unpack('<q', size_buf)
            if (data_len >= msg_size + 8):
                msg = (data[7 : (7 + msg_size)]).decode().replace('\x00', '')
                q_recv.put(msg)
                del data[:(7 + msg_size + 1)]
                self.decode_data(data, q_recv)

    def __init__(self, host, port, ) -> None:
        self.is_client_set = False
        self.host = host
        self.port = port

        self.serv = None

    def accept_client(self) -> bool:
        try:
            self.serv = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
            self.serv.bind((self.host, self.port))
            self.serv.listen(1)
            self.client, self.address = self.serv.accept()
        
            # read init info
            self.client.setblocking(True) 
            self.is_client_set = True
            return True

        except:
            # process particular exceptions
            return False

    def disconnect(self):
        if (self.is_client_set):
            self.is_client_set = False
            self.serv.close()
            return

    def process_q_send(self, q_send:Queue):
        while True:
            if (not self.is_client_set):
                return
        
            while (not q_send.empty()):
                cmd = q_send.get()
                self.send_data(cmd)
            
            sleep(0.1)

    def shutdown(self):
        if (self.serv != None):
            if (self.is_client_set):
                self.serv.shutdown(SHUT_RDWR)
            self.serv.close()

if __name__ == "__main__":
    s = SocketSrv('127.0.0.1', 17500)
    s.accept_client()
    print('Client connected')

    def read_data():
        while True:
            msg = s.receive_data()
            print(msg)
            s.send_data('Rcvd: ' + msg)

    th_read = threading.Thread(target=read_data)
    th_read.start()

    th_read.join()
