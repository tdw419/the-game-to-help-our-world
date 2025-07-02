# PXGlyphReader.gd
# This utility script is responsible for reading pixel-encoded glyphs from a Godot Image
# and converting them back into a text string. It acts as the "eye and parser" for
# the PXOS kernel to interpret symbolic directives from the display.

extends RefCounted # Extend RefCounted for easy instantiation and memory management

# --- Configuration (Must match PXGlyphCompiler.gd) ---
# Define the size of each glyph in pixels.
const GLYPH_WIDTH = 3
const GLYPH_HEIGHT = 3

# Define the spacing between characters.
const GLYPH_SPACING_X = 1
const GLYPH_SPACING_Y = 1 # Not directly used in horizontal reading, but good for consistency

# Define the color used for "on" pixels in a glyph.
const GLYPH_ACTIVE_COLOR = Color(1.0, 1.0, 1.0) # White for active pixels
const GLYPH_INACTIVE_COLOR = Color(0.0, 0.0, 0.0, 0.0) # Transparent black for inactive pixels

# --- Glyph Definitions (Must match PXGlyphCompiler.gd) ---
# A dictionary mapping pixel patterns back to their characters.
# This is the inverse of the glyph_patterns in PXGlyphCompiler.gd.
# Each key is a string representation of the 2D array (for hashing/comparison).
var glyph_patterns_inverse = {
    str([[0, 1, 0], [1, 0, 1], [1, 1, 1]]): "A",
    str([[1, 1, 0], [1, 1, 0], [1, 1, 0]]): "B",
    str([[0, 1, 1], [1, 0, 0], [0, 1, 1]]): "C",
    str([[1, 1, 0], [1, 0, 1], [1, 1, 0]]): "D",
    str([[1, 1, 1], [1, 1, 0], [1, 1, 1]]): "E",
    str([[1, 0, 1], [1, 1, 1], [1, 0, 1]]): "H",
    str([[1, 0, 0], [1, 0, 0], [1, 1, 1]]): "L",
    str([[0, 1, 0], [1, 0, 1], [0, 1, 0]]): "O",
    str([[1, 1, 0], [1, 1, 0], [1, 0, 0]]): "P",
    str([[1, 1, 0], [1, 1, 0], [1, 0, 1]]): "R",
    str([[0, 1, 1], [0, 1, 0], [1, 1, 0]]): "S",
    str([[1, 1, 1], [0, 1, 0], [0, 1, 0]]): "T",
    str([[1, 0, 1], [0, 1, 0], [1, 0, 1]]): "X",
    str([[1, 1, 1], [0, 1, 0], [1, 1, 1]]): "Z",
    str([[0, 0, 0], [0, 0, 0], [0, 0, 0]]): " ", # Space character
    str([[0, 0, 0], [0, 0, 0], [0, 1, 0]]): ".", # Period
    str([[0, 1, 0], [0, 1, 0], [0, 1, 0]]): "!"  # Exclamation mark
}

# --- Core Functionality ---

func read_glyphs_from_image(
    source_image: Image,
    scan_region: Rect2
) -> String:
    """
    Scans a defined region of a source Image, detects pixel clusters that match
    known glyphs, and reconstructs them into a text string.

    Args:
        source_image (Image): The Godot Image object to read the glyphs from.
                              Must be locked before calling this function.
        scan_region (Rect2): The rectangular area (x, y, width, height) to scan for glyphs.

    Returns:
        String: The reconstructed text string. Returns an empty string if no glyphs are found
                or if the image is not valid.
    """
    if not source_image or not source_image.is_locked():
        print_err("PXGlyphReader: Source image is null or not locked. Cannot read glyphs.")
        return ""

    var recognized_text = ""
    var current_scan_x = int(scan_region.position.x)
    var scan_y = int(scan_region.position.y) # Assuming single line for now

    # Iterate horizontally across the scan region, checking for glyphs
    while current_scan_x < scan_region.position.x + scan_region.size.x:
        var glyph_pixels = []
        var is_empty_column = true

        # Extract pixels for a potential glyph
        for y_offset in range(GLYPH_HEIGHT):
            var row_pixels = []
            for x_offset in range(GLYPH_WIDTH):
                var pixel_x = current_scan_x + x_offset
                var pixel_y = scan_y + y_offset

                # Ensure pixel is within image and scan region bounds
                if pixel_x >= 0 and pixel_x < source_image.get_width() and \
                   pixel_y >= 0 and pixel_y < source_image.get_height() and \
                   scan_region.has_point(Vector2(pixel_x, pixel_y)):

                    var pixel_color = source_image.get_pixel(pixel_x, pixel_y)
                    # Compare colors with a small tolerance for floating point inaccuracies
                    if pixel_color.is_equal_approx(GLYPH_ACTIVE_COLOR):
                        row_pixels.append(1)
                        is_empty_column = false
                    else:
                        row_pixels.append(0)
                else:
                    # If out of bounds, treat as inactive pixel for pattern matching
                    row_pixels.append(0)
            glyph_pixels.append(row_pixels)

        # Convert the extracted 2D array pattern to a string for dictionary lookup
        var pattern_str = str(glyph_pixels)
        var recognized_char = glyph_patterns_inverse.get(pattern_str)

        if recognized_char != null:
            recognized_text += recognized_char
            # Move cursor past the current glyph and its spacing
            current_scan_x += GLYPH_WIDTH + GLYPH_SPACING_X
        elif is_empty_column:
            # If it's an empty column (all 0s) and not a recognized glyph,
            # it might be part of the spacing between words or just empty space.
            # We'll advance by one pixel to avoid getting stuck.
            current_scan_x += 1
            # You might add logic here to recognize larger empty blocks as spaces
            # For simplicity, we'll just advance.
        else:
            # Unrecognized pattern that's not fully empty, might be noise or unknown glyph.
            # For now, we'll treat it as an unknown character and advance.
            recognized_text += "?" # Or some other placeholder for unknown glyphs
            current_scan_x += GLYPH_WIDTH + GLYPH_SPACING_X
            print_warn("PXGlyphReader: Unrecognized glyph pattern at (", current_scan_x - GLYPH_WIDTH, ",", scan_y, "): ", pattern_str)


    return recognized_text

# --- Example Usage (for testing/demonstration) ---
# You can uncomment and run this in a _ready() function of a Node
# to see how it reads text from an image.
# This assumes you have an Image with glyphs drawn on it (e.g., by PXGlyphCompiler).

# func _ready():
#     # Simulate an image with some compiled text (e.g., from PXBootPainter)
#     var test_image_width = 100
#     var test_image_height = 50
#     var test_image = Image.new()
#     test_image.create(test_image_width, test_image_height, false, Image.FORMAT_RGBA8)
#     test_image.fill(Color(0.2, 0.2, 0.2, 1.0)) # Dark grey background
#     test_image.lock()
#
#     # Use PXGlyphCompiler to draw some text on this test image
#     var compiler = PXGlyphCompiler.new()
#     var text_to_draw = "HELLO PXOS!"
#     var draw_start_pos = Vector2(5, 5)
#     compiler.compile_text_to_image(test_image, text_to_draw, draw_start_pos, true)
#
#     # Now, use PXGlyphReader to read it back
#     var reader = PXGlyphReader.new()
#     # Define the region where the text was drawn
#     var scan_region = Rect2(draw_start_pos.x, draw_start_pos.y,
#                             (GLYPH_WIDTH + GLYPH_SPACING_X) * text_to_draw.length(), GLYPH_HEIGHT)
#
#     var read_text = reader.read_glyphs_from_image(test_image, scan_region)
#     test_image.unlock()
#
#     print("PXGlyphReader: Original text: '", text_to_draw, "'")
#     print("PXGlyphReader: Read text:     '", read_text, "'")
#
#     if text_to_draw == read_text:
#         print("PXGlyphReader: Text read successfully matches original!")
#     else:
#         print_err("PXGlyphReader: Mismatch between original and read text.")

