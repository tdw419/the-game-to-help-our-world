
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple

# Constants
CANVAS_WIDTH: int = 800
CANVAS_HEIGHT: int = 600
CHAR_SIZE: int = 20
FONT = ("Courier", 14)
CURSOR_START_X: int = 10
CURSOR_START_Y: int = 10

class CanvasTerminal:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the canvas terminal environment."""
        self.root = root
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='black')
        self.canvas.pack()

        self.cursor_x: int = CURSOR_START_X
        self.cursor_y: int = CURSOR_START_Y
        self.memory: List[Tuple[int, int, str, str]] = []
        self.undo_stack: List[Tuple[int, int, str, str]] = []
        self.redo_stack: List[Tuple[int, int, str, str]] = []

        self.status_label = tk.Label(root, text="", fg="white", bg="black")
        self.status_label.pack(fill=tk.X)

        root.bind("<Key>", self.on_key_press)

        # Control buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        tk.Button(self.button_frame, text="Clear", command=self.reset).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Redo", command=self.redo).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save", command=self.save_canvas).pack(side=tk.LEFT)

    def __repr__(self) -> str:
        return f"CanvasTerminal(cursor=({self.cursor_x},{self.cursor_y}), memory={len(self.memory)} blocks)"

    def calculate_color(self, ascii_val: int) -> str:
        r = (ascii_val * 3) % 256
        g = (ascii_val * 5) % 256
        b = (ascii_val * 7) % 256
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw_block(self, x: int, y: int, color: str, char: str) -> None:
        self.canvas.create_rectangle(
            x, y, x + CHAR_SIZE, y + CHAR_SIZE,
            fill=color, outline=color
        )
        self.canvas.create_text(
            x + 2, y + 2,
            anchor='nw', text=char,
            fill='white', font=FONT
        )

    def update_cursor(self) -> None:
        self.cursor_x += CHAR_SIZE
        if self.cursor_x > CANVAS_WIDTH - CHAR_SIZE:
            self.cursor_x = CURSOR_START_X
            self.cursor_y += CHAR_SIZE

        if self.cursor_y > CANVAS_HEIGHT - CHAR_SIZE:
            self.cursor_y = CURSOR_START_Y

    def on_key_press(self, event: tk.Event) -> None:
        try:
            if event.char and event.char.isprintable():
                ascii_val = ord(event.char)
                hex_color = self.calculate_color(ascii_val)
                self.draw_block(self.cursor_x, self.cursor_y, hex_color, event.char)
                self.memory.append((self.cursor_x, self.cursor_y, event.char, hex_color))
                self.undo_stack.append((self.cursor_x, self.cursor_y, event.char, hex_color))
                self.redo_stack.clear()
                self.update_cursor()
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def redraw_memory(self) -> None:
        self.canvas.delete("all")
        for x, y, char, color in self.memory:
            self.draw_block(x, y, color, char)

    def undo(self) -> None:
        if self.memory:
            action = self.memory.pop()
            self.redo_stack.append(action)
            self.redraw_memory()
            self.status_label.config(text="Undo successful", fg="white")
        else:
            self.status_label.config(text="Nothing to undo", fg="yellow")

    def redo(self) -> None:
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.memory.append(action)
            self.draw_block(*action)
            self.status_label.config(text="Redo successful", fg="white")
        else:
            self.status_label.config(text="Nothing to redo", fg="yellow")

    def reset(self) -> None:
        self.canvas.delete("all")
        self.cursor_x = CURSOR_START_X
        self.cursor_y = CURSOR_START_Y
        self.memory.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.status_label.config(text="Canvas reset.", fg="white")

    def save_canvas(self) -> None:
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png"), ("PostScript files", "*.ps")])
            if file_path:
                if file_path.endswith(".png"):
                    x = self.root.winfo_rootx() + self.canvas.winfo_x()
                    y = self.root.winfo_rooty() + self.canvas.winfo_y()
                    x1 = x + self.canvas.winfo_width()
                    y1 = y + self.canvas.winfo_height()
                    ImageGrab.grab().crop((x, y, x1, y1)).save(file_path)
                    self.status_label.config(text=f"Saved PNG to {file_path}", fg="green")
                elif file_path.endswith(".ps"):
                    self.canvas.postscript(file=file_path)
                    self.status_label.config(text=f"Saved PS to {file_path}", fg="green")
        except Exception as e:
            self.status_label.config(text=f"Failed to save file: {str(e)}", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Canvas Terminal v0.4")
    app = CanvasTerminal(root)
    root.mainloop()
