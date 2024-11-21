"""
DT-Box
Pavel Chigirev, pavelchigirev.com, 2023-2024
See LICENSE.txt for details
"""

from tkinter import ttk

class DTBoxTreeConfig:
    def __init__(self):
        self.columns = []
        self.buttons = []

    def add_column(self, name:str, width:int):
        self.columns.append([name, width])

    def add_button(self, name:str, function:callable, width:int, padx:int):
        self.buttons.append([name, function, width, padx])

class DTBoxTree:
    def add_row(self):
        self.tree_height_ind += 1
        self.tree.configure(height=self.tree_height_ind)

    def delete_row(self):
        if (self.tree_height_ind >= 2):
            self.tree_height_ind -= 1
            self.tree.configure(height=self.tree_height_ind)

    def toggle(self):
        if self.frame_tree.grid_info():
            self.frame_tree.grid_remove()
        else:
            self.frame_tree.grid()

    def create_tree(self, dtbox_tree_config):
        columns = dtbox_tree_config.columns
        self.frame_tree = ttk.Frame(self.root)
        num_columns = len(columns)
        columns_str_idx = [str(i) for i in range(1, num_columns + 1)]
        self.tree_height_ind = 5
        self.tree = ttk.Treeview(self.frame_tree, columns=columns_str_idx, show="headings", height=self.tree_height_ind)
        for i in range(num_columns):
            self.tree.heading(i+1, text=columns[i][0])
            self.tree.column(i+1, width=columns[i][1])

        self.scrollbar = ttk.Scrollbar(self.frame_tree, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side="left")

    def create_buttons(self, dtbox_tree_config):
        buttons = dtbox_tree_config.buttons
        self.frame_buttons = ttk.Frame(self.root)
        self.label = ttk.Label(self.frame_buttons, text=self.name)
        self.label.pack(side="left")

        for btn in buttons:
            button = ttk.Button(self.frame_buttons, text=btn[0], command=btn[1], width=btn[2])
            button.pack(side="left", padx=(btn[3], 0))

        self.add_row2_btn = ttk.Button(self.frame_buttons, text=" + ", command=self.add_row, width=3)
        self.detele_row2_btn = ttk.Button(self.frame_buttons, text=" - ", command=self.delete_row, width=3)
        self.exp_coll2_button = ttk.Button(self.frame_buttons, text="S/H", command=self.toggle, width=4)

        self.add_row2_btn.pack(side="left", padx=(self.indent, 0))
        self.detele_row2_btn.pack(side="left", padx=(5, 0))
        self.exp_coll2_button.pack(side="left", padx=(5, 0))

    def __init__(self, root, label_text, indent): 
        self.root = root
        self.name = label_text
        self.indent = indent