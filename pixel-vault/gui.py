import tkinter as tk
from tkinter import filedialog, messagebox
from encoder import encode_file_to_image
from decoder import decode_image_to_file

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
        messagebox.showinfo("Success", f"File restored to {output_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# GUI setup
root = tk.Tk()
root.title("Pixel Vault Backup Utility")
root.geometry("400x200")

label = tk.Label(root, text="Pixel Vault", font=("Arial", 16))
label.pack(pady=20)

encode_btn = tk.Button(root, text="Backup File to Image", command=encode_action, width=30)
encode_btn.pack(pady=10)

decode_btn = tk.Button(root, text="Restore File from Ima_
