import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional, Dict, Any
import threading
import time
import subprocess
import os

# --- Global Constants and Settings ---
SETTINGS = {
    "canvas_width": 800,
    "canvas_height": 600,
    "char_size": 20,
    "font": ("Courier", 14),
    "cursor_start_x": 10,
    "cursor_start_y": 10,
    "max_undo_redo": 1000,  # Limit memory size for performance
    "blink_rate": 500,  # Cursor blink rate in ms
    "color_cache_size": 256  # Cache for color calculations
}

def launch_modules():
    base_dir = os.path.dirname(__file__)
    modules = [
        "terminal.py",
        "command.py",
        "memory.py",
        "cpu.py",
        "cursor.py",
        "disk.py"
    ]
    for mod in modules:
        try:
            subprocess.Popen(["python", mod], cwd=base_dir)
            print(f"Started {mod}")
        except Exception as e:
            print(f"Failed to launch {mod}: {e}")

if __name__ == "__main__":
    launch_modules()


# ... your existing launch_modules() code ...

if __name__ == "__main__":
    launch_modules()

    from terminal import TerminalCanvas  # or terminal_canvas, if that's the right name

    root = tk.Tk()
    canvas = TerminalCanvas(
        master=root,
        canvas_width=SETTINGS["canvas_width"],
        canvas_height=SETTINGS["canvas_height"],
        char_size=SETTINGS["char_size"],
        font=SETTINGS["font"]
    )
    canvas.run()



    # Use correct module name
    from terminal import TerminalCanvas
    canvas = TerminalCanvas()
    canvas.run()
	
	print("TerminalCanvas methods:", dir(canvas))
	canvas.run()
	


