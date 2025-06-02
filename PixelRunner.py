# File: /ColorOS/PixelRunner.py
# Executes .pxl image programs as native pixel opcodes

from PIL import Image

class PixelRunner:
    def __init__(self, canvas):
        self.canvas = canvas
        self.pixels = self.canvas.load()
        self.width, self.height = self.canvas.size
        self.instruction_pointer = (0, 0)
        self.running = True

    def get_pixel(self, x, y):
        return self.pixels[x, y][:3]

    def set_pixel(self, x, y, color):
        self.pixels[x, y] = color

    def execute(self):
        x, y = self.instruction_pointer
        while self.running and y < self.height:
            opcode = self.get_pixel(x, y)
            if opcode == (0, 0, 0):  # END
                self.running = False
            elif opcode == (255, 255, 255):  # WRITE white
                tx, ty = self.get_pixel(x+1, y)
                self.set_pixel(tx, ty, (255, 255, 255))
            elif opcode == (1, 1, 1):  # CLICK_AT check
                cx, cy = self.get_pixel(x+1, y)
                tx, ty = self.get_pixel(x+2, y)
                if (cx, cy) == (tx, ty):
                    x += 1  # skip to next
            # Add more opcodes as needed
            x += 1
            if x >= self.width:
                x = 0
                y += 1
            self.instruction_pointer = (x, y)
