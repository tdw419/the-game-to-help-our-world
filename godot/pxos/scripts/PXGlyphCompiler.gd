# PXGlyphCompiler.gd
# This utility script is responsible for converting text strings into
# pixel-encoded glyphs that can be drawn onto a Godot Image.
# The PXOS kernel can then interpret these pixel patterns as commands or data.

extends RefCounted # Extend RefCounted for easy instantiation and memory management

# --- Configuration ---
# Define the size of each glyph in pixels (e.g., 3x3 or 5x5).
# A 3x3 grid is simpler for initial testing.
const GLYPH_WIDTH = 3
const GLYPH_HEIGHT = 3

# Define the spacing between characters when drawing text.
const GLYPH_SPACING_X = 1
const GLYPH_SPACING_Y = 1

# Define the color to use for "on" pixels in a glyph.
# This can be any color, but for clarity, let's use a distinct one.
const GLYPH_ACTIVE_COLOR = Color(1.0, 1.0, 1.0) # White for active pixels
const GLYPH_INACTIVE_COLOR = Color(0.0, 0.0, 0.0, 0.0) # Transparent black for inactive pixels

# --- Glyph Definitions ---
# A dictionary mapping characters to their pixel patterns.
# Each pattern is a 2D array (list of lists) where 1 means GLYPH_ACTIVE_COLOR
# and 0 means GLYPH_INACTIVE_COLOR.
# This is a simplified 3x3 representation.

var glyph_patterns = {
    "A": [
        [0, 1, 0],
        [1, 0, 1],
        [1, 1, 1]
    ],
    "B": [
        [1, 1, 0],
        [1, 1, 0],
        [1, 1, 0]
    ],
    "C": [
        [0, 1, 1],
        [1, 0, 0],
        [0, 1, 1]
    ],
    "D": [
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 0]
    ],
    "E": [
        [1, 1, 1],
        [1, 1, 0],
        [1, 1, 1]
    ],
    "H": [
        [1, 0, 1],
        [1, 1, 1],
        [1, 0, 1]
    ],
    "L": [
        [1, 0, 0],
        [1, 0, 0],
        [1, 1, 1]
    ],
    "O": [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0]
    ],
    "P": [
        [1, 1, 0],
        [1, 1, 0],
        [1, 0, 0]
    ],
    "R": [
        [1, 1, 0],
        [1, 1, 0],
        [1, 0, 1]
    ],
    "S": [
        [0, 1, 1],
        [0, 1, 0],
        [1, 1, 0]
    ],
    "T": [
        [1, 1, 1],
        [0, 1, 0],
        [0, 1, 0]
    ],
    "X": [
        [1, 0, 1],
        [0, 1, 0],
        [1, 0, 1]
    ],
    "Z": [
        [1, 1, 1],
        [0, 1, 0],
        [1, 1, 1]
    ],
    " ": [ # Space character (empty glyph)
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ],
    ".": [ # Period
        [0, 0, 0],
        [0, 0, 0],
        [0, 1, 0]
    ],
    "!": [ # Exclamation mark
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0]
    ]
    # Add more characters as needed
}

# --- Core Functionality ---

func compile_text_to_image(
    target_image: Image,
    text: String,
    start_pos: Vector2,
    clear_area: bool = false
) -> bool:
    """
    Compiles a given text string into pixel glyphs and draws them onto a target Image.

    Args:
        target_image (Image): The Godot Image object to draw the glyphs onto.
                              Must be locked before calling this function.
        text (String): The text string to compile.
        start_pos (Vector2): The top-left pixel coordinate to start drawing the text.
        clear_area (bool): If true, clears the area where text will be drawn before drawing.

    Returns:
        bool: True if compilation and drawing was successful, false otherwise.
    """
    if not target_image or not target_image.is_locked():
        print_err("PXGlyphCompiler: Target image is null or not locked. Cannot compile text.")
        return false

    var current_draw_x = int(start_pos.x)
    var current_draw_y = int(start_pos.y)

    # Calculate the total width and height of the text block for clearing
    var total_text_width = (GLYPH_WIDTH + GLYPH_SPACING_X) * text.length() - GLYPH_SPACING_X
    var total_text_height = GLYPH_HEIGHT

    if clear_area:
        # Clear the calculated area with GLYPH_INACTIVE_COLOR
        for y_clear in range(current_draw_y, current_draw_y + total_text_height):
            for x_clear in range(current_draw_x, current_draw_x + total_text_width):
                if x_clear >= 0 and x_clear < target_image.get_width() and \
                   y_clear >= 0 and y_clear < target_image.get_height():
                    target_image.set_pixel(x_clear, y_clear, GLYPH_INACTIVE_COLOR)


    for i in range(text.length()):
        var char = text[i].to_upper() # Convert to uppercase to match glyph definitions
        var glyph_pattern = glyph_patterns.get(char)

        if glyph_pattern == null:
            print_warn("PXGlyphCompiler: No glyph pattern found for character: '", char, "'. Skipping.")
            # Use a blank glyph for unknown characters
            glyph_pattern = glyph_patterns[" "]

        # Draw the glyph pixel by pixel
        for y_offset in range(GLYPH_HEIGHT):
            for x_offset in range(GLYPH_WIDTH):
                var pixel_value = glyph_pattern[y_offset][x_offset]
                var pixel_color = GLYPH_INACTIVE_COLOR
                if pixel_value == 1:
                    pixel_color = GLYPH_ACTIVE_COLOR

                var target_x = current_draw_x + x_offset
                var target_y = current_draw_y + y_offset

                # Ensure pixel is within image bounds before setting
                if target_x >= 0 and target_x < target_image.get_width() and \
                   target_y >= 0 and target_y < target_image.get_height():
                    target_image.set_pixel(target_x, target_y, pixel_color)
                else:
                    print_warn("PXGlyphCompiler: Pixel for '", char, "' at (", target_x, ", ", target_y, ") is out of image bounds. Skipping.")

        # Move to the next character position
        current_draw_x += GLYPH_WIDTH + GLYPH_SPACING_X

    return true

# --- Example Usage (for testing/demonstration) ---
# You can uncomment and run this in a _ready() function of a Node
# to see how it compiles text to an image.

# func _ready():
#     var test_image_width = 100
#     var test_image_height = 50
#     var test_image = Image.new()
#     test_image.create(test_image_width, test_image_height, false, Image.FORMAT_RGBA8)
#     test_image.fill(Color(0.2, 0.2, 0.2, 1.0)) # Fill with a dark grey background
#     test_image.lock()
#
#     var compiler = PXGlyphCompiler.new()
#     var text_to_draw = "HELLO PXOS!"
#     var draw_start_pos = Vector2(5, 5)
#
#     if compiler.compile_text_to_image(test_image, text_to_draw, draw_start_pos, true):
#         test_image.unlock()
#         print("PXGlyphCompiler: Successfully compiled text to image.")
#
#         # To visually see the result, you'd typically update a TextureRect:
#         # var texture_rect = get_node_or_null("YourTextureRectNodePath")
#         # if texture_rect:
#         #     var new_texture = ImageTexture.new()
#         #     new_texture.create_from_image(test_image, 0)
#         #     texture_rect.texture = new_texture
#         # else:
#         #     print_err("PXGlyphCompiler: Could not find TextureRect to display compiled image.")
#     else:
#         test_image.unlock()
#         print_err("PXGlyphCompiler: Failed to compile text to image.")

