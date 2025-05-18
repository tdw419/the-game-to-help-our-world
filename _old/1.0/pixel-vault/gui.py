import tkinter as tk
from tkinter import filedialog, messagebox
from encoder import encode_file_to_image
from decoder import decode_image_to_file
from metadata import generate_metadata, save_metadata
import subprocess
import os
import csv
import time

LOG_FILE = "pixel_vault_log.csv"

def log_action(action, file):
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([time.ctime(), action, file])

def encode_action():
    file_path = filedialog.askopenfilename(title="Select File to Backup")
    if not file_path:
        return

    output_path = filedialog.asksaveasfilename(defaultextension=".png",
                                               filetypes=[("PNG Image", "*.png")],
                                               title="Save Backup Image As")
    if not output_path:
        return

    try:
        encode_file_to_image(file_path, output_path, compress=True)
        metadata = generate_metadata(file_path)
        save_metadata(metadata, output_path)
        log_action("Backup", file_path)
        messagebox.showinfo("Success", f"Backup saved to {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def decode_action():
    image_path = filedialog.askopenfilename(title="Select Backup Image",
                                            filetypes=[("PNG Image", "*.png")])
    if not image_path:
        return

    output_path = filedialog.asksaveasfilename(title="Restore File As")
    if not output_path:
        return

    try:
        decode_image_to_file(image_path, output_path, decompress=True)
        log_action("Restore", output_path)
        messagebox.showinfo("Success", f"File restored to {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def open_folder_sync():
    subprocess.Popen(["python", "folder_sync_gui.py"])

def open_benchmark_tool():
    subprocess.Popen(["python", "backup_benchmark.py"])

def batch_backup():
    folder_path = filedialog.askdirectory(title="Select Folder to Backup")
    if not folder_path:
        return

    output_folder = filedialog.askdirectory(title="Select Output Folder for Backups")
    if not output_folder:
        return

    try:
        for filename in os.listdir(folder_path):
            src_path = os.path.join(folder_path, filename)
            if os.path.isfile(src_path):
                output_path = os.path.join(output_folder, filename + ".png")
                encode_file_to_image(src_path, output_path, compress=True)
                metadata = generate_metadata(src_path)
                save_metadata(metadata, output_path)
                log_action("Batch Backup", src_path)
        messagebox.showinfo("Success", "Batch backup complete.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def open_batch_restore():
    subprocess.Popen(["python", "restore_batch.py"])

def open_log_viewer():
    subprocess.Popen(["python", "log_viewer.py"])

def open_packager():
    subprocess.Popen(["python", "packager.py"])

# GUI setup
root = tk.Tk()
root.title("Pixel Vault Backup Utility")
root.geometry("400x450")

label = tk.Label(root, text="Pixel Vault", font=("Arial", 16))
label.pack(pady=20)

encode_btn = tk.Button(root, text="Backup File to Image", command=encode_action, width=30)
encode_btn.pack(pady=5)

decode_btn = tk.Button(root, text="Restore File from Image", command=decode_action, width=30)
decode_btn.pack(pady=5)

batch_btn = tk.Button(root, text="Batch Backup Folder", command=batch_backup, width=30)
batch_btn.pack(pady=5)

restore_btn = tk.Button(root, text="Batch Restore Folder", command=open_batch_restore, width=30)
restore_btn.pack(pady=5)

sync_btn = tk.Button(root, text="Folder Sync Tool", command=open_folder_sync, width=30)
sync_btn.pack(pady=5)

benchmark_btn = tk.Button(root, text="Run Backup Benchmark", command=open_benchmark_tool, width=30)
benchmark_btn.pack(pady=5)

log_btn = tk.Button(root, text="View Backup Log", command=open_log_viewer, width=30)
log_btn.pack(pady=5)

packager_btn = tk.Button(root, text="Build EXE Package", command=open_packager, width=30)
packager_btn.pack(pady=5)

root.mainloop()
