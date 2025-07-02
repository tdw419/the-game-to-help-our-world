# PXScrollLibrary.gd
# This module acts as a central library for storing and managing multiple
# named RRE scrolls directly within PXOS's pixel memory. It allows for
# saving, retrieving, and listing various learned or predefined behaviors.

extends Node

# --- Configuration ---
# The Rect2 defining the overall area on the canvas where the scroll library
# will store its scrolls. This must be a sub-region within PXMemoryRegion.
@export var library_storage_region: Rect2 = Rect2(0, 0, 80, 128) # Example: Large top-left area for library

# The maximum number of scrolls this library can store.
@export var max_scrolls: int = 10

# The height allocated for each scroll entry within the library_storage_region.
# This determines how many lines/pixels each stored scroll can occupy.
@export var scroll_entry_height: int = 10 # Height in pixels per stored scroll

# --- Dependencies ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To write/read scrolls
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging library activity

# --- Internal State ---
# A dictionary to map scroll names to their storage metadata (e.g., start_y_offset, height).
# {"scroll_name": {"start_y": int, "height": int}}
var scroll_index: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_ztxt_memory or not px_scroll_log:
        print_err("PXScrollLibrary: Essential dependencies missing. Library disabled.")
        set_process(false)
        return

    print("PXScrollLibrary: Initialized. Ready to manage scrolls.")
    # Clear the entire library storage region at startup
    px_ztxt_memory._clear_region(library_storage_region)
    _rebuild_index_from_memory() # Attempt to rebuild index from existing memory content

# --- Core Library API ---

func save_scroll(scroll_name: String, scroll_content_array: Array[String]) -> bool:
    """
    Saves a scroll (array of RRE commands) to the library's pixel memory region.
    It attempts to find an available slot or overwrite an existing one.

    Args:
        scroll_name (String): The unique name for this scroll.
        scroll_content_array (Array[String]): The RRE commands (e.g., [":: EXECUTE PING"]).

    Returns:
        bool: True if the scroll was successfully saved, false otherwise.
    """
    if scroll_index.has(scroll_name):
        _log_library_activity("Overwriting existing scroll: '" + scroll_name + "'.")
        var existing_slot = scroll_index[scroll_name]
        return _write_scroll_to_slot(scroll_name, scroll_content_array, existing_slot.start_y)

    if scroll_index.size() >= max_scrolls:
        _log_library_activity("ERROR: Library full. Cannot save '" + scroll_name + "'.")
        print_err("PXScrollLibrary: Library full. Max scrolls reached.")
        return false

    # Find the next available slot
    var next_y_offset = scroll_index.size() * scroll_entry_height # Simple sequential allocation
    if next_y_offset + scroll_entry_height > library_storage_region.size.y:
        _log_library_activity("ERROR: Not enough space for new scroll '" + scroll_name + "'.")
        print_err("PXScrollLibrary: Not enough vertical space for new scroll.")
        return false

    var success = _write_scroll_to_slot(scroll_name, scroll_content_array, next_y_offset)
    if success:
        scroll_index[scroll_name] = {"start_y": next_y_offset, "height": scroll_entry_height}
        _log_library_activity("Saved new scroll: '" + scroll_name + "' at Y=" + str(next_y_offset))
    return success


func load_scroll(scroll_name: String) -> Array[String]:
    """
    Loads a scroll (array of RRE commands) from the library's pixel memory region.

    Args:
        scroll_name (String): The name of the scroll to load.

    Returns:
        Array[String]: The loaded RRE commands, or an empty array if not found.
    """
    if not scroll_index.has(scroll_name):
        _log_library_activity("ERROR: Scroll '" + scroll_name + "' not found in library.")
        print_err("PXScrollLibrary: Scroll '" + scroll_name + "' not found.")
        return []

    var slot_info = scroll_index[scroll_name]
    var source_region = Rect2(
        library_storage_region.position.x,
        library_storage_region.position.y + slot_info.start_y,
        library_storage_region.size.x,
        slot_info.height
    )

    var full_scroll_content_ztxt = px_ztxt_memory.read_ztxt(source_region)
    var loaded_scroll_array = _parse_recorded_scroll_content(full_scroll_content_ztxt)

    _log_library_activity("Loaded scroll: '" + scroll_name + "' (" + str(loaded_scroll_array.size()) + " steps).")
    return loaded_scroll_array

func get_available_scroll_names() -> Array[String]:
    """Returns a list of all scroll names currently in the library."""
    var names = scroll_index.keys()
    names.sort()
    return names

# --- Internal Helper Functions ---

func _write_scroll_to_slot(scroll_name: String, scroll_content_array: Array[String], y_offset: int) -> bool:
    """Writes the scroll content to a specific vertical slot in the library region."""
    var target_region = Rect2(
        library_storage_region.position.x,
        library_storage_region.position.y + y_offset,
        library_storage_region.size.x,
        scroll_entry_height
    )

    # Add header and footer for identification
    var full_scroll_content = ["# RECORDED_SCROLL: " + scroll_name + " @ " + str(OS.get_unix_time_from_system())]
    full_scroll_content.append_array(scroll_content_array)
    full_scroll_content.append("# END_RECORDING")

    # Ensure content fits within the allocated height for the slot
    var line_height_px = px_ztxt_memory.px_glyph_compiler.GLYPH_HEIGHT + px_ztxt_memory.px_glyph_compiler.GLYPH_SPACING_Y
    var max_lines_in_slot = floor(scroll_entry_height / line_height_px)
    if full_scroll_content.size() > max_lines_in_slot:
        print_warn("PXScrollLibrary: Scroll '", scroll_name, "' content too long for slot. Truncating.")
        full_scroll_content = full_scroll_content.slice(0, max_lines_in_slot)

    return px_ztxt_memory.write_ztxt(target_region, "\n".join(full_scroll_content))


func _parse_recorded_scroll_content(full_scroll_content_ztxt: String) -> Array[String]:
    """Parses the raw zTXT content of a recorded scroll, removing headers/footers."""
    var lines = full_scroll_content_ztxt.split("\n", false)
    var parsed_scroll: Array[String] = []
    var in_content_section = false
    for line in lines:
        var trimmed_line = line.strip_edges()
        if trimmed_line.begins_with("# RECORDED_SCROLL:"):
            in_content_section = true
            continue
        if trimmed_line.begins_with("# END_RECORDING"):
            in_content_section = false
            break
        if in_content_section and not trimmed_line.is_empty():
            parsed_scroll.append(trimmed_line)
    return parsed_scroll

func _rebuild_index_from_memory():
    """
    Attempts to rebuild the scroll_index by scanning the library_storage_region
    for recorded scroll headers. This allows persistence across restarts.
    (This is a simplified scan; a robust system would need more complex parsing)
    """
    _log_library_activity("Rebuilding index from memory...")
    scroll_index.clear()
    var line_height = px_ztxt_memory.px_glyph_compiler.GLYPH_HEIGHT + px_ztxt_memory.px_glyph_compiler.GLYPH_SPACING_Y

    for i in range(max_scrolls):
        var y_offset = i * scroll_entry_height
        var scan_region_header = Rect2(
            library_storage_region.position.x,
            library_storage_region.position.y + y_offset,
            library_storage_region.size.x,
            line_height # Just scan the first line for header
        )
        if scan_region_header.position.y + scan_region_header.size.y > library_storage_region.position.y + library_storage_region.size.y:
            break # Out of bounds

        var header_line = px_ztxt_memory.read_ztxt(scan_region_header).strip_edges()
        if header_line.begins_with("# RECORDED_SCROLL:"):
            var parts = header_line.split(":", false, 1) # Split "RECORDED_SCROLL: NAME @ TIMESTAMP"
            if parts.size() > 1:
                var name_and_timestamp = parts[1].strip_edges()
                var name_parts = name_and_timestamp.split(" @ ", false, 1)
                var scroll_name = name_parts[0].strip_edges()
                scroll_index[scroll_name] = {"start_y": y_offset, "height": scroll_entry_height}
                _log_library_activity("Found existing scroll: '" + scroll_name + "' at Y=" + str(y_offset))
        elif not header_line.is_empty():
            # If it's not a header but not empty, it's either corrupted or an old format.
            # For robustness, you might clear this slot or flag it.
            pass # print_warn("PXScrollLibrary: Found non-header content at slot ", i, ": ", header_line.left(10))


# --- Logging ---

func _log_library_activity(message: String):
    """
    Helper function to log library activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("LIB: " + message)
    else:
        print("PXScrollLibrary (Console Log): ", message)

