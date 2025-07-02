# PXMemoryPatternDetector.gd
# Scans memory for specific byte patterns and executes callbacks on match.

extends Node

# --- Dependencies ---
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # Adjust path as needed

# --- Pattern Definition ---
class_name PatternRule
var pattern: Array[int]     # e.g., [72, 101, 108, 108, 111]
var callback: Callable
var persistent: bool = false
var has_fired: bool = false

func _init(_pattern: Array[int], _callback: Callable, _persistent := false):
    pattern = _pattern
    callback = _callback
    persistent = _persistent

# Scan dimensions
@export var scan_region: Rect2 = Rect2(0, 0, 64, 64) # Full memory area by default
# Note: It's good practice to ensure this scan_region does not exceed the
# actual dimensions of the PXMemoryRegion to avoid out-of-bounds reads.
# This can be validated in _ready or when setting the region.

var active_patterns: Array[PatternRule] = []

# --- Lifecycle ---
func _process(_delta):
    if not px_memory:
        print_err("PXMemoryPatternDetector: PXMemoryRegion not found. Cannot process patterns.")
        return

    # Iterate through a copy of active_patterns to allow modifications during iteration
    # (e.g., if a non-persistent rule removes itself)
    for i in range(active_patterns.size() - 1, -1, -1):
        var rule = active_patterns[i]
        var match_result = search_for_pattern(rule.pattern) # This returns true/false for now

        if match_result:
            if not rule.has_fired or rule.persistent:
                rule.callback.call(rule.pattern) # Callback receives the matched pattern
                rule.has_fired = true
        else:
            rule.has_fired = false # Reset if condition no longer met

# --- Pattern API ---

func add_pattern(pattern: Array[int], callback: Callable, persistent := false):
    """
    Registers a byte pattern to watch for.

    Args:
        pattern (Array[int]): e.g. [42, 101, 99], use -1 for wildcard (or null if you prefer, then update search_for_pattern)
                              Note: Using -1 for wildcard as Godot's Array[int] doesn't natively support null.
        callback (Callable): Function to call when pattern is matched. Takes (Array[int] matched_pattern).
        persistent (bool): Fire repeatedly if pattern persists.
    """
    # Ensure pattern elements are within byte range or are -1 for wildcard
    for i in range(pattern.size()):
        if pattern[i] != -1: # -1 as wildcard
            pattern[i] = clamp(pattern[i], 0, 255)

    active_patterns.append(PatternRule.new(pattern, callback, persistent))
    print("PXMemoryPatternDetector: Watching for pattern ", pattern)

func clear_patterns():
    active_patterns.clear()
    print("PXMemoryPatternDetector: All patterns cleared.")

# --- Pattern Search Core ---

func search_for_pattern(pattern: Array[int]) -> bool:
    """
    Searches for the given byte pattern within the defined scan_region of PXMemoryRegion.

    Args:
        pattern (Array[int]): The byte sequence to search for. Use -1 for wildcard.

    Returns:
        bool: True if the pattern is found, false otherwise.
    """
    if not px_memory:
        print_err("PXMemoryPatternDetector: PXMemoryRegion not available for pattern search.")
        return false
    if pattern.is_empty():
        return false

    var mem_rect = px_memory.memory_region_rect # Get the actual memory region from PXMemory
    var effective_scan_region = scan_region.intersection(mem_rect) # Ensure scan doesn't go outside memory

    if effective_scan_region.size.x <= 0 or effective_scan_region.size.y <= 0:
        print_warn("PXMemoryPatternDetector: Effective scan region is invalid or empty: ", effective_scan_region)
        return false

    var width = int(effective_scan_region.size.x)
    var height = int(effective_scan_region.size.y)
    var start_x = int(effective_scan_region.position.x)
    var start_y = int(effective_scan_region.position.y)

    # Flattened scan: raster order (left to right, top to bottom)
    var memory_stream: Array[int] = []
    for y in range(start_y, start_y + height):
        for x in range(start_x, start_x + width):
            var byte_val = px_memory.read_byte(x, y)
            # If read_byte returns -1 (error/out of bounds), treat it as a non-matchable value
            # or handle based on desired behavior. For now, we'll append it.
            memory_stream.append(byte_val)

    # Sliding window search
    var plen = pattern.size()
    if plen == 0: return false # No pattern to search for

    for i in range(memory_stream.size() - plen + 1):
        var match = true
        for j in range(plen):
            # Check for wildcard (-1) or exact match
            if pattern[j] != -1 and pattern[j] != memory_stream[i + j]:
                match = false
                break
        if match:
            return true
    return false

