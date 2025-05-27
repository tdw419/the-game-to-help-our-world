import tkinter as tk

class CanvasOS:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=800, height=600, bg='black')
        self.canvas.pack()

        self.cursor_x = 0
        self.cursor_y = 0
        self.char_size = 10  # pixel block size

        # Text memory area as a list of chars (each mapped to color)
        self.memory = []

        # Create a visual text buffer on screen
        self.root.bind("<Key>", self.on_key_press)

    def on_key_press(self, event):
        if event.char:
            ascii_val = ord(event.char)
            r = (ascii_val * 3) % 256
            g = (ascii_val * 5) % 256
            b = (ascii_val * 7) % 256
            hex_color = f'#{r:02x}{g:02x}{b:02x}'

            self.canvas.create_rectangle(
                self.cursor_x, self.cursor_y,
                self.cursor_x + self.char_size, self.cursor_y + self.char_size,
                fill=hex_color, outline=hex_color
            )

            self.memory.append((self.cursor_x, self.cursor_y, hex_color))

            self.cursor_x += self.char_size
            if self.cursor_x > 800 - self.char_size:
                self.cursor_x = 0
                self.cursor_y += self.char_size

            if self.cursor_y > 600 - self.char_size:
                self.cursor_y = 0

if __name__ == "__main__":
    root = tk.Tk()
    root.title("CanvasOS v0.1")
    app = CanvasOS(root)
    root.mainloop()
