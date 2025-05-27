
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional

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

        self.status_label = tk.Label(root, text="", fg="white", bg="black")
        self.status_label.pack(fill=tk.X)

        root.bind("<Key>", self.on_key_press)

        # Control buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        tk.Button(self.button_frame, text="Clear", command=self.reset).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save", command=self.save_canvas).pack(side=tk.LEFT)

    def __repr__(self) -> str:
        """Return a string representation of the current canvas state."""
        return f"CanvasTerminal(cursor=({self.cursor_x},{self.cursor_y}), memory={len(self.memory)} blocks)"

    def calculate_color(self, ascii_val: int) -> str:
        """Calculate a hex color string based on ASCII value."""
        r = (ascii_val * 3) % 256
        g = (ascii_val * 5) % 256
        b = (ascii_val * 7) % 256
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw_block(self, x: int, y: int, color: str, char: str) -> None:
        """Draw a colored block and character on the canvas."""
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
        """Update the cursor position for the next character."""
        self.cursor_x += CHAR_SIZE
        if self.cursor_x > CANVAS_WIDTH - CHAR_SIZE:
            self.cursor_x = CURSOR_START_X
            self.cursor_y += CHAR_SIZE

        if self.cursor_y > CANVAS_HEIGHT - CHAR_SIZE:
            self.cursor_y = CURSOR_START_Y

    def on_key_press(self, event: tk.Event) -> None:
        """Handle key press events and update the canvas."""
        try:
            if event.char and event.char.isprintable():
                ascii_val = ord(event.char)
                hex_color = self.calculate_color(ascii_val)
                self.draw_block(self.cursor_x, self.cursor_y, hex_color, event.char)
                self.memory.append((self.cursor_x, self.cursor_y, event.char, hex_color))
                self.undo_stack.append((self.cursor_x, self.cursor_y, event.char, hex_color))
                self.update_cursor()
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}", fg="red")

    def reset(self) -> None:
        """Reset the canvas to its initial state."""
        self.canvas.delete("all")
        self.cursor_x = CURSOR_START_X
        self.cursor_y = CURSOR_START_Y
        self.memory.clear()
        self.undo_stack.clear()
        self.status_label.config(text="Canvas reset.", fg="white")

    def save_canvas(self) -> None:
        """Prompt user to save canvas as PNG or PS format."""
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
    root.title("Canvas Terminal v0.3")
    app = CanvasTerminal(root)
    root.mainloop()
