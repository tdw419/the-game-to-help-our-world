# GPUExec_minimal.py — Minimal Pixel Executor for ColorOS Boot Testing
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import Canvas
import os

WIDTH, HEIGHT = 512, 512  # GUI window size
PXLSIZE = 1               # 1:1 pixel rendering

class GPUExec:
    def __init__(self, image_path="boot.pxl.png"):
        self.image_path = image_path
        self.load_image()
        self.init_gui()

    def load_image(self):
        if not os.path.exists(self.image_path):
            print(f"ERROR: '{self.image_path}' not found. Run with --generate-boot-image.")
            exit(1)
        self.img = Image.open(self.image_path).convert("RGB")
        self.width, self.height = self.img.size
        self.data = np.array(self.img)
        print(f"[GPUExec] Loaded {self.width}x{self.height} image.")

    def init_gui(self):
        self.root = tk.Tk()
        self.root.title("GPUExec Minimal")
        self.canvas = Canvas(self.root, width=WIDTH, height=HEIGHT)
        self.canvas.pack()
        self.render_canvas()
        self.root.after_idle(self.execute_pixels)
        self.root.mainloop()

    def render_canvas(self):
        pil_img = Image.fromarray(self.data, mode='RGB')
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        self.root.update_idletasks()

    def execute_pixels(self):
        print("[GPUExec] Executing pixel instructions...")
        pc = 0
        max_pc = self.width * self.height

        def xy(index): return index % self.width, index // self.width

        while pc < max_pc:
            x, y = xy(pc)
            if y >= self.height:
                break
            r, g, b = self.data[y, x]

            if r == 0xF0:  # SYSCALL
                print(f"[SYSCALL] Pixel ({x},{y}) — ID {g}")
                self.data[y, x] = [255, 255, 0]  # Yellow
            elif r == 0x01:  # WRITE_PIXEL to (g, b)
                if 0 <= g < self.width and 0 <= b < self.height:
                    self.data[b, g] = [255, 0, 0]  # Red
                    print(f"[WRITE] → Pixel ({g},{b}) = Red")
            elif r == 0xFF:  # END
                print(f"[END] at ({x},{y})")
                break
            else:
                print(f"[SKIP] Unknown opcode {r:02X} at ({x},{y})")
            pc += 1
            self.render_canvas()

        print("[GPUExec] Execution complete.")
        self.render_canvas()

# Boot image generator
def generate_boot_image(filename="boot.pxl.png"):
    print(f"\n[Generator] Creating '{filename}'...")
    w, h = 16, 16
    pixels = np.zeros((h, w, 3), dtype=np.uint8)

    program = [
        [0xF0, 0x01, 0x00],  # SYSCALL ID 1
        [0x01, 0x03, 0x03],  # WRITE (3,3)
        [0xF0, 0x02, 0x00],  # SYSCALL ID 2
        [0x01, 0x04, 0x04],  # WRITE (4,4)
        [0xF0, 0x03, 0x00],  # SYSCALL ID 3
        [0xFF, 0x00, 0x00],  # END
    ]

    for i, inst in enumerate(program):
        x, y = i % w, i // w
        pixels[y, x] = inst

    Image.fromarray(pixels, mode='RGB').save(filename)
    print("[Generator] Boot image written.")

# Run
if __name__ == "__main__":
    import sys
    if "--generate-boot-image" in sys.argv:
        generate_boot_image()
    else:
        GPUExec("boot.pxl.png")
