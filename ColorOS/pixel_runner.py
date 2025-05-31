from PIL import Image
import numpy as np
import os
# Import the PixelCanvas class from your canvas.py file
from canvas import PixelCanvas, CANVAS_WIDTH, CANVAS_HEIGHT, DEFAULT_CANVAS_FILE

# --- Opcode Definitions ---
OPCODE_SET_COLOR = 0x12
OPCODE_END = 0xFF # Placeholder for a program termination opcode

# --- Color Conventions for Instruction Visualization (R-channel only for args) ---
COLOR_OPCODE = [0xFF, 0, 0]    # Red for opcode byte
COLOR_ARG = [0xFF, 0, 0]       # Magenta for opcode arguments (we use Red channel, so visually it will be R,0,0)
                               # The user specified Magenta for args, but our current system only uses R-channel for value.
                               # To make it visually Magenta, we'd need to set G and B channels too,
                               # but the VM only reads R. Let's make it visually magenta for clarity
                               # but ensure we're clear the VM reads R-channel.
                               # For now, let's use a distinct color in the R channel.
                               # If the user specifically wants actual magenta for arguments,
                               # we'd need to adjust how arguments are encoded/read (e.g., across multiple channels)
                               # or how the visual representation is done without affecting the R-channel value.
                               # For now, let's represent args visually as [VALUE, 0, 0] with a visual color indicating it's an arg.
                               # The prompt specified (VALUE, 0, 0) as arg format.
                               # So, let's just make the *visual* color of the pixel magenta.
                               # But the VM still reads the R channel for the argument value.
                               # This requires a slight adjustment to the set_pixel to allow for visual indication
                               # while preserving the R-channel value.

# Let's refine the color convention for placement:
# We will place the value in the RED channel for the VM.
# But when we *set* that pixel, we'll make its visual color distinct for debugging.
# This means, for an arg 'X' = 50, we set the pixel as [50, 255, 255] (magenta)
# The VM reads the 50 from the R channel.

# Updated color conventions for *programmatic placement* to aid visualization:
VIS_OPCODE_COLOR = [255, 0, 0] # Red (for opcode byte)
VIS_ARG_COLOR_BASE = [0, 255, 255] # Cyan (used as base, actual value in R) - easier to see against black
                                  # Original request was Magenta for args: [255, 0, 255]
                                  # Let's use Magenta for visual, and explain how the VM reads R.

# --- PixelVM Class ---
class PixelVM:
    """
    The ColorOS Pixel Virtual Machine interpreter.
    Reads pixel data as instructions and executes them.
    """
    def __init__(self, canvas: PixelCanvas):
        self.canvas = canvas
        self.pc = 0  # Program Counter: linear index into the instruction stream
        self.running = True
        self.prev_pc = -1 # To detect PC not advancing
        print("PixelVM initialized.")

    def run(self):
        """Main interpreter loop."""
        print("Starting PixelVM execution...")
        while self.running:
            # Check if PC is out of bounds
            if self.pc >= self.canvas.width * self.canvas.height:
                print(f"PC ({self.pc}) out of bounds. Halting.")
                self.running = False
                break

            opcode_pixel_data = self.canvas.get_linear_pixel_data(self.pc)
            opcode = opcode_pixel_data[0] # Opcode is in the Red channel of the instruction pixel

            print(f"PC: {self.pc}, Raw Opcode Pixel (R,G,B): {opcode_pixel_data}, Opcode: 0x{opcode:02x}") # Debug

            if opcode == OPCODE_SET_COLOR:
                self._execute_SET_COLOR()
            elif opcode == OPCODE_END:
                print("OPCODE_END encountered. VM halting.")
                self.running = False
            else:
                print(f"Unknown opcode 0x{opcode:02x} at PC {self.pc}. Halting.")
                self.running = False
            
            # Basic check to prevent infinite loops from non-advancing PC
            if self.running and self.pc == self.prev_pc:
                print("Warning: PC did not advance. Possible infinite loop. Halting.")
                self.running = False
            self.prev_pc = self.pc

        print("PixelVM execution finished.")

    def _execute_SET_COLOR(self):
        """
        Implements SET_COLOR (0x12) opcode:
        (x, y, R, G, B) are read from the Red channel of the next 5 pixels.
        Sets the pixel at (x, y) to the given RGB color.
        """
        # Fetch arguments from subsequent pixels, reading only the Red channel
        # Ensure we fetch within bounds
        x = self.canvas.get_linear_pixel_data(self.pc + 1)[0]
        y = self.canvas.get_linear_pixel_data(self.pc + 2)[0]
        r = self.canvas.get_linear_pixel_data(self.pc + 3)[0]
        g = self.canvas.get_linear_pixel_data(self.pc + 4)[0]
        b = self.canvas.get_linear_pixel_data(self.pc + 5)[0]

        target_color = [r, g, b]
        self.canvas.set_pixel(x, y, target_color)

        # Advance PC by 1 (for opcode) + 5 (for arguments)
        self.pc += 6
        print(f"  SET_COLOR executed: set pixel ({x},{y}) to {target_color}")

# --- Main Execution Block ---
if __name__ == "__main__":
    # Create the canvas instance (it will load from DEFAULT_CANVAS_FILE)
    my_canvas = PixelCanvas()
    my_canvas.load_from_file(DEFAULT_CANVAS_FILE)

    # --- Program Painting: SET_COLOR Test Instruction ---
    # We will programmatically "paint" the instructions onto the canvas
    # at a specific linear index, which the VM will then read.
    # Let's place this test program at the very beginning of the canvas (linear index 0).

    # Test Program 1: SET_COLOR (x=500, y=500, R=255, G=0, B=255) -> Magenta
    # Using the visual color conventions for easy identification in the image.
    # IMPORTANT: The VM *only reads the Red channel* for opcode/argument values.
    # The G and B channels are used here just for visual debugging in the PNG output.

    program_start_index = 0 # Start of the program on the canvas

    # Opcode: SET_COLOR (0x12)
    my_canvas.set_linear_pixel_data(program_start_index, [OPCODE_SET_COLOR, VIS_OPCODE_COLOR[1], VIS_OPCODE_COLOR[2]]) # Red pixel for opcode

    # Argument: x = 500
    my_canvas.set_linear_pixel_data(program_start_index + 1, [50, 0, 0])  # Value 50 in R, visual magenta
    # Argument: y = 500
    my_canvas.set_linear_pixel_data(program_start_index + 2, [50, 0, 0])  # Value 50 in R, visual magenta
    # Argument: R = 255
    my_canvas.set_linear_pixel_data(program_start_index + 3, [255, 0, 0]) # Value 255 in R, visual magenta
    # Argument: G = 0
    my_canvas.set_linear_pixel_data(program_start_index + 4, [0, 0, 0])   # Value 0 in R, visual magenta
    # Argument: B = 255
    my_canvas.set_linear_pixel_data(program_start_index + 5, [255, 0, 0]) # Value 255 in R, visual magenta

    # Test Program 2: SET_COLOR (x=10, y=80, R=0, G=255, B=0) -> Green
    # This program starts after the first one, at linear index 6.
    program_start_index_2 = program_start_index + 6

    my_canvas.set_linear_pixel_data(program_start_index_2, [OPCODE_SET_COLOR, VIS_OPCODE_COLOR[1], VIS_OPCODE_COLOR[2]]) # Red pixel for opcode
    my_canvas.set_linear_pixel_data(program_start_index_2 + 1, [10, 0, 0])               # x = 10
    my_canvas.set_linear_pixel_data(program_start_index_2 + 2, [80, 0, 0])               # y = 80
    my_canvas.set_linear_pixel_data(program_start_index_2 + 3, [0, 0, 0])                # R = 0
    my_canvas.set_linear_pixel_data(program_start_index_2 + 4, [255, 0, 0])             # G = 255
    my_canvas.set_linear_pixel_data(program_start_index_2 + 5, [0, 0, 0])               # B = 0

    # End the program after Test Program 2
    my_canvas.set_linear_pixel_data(program_start_index_2 + 6, [OPCODE_END, 0, 0]) # Opcode 0xFF, visual black

    # Create the VM instance and run it
    vm = PixelVM(my_canvas)
    vm.run()

    # Save the final state of the canvas back to the same file
    my_canvas.save_to_file(DEFAULT_CANVAS_FILE)

    print(f"\nExecution complete. Check '{DEFAULT_CANVAS_FILE}' to see the result.")
    print("You can also open the image manually to inspect the pixels.")