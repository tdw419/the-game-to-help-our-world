import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional, Dict

# --- Global Constants and Settings ---
SETTINGS = {
    "canvas_width": 800,
    "canvas_height": 600,
    "char_size": 20,
    "font": ("Courier", 14),
    "cursor_start_x": 10,
    "cursor_start_y": 10,
    "max_undo_redo": 1000 # Limit memory size for performance
}

# --- 1. TerminalCanvas Class ---
class TerminalCanvas:
    """Manages all drawing operations and visual state on the Tkinter canvas."""
    def __init__(self, master: tk.Tk, canvas_width: int, canvas_height: int, char_size: int, font: Tuple[str, int]) -> None:
        self.canvas = tk.Canvas(master, width=canvas_width, height=canvas_height, bg='black')
        self.canvas.pack()
        self.char_size = char_size
        self.font = font
        self.status_label = tk.Label(master, text="Welcome to Canvas Terminal!", fg="white", bg="black")
        self.status_label.pack(fill=tk.X)
        self.blink_id = None # To store after() job ID for blinking cursor

    def calculate_color(self, ascii_val: int) -> str:
        """Calculate a hex color string based on ASCII value."""
        r = (ascii_val * 3) % 256
        g = (ascii_val * 5) % 256
        b = (ascii_val * 7) % 256
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw_block(self, x: int, y: int, color: str, char: str) -> None:
        """Draw a colored block and character on the canvas."""
        try:
            self.canvas.create_rectangle(
                x, y, x + self.char_size, y + self.char_size,
                fill=color, outline=color, tags="char_block"
            )
            self.canvas.create_text(
                x + 2, y + 2,
                anchor='nw', text=char,
                fill='white', font=self.font, tags="char_text"
            )
        except Exception as e:
            self.show_status(f"Draw Error: {str(e)}", "red")

    def draw_cursor(self, x: int, y: int) -> None:
        """Draws or moves a blinking cursor indicator."""
        self.canvas.delete("cursor") # Remove previous cursor
        self.canvas.create_rectangle(
            x, y, x + self.char_size - 2, y + self.char_size - 2,
            outline="white", width=1, tags="cursor"
        )
        # Restart blinking
        if self.blink_id:
            self.canvas.after_cancel(self.blink_id)
        self.blink_id = self.canvas.after(500, self._blink_cursor)

    def _blink_cursor(self) -> None:
        """Makes the cursor blink."""
        if self.canvas.find_withtag("cursor"):
            current_state = self.canvas.itemcget("cursor", "state")
            new_state = "hidden" if current_state == "normal" else "normal"
            self.canvas.itemconfigure("cursor", state=new_state)
            self.blink_id = self.canvas.after(500, self._blink_cursor) # Reschedule blink

    def clear_all(self) -> None:
        """Clears all items from the canvas."""
        self.canvas.delete("all")
        if self.blink_id:
            self.canvas.after_cancel(self.blink_id) # Stop blinking when cleared

    def clear_characters(self) -> None:
        """Clears only character-related items from the canvas."""
        self.canvas.delete("char_block", "char_text")

    def show_status(self, message: str, color: str = "white") -> None:
        """Updates the status label."""
        self.status_label.config(text=message, fg=color)

    def scroll_content(self, offset_y: int) -> None:
        """Moves all canvas content vertically."""
        self.canvas.move("all", 0, offset_y)

    def get_canvas_dims(self) -> Tuple[int, int]:
        """Returns canvas width and height."""
        return self.canvas.winfo_width(), self.canvas.winfo_height()

    def save_to_file(self, root_window: tk.Tk) -> None:
        """Save canvas as PNG or PS file."""
        try:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                     filetypes=[("PNG files", "*.png"), ("PostScript files", "*.ps")])
            if file_path:
                if file_path.endswith(".png"):
                    # Get exact canvas coordinates on screen
                    x = root_window.winfo_rootx() + self.canvas.winfo_x()
                    y = root_window.winfo_rooty() + self.canvas.winfo_y()
                    x1 = x + self.canvas.winfo_width()
                    y1 = y + self.canvas.winfo_height()
                    ImageGrab.grab().crop((x, y, x1, y1)).save(file_path)
                    self.show_status(f"Saved PNG to {file_path}", "green")
                elif file_path.endswith(".ps"):
                    self.canvas.postscript(file=file_path)
                    self.show_status(f"Saved PS to {file_path}", "green")
        except Exception as e:
            self.show_status(f"Save Error: {str(e)}", "red")

