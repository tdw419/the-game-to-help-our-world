# PXScrollRegion.gd
# This script manages a dedicated scrollable region on the PXOS display.
# It maintains a buffer of text lines (represented as glyphs) and
# automatically scrolls them, providing a persistent visual log or memory tape.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas this scroll region occupies.
# Example: Rect2(0, 30, 40, 30) for a region at (0,30) with width 40, height 30.
@export var scroll_region_rect: Rect2 = Rect2(0, 30, 40, 30)

# The frequency at which the scroll region will redraw its content.
# This is separate from adding new lines, which can happen instantly.
const SCROLL_REDRAW_FREQUENCY = 5 # Redraws every 5 frames (approx. 12 times per second)

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
var glyph_compiler: PXGlyphCompiler = null

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# --- Internal State ---
var current_lines: Array = [] # Stores the text strings for each line in the scroll buffer
var max_lines_in_region = 0 # Calculated based on region height and glyph height
var frame_counter = 0 # For managing redraw frequency

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXScrollRegion: Failed to initialize PXGlyphCompiler.")
        return

    # Get the display image reference and lock it for access
    if display_screen and display_screen.texture:
        display_image = display_screen.texture.get_data()
        if display_image:
            display_image.lock() # Lock the image for pixel access
            print("PXScrollRegion: Initialized. Operating in region: ", scroll_region_rect)
            # Calculate max lines that can fit
            max_lines_in_region = floor(scroll_region_rect.size.y / (glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y))
            if max_lines_in_region <= 0:
                print_err("PXScrollRegion: Scroll region too small to fit any lines.")
                return

            # Clear the initial scroll region on the display
            clear_region(scroll_region_rect)
            update_display() # Apply initial clear to screen
        else:
            print_err("PXScrollRegion: Could not get image data from display_screen texture.")
    else:
        print_err("PXScrollRegion: 'DisplayScreen' TextureRect or its texture not found. Cannot operate.")

func _process(delta):
    # Only run if initialized and image is locked
    if display_image and display_image.is_locked():
        frame_counter += 1
        if frame_counter >= SCROLL_REDRAW_FREQUENCY:
            frame_counter = 0 # Reset counter
            # Redraw the scroll content periodically
            update_scroll_display()

func _exit_tree():
    # Unlock the image when the node is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXScrollRegion: Cleaned up image lock.")

# --- Core Scroll Region Logic ---

func add_line(text: String):
    """
    Adds a new line of text to the scroll region.
    If the region is full, the oldest line is removed (scrolled out).
    """
    if not display_image or not display_image.is_locked():
        print_err("PXScrollRegion: Display image not available or locked. Cannot add line.")
        return

    print("PXScrollRegion: Adding line: '", text, "'")
    current_lines.append(text)

    # If the number of lines exceeds the maximum capacity, remove the oldest line
    while current_lines.size() > max_lines_in_region:
        current_lines.pop_front()
        print("PXScrollRegion: Scrolled out oldest line.")

    # Immediately update the display after adding a new line
    update_scroll_display()

func update_scroll_display():
    """
    Redraws all current lines within the scroll region, simulating a scroll effect.
    """
    if not display_image or not display_image.is_locked():
        print_err("PXScrollRegion: Display image not available or locked for redraw.")
        return
    if not glyph_compiler:
        print_err("PXScrollRegion: Glyph compiler not initialized for redraw.")
        return

    # Clear the entire scroll region before redrawing all lines
    clear_region(scroll_region_rect)

    var current_y_offset = 0
    for line_text in current_lines:
        var draw_pos = Vector2(scroll_region_rect.position.x, scroll_region_rect.position.y + current_y_offset)

        # Ensure the line fits within the scroll region's height
        if draw_pos.y + glyph_compiler.GLYPH_HEIGHT <= scroll_region_rect.position.y + scroll_region_rect.size.y:
            # Compile and draw the line
            var success = glyph_compiler.compile_text_to_image(display_image, line_text, draw_pos, false)
            if not success:
                print_err("PXScrollRegion: Failed to draw line: '", line_text, "'")
        else:
            # This line would be scrolled off the bottom, so stop drawing
            break

        current_y_offset += glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y

    # Apply the changes to the actual TextureRect on screen
    update_display()
    print("PXScrollRegion: Display updated with scrolled content.")

func clear_region(region: Rect2):
    """
    Helper function to clear a specified region on the display image.
    """
    if not display_image or not display_image.is_locked(): return

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, glyph_compiler.GLYPH_INACTIVE_COLOR) # Use inactive color for clearing


func update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXScrollRegion: 'DisplayScreen' TextureRect not found for display update.")

