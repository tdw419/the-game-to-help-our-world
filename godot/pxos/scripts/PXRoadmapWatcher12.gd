# PXRoadmapWatcher.gd
# This module acts as a vigilant watcher for new roadmap scrolls in a designated
# memory region. When a new roadmap is detected, it automatically loads and
# activates it via PXRoadmapExecutor.gd, enabling autonomous roadmap ingestion.
#
# UPDATED: Now specifically watches the ROADMAP_SCROLL_REGION (where map.py embeds roadmaps)
# and uses PXZTXTMemory to read its content.

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas where the watcher will look for new roadmaps.
# This should match the ROADMAP_SCROLL_REGION_ORIGIN and dimensions from map.py.
@export var watched_roadmap_region: Rect2 = Rect2(10, 80, 60, 40) # Matches map.py's ROADMAP_SCROLL_REGION

# How often the watcher scans its region for new roadmaps (in seconds).
@export var scan_frequency_sec: float = 2.0

# --- Dependencies ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To read roadmaps from memory
@onready var px_roadmap_executor: PXRoadmapExecutor = get_node_or_null("../PXRoadmapExecutor") # To execute detected roadmaps
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging watcher activity

# --- Internal State ---
var time_since_last_scan: float = 0.0
var _last_read_roadmap_hash: int = 0 # To detect changes in the watched region

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_ztxt_memory or not px_roadmap_executor or not px_scroll_log:
        print_err("PXRoadmapWatcher: Essential dependencies missing. Watcher disabled.")
        set_process(false)
        return

    print("PXRoadmapWatcher: Initialized. Ready to watch for new roadmaps in region: ", watched_roadmap_region)
    # Clear the watched region at startup (optional, as map.py might draw into it)
    # px_ztxt_memory._clear_region(watched_roadmap_region) # Don't clear if map.py draws into it

func _process(delta):
    time_since_last_scan += delta
    if time_since_last_scan >= scan_frequency_sec:
        time_since_last_scan = 0.0
        _scan_for_new_roadmap()

# --- Core Watcher Logic ---

func _scan_for_new_roadmap():
    """
    Scans the watched_roadmap_region for new roadmap content.
    If a new roadmap is detected, it triggers its execution.
    """
    var current_roadmap_ztxt = px_ztxt_memory.read_ztxt(watched_roadmap_region).strip_edges()

    # Calculate a simple hash to detect changes
    var current_hash = current_roadmap_ztxt.hash()

    if current_hash != _last_read_roadmap_hash and not current_roadmap_ztxt.is_empty():
        _log_watcher_activity("New roadmap detected! Hash: " + str(current_hash))
        print("PXRoadmapWatcher: New roadmap detected in watched region.")

        # Optionally clear the region to consume the roadmap.
        # If map.py is the sole writer, it will redraw, so clearing here might cause flicker.
        # For a one-shot trigger, clearing is good. For continuous monitoring, maybe not.
        # For now, let's clear it to ensure it's consumed.
        px_ztxt_memory.write_ztxt(watched_roadmap_region, "")
        _last_read_roadmap_hash = 0 # Reset hash after consumption

        # Parse the roadmap content
        var roadmap_steps = _parse_roadmap_content(current_roadmap_ztxt)

        if not roadmap_steps.is_empty():
            # Trigger execution of the new roadmap
            px_roadmap_executor.execute_roadmap(roadmap_steps)
            _log_watcher_activity("Activated new roadmap (" + str(roadmap_steps.size()) + " steps).")
        else:
            _log_watcher_activity("Detected empty or malformed roadmap. Not activating.")
    elif current_roadmap_ztxt.is_empty():
        _last_read_roadmap_hash = 0 # Reset hash if region becomes empty
        # _log_watcher_activity("Watched region is empty.") # Too chatty


func _parse_roadmap_content(ztxt_content: String) -> Array[String]:
    """
    Parses the raw zTXT content into an array of roadmap steps.
    Assumes each line is a step. Handles headers/footers.
    """
    var lines = ztxt_content.split("\n", false)
    var parsed_roadmap: Array[String] = []
    var in_content_section = false
    for line in lines:
        var trimmed_line = line.strip_edges()
        if trimmed_line.begins_with("# RECORDED_SCROLL:") or trimmed_line.begins_with(":: BEGIN ROADMAP"):
            in_content_section = true
            continue
        if trimmed_line.begins_with("# END_RECORDING") or trimmed_line.begins_with(":: END ROADMAP ::"):
            in_content_section = false
            break
        if in_content_section and not trimmed_line.is_empty():
            parsed_roadmap.append(trimmed_line)
    return parsed_roadmap

# --- Logging ---

func _log_watcher_activity(message: String):
    """
    Helper function to log watcher activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("WATCHER: " + message)
    else:
        print("PXRoadmapWatcher (Console Log): ", message)

