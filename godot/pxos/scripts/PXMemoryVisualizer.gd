# PXMemoryVisualizer.gd
# This script creates a read-only overlay on the PXOS display to
# visualize the byte values stored within the PXMemoryRegion.
# It renders small glyphs (numbers) above each memory pixel,
# acting as a live RAM inspector or debugger.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas where this visualizer will draw.
# This should typically overlap the PXMemoryRegion's rect.
@export var visualizer_region_rect: Rect2 = Rect2(45, 0, 15, 64) # Example: Same as memory region

# Offset from the memory pixel's top-left corner to draw the visualization glyph.
# Adjust this to position the number correctly above/on the memory pixel.
@export var display_offset: Vector2 = Vector2(0, 0) # No offset, draw directly on pixel

# The frequency at which the visualizer will update its display.
const VISUALIZER_UPDATE_FREQUENCY = 10 # Update every 10 frames (approx. 6 times per second)

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # Reference to the PXMemory node

var glyph_compiler: PXGlyphCompiler = null

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# A simple frame counter for managing update frequency
var frame_counter = 0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_compiler = PXGlyphCompiler.new()
    if not glyph_compiler:
        print_err("PXMemoryVisualizer: Failed to initialize PXGlyphCompiler.")
        return

    # Get the display image reference and lock it for access
    if display_screen and display_screen.texture:
        display_image = display_screen.texture.get_data()
        if display_image:
            display_image.lock() # Lock the image for pixel access
            print("PXMemoryVisualizer: Initialized. Visualizing region: ", visualizer_region_rect)
            # Clear the visualizer region initially
            clear_region(visualizer_region_rect)
            update_display() # Apply initial clear to screen
        else:
            print_err("PXMemoryVisualizer: Could not get image data from display_screen texture.")
    else:
        print_err("PXMemoryVisualizer: 'DisplayScreen' TextureRect or its texture not found. Cannot operate.")

    if not px_memory:
        print_err("PXMemoryVisualizer: 'PXMemory' node (PXMemoryRegion.gd) not found. Cannot visualize memory.")
        # Disable processing if memory region is not found
        set_process(false)


func _process(delta):
    # Only run if initialized and image is locked
    if display_image and display_image.is_locked() and px_memory:
        frame_counter += 1
        if frame_counter >= VISUALIZER_UPDATE_FREQUENCY:
            frame_counter = 0 # Reset counter
            update_visualizer()

func _exit_tree():
    # Unlock the image when the node is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXMemoryVisualizer: Cleaned up image lock.")

# --- Core Visualizer Logic ---

func update_visualizer():
    """
    Reads byte values from the PXMemoryRegion and renders them as glyphs
    onto the display within the visualizer's defined region.
    """
    if not display_image or not display_image.is_locked(): return
    if not px_memory: return
    if not glyph_compiler: return

    print("PXMemoryVisualizer: Updating memory visualization...")

    # Clear the entire visualizer region before redrawing to prevent artifacts
    clear_region(visualizer_region_rect)

    # Iterate through each pixel within the PXMemoryRegion's defined area
    # and visualize its byte value.
    var mem_rect = px_memory.memory_region_rect
    for y in range(int(mem_rect.position.y), int(mem_rect.position.y + mem_rect.size.y)):
        for x in range(int(mem_rect.position.x), int(mem_rect.position.x + mem_rect.size.x)):
            # Ensure we are within the visualizer's own drawing bounds
            if not visualizer_region_rect.has_point(Vector2(x, y)):
                continue # Skip if this memory pixel is outside our visualization area

            var byte_value = px_memory.read_byte(x, y) # Read the byte value from PXMemoryRegion

            if byte_value != -1: # -1 indicates an error/out of bounds read
                var text_to_display = str(byte_value) # Convert byte to string (0-255)

                # Calculate the drawing position for the glyph
                # This positions the glyph relative to the memory pixel it represents
                var draw_pos = Vector2(x, y) + display_offset

                # Ensure the glyph will be drawn within the visualizer's region and image bounds
                if draw_pos.x + glyph_compiler.GLYPH_WIDTH <= visualizer_region_rect.position.x + visualizer_region_rect.size.x and \
                   draw_pos.y + glyph_compiler.GLYPH_HEIGHT <= visualizer_region_rect.position.y + visualizer_region_rect.size.y:
                    
                    # Compile and draw the number glyph
                    var success = glyph_compiler.compile_text_to_image(display_image, text_to_display, draw_pos, false)
                    if not success:
                        print_err("PXMemoryVisualizer: Failed to draw glyph for byte value ", byte_value, " at (", x, ",", y, ")")
                else:
                    print_warn("PXMemoryVisualizer: Glyph for (", x, ",", y, ") would be drawn out of visualizer bounds. Skipping.")
            else:
                # print_warn("PXMemoryVisualizer: Could not read byte at (", x, ",", y, ").")
                pass # Already logged by PXMemoryRegion if it's an error

    # Apply the changes to the actual TextureRect on screen
    update_display()
    print("PXMemoryVisualizer: Memory visualization updated.")


func clear_region(region: Rect2):
    """
    Helper function to clear a specified region on the display image.
    Sets all pixels in the region to transparent black.
    """
    if not display_image or not display_image.is_locked(): return

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, Color(0, 0, 0, 0)) # Set to transparent black


func update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXMemoryVisualizer: 'DisplayScreen' TextureRect not found for display update.")

