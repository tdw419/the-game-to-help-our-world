# settings.py

SETTINGS = {
    "canvas_width": 800,
    "canvas_height": 600,
    "char_size": 10,
    "font": ("Consolas", 10),
    "cursor_start_x": 0,
    "cursor_start_y": 0,
    "history_capacity": 50,
    "disk_total_size_pixels": 1024 * 1024, # Example: 1MB disk
    "disk_block_size_pixels": 4096, # Example: 4KB blocks
    "cpu_speed_hz": 100, # CPU cycles per second
    "window_width": 800,
    "window_height": 650,

    # Add this missing key:
    "blink_rate": 500, # Cursor blink rate in milliseconds (e.g., 500ms for half a second)
}