# black-vault/log_viewer.py

import tkinter as tk
from tkinter import ttk
import os
import csv

LOG_FILE = "pixel_vault_log.csv"

class LogViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Pixel Vault Log Viewer")
        self.master.geometry("600x400")

        self.tree = ttk.Treeview(master, columns=("time", "action", "file"), show="headings")
        self.tree.heading("time", text="Time")
        self.tree.heading("action", text="Action")
        self.tree.heading("file", text="File")
        self.tree.pack(expand=True, fill=tk.BOTH)

        self.load_log()

    def load_log(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 3:
                        self.tree.insert("", "end", values=(row[0], row[1], row[2]))

if __name__ == '__main__':
    root = tk.Tk()
    app = LogViewer(root)
    root.mainloop()
