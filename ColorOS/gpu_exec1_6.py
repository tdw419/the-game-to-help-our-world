# GPUExec.py v1.6 — Color OS Pixel Executor (Simulated)
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import Canvas
import os # Added for file existence check

WIDTH, HEIGHT = 1024, 768
PXLSIZE = 1  # Render 1:1

class GPUExec:
    def __init__(self, image_path="boot.pxl.png"):
        self.image_path = image_path
        self.load_image()
        self.init_gui()

    def load_image(self):
        if not os.path.exists(self.image_path):
            print(f"ERROR: Image file '{self.image_path}' not found. Please ensure it exists.")
            print("Hint: Run with 'python your_script_name.py --generate-boot-image' to create a sample.")
            exit(1) # Exit if the boot image is missing
        print(f"[GPUExec] Loading image: {self.image_path}")
        self.img = Image.open(self.image_path).convert("RGB")
        self.width, self.height = self.img.size
        self.data = np.array(self.img)
        print(f"[GPUExec] Image loaded: {self.width}x{self.height}")

    def init_gui(self):
        self.root = tk.Tk()
        self.root.title("GPUExec v1.6 — Pixel Execution Monitor")
        self.canvas = Canvas(self.root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()
        self.render_canvas()
        # Using after_idle to ensure GUI is ready before execution starts
        self.root.after_idle(self.execute_pixels)
        self.root.mainloop()

    def render_canvas(self):
        self.canvas.delete("all")
        # Optimization: Create a PhotoImage from the numpy array for faster rendering
        # This avoids drawing individual rectangles, which is very slow for large canvases.
        pil_img = Image.fromarray(self.data, mode='RGB')
        self.tk_img = tk.PhotoImage(image=pil_img)
        self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
        self.root.update_idletasks() # Ensure canvas updates immediately

    def execute_pixels(self):
        print("[GPUExec] Beginning opcode execution pass...")
        pc = 0  # Program counter in linear image space
        max_pc = self.width * self.height

        def xy_from_index(index):
            return index % self.width, index // self.width

        # Delay for visualization (optional, for debugging flow)
        # self.root.after(50, self.execute_next_instruction, pc, max_pc, xy_from_index)
        # For now, let's keep it immediate for quick execution.

        while pc < max_pc:
            x, y = xy_from_index(pc)
            
            # Ensure pixel coordinates are within bounds before accessing
            if not (0 <= y < self.height and 0 <= x < self.width):
                print(f"[ERROR] Program Counter (PC) out of bounds at index {pc}. Halting.")
                break

            r, g, b = self.data[y, x]

            if r == 0xF0: # SYSCALL
                print(f"[SysCall] Pixel ({x},{y}) — ID {g}")
                # Simulate action by modifying pixel at PC.
                # Note: Modifying the instruction pixel itself might be confusing,
                # but it serves as a visual indicator of execution.
                self.data[y, x] = [255, 0, 0] # Turn red
                pc += 1 # Advance PC after instruction
            elif r == 0x01:  # WRITE_PIXEL to (g, b)
                if 0 <= b < self.height and 0 <= g < self.width:
                    print(f"[WRITE] Pixel at ({g},{b}) set to RED")
                    self.data[b, g] = [255, 0, 0]  # Red
                else:
                    print(f"[WARN] WRITE_PIXEL target ({g},{b}) out of bounds.")
                pc += 1 # Advance PC after instruction
            elif r == 0x02:  # INVERT_PIXEL at (g, b)
                if 0 <= b < self.height and 0 <= g < self.width:
                    old = self.data[b, g]
                    self.data[b, g] = [255 - c for c in old]
                    print(f"[INVERT] Pixel at ({g},{b}) from {old} to {self.data[b,g]}")
                else:
                    print(f"[WARN] INVERT_PIXEL target ({g},{b}) out of bounds.")
                pc += 1 # Advance PC after instruction
            elif r == 0x03:  # JUMP_IF_RED at (g, b)
                if 0 <= b < self.height and 0 <= g < self.width:
                    target_pixel_color = self.data[b, g]
                    # Check if target pixel is predominantly red
                    if target_pixel_color[0] > 200 and target_pixel_color[1] < 50 and target_pixel_color[2] < 50:
                        print(f"[JUMP] RED found at ({g},{b}), skipping 1 instruction (PC + 1)")
                        pc += 2 # Skip current instruction + next one (effectively jumping over 1)
                    else:
                        print(f"[JUMP] Pixel at ({g},{b}) not red. No jump.")
                        pc += 1 # Advance PC normally
                else:
                    print(f"[WARN] JUMP_IF_RED target ({g},{b}) out of bounds. No jump.")
                    pc += 1 # Advance PC normally
            elif r == 0xFF:  # END
                print(f"[END] execution at pixel ({x},{y})")
                break # Halt execution
            else:
                # Handle unknown opcodes
                print(f"[ERROR] Unknown opcode {r:02X} at ({x},{y}). Halting.")
                break # Halt execution

            # Important: Re-render after each instruction to show progress visually.
            # This can be slow for large programs; for full speed, render only at end.
            self.render_canvas()
            
            # Optional: Add a small delay to slow down execution for visual debugging
            # self.root.update() # Process events
            # self.root.after(1) # Delay in milliseconds

        print("[GPUExec] Opcode execution pass complete.")
        self.render_canvas() # Final render

# Main execution block
if __name__ == "__main__":
    import sys

    def generate_boot_image(filename="boot.pxl.png"):
        print(f"\n--- Generating sample {filename} ---")
        # Create a small image for the test program
        # Make it at least big enough for the program and some pixels to write to
        test_width, test_height = 20, 20
        test_pixels = np.zeros((test_height, test_width, 3), dtype=np.uint8) # RGB

        # Instructions
        # 0x01: WRITE_PIXEL (G, B) -> Red
        # 0x02: INVERT_PIXEL (G, B)
        # 0x03: JUMP_IF_RED (G, B)
        # 0xF0: SYSCALL (G=ID, B=unused)
        # 0xFF: END

        # Program sequence:
        program = [
            # Instruction 0: SYSCALL (ID 1)
            [0xF0, 0x01, 0x00],
            # Instruction 1: WRITE_PIXEL (5, 5) -> Red
            [0x01, 0x05, 0x05],
            # Instruction 2: INVERT_PIXEL (5, 5) (was Red, now Black)
            [0x02, 0x05, 0x05],
            # Instruction 3: JUMP_IF_RED (5, 5) (not red, so no jump)
            [0x03, 0x05, 0x05],
            # Instruction 4: SYSCALL (ID 2)
            [0xF0, 0x02, 0x00],
            # Instruction 5: WRITE_PIXEL (7, 7) -> Red
            [0x01, 0x07, 0x07],
            # Instruction 6: JUMP_IF_RED (7, 7) (is red, so jump over next instruction)
            [0x03, 0x07, 0x07],
            # Instruction 7: This instruction will be skipped if 0x03 jumps
            [0x01, 0x09, 0x09], # WRITE_PIXEL (9,9) -> This should NOT execute
            # Instruction 8: SYSCALL (ID 3) - will execute if 0x03 jumped
            [0xF0, 0x03, 0x00], 
            # Instruction 9: END
            [0xFF, 0x00, 0x00]
        ]

        # Place the program at the top-left
        prog_idx = 0
        for y_coord in range(len(program)):
            if y_coord >= test_height: break
            for x_coord in range(len(program[y_coord])):
                if x_coord >= test_width: break
                test_pixels[y_coord, x_coord] = program[y_coord][x_coord]

        # Initialize some pixels for testing WRITE_PIXEL and INVERT_PIXEL targets
        test_pixels[5, 5] = [0, 0, 0] # Black pixel at (5,5)
        test_pixels[7, 7] = [0, 0, 0] # Black pixel at (7,7)
        test_pixels[9, 9] = [0, 0, 0] # Black pixel at (9,9)

        img = Image.fromarray(test_pixels, mode='RGB')
        img.save(filename)
        print(f"Sample '{filename}' created with a small test program.")
        print("Run again without --generate-boot-image to execute it.")
        print("Expected Output:")
        print("  [SysCall] ... ID 1")
        print("  [WRITE] ... (5,5) ...")
        print("  [INVERT] ... (5,5) ... (Black)")
        print("  [JUMP] Pixel at (5,5) not red. No jump.")
        print("  [SysCall] ... ID 2")
        print("  [WRITE] ... (7,7) ...")
        print("  [JUMP] RED found at (7,7), skipping 1 instruction (PC + 1)")
        print("  [SysCall] ... ID 3")
        print("  [END] ...")
        print("  Pixel (9,9) should remain black (not written to red).")
        print("---------------------------------------------------\n")

    if "--generate-boot-image" in sys.argv:
        generate_boot_image()
    else:
        # Default WIDTH and HEIGHT for the Tkinter window
        # For the generated boot image, the actual image size is smaller (20x20)
        # but the canvas size remains 1024x768 to provide a consistent window.
        # The image will be drawn at the top-left of this large canvas.
        app = GPUExec(image_path="boot.pxl.png")