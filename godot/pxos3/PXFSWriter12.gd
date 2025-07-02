# PXFSWriter.gd
# This module is responsible for writing conceptual "files" into the Pixel Native
# File System (PXFS) grid on the DisplayScreen. It encodes file metadata
# (type, flags, size, hash, timestamp, origin) and conceptually writes content
# as pixels into designated file blocks.
#
# UPDATED: Now includes write_file_auto() to automatically find the next available slot.

extends Node

# --- Configuration ---
# These constants MUST match the PXFS_EXPANDED_ constants used in map.py
# after PXFS_RRE_v1.0 Phase 1 has been executed.
@export var fs_root_origin: Vector2 = Vector2(10, 10) # Top-left corner of the filesystem zone
@export var fs_block_width: int = 12 # Expanded block width from map.py
@export var fs_block_height: int = 12 # Expanded block height from map.py
@export var files_per_row: int = 20 # Expanded files per row from map.py
@export var fs_padding: int = 2 # Padding between blocks from map.py

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # The target display
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging writer activity
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # To get underlying image data

# --- Internal State ---
var _display_image: Image = null # Cached reference to the display image
var _next_available_block_col: int = 0
var _next_available_block_row: int = 0

# --- Godot Lifecycle Methods ---

func _ready():
    if not display_screen or not px_scroll_log or not px_memory:
        print_err("PXFSWriter: Essential dependencies missing. Writer disabled.")
        set_process(false)
        return

    _display_image = px_memory.display_image # Direct access to the shared image
    if not _display_image or not _display_image.is_locked():
        print_err("PXFSWriter: PXMemory's display image not available or not locked. Writer disabled.")
        set_process(false)
        return

    print("PXFSWriter: Initialized. Ready to write files to PXFS.")
    _scan_for_next_available_slot() # Initialize slot counter

# --- Core PXFS Writing API ---

func write_file(
    filename: String,
    content: String, # Conceptual content, not necessarily written pixel-by-pixel yet
    block_col: int,
    block_row: int,
    file_type_color: Color = Color(0.0, 0.0, 1.0), # Default blue for GDScript/Code
    flags_color: Color = Color(0.2, 0.2, 0.2), # Default grey for flags
    origin_agent_color: Color = Color(0.0, 0.0, 0.0) # Default black for origin
) -> bool:
    """
    Writes a conceptual file into a specific block in the PXFS grid.
    Encodes metadata into header pixels and conceptually represents content.

    Args:
        filename (String): The name of the file.
        content (String): The conceptual content of the file (used for size/hash).
        block_col (int): The column index of the target block.
        block_row (int): The row index of the target block.
        file_type_color (Color): Color representing file type (e.g., (0,0,1) for .gd).
        flags_color (Color): Color representing flags (e.g., (0,1,0) for executable).
        origin_agent_color (Color): Color representing originating agent.

    Returns:
        bool: True if the file was successfully written, false otherwise.
    """
    if not _display_image or not _display_image.is_locked():
        _log_writer_activity("ERROR: Display image not available or locked.")
        return false

    var x0 = int(fs_root_origin.x) + block_col * (fs_block_width + fs_padding)
    var y0 = int(fs_root_origin.y) + block_row * (fs_block_height + fs_padding)

    var x1 = x0 + fs_block_width
    var y1 = y0 + fs_block_height

    # Check if block is within the overall image bounds
    if x0 < 0 or y0 < 0 or \
       x1 > _display_image.get_width() or \
       y1 > _display_image.get_height():
        _log_writer_activity("ERROR: Block (" + str(block_col) + "," + str(block_row) + ") out of image bounds.")
        return false

    _log_writer_activity("Writing file '" + filename + "' to PXFS block (" + str(block_col) + "," + str(block_row) + ").")

    # --- Draw Block Border and Fill ---
    # Draw border (conceptually, we're writing pixels directly)
    for px in range(x0, x1):
        if px < _display_image.get_width():
            if y0 < _display_image.get_height(): _display_image.set_pixel(px, y0, Color(1,1,1)) # Top border
            if y1-1 < _display_image.get_height(): _display_image.set_pixel(px, y1-1, Color(1,1,1)) # Bottom border
    for py in range(y0, y1):
        if py < _display_image.get_height():
            if x0 < _display_image.get_width(): _display_image.set_pixel(x0, py, Color(1,1,1)) # Left border
            if x1-1 < _display_image.get_width(): _display_image.set_pixel(x1-1, py, Color(1,1,1)) # Right border

    # Fill the block (conceptual content representation)
    var fill_color = Color(0.8, 0.8, 0.8, 1.0) # Light grey fill
    # A simple way to represent content: hash of content determines fill color
    var content_hash_val = _generate_simple_hash(content) % 256
    fill_color = Color(content_hash_val/255.0, content_hash_val/255.0, content_hash_val/255.0, 1.0).lerp(Color(0.5,0.5,0.8), content_hash_val/255.0) # Blueish tint based on hash

    for px in range(x0 + 1, x1 - 1):
        for py in range(y0 + 1, y1 - 1):
            if px < _display_image.get_width() and py < _display_image.get_height():
                _display_image.set_pixel(px, py, fill_color)

    # --- Encode Metadata in Header Pixels ---
    # 1st pixel: File type
    _display_image.set_pixel(x0 + 1, y0 + 1, file_type_color)
    # 2nd pixel: Flags
    _display_image.set_pixel(x0 + 2, y0 + 1, flags_color)
    # 3rd-4th pixel: File size (encoded into 2 pixels: LSB, MSB)
    var file_size = min(len(content), 65535) # Max size for 2 bytes
    _display_image.set_pixel(x0 + 3, y0 + 1, Color(file_size % 256 / 255.0, file_size // 256 / 255.0, 0.0))
    
    # 5th pixel: Filename hash (conceptual, 1 byte)
    var filename_hash_val = _generate_simple_hash(filename) % 256
    _display_image.set_pixel(x0 + 5, y0 + 1, Color(filename_hash_val/255.0, filename_hash_val/255.0, filename_hash_val/255.0))

    # 6th pixel: Last modified timestamp (color = seconds modulo)
    var current_timestamp = int(OS.get_unix_time_from_system())
    var ts_r = (current_timestamp >> 16) & 0xFF
    var ts_g = (current_timestamp >> 8) & 0xFF
    ts_b = current_timestamp & 0xFF
    _display_image.set_pixel(x0 + 6, y0 + 1, Color(ts_r/255.0, ts_g/255.0, ts_b/255.0))

    # 7th pixel: File origin agent ID (conceptual RGB agent codes)
    _display_image.set_pixel(x0 + 7, y0 + 1, origin_agent_color)

    _update_display() # Update the display to show changes
    _log_writer_activity("File '" + filename + "' written to PXFS.")
    return true

func write_file_auto(
    filename: String,
    content: String,
    file_type_color: Color = Color(0.0, 0.0, 1.0),
    flags_color: Color = Color(0.2, 0.2, 0.2),
    origin_agent_color: Color = Color(0.0, 0.0, 0.0)
) -> bool:
    """
    Writes a conceptual file to the next available slot in the PXFS grid.

    Args:
        filename (String): The name of the file.
        content (String): The conceptual content of the file.
        file_type_color (Color): Color representing file type.
        flags_color (Color): Color representing flags.
        origin_agent_color (Color): Color representing originating agent.

    Returns:
        bool: True if the file was successfully written, false otherwise.
    """
    var max_rows = floor(px_memory.memory_region_rect.size.y / (fs_block_height + fs_padding)) # Max rows in memory region
    var max_cols = files_per_row

    # Attempt to write to the next available slot
    for r in range(_next_available_block_row, max_rows):
        for c in range(_next_available_block_col if r == _next_available_block_row else 0, max_cols):
            # Check if this slot is already occupied (conceptually, by checking a pixel)
            # This is a very basic check; a real FS would have a more robust block allocation map.
            var x0_check = int(fs_root_origin.x) + c * (fs_block_width + fs_padding)
            var y0_check = int(fs_root_origin.y) + r * (fs_block_height + fs_padding)
            
            # Check if the block's top-left pixel (x0, y0) is clear (e.g., black/transparent)
            # This is a simplification; a real check would involve reading metadata.
            if x0_check < _display_image.get_width() and y0_check < _display_image.get_height():
                var pixel_at_origin = _display_image.get_pixel(x0_check, y0_check)
                if pixel_at_origin.r < 0.1 and pixel_at_origin.g < 0.1 and pixel_at_origin.b < 0.1: # Check for near black/transparent
                    # Found an empty slot
                    _next_available_block_col = c + 1
                    _next_available_block_row = r
                    if _next_available_block_col >= max_cols: # Wrap to next row
                        _next_available_block_col = 0
                        _next_available_block_row += 1
                    return write_file(filename, content, c, r, file_type_color, flags_color, origin_agent_color)
            else:
                _log_writer_activity("WARNING: Auto-slot check out of bounds at (" + str(c) + "," + str(r) + ").")
                
    _log_writer_activity("ERROR: No available PXFS slot found.")
    print_err("PXFSWriter: No available PXFS slot found.")
    return false

func _scan_for_next_available_slot():
    """
    Scans the PXFS region to find the first available (empty) block
    and initializes _next_available_block_col/_next_available_block_row.
    This runs once at _ready.
    """
    _log_writer_activity("Scanning for next available PXFS slot...")
    var max_rows = floor(px_memory.memory_region_rect.size.y / (fs_block_height + fs_padding))
    var max_cols = files_per_row

    for r in range(max_rows):
        for c in range(max_cols):
            var x0_check = int(fs_root_origin.x) + c * (fs_block_width + fs_padding)
            var y0_check = int(fs_root_origin.y) + r * (fs_block_height + fs_padding)
            
            if x0_check < _display_image.get_width() and y0_check < _display_image.get_height():
                var pixel_at_origin = _display_image.get_pixel(x0_check, y0_check)
                if pixel_at_origin.r < 0.1 and pixel_at_origin.g < 0.1 and pixel_at_origin.b < 0.1: # Check for near black/transparent
                    _next_available_block_col = c
                    _next_available_block_row = r
                    _log_writer_activity("Found initial empty slot at (" + str(c) + "," + str(r) + ").")
                    return
            else:
                _log_writer_activity("WARNING: Initial scan out of bounds at (" + str(c) + "," + str(r) + ").")
                break # Stop scanning this row if out of bounds

    _log_writer_activity("No empty slot found during initial scan. Starting at (0,0).")
    _next_available_block_col = 0
    _next_available_block_row = 0


# --- Helper Functions ---

func _generate_simple_hash(text: String) -> int:
    """Generates a simple integer hash for text content."""
    var hash_val = 0
    for char_code in text.to_utf8_buffer():
        hash_val = (hash_val * 31 + char_code) & 0xFFFFFFFF # Keep within 32-bit int
    return hash_val

func _update_display():
    """
    Updates the TextureRect with the modified display_image.
    """
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(_display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXFSWriter: 'DisplayScreen' TextureRect not found for display update.")

# --- Logging ---

func _log_writer_activity(message: String):
    """
    Helper function to log writer activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("FS_WRITER: " + message)
    else:
        print("PXFSWriter (Console Log): ", message)

