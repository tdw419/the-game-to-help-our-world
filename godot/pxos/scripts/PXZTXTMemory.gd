# PXZTXTMemory.gd
# This module provides a higher-level abstraction for reading and writing
# pixel-encoded text (zTXT) to specific sub-regions within the PXMemoryRegion.
# It uses PXGlyphCompiler and PXGlyphReader to convert text to/from pixels.

extends Node

# --- Configuration ---
# Define the sub-regions within PXMemoryRegion for various zTXT purposes.
# These Rect2s are relative to the overall display, not relative to PXMemoryRegion itself.
# Ensure these do NOT overlap with other critical PXOS regions (like PXMemory's main data).
# They should ideally be within the PXMemoryRegion's overall Rect2.
@export var runtime_active_region: Rect2 = Rect2(45, 0, 15, 10) # Example: Top part of memory for active trace
@export var runtime_introspections_region: Rect2 = Rect2(45, 10, 15, 20) # Example: Middle part for introspections
@export var runtime_next_region: Rect2 = Rect2(45, 30, 15, 5) # Example: Small part for next directives

# --- Dependencies ---
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # The underlying byte memory
var px_glyph_compiler: PXGlyphCompiler = null # For converting text to glyphs
var px_glyph_reader: PXGlyphReader = null     # For converting glyphs to text

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize glyph utilities
    px_glyph_compiler = PXGlyphCompiler.new()
    px_glyph_reader = PXGlyphReader.new()

    if not px_glyph_compiler or not px_glyph_reader:
        print_err("PXZTXTMemory: Failed to initialize glyph utilities. Disabling.")
        set_process(false)
        return
    if not px_memory:
        print_err("PXZTXTMemory: PXMemory node not found. Cannot operate on memory. Disabling.")
        set_process(false)
        return

    print("PXZTXTMemory: Initialized. Ready for zTXT operations.")

# --- Core zTXT Read/Write API ---

func write_ztxt(target_region: Rect2, text: String) -> bool:
    """
    Writes text as pixel-encoded glyphs (zTXT) into a specified region
    within the PXMemoryRegion.

    Args:
        target_region (Rect2): The region on the display where the zTXT will be written.
                               This should be a sub-region of PXMemoryRegion.
        text (String): The text string to write.

    Returns:
        bool: True if the write was successful, false otherwise.
    """
    if not px_memory.display_image or not px_memory.display_image.is_locked():
        print_err("PXZTXTMemory: PXMemory's display_image not available or locked. Cannot write zTXT.")
        return false

    # Clear the target region before writing new text
    _clear_region(target_region)

    # Compile and draw the text into PXMemory's image.
    # PXGlyphCompiler draws directly onto the Image.
    var success = px_glyph_compiler.compile_text_to_image(
        px_memory.display_image, # Use PXMemory's internal image
        text,
        target_region.position,
        false # Don't clear by default, we cleared the whole region above
    )

    if success:
        px_memory.update_display() # Update PXMemory's display to show changes
        return true
    else:
        print_err("PXZTXTMemory: Failed to write zTXT to region ", target_region, ": '", text, "'")
        return false


func read_ztxt(source_region: Rect2) -> String:
    """
    Reads pixel-encoded glyphs (zTXT) from a specified region within the
    PXMemoryRegion and reconstructs them into a text string.

    Args:
        source_region (Rect2): The region on the display where the zTXT is located.

    Returns:
        String: The reconstructed text string.
    """
    if not px_memory.display_image or not px_memory.display_image.is_locked():
        print_err("PXZTXTMemory: PXMemory's display_image not available or locked. Cannot read zTXT.")
        return ""

    # Read the text using PXGlyphReader
    var read_text = px_glyph_reader.read_glyphs_from_image(
        px_memory.display_image, # Use PXMemory's internal image
        source_region
    )
    return read_text

# --- Helper Functions ---

func _clear_region(region: Rect2):
    """
    Helper function to clear a specified region on PXMemory's display image.
    Sets all pixels in the region to transparent black.
    """
    if not px_memory.display_image or not px_memory.display_image.is_locked(): return
    if not px_glyph_compiler: return # Need compiler for GLYPH_INACTIVE_COLOR

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < px_memory.display_image.get_width() and y >= 0 and y < px_memory.display_image.get_height():
                px_memory.display_image.set_pixel(x, y, px_glyph_compiler.GLYPH_INACTIVE_COLOR)

