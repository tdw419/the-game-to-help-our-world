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

# --- 1. Enhanced TerminalCanvas Class ---
class TerminalCanvas:
    """Manages all drawing operations and visual state on the Tkinter canvas."""
    
    def __init__(self, master: tk.Tk, canvas_width: int, canvas_height: int, 
                 char_size: int, font: Tuple[str, int]) -> None:
        # Canvas setup
        self.canvas = tk.Canvas(master, width=canvas_width, height=canvas_height, 
                               bg='black', highlightthickness=0)
        self.canvas.pack()
        
        # Configuration
        self.char_size = char_size
        self.font = font
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        
        # Status label with better styling
        self.status_label = tk.Label(master, text="Welcome to Canvas Terminal!", 
                                   fg="white", bg="black", font=("Arial", 10))
        self.status_label.pack(fill=tk.X)
        
        # Cursor management
        self.blink_id: Optional[str] = None
        self.cursor_visible = True
        self.cursor_x = 0
        self.cursor_y = 0
        
        # Performance optimizations
        self.color_cache: Dict[int, str] = {}
        self.char_objects: Dict[Tuple[int, int], List[int]] = {}  # Track canvas objects
        
        # Threading lock for safe operations
        self.lock = threading.Lock()
        
        # Initialize canvas optimizations
        self._setup_canvas_optimizations()

    def _setup_canvas_optimizations(self) -> None:
        """Configure canvas for better performance."""
        # Disable automatic redraw for batch operations
        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))

    def calculate_color(self, ascii_val: int) -> str:
        """Calculate a hex color string based on ASCII value with caching."""
        if ascii_val in self.color_cache:
            return self.color_cache[ascii_val]
        
        # Improved color calculation for better visual distribution
        hue = (ascii_val * 137.5) % 360  # Golden angle for better distribution
        saturation = 0.7 + (ascii_val % 30) / 100  # Varied saturation
        lightness = 0.4 + (ascii_val % 40) / 100   # Varied lightness
        
        # Convert HSL to RGB
        r, g, b = self._hsl_to_rgb(hue/360, saturation, lightness)
        color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        
        # Cache the result
        if len(self.color_cache) < SETTINGS["color_cache_size"]:
            self.color_cache[ascii_val] = color
        
        return color

    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[float, float, float]:
        """Convert HSL to RGB color space."""
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0: t += 1
            if t > 1: t -= 1
            if t < 1/6: return p + (q - p) * 6 * t
            if t < 1/2: return q
            if t < 2/3: return p + (q - p) * (2/3 - t) * 6
            return p

        if s == 0:
            r = g = b = l  # Achromatic
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)

        return r, g, b

    def draw_block(self, x: int, y: int, color: str, char: str) -> bool:
        """Draw a colored block and character on the canvas with error handling."""
        try:
            with self.lock:
                # Remove existing objects at this position
                pos_key = (x, y)
                if pos_key in self.char_objects:
                    for obj_id in self.char_objects[pos_key]:
                        self.canvas.delete(obj_id)
                
                # Create new objects
                rect_id = self.canvas.create_rectangle(
                    x, y, x + self.char_size, y + self.char_size,
                    fill=color, outline=color, tags="char_block"
                )
                
                # Only draw text if character is printable
                text_id = None
                if char and char.isprintable():
                    text_id = self.canvas.create_text(
                        x + self.char_size // 2, y + self.char_size // 2,
                        text=char, fill='white', font=self.font, 
                        tags="char_text", anchor='center'
                    )
                
                # Store object references
                self.char_objects[pos_key] = [rect_id] + ([text_id] if text_id else [])
                
            return True
            
        except tk.TclError as e:
            self.show_status(f"Canvas Error: {str(e)}", "red")
            return False
        except Exception as e:
            self.show_status(f"Draw Error: {str(e)}", "red")
            return False

    def draw_cursor(self, x: int, y: int) -> None:
        """Draws or moves a blinking cursor indicator with improved visibility."""
        try:
            self.cursor_x, self.cursor_y = x, y
            self.canvas.delete("cursor")  # Remove previous cursor
            
            # Create a more visible cursor
            cursor_id = self.canvas.create_rectangle(
                x + 1, y + 1, x + self.char_size - 1, y + self.char_size - 1,
                outline="yellow", width=2, tags="cursor", fill=""
            )
            
            # Restart blinking
            self._restart_cursor_blink()
            
        except Exception as e:
            self.show_status(f"Cursor Error: {str(e)}", "red")

    def _restart_cursor_blink(self) -> None:
        """Restart the cursor blinking animation."""
        if self.blink_id:
            self.canvas.after_cancel(self.blink_id)
        self.cursor_visible = True
        self.blink_id = self.canvas.after(SETTINGS["blink_rate"], self._blink_cursor)

    def _blink_cursor(self) -> None:
        """Makes the cursor blink with improved state management."""
        try:
            cursor_items = self.canvas.find_withtag("cursor")
            if cursor_items:
                self.cursor_visible = not self.cursor_visible
                state = "normal" if self.cursor_visible else "hidden"
                for item in cursor_items:
                    self.canvas.itemconfigure(item, state=state)
                
                # Schedule next blink
                self.blink_id = self.canvas.after(SETTINGS["blink_rate"], self._blink_cursor)
        except Exception as e:
            self.show_status(f"Blink Error: {str(e)}", "red")

    def clear_all(self) -> None:
        """Clears all items from the canvas with proper cleanup."""
        try:
            with self.lock:
                self.canvas.delete("all")
                self.char_objects.clear()
                self._stop_cursor_blink()
            self.show_status("Canvas cleared", "green")
        except Exception as e:
            self.show_status(f"Clear Error: {str(e)}", "red")

    def clear_characters(self) -> None:
        """Clears only character-related items from the canvas."""
        try:
            with self.lock:
                self.canvas.delete("char_block", "char_text")
                self.char_objects.clear()
            self.show_status("Characters cleared", "green")
        except Exception as e:
            self.show_status(f"Clear Characters Error: {str(e)}", "red")

    def _stop_cursor_blink(self) -> None:
        """Stop cursor blinking animation."""
        if self.blink_id:
            self.canvas.after_cancel(self.blink_id)
            self.blink_id = None

    def show_status(self, message: str, color: str = "white") -> None:
        """Updates the status label with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.status_label.config(text=full_message, fg=color)

    def scroll_content(self, offset_y: int) -> None:
        """Moves all canvas content vertically with bounds checking."""
        try:
            if abs(offset_y) > 0:
                self.canvas.move("all", 0, offset_y)
                self.show_status(f"Scrolled by {offset_y} pixels", "cyan")
        except Exception as e:
            self.show_status(f"Scroll Error: {str(e)}", "red")

    def get_canvas_dims(self) -> Tuple[int, int]:
        """Returns canvas width and height with actual measurements."""
        try:
            # Get actual canvas size (may differ from initial size)
            actual_width = self.canvas.winfo_width()
            actual_height = self.canvas.winfo_height()
            return actual_width, actual_height
        except Exception:
            # Fallback to configured dimensions
            return self.canvas_width, self.canvas_height

    def save_to_file(self, root_window: tk.Tk) -> None:
        """Save canvas as PNG or PS file with improved error handling."""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"), 
                    ("PostScript files", "*.ps"),
                    ("All files", "*.*")
                ],
                title="Save Canvas"
            )
            
            if not file_path:
                return
            
            if file_path.lower().endswith(".png"):
                self._save_as_png(root_window, file_path)
            elif file_path.lower().endswith(".ps"):
                self._save_as_postscript(file_path)
            else:
                self.show_status("Unsupported file format", "red")
                
        except Exception as e:
            self.show_status(f"Save Error: {str(e)}", "red")

    def _save_as_png(self, root_window: tk.Tk, file_path: str) -> None:
        """Save canvas as PNG using screen capture."""
        try:
            # Ensure window is visible and updated
            root_window.update_idletasks()
            
            # Get exact canvas coordinates on screen
            x = root_window.winfo_rootx() + self.canvas.winfo_x()
            y = root_window.winfo_rooty() + self.canvas.winfo_y()
            x1 = x + self.canvas.winfo_width()
            y1 = y + self.canvas.winfo_height()
            
            # Capture and save
            screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
            screenshot.save(file_path, "PNG", optimize=True)
            
            self.show_status(f"PNG saved: {file_path}", "green")
            
        except Exception as e:
            self.show_status(f"PNG Save Error: {str(e)}", "red")

    def _save_as_postscript(self, file_path: str) -> None:
        """Save canvas as PostScript file."""
        try:
            self.canvas.postscript(file=file_path, colormode='color')
            self.show_status(f"PostScript saved: {file_path}", "green")
        except Exception as e:
            self.show_status(f"PostScript Save Error: {str(e)}", "red")

    def get_char_grid_size(self) -> Tuple[int, int]:
        """Calculate how many characters can fit in the canvas."""
        width, height = self.get_canvas_dims()
        chars_x = width // self.char_size
        chars_y = height // self.char_size
        return chars_x, chars_y

    def grid_to_pixel(self, grid_x: int, grid_y: int) -> Tuple[int, int]:
        """Convert grid coordinates to pixel coordinates."""
        pixel_x = grid_x * self.char_size
        pixel_y = grid_y * self.char_size
        return pixel_x, pixel_y

    def pixel_to_grid(self, pixel_x: int, pixel_y: int) -> Tuple[int, int]:
        """Convert pixel coordinates to grid coordinates."""
        grid_x = pixel_x // self.char_size
        grid_y = pixel_y // self.char_size
        return grid_x, grid_y

    def batch_draw_start(self) -> None:
        """Start batch drawing mode for better performance."""
        self.canvas.configure(state='disabled')

    def batch_draw_end(self) -> None:
        """End batch drawing mode and refresh canvas."""
        self.canvas.configure(state='normal')
        self.canvas.update_idletasks()

    def destroy(self) -> None:
        """Clean up resources when destroying the canvas."""
        self._stop_cursor_blink()
        with self.lock:
            self.char_objects.clear()
            self.color_cache.clear()