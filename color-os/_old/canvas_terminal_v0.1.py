import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageGrab
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
        self.font = ("Courier", 14)

        root.bind("<Key>", self.on_key_press)

        # Control buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        tk.Button(self.button_frame, text="Clear", command=self.clear_canvas).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save as PNG", command=self.save_canvas_as_png).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save as PS", command=self.save_canvas_as_ps).pack(side=tk.LEFT)

    def calculate_color(self, ascii_val):
        r = (ascii_val * 3) % 256
        g = (ascii_val * 5) % 256
        b = (ascii_val * 7) % 256
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw_block(self, x, y, color, char):
        self.canvas.create_rectangle(
            x, y,
            x + self.char_size, y + self.char_size,
            fill=color, outline=color
        )
        self.canvas.create_text(
            x + 2, y + 2,
            anchor='nw', text=char,
            fill='white', font=self.font
        )

    def update_cursor(self):
        self.cursor_x += self.char_size
        if self.cursor_x > self.width - self.char_size:
            self.cursor_x = 10
            self.cursor_y += self.char_size

        if self.cursor_y > self.height - self.char_size:
            self.cursor_y = 10

    def on_key_press(self, event):
        if event.char and event.char.isprintable():
            ascii_val = ord(event.char)
            hex_color = self.calculate_color(ascii_val)

            self.draw_block(self.cursor_x, self.cursor_y, hex_color, event.char)
            self.memory.append((self.cursor_x, self.cursor_y, event.char, hex_color))

            self.update_cursor()

    def clear_canvas(self):
        self.canvas.delete("all")
        self.cursor_x = 10
        self.cursor_y = 10
        self.memory = []

    def save_canvas_as_png(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            x = self.root.winfo_rootx() + self.canvas.winfo_x()
            y = self.root.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            ImageGrab.grab().crop((x,y,x1,y1)).save(file_path)

    def save_canvas_as_ps(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PostScript files", "*.ps")])
        if file_path:
            self.canvas.postscript(file=file_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Canvas Terminal v0.1")
    app = CanvasTerminal(root)
    root.mainloop()
