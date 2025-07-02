# PXFSReader.gd
# This Godot-side module reads and interprets the pixel-native file system (PXFS)
# drawn by map.py on the DisplayScreen. It can retrieve file metadata
# encoded in pixel blocks and list conceptual files.
#
# UPDATED: Now includes read_file_by_name() to load conceptual file content.

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
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # The source of visual memory
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging reader activity
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # To get underlying image data
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # NEW: For reading block content as zTXT

# --- Internal State ---
var _display_image: Image = null # Cached reference to the display image

# --- Godot Lifecycle Methods ---

func _ready():
    if not display_screen or not px_scroll_log or not px_memory or not px_ztxt_memory:
        print_err("PXFSReader: Essential dependencies missing. Reader disabled.")
        set_process(false)
        return

    _display_image = px_memory.display_image # Direct access to the shared image
    if not _display_image or not _display_image.is_locked():
        print_err("PXFSReader: PXMemory's display image not available or not locked. Reader disabled.")
        set_process(false)
        return

    print("PXFSReader: Initialized. Ready to read PXFS.")

# --- Core PXFS Reading API ---

func get_file_metadata(block_col: int, block_row: int) -> Dictionary:
    """
    Reads metadata from a specific file block in the PXFS.

    Args:
        block_col (int): The column index of the file block (0-indexed).
        block_row (int): The row index of the file block (0-indexed).

    Returns:
        Dictionary: A dictionary containing parsed metadata, or empty if block is out of bounds
                    or appears empty (no border drawn).
    """
    var metadata = {}
    
    var x0 = int(fs_root_origin.x) + block_col * (fs_block_width + fs_padding)
    var y0 = int(fs_root_origin.y) + block_row * (fs_block_height + fs_padding)

    # Check if block is within the overall image bounds
    if x0 < 0 or y0 < 0 or \
       x0 + fs_block_width > _display_image.get_width() or \
       y0 + fs_block_height > _display_image.get_height():
        # _log_reader_activity("Block (" + str(block_col) + "," + str(block_row) + ") out of image bounds.") # Too chatty
        return metadata

    # Check if the block border is drawn (simple way to detect if block is "used")
    # Check top-left corner pixel of the border
    var border_pixel = _display_image.get_pixel(x0, y0)
    if not (border_pixel.r > 0.9 and border_pixel.g > 0.9 and border_pixel.b > 0.9): # Check for white border
        return metadata # Assume block is empty/unused if no white border

    # Read header pixels
    var type_color = _display_image.get_pixel(x0 + 1, y0 + 1)
    var flags_color = _display_image.get_pixel(x0 + 2, y0 + 1)
    var size_pixel = _display_image.get_pixel(x0 + 3, y0 + 1)
    var filename_hash_pixel = _display_image.get_pixel(x0 + 5, y0 + 1)
    var last_modified_pixel = _display_image.get_pixel(x0 + 6, y0 + 1)
    var origin_agent_color = _display_image.get_pixel(x0 + 7, y0 + 1)

    # Decode metadata
    metadata["type_color"] = type_color
    metadata["flags_color"] = flags_color
    metadata["size"] = int(size_pixel.r * 255) + int(size_pixel.g * 255) * 256 # Reconstruct size
    metadata["filename_hash"] = int(filename_hash_pixel.r * 255) # Assuming grayscale hash
    metadata["last_modified_ts"] = (int(last_modified_pixel.r * 255) << 16) | \
                                   (int(last_modified_pixel.g * 255) << 8) | \
                                   int(last_modified_pixel.b * 255)
    metadata["origin_agent_color"] = origin_agent_color
    
    # Conceptual interpretation of colors/flags
    metadata["is_executable"] = flags_color.r > 0.5 # Red channel for executable flag
    metadata["is_mutated"] = flags_color.g > 0.5 # Green channel for mutated flag
    
    # _log_reader_activity("Read metadata for block (" + str(block_col) + "," + str(block_row) + "): Size=" + str(metadata["size"])) # Too chatty
    return metadata

func list_pxfs_files() -> Array[Dictionary]:
    """
    Scans the entire PXFS region and lists all detected file blocks with their metadata.

    Returns:
        Array[Dictionary]: A list of dictionaries, each representing a file.
    """
    var files_found: Array[Dictionary] = []
    # Max rows/cols calculated based on the entire display image size, not just a sub-region
    var max_rows = floor((_display_image.get_height() - fs_root_origin.y) / (fs_block_height + fs_padding))
    var max_cols = files_per_row

    for row in range(max_rows):
        for col in range(max_cols):
            var metadata = get_file_metadata(col, row)
            if not metadata.is_empty():
                # Add block coordinates for reference
                metadata["block_col"] = col
                metadata["block_row"] = row
                files_found.append(metadata)
    _log_reader_activity("Scanned PXFS. Found " + str(files_found.size()) + " files.")
    return files_found

func read_file_by_name(filename: String) -> String:
    """
    Attempts to find a file by its conceptual filename (hash) and reads its content.
    This is a conceptual read, assuming content is stored as zTXT in the block.

    Args:
        filename (String): The name of the file to read.

    Returns:
        String: The conceptual content of the file, or empty string if not found.
    """
    _log_reader_activity("Attempting to read file: '" + filename + "' from PXFS.")
    var target_hash = _generate_simple_hash(filename) % 256 # Match map.py's hash logic

    var all_files = list_pxfs_files()
    for file_info in all_files:
        if file_info.get("filename_hash") == target_hash:
            # Found a block with matching hash. Now, read its content.
            # Assume content is stored as zTXT starting from a specific offset within the block.
            # For simplicity, we assume the content fills the rest of the block after header.
            var x0 = int(fs_root_origin.x) + file_info.block_col * (fs_block_width + fs_padding)
            var y0 = int(fs_root_origin.y) + file_info.block_row * (fs_block_height + fs_padding)

            var content_read_region = Rect2(
                x0 + 1, # Start after border and header pixels
                y0 + 2, # Start after header row
                fs_block_width - 2, # Width of content area
                fs_block_height - 3 # Height of content area
            )
            
            # Read zTXT from this content region
            var content_ztxt = px_ztxt_memory.read_ztxt(content_read_region)
            _log_reader_activity("Read content for '" + filename + "': " + content_ztxt.left(20) + "...")
            return content_ztxt
    
    _log_reader_activity("File '" + filename + "' not found in PXFS.")
    return ""

# --- Helper Functions ---

func _generate_simple_hash(text: String) -> int:
    """Generates a simple integer hash for text content (must match map.py)."""
    var hash_val = 0
    for char_code in text.to_utf8_buffer():
        hash_val = (hash_val * 31 + char_code) & 0xFFFFFFFF # Keep within 32-bit int
    return hash_val

# --- Logging ---

func _log_reader_activity(message: String):
    """
    Helper function to log reader activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("FS_READER: " + message)
    else:
        print("PXFSReader (Console Log): ", message)

