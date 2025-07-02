# PXFSReader.gd
# This Godot-side module reads and interprets the pixel-native file system (PXFS)
# drawn by map.py on the DisplayScreen. It can retrieve file metadata
# encoded in pixel blocks and list conceptual files.
#
# UPDATED: Now configurable to match the expanded PXFS dimensions from map.py.

extends Node

# --- Configuration ---
# These constants MUST match the PXFS_EXPANDED_ constants in map.py
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

# --- Internal State ---
var _display_image: Image = null # Cached reference to the display image

# --- Godot Lifecycle Methods ---

func _ready():
    if not display_screen or not px_scroll_log or not px_memory:
        print_err("PXFSReader: Essential dependencies missing. Reader disabled.")
        set_process(false)
        return

    # Get the display image from PXMemory, assuming PXMemory manages it.
    # PXMemoryRegion typically holds a locked image.
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
        Dictionary: A dictionary containing parsed metadata, or empty if block is out of bounds.
    """
    var metadata = {}
    
    var x0 = int(fs_root_origin.x) + block_col * (fs_block_width + fs_padding)
    var y0 = int(fs_root_origin.y) + block_row * (fs_block_height + fs_padding)

    # Check if block is within the overall image bounds
    if x0 < 0 or y0 < 0 or \
       x0 + fs_block_width > _display_image.get_width() or \
       y0 + fs_block_height > _display_image.get_height():
        _log_reader_activity("Block (" + str(block_col) + "," + str(block_row) + ") out of image bounds.")
        return metadata

    # Read header pixels
    var type_color = _display_image.get_pixel(x0 + 1, y0 + 1)
    var flags_color = _display_image.get_pixel(x0 + 2, y0 + 1)
    var size_pixel = _display_image.get_pixel(x0 + 3, y0 + 1)
    var hash_color = _display_image.get_pixel(x0 + 4, y0 + 1)

    # Decode metadata
    metadata["type_color"] = type_color
    metadata["flags_color"] = flags_color
    metadata["size"] = int(size_pixel.r * 255) + int(size_pixel.g * 255) * 256 # Reconstruct size
    metadata["hash_color"] = hash_color
    
    # Conceptual interpretation of colors/flags
    metadata["is_executable"] = flags_color.r > 0.5 # Red channel for executable flag
    metadata["is_mutated"] = flags_color.g > 0.5 # Green channel for mutated flag
    
    _log_reader_activity("Read metadata for block (" + str(block_col) + "," + str(block_row) + "): Size=" + str(metadata["size"]))
    return metadata

func list_pxfs_files() -> Array[Dictionary]:
    """
    Scans the entire PXFS region and lists all detected file blocks with their metadata.

    Returns:
        Array[Dictionary]: A list of dictionaries, each representing a file.
    """
    var files_found: Array[Dictionary] = []
    var max_rows = floor(library_storage_region.size.y / (fs_block_height + fs_padding)) # Assuming library_storage_region covers FS
    var max_cols = files_per_row

    for row in range(max_rows):
        for col in range(max_cols):
            var metadata = get_file_metadata(col, row)
            if not metadata.is_empty():
                # Add block coordinates for reference
                metadata["block_col"] = col
                metadata["block_row"] = row
                files_found.append(metadata)
            else:
                # If a block is empty/out of bounds, assume no more files in this row/section
                # This simple logic might need refinement for sparse filesystems.
                pass # print_warn("PXFSReader: No file found at (", col, ",", row, ").")

    _log_reader_activity("Scanned PXFS. Found " + str(files_found.size()) + " files.")
    return files_found

# --- Logging ---

func _log_reader_activity(message: String):
    """
    Helper function to log reader activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("FS_READER: " + message)
    else:
        print("PXFSReader (Console Log): ", message)

