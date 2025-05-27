import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional, Dict, Any
import threading
import time

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


import subprocess
import os

def launch_modules():
    base_dir = os.path.dirname(__file__)
    modules = [
        "terminal.py",
        "command.py",
        "memory.py"
		"cpu.py"
		"cursor.py"
		"disk.py"
		"memory.py"
    ]
    for mod in modules:
        try:
            subprocess.Popen(["python", mod], cwd=base_dir)
            print(f"Started {mod}")
        except Exception as e:
            print(f"Failed to launch {mod}: {e}")

if __name__ == "__main__":
    launch_modules()

    # Your existing canvas.py code goes here...
    # For example:
    from terminal_canvas import TerminalCanvas
    canvas = TerminalCanvas()
    canvas.run()
