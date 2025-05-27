
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import io

class CanvasTerminal:
    def __init__(self, root):
        self.root = root
        self.width = 800
        self.height = 600
        self.char_size = 20
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, bg='black')
        self.canvas.pack()

        self.cursor_x = 10
        self.cursor_y = 10
        self.memory = []
        self.font = ("Courier", 10)

        root.bind("<Key>", self.on_key_press)

        # Control buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        tk.Button(self.button_frame, text="Clear", command=self.clear_canvas).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save", command=self.save_canvas).pack(side=tk.LEFT)

    def on_key_press(self, event):
        if event.char and event.char.isprintable():
            ascii_val = ord(event.char)
            r = (ascii_val * 3) % 256
            g = (ascii_val * 5) % 256
            b = (ascii_val * 7) % 256
            hex_color = f'#{r:02x}{g:02x}{b:02x}'

            # Draw background block
            self.canvas.create_rectangle(
                self.cursor_x, self.cursor_y,
                self.cursor_x + self.char_size, self.cursor_y + self.char_size,
                fill=hex_color, outline=hex_color
            )

            # Draw character
            self.canvas.create_text(
                self.cursor_x + 2, self.cursor_y + 2,
                anchor='nw', text=event.char,
                fill='white', font=self.font
            )

            self.memory.append((self.cursor_x, self.cursor_y, event.char, hex_color))

            self.cursor_x += self.char_size
            if self.cursor_x > self.width - self.char_size:
                self.cursor_x = 10
                self.cursor_y += self.char_size

            if self.cursor_y > self.height - self.char_size:
                self.cursor_y = 10

    def clear_canvas(self):
        self.canvas.delete("all")
        self.cursor_x = 10
        self.cursor_y = 10
        self.memory = []

    def save_canvas(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PostScript files", "*.ps")])
        if file_path:
            self.canvas.postscript(file=file_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Canvas Terminal v0.1")
    app = CanvasTerminal(root)
    root.mainloop()
