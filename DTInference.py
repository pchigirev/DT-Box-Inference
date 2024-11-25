"""
DT-Box-Inference
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import webbrowser

import queue
from DTBoxTree import *
from DTBoxLogger import *
from ModelContainer import *

# pyinstaller --clean --noconsole --onedir --hiddenimport numpy --hiddenimport tensorflow --hiddenimport keras --hiddenimport scikit-learn --icon "Logo2.ico" --add-data "Logo2.ico;." --name "DT-Box-Inference" DTInference.py

script_dir = os.path.dirname(os.path.realpath(__file__))
icon_path = os.path.join(script_dir, 'Logo2.ico')

class DTBoxInference:
    def __init__(self):
        self.containers = {}
        self.start_port = 16505

        self.q_state = queue.Queue()
        self.q_log_messages = queue.Queue()

        self.is_shut_down = False

        self.root = tk.Tk()
        self.root.title("DT-Box-Inference")
        self.root.resizable(False, False)

        self.icon_path = icon_path
        self.root.iconbitmap(self.icon_path)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.sm_str_var = tk.StringVar()
        self.tf_str_var = tk.StringVar()
        self.md_str_var = tk.StringVar()
        self.pr_str_var = tk.StringVar()
        self.st_str_var = tk.StringVar()

        self.style = ttk.Style()
        self.style.theme_use("vista")

        self.always_on_top = tk.BooleanVar()
        self.always_on_top.set(True)
        self.root.wm_attributes("-topmost", 1)

        self.dtbox_tree = DTBoxTree(self.root, "Models:", 189)
        
        dtbox_tree_config = DTBoxTreeConfig()
        dtbox_tree_config.add_column("Model Name", 200)
        dtbox_tree_config.add_column("Port", 80)
        dtbox_tree_config.add_column("Status", 261)
        self.dtbox_tree.create_tree(dtbox_tree_config)

        dtbox_tree_config.add_button("Add Model", lambda:self.on_add_model_button(), 14, 10)
        dtbox_tree_config.add_button("Remove Model", lambda:self.on_del_model_button(), 14, 10)
        self.dtbox_tree.create_buttons(dtbox_tree_config)

        self.logger = DTBoxLogger(self.root, "Inference Log:", 188)
        self.logger.create_log_window()
        self.logger.create_buttons()

        self.frame_footer = ttk.Frame(self.root)
        self.checkbutton = tk.Checkbutton(self.frame_footer, text="Always on Top", variable=self.always_on_top, command=self.set_always_on_top)
        self.checkbutton.pack(side='left')
        self.link = tk.Label(self.frame_footer, text="https://pavelchigirev.com/", fg="blue", cursor="hand2")
        self.link.pack(side='left', padx=(300, 0))
        self.link.bind("<Button-1>", self.link_callback)

        # Grid layout
        self.dtbox_tree.frame_buttons.grid(row=0, column=0, sticky='w', padx=10, pady=(10, 7))
        self.dtbox_tree.frame_tree.grid(row=1, column=0, sticky='w', padx=10, pady=(0, 7))
        self.logger.frame_buttons.grid(row=2, column=0, sticky='w', padx=10, pady=(0, 7))
        self.logger.frame_log.grid(row=3, column=0, sticky='w', padx=10, pady=(0, 7))
        self.frame_footer.grid(row=4, padx=10, pady=(0, 3), sticky='w')

        self.text_handler = LogHandler(self.logger.text)
        self.text_handler.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s.%(msecs)03d: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.text_handler.setFormatter(self.formatter)

        # Get the logger and set its handler
        self.dtlogger = logging.getLogger() 
        self.dtlogger.propagate = True
        self.dtlogger.addHandler(self.text_handler)
        self.dtlogger.setLevel(logging.INFO)
        self.q_log_messages.put("Welcome to DT-Box-Inference")

        self.root.after(100, self.process_states)
        self.root.after(200, self.process_log_messages)
        self.root.mainloop()

    def link_callback(self, event):
        webbrowser.open_new(r"https://pavelchigirev.com/")

    def set_always_on_top(self):
        self.root.wm_attributes("-topmost", self.always_on_top.get())

    def allow_log_latencies(self):
        return self.logger.show_latencies.get()

    def process_states(self):
        # Model states
        while not self.q_state.empty():
            state = self.q_state.get()
            state_vals = state.split(',')
            item_ids = self.dtbox_tree.tree.get_children()
            for item_id in item_ids:
                item_values = (self.dtbox_tree.tree.item(item_id))['values']
                if (item_values[1] == int(state_vals[0])):
                    self.dtbox_tree.tree.set(item_id, 3, state_vals[1])

        self.root.after(100, self.process_states)   

    def process_log_messages(self):
        while not self.q_log_messages.empty():
            msg = self.q_log_messages.get()
            self.dtlogger.info(msg)
        
        self.root.after(200, self.process_log_messages)

    def on_add_model_button(self):
        filename = filedialog.askopenfilename(filetypes=(("Keras model files", "*.keras"),))
        if filename:
            file_with_extension = os.path.basename(filename)
            file_without_extension = os.path.splitext(file_with_extension)[0]

            container = ModelContainer(self.start_port, filename, file_with_extension, self.q_state, self.q_log_messages, self.allow_log_latencies)
            self.containers[str(self.start_port)] = container
            self.start_port += 1

            self.dtbox_tree.tree.insert('', 'end', values=[file_without_extension, container.port, 'Added'])
            
            self.th_cc = threading.Thread(target=container.start_container, args=())
            self.th_cc.start()

    def on_start_model_button(self):
        selection = self.dtbox_tree.tree.selection()
        if (len(selection) == 0):
            return
        item = selection[0]
        item_values = self.dtbox_tree.tree.item(item, 'values')
        if item_values[1] not in self.containers.keys(): raise Exception("Cannot find container")
        self.th_cc = threading.Thread(target=self.containers[item_values[1]].start_container, args=())
        self.th_cc.start()

    def on_stop_model_button(self):
        pass

    def on_del_model_button(self):
        selection = self.dtbox_tree.tree.selection()
        if (len(selection) == 0):
            return
        
        item = selection[0]
        item_values = self.dtbox_tree.tree.item(item, 'values')
        if item_values[1] not in self.containers.keys(): raise Exception("Cannot find container")

        response = messagebox.askyesno("Confirm Model Removal", "Are you sure you want to stop model inference?")
        if response:
            container = self.containers.pop(item_values[1])
            self.dtbox_tree.tree.delete(selection)
                                    
            self.th_cc = threading.Thread(target=container.stop_container, args=())
            self.th_cc.start()

    def on_closing(self):
        stop_ths = []
        for key in self.containers:
            th = threading.Thread(target=self.containers[key].on_closing, args=())
            th.start()
            stop_ths.append(th)

        for th in stop_ths:
            th.join()

        self.root.destroy()

if __name__ == '__main__': DTBoxInference()