# File: /ColorOS/PixelUI.py
# Part of Color OS – Basic pixel-native window and cursor rendering

from PIL import Image, ImageDraw

class PixelUI:
    def __init__(self, canvas):
        self.canvas = canvas
        self.draw = ImageDraw.Draw(self.canvas)
        self.windows = []
        self.cursor_pos = (0, 0)

    def add_window(self, x, y, w, h, title="Window"):
        self.windows.append({"x": x, "y": y, "w": w, "h": h, "title": title})

    def move_cursor(self, x, y):
        self.cursor_pos = (x, y)

    def render_windows(self):
        for win in self.windows:
            x, y, w, h, title = win["x"], win["y"], win["w"], win["h"], win["title"]
            self.draw.rectangle([x, y, x + w, y + h], outline=(255, 255, 255), width=1)
            self.draw.rectangle([x, y, x + w, y + 10], fill=(50, 50, 50))
            self.draw.text((x + 2, y), title, fill=(255, 255, 255))

    def render_cursor(self):
        x, y = self.cursor_pos
        cursor_shape = [
            (x, y), (x+1, y), (x+2, y),
            (x, y+1), (x+1, y+1),
            (x, y+2)
        ]
        for px, py in cursor_shape:
            if 0 <= px < self.canvas.width and 0 <= py < self.canvas.height:
                self.canvas.putpixel((px, py), (255, 255, 0))

    def draw_ui(self):
        self.render_windows()
        self.render_cursor()
