"""
DT-Box
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

import logging
import tkinter as tk
from tkinter import ttk, font

class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, message):
        if message.strip() != "":
            self.logger.log(self.log_level, message.strip())

    def flush(self):
        pass

class LogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.after(0, self.update_text_widget, msg)

    def update_text_widget(self, msg):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.configure(state='disabled')
        self.text_widget.yview(tk.END)

class DTBoxLogger:
    def add_row(self):
        self.log_height += 1
        self.text.configure(height=self.log_height)

    def delete_row(self):
        if (self.log_height >= 2):
            self.log_height -= 1
            self.text.configure(height=self.log_height)

    def toggle(self):
        if self.frame_log.grid_info():
            self.frame_log.grid_remove()
        else:
            self.frame_log.grid()

    def create_log_window(self):
        self.frame_log = ttk.Frame(self.root)
        self.log_height = 15
        custom_font = font.Font(family="Consolas", size=10)
        self.text = tk.Text(self.frame_log, state='disabled', wrap='none', height=self.log_height, width=77, font=custom_font)
        
        # Create a vertical scrollbar
        self.v_scroll = tk.Scrollbar(self.frame_log, orient='vertical', command=self.text.yview)
        self.v_scroll.pack(side='right', fill='y')
        
        # Create a horizontal scrollbar
        self.h_scroll = tk.Scrollbar(self.frame_log, orient='horizontal', command=self.text.xview)
        self.h_scroll.pack(side='bottom', fill='x')
        
        # Configure the text widget to use scrollbars
        self.text.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        self.text.pack(side='left', fill='both', expand=True)

    def create_buttons(self):
        self.frame_buttons = ttk.Frame(self.root)
        self.label = ttk.Label(self.frame_buttons, text=self.name)
        self.label.pack(side="left")
        self.checkbutton = tk.Checkbutton(self.frame_buttons, text="Log single prediction time", variable=self.show_latencies)
        self.checkbutton.pack(side="left", padx=(10, 0))

        self.tree_height_ind = 4
        self.add_row2_btn = ttk.Button(self.frame_buttons, text=" + ", command=self.add_row, width=3)
        self.detele_row2_btn = ttk.Button(self.frame_buttons, text=" - ", command=self.delete_row, width=3)
        self.exp_coll2_button = ttk.Button(self.frame_buttons, text="S/H", command=self.toggle, width=4)

        self.add_row2_btn.pack(side="left", padx=(self.indent, 0))
        self.detele_row2_btn.pack(side="left", padx=(5, 0))
        self.exp_coll2_button.pack(side="left", padx=(5, 0))

    def __init__(self, root, label_text, indent): 
        self.root = root
        self.name = label_text
        self.show_latencies = tk.BooleanVar()
        self.show_latencies.set(True)
        self.indent = indent