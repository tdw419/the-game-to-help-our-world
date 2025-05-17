# pixel-vault/restore_batch.py

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from decoder import decode_image_to_file

def batch_restore():
    image_folder = filedialog.askdirectory(title="Select Folder Containing Backup Images")
    if not image_folder:
        return

    output_folder = filedialog.askdirectory(title="Select Output Folder for Restored Files")
    if not output_folder:
        return

    restored_count = 0

    for filename in os.listdir(image_folder):
        if filename.endswith(".png"):
            input_path = os.path.join(image_folder, filename)
            output_filename = filename.rsplit(".png", 1)[0]  # Remove .png
            output_path = os.path.join(output_folder, output_filename)

            try:
                decode_image_to_file(input_path, output_path, decompress=True)
                restored_count += 1
            except Exception as e:
                print(f"Failed to restore {filename}: {e}")

    messagebox.showinfo("Restore Complete", f"Restored {restored_count} files.")

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    batch_restore()
