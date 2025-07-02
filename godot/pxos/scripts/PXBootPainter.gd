# PXBootPainter.gd
# This script is responsible for "bootstrapping" the PXOS by drawing
# initial pixel-based opcodes directly onto a TextureRect in the scene.
# This simulates the initial state of the display that the PXKernel
# will then observe and interpret.

extends TextureRect

# --- Configuration ---
# Define the same opcode colors as in PXKernelDisplayReflector.gd for consistency.
const PXL_HALT = Color(1.0, 0.0, 0.0)        # Red pixel: Stop execution
const PXL_PRINT_HELLO = Color(0.0, 1.0, 0.0) # Green pixel: Print "Hello"
const PXL_JUMP_TO_X = Color(0.0, 0.0, 1.0)   # Blue pixel: Jump to a new X coordinate

# --- Godot Lifecycle Methods ---

func _ready():
    # Ensure the TextureRect is properly set up for drawing.
    # We want to create a new Image and set it as the texture.
    var image_width = 64  # Small canvas for initial boot pixels
    var image_height = 64 # Small canvas for initial boot pixels

    # Create a new Image to draw on. Use RGBA8 for full color support.
    var boot_image = Image.new()
    boot_image.create(image_width, image_height, false, Image.FORMAT_RGBA8)
    boot_image.fill(Color(0.0, 0.0, 0.0, 0.0)) # Fill with transparent black initially

    boot_image.lock() # Lock the image for pixel manipulation

    print("PXBootPainter: Drawing initial boot pixels...")

    # --- Draw Initial Opcode Grid ---
    # (0,0) = PXL_HALT
    boot_image.set_pixel(0, 0, PXL_HALT)
    print("  Painted PXL_HALT at (0, 0)")

    # (1,0) = PXL_PRINT_HELLO
    boot_image.set_pixel(1, 0, PXL_PRINT_HELLO)
    print("  Painted PXL_PRINT_HELLO at (1, 0)")

    # (2,0) = PXL_JUMP_TO_X
    boot_image.set_pixel(2, 0, PXL_JUMP_TO_X)
    print("  Painted PXL_JUMP_TO_X at (2, 0)")

    # (3,0) = Argument for PXL_JUMP_TO_X (e.g., X = 102)
    # To encode 102 into a color channel (0-255), normalize it to 0-1.
    # 102 / 255.0 = 0.4
    var jump_arg_x = 102
    var arg_color = Color(float(jump_arg_x) / 255.0, 0.0, 0.0) # Encode X in R channel
    boot_image.set_pixel(3, 0, arg_color)
    print("  Painted JUMP_TO_X argument (X=", jump_arg_x, ") at (3, 0) with color ", arg_color)

    boot_image.unlock() # Unlock the image after drawing

    # Create a new ImageTexture from the drawn image and set it to this TextureRect.
    var boot_texture = ImageTexture.new()
    boot_texture.create_from_image(boot_image, 0) # 0 for default flags
    self.texture = boot_texture

    # Configure the TextureRect to display the image properly
    self.expand_mode = TextureRect.EXPAND_IGNORE_SIZE # Don't expand beyond content
    self.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
    self.custom_minimum_size = Vector2(image_width, image_height) # Set minimum size to image size
    self.size = Vector2(image_width, image_height) # Set actual size

    print("PXBootPainter: Boot pixels rendered to TextureRect.")

