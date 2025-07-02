# PXRoadmapMemoryRegion.gd
# This script manages a dedicated region on the PXOS display for storing
# and retrieving roadmaps as pixel-encoded glyphs. It acts as a visual
# persistent storage for the system's evolutionary plans.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas where roadmaps will be stored.
# This region should be large enough to hold your roadmap steps as glyphs.
# Example: Rect2(0, 60, 80, 20) for a region at (0,60) with width 80, height 20.
@export var roadmap_storage_region: Rect2 = Rect2(0, 60, 80, 20)

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
var px_glyph_compiler: PXGlyphCompiler = null # For writing roadmaps as glyphs
var px_glyph_reader: PXGlyphReader = null     # For reading roadmaps as glyphs

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# --- Internal State ---
# No specific internal state for this module beyond its dependencies and region.

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize glyph utilities
    px_glyph_compiler = PXGlyphCompiler.new()
    px_glyph_reader = PXGlyphReader.new()

    if not px_glyph_compiler or not px_glyph_reader:
        print_err("PXRoadmapMemoryRegion: Failed to initialize glyph utilities. Disabling.")
        set_process(false)
        return

    # Get the display image reference and lock it for access
    if display_screen and display_screen.texture:
        display_image = display_screen.texture.get_data()
        if display_image:
            display_image.lock() # Lock the image for pixel access
            print("PXRoadmapMemoryRegion: Initialized. Storage region: ", roadmap_storage_region)
            # Clear the initial roadmap storage region
            clear_region(roadmap_storage_region)
            update_display() # Apply initial clear
        else:
            print_err("PXRoadmapMemoryRegion: Could not get display image data.")
    else:
        print_err("PXRoadmapMemoryRegion: 'DisplayScreen' TextureRect or its texture not found. Cannot operate.")
        set_process(false)
        return

func _exit_tree():
    # Unlock the image when the node is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXRoadmapMemoryRegion: Cleaned up image lock.")

# --- Core Roadmap Storage Logic ---

func write_roadmap_to_memory(roadmap_steps: Array[String]) -> bool:
    """
    Writes an array of roadmap steps as glyphs into the designated memory region.
    Each step is written on a new line within the region.

    Args:
        roadmap_steps (Array[String]): The roadmap steps to write.

    Returns:
        bool: True if the roadmap was successfully written, false otherwise.
    """
    if not display_image or not display_image.is_locked():
        print_err("PXRoadmapMemoryRegion: Display image not available or locked. Cannot write roadmap.")
        return false
    if not px_glyph_compiler:
        print_err("PXRoadmapMemoryRegion: Glyph compiler not available. Cannot write roadmap.")
        return false

    print("PXRoadmapMemoryRegion: Writing roadmap to memory (", roadmap_steps.size(), " steps)...")
    clear_region(roadmap_storage_region) # Clear region before writing new roadmap

    var current_y_offset = 0
    var line_height = px_glyph_compiler.GLYPH_HEIGHT + px_glyph_compiler.GLYPH_SPACING_Y

    for i in range(roadmap_steps.size()):
        var step_text = roadmap_steps[i]
        var draw_pos = Vector2(roadmap_storage_region.position.x, roadmap_storage_region.position.y + current_y_offset)

        # Ensure the line fits within the storage region's height
        if draw_pos.y + px_glyph_compiler.GLYPH_HEIGHT > roadmap_storage_region.position.y + roadmap_storage_region.size.y:
            print_warn("PXRoadmapMemoryRegion: Roadmap too long to fit in region. Truncating.")
            break # Stop writing if no more space

        var success = px_glyph_compiler.compile_text_to_image(display_image, step_text, draw_pos, false)
        if not success:
            print_err("PXRoadmapMemoryRegion: Failed to write roadmap step '", step_text, "'.")
            return false # Indicate failure
        current_y_offset += line_height

    _update_display() # Update the display to show the newly written roadmap
    print("PXRoadmapMemoryRegion: Roadmap written successfully.")
    return true


func read_roadmap_from_memory() -> Array[String]:
    """
    Reads glyphs from the designated memory region and reconstructs them into
    an array of roadmap steps. Each line of glyphs is treated as one step.

    Returns:
        Array[String]: An array of strings representing the roadmap steps.
    """
    var read_roadmap: Array[String] = []
    if not display_image or not display_image.is_locked():
        print_err("PXRoadmapMemoryRegion: Display image not available or locked. Cannot read roadmap.")
        return read_roadmap
    if not px_glyph_reader:
        print_err("PXRoadmapMemoryRegion: Glyph reader not available. Cannot read roadmap.")
        return read_roadmap

    print("PXRoadmapMemoryRegion: Reading roadmap from memory...")

    var line_height = px_glyph_compiler.GLYPH_HEIGHT + px_glyph_compiler.GLYPH_SPACING_Y
    var current_y = int(roadmap_storage_region.position.y)

    while current_y < roadmap_storage_region.position.y + roadmap_storage_region.size.y:
        var line_scan_region = Rect2(roadmap_storage_region.position.x, current_y, roadmap_storage_region.size.x, px_glyph_compiler.GLYPH_HEIGHT)
        var line_text = px_glyph_reader.read_glyphs_from_image(display_image, line_scan_region)

        if line_text.strip_edges().is_empty():
            # Stop if we encounter an empty line, assuming end of roadmap
            break
        read_roadmap.append(line_text.strip_edges()) # Add stripped text to roadmap
        current_y += line_height

    print("PXRoadmapMemoryRegion: Roadmap read (", read_roadmap.size(), " steps): ", read_roadmap)
    return read_roadmap

# --- Helper Functions ---

func clear_region(region: Rect2):
    """
    Helper function to clear a specified region on the display image.
    Sets all pixels in the region to transparent black.
    """
    if not display_image or not display_image.is_locked(): return
    if not px_glyph_compiler: return # Need compiler for GLYPH_INACTIVE_COLOR

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, px_glyph_compiler.GLYPH_INACTIVE_COLOR)

func _update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXRoadmapMemoryRegion: 'DisplayScreen' TextureRect not found for display update.")

