
import tkinter as tk
from tkinter import filedialog
from PIL import ImageGrab
from typing import List, Tuple

# Constants
SETTINGS = {
    "canvas_width": 800,
    "canvas_height": 600,
    "char_size": 20,
    "font": ("Courier", 14),
    "cursor_start_x": 10,
    "cursor_start_y": 10,
}

class CanvasTerminal:
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the Canvas Terminal environment."""
        self.root = root
        self.canvas = tk.Canvas(root, width=SETTINGS["canvas_width"], height=SETTINGS["canvas_height"], bg='black')
        self.canvas.pack()

        self.cursor_x = SETTINGS["cursor_start_x"]
        self.cursor_y = SETTINGS["cursor_start_y"]
        self.memory: List[Tuple[int, int, str, str]] = []
        self.undo_stack: List[Tuple[int, int, str, str]] = []
        self.redo_stack: List[Tuple[int, int, str, str]] = []

        self.status_label = tk.Label(root, text="", fg="white", bg="black")
        self.status_label.pack(fill=tk.X)

        self.command_entry = tk.Entry(root, font=("Courier", 12), bg="black", fg="lime")
        self.command_entry.pack(fill=tk.X)
        self.command_entry.bind("<Return>", self.execute_command)

        root.bind("<Key>", self.on_key_press)

        # Buttons
        self.button_frame = tk.Frame(root)
        self.button_frame.pack()
        tk.Button(self.button_frame, text="Clear", command=self.reset).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Undo", command=self.undo).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Redo", command=self.redo).pack(side=tk.LEFT)
        tk.Button(self.button_frame, text="Save", command=self.save_canvas).pack(side=tk.LEFT)

    def calculate_color(self, ascii_val: int) -> str:
        """Calculate RGB color from ASCII value."""
        r = (ascii_val * 3) % 256
        g = (ascii_val * 5) % 256
        b = (ascii_val * 7) % 256
        return f'#{r:02x}{g:02x}{b:02x}'

    def draw_block(self, x: int, y: int, color: str, char: str) -> None:
        """Draw a colored block and character on the canvas."""
        self.canvas.create_rectangle(
            x, y, x + SETTINGS["char_size"], y + SETTINGS["char_size"],
            fill=color, outline=color
        )
        self.canvas.create_text(
            x + 2, y + 2,
            anchor='nw', text=char,
            fill='white', font=SETTINGS["font"]
        )

    def update_cursor(self) -> None:
        """Advance the cursor for next character."""
        self.cursor_x += SETTINGS["char_size"]
        if self.cursor_x > SETTINGS["canvas_width"] - SETTINGS["char_size"]:
            self.cursor_x = SETTINGS["cursor_start_x"]
            self.cursor_y += SETTINGS["char_size"]
        if self.cursor_y > SETTINGS["canvas_height"] - SETTINGS["char_size"]:
            self.cursor_y = SETTINGS["cursor_start_y"]

    def on_key_press(self, event: tk.Event) -> None:
        """Handle key press for canvas input."""
        if event.char and event.char.isprintable():
            ascii_val = ord(event.char)
            color = self.calculate_color(ascii_val)
            self.draw_block(self.cursor_x, self.cursor_y, color, event.char)
            self.memory.append((self.cursor_x, self.cursor_y, event.char, color))
            self.undo_stack.append((self.cursor_x, self.cursor_y, event.char, color))
            self.redo_stack.clear()
            self.update_cursor()

    def reset(self) -> None:
        """Clear the canvas and reset cursor."""
        self.canvas.delete("all")
        self.cursor_x = SETTINGS["cursor_start_x"]
        self.cursor_y = SETTINGS["cursor_start_y"]
        self.memory.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.status_label.config(text="Canvas reset.", fg="white")

    def undo(self) -> None:
        """Undo the last drawn character."""
        if self.memory:
            action = self.memory.pop()
            self.redo_stack.append(action)
            self.redraw_memory()
            self.status_label.config(text="Undo successful.", fg="white")
        else:
            self.status_label.config(text="Nothing to undo.", fg="yellow")

    def redo(self) -> None:
        """Redo the last undone action."""
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.memory.append(action)
            self.draw_block(*action)
            self.status_label.config(text="Redo successful.", fg="white")
        else:
            self.status_label.config(text="Nothing to redo.", fg="yellow")

    def redraw_memory(self) -> None:
        """Redraw the canvas from memory."""
        self.canvas.delete("all")
        for x, y, char, color in self.memory:
            self.draw_block(x, y, color, char)

    def save_canvas(self) -> None:
        """Save the canvas as PNG or PostScript."""
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

    def execute_command(self, event: tk.Event) -> None:
        """Execute canvas commands from user input."""
        cmd = self.command_entry.get().strip()
        self.command_entry.delete(0, tk.END)
        try:
            if cmd.lower().startswith("set"):
                parts = cmd.split()
                if len(parts) == 4 and parts[2] == "=":
                    coords_str = parts[1].strip("()")
                    x_str, y_str = coords_str.split(",")
                    x, y = int(x_str.strip()), int(y_str.strip())
                    r, g, b = map(int, parts[3].split(","))
                    color = f'#{r:02x}{g:02x}{b:02x}'
                    self.canvas.create_rectangle(x, y, x + SETTINGS["char_size"], y + SETTINGS["char_size"],
                                                 fill=color, outline=color)
                    self.status_label.config(text=f"Set ({x},{y}) = {color}", fg="cyan")
                else:
                    self.status_label.config(text="Usage: SET (x,y) = r,g,b", fg="yellow")
            else:
                self.status_label.config(text=f"Unknown command: {cmd}", fg="yellow")
        except Exception as e:
            self.status_label.config(text=f"Command Error: {str(e)}", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Canvas Terminal v0.6")
    app = CanvasTerminal(root)
    root.mainloop()
