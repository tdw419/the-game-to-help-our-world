# PXZTXTMemory.gd
# This module provides a higher-level abstraction for reading and writing
# pixel-encoded text (zTXT) to specific sub-regions within the PXMemoryRegion.
# It uses PXGlyphCompiler and PXGlyphReader to convert text to/from pixels.
#
# UPDATED: Now supports writing multi-line text (roadmaps) correctly.

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
    within the PXMemoryRegion. This function now handles multi-line input.

    Args:
        target_region (Rect2): The region on the display where the zTXT will be written.
                               This should be a sub-region of PXMemoryRegion.
        text (String): The text string to write. Can contain newlines.

    Returns:
        bool: True if the write was successful, false otherwise.
    """
    if not px_memory.display_image or not px_memory.display_image.is_locked():
        print_err("PXZTXTMemory: PXMemory's display_image not available or locked. Cannot write zTXT.")
        return false

    # Clear the target region before writing new text
    _clear_region(target_region)

    var lines = text.split("\n", false) # Split into lines
    var current_y_offset = 0
    var line_height = px_glyph_compiler.GLYPH_HEIGHT + px_glyph_compiler.GLYPH_SPACING_Y
    var success_all_lines = true

    for line_content in lines:
        var draw_pos = Vector2(target_region.position.x, target_region.position.y + current_y_offset)

        # Ensure the line fits within the target region's height
        if draw_pos.y + px_glyph_compiler.GLYPH_HEIGHT > target_region.position.y + target_region.size.y:
            print_warn("PXZTXTMemory: Text too long to fit in region. Truncating.")
            success_all_lines = false
            break # Stop writing if no more space

        # Compile and draw the line into PXMemory's image.
        var success_line = px_glyph_compiler.compile_text_to_image(
            px_memory.display_image, # Use PXMemory's internal image
            line_content,
            draw_pos,
            false # Don't clear by default, we cleared the whole region once
        )
        if not success_line:
            success_all_lines = false
            print_err("PXZTXTMemory: Failed to write line '", line_content, "' to region ", target_region)

        current_y_offset += line_height

    px_memory.update_display() # Update PXMemory's display to show changes
    return success_all_lines


func read_ztxt(source_region: Rect2) -> String:
    """
    Reads pixel-encoded glyphs (zTXT) from a specified region within the
    PXMemoryRegion and reconstructs them into a text string.
    This function now handles multi-line reading.

    Args:
        source_region (Rect2): The region on the display where the zTXT is located.

    Returns:
        String: The reconstructed text string.
    """
    if not px_memory.display_image or not px_memory.display_image.is_locked():
        print_err("PXZTXTMemory: PXMemory's display_image not available or locked. Cannot read zTXT.")
        return ""

    var read_lines: Array[String] = []
    var current_y = int(source_region.position.y)
    var line_height = px_glyph_compiler.GLYPH_HEIGHT + px_glyph_compiler.GLYPH_SPACING_Y

    while current_y < source_region.position.y + source_region.size.y:
        var line_scan_region = Rect2(source_region.position.x, current_y, source_region.size.x, px_glyph_compiler.GLYPH_HEIGHT)
        var line_text = px_glyph_reader.read_glyphs_from_image(px_memory.display_image, line_scan_region)

        if line_text.strip_edges().is_empty() and current_y > source_region.position.y:
            # If we read an empty line after the first line, assume end of content
            break
        read_lines.append(line_text.strip_edges())
        current_y += line_height

    return "\n".join(read_lines)


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

