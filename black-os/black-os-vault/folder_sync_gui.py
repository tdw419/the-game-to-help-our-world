# black-vault/folder_sync_gui.py

import os
import tkinter as tk
from tkinter import filedialog, ttk
from encoder import encode_file_to_image

class FolderSyncApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Pixel Vault Folder Sync")
        self.master.geometry("800x500")

        self.src_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        # Folder selectors
        top_frame = tk.Frame(self.master)
        top_frame.pack(pady=10, fill=tk.X)

        tk.Label(top_frame, text="Source Folder:").grid(row=0, column=0, sticky='e')
        tk.Entry(top_frame, textvariable=self.src_folder, width=60).grid(row=0, column=1)
        tk.Button(top_frame, text="Browse", command=self.browse_src).grid(row=0, column=2)

        tk.Label(top_frame, text="Backup Folder:").grid(row=1, column=0, sticky='e')
        tk.Entry(top_frame, textvariable=self.dest_folder, width=60).grid(row=1, column=1)
        tk.Button(top_frame, text="Browse", command=self.browse_dest).grid(row=1, column=2)

        # File table
        self.tree = ttk.Treeview(self.master, columns=("status"), show="headings")
        self.tree.heading("status", text="File")
        self.tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Buttons
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Compare Folders", command=self.compare_folders).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Backup Selected Files", command=self.backup_selected).pack(side=tk.LEFT, padx=5)

    def browse_src(self):
        folder = filedialog.askdirectory()
        if folder:
            self.src_folder.set(folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def compare_folders(self):
        self.tree.delete(*self.tree.get_children())
        src_files = os.listdir(self.src_folder.get())
        dest_files = os.listdir(self.dest_folder.get())
        for f in src_files:
            if f + ".png" in dest_files:
                status = "Backed up"
            else:
                status = "Needs backup"
            self.tree.insert("", "end", values=(f,), tags=(status,))

        self.tree.tag_configure("Needs backup", background="lightyellow")
        self.tree.tag_configure("Backed up", background="lightgreen")

    def backup_selected(self):
        selected = self.tree.selection()
        for item in selected:
            filename = self.tree.item(item, "values")[0]
            src_path = os.path.join(self.src_folder.get(), filename)
            dest_path = os.path.join(self.dest_folder.get(), filename + ".png")
            encode_file_to_image(src_path, dest_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderSyncApp(root)
    root.mainloop()
