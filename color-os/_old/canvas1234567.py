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

