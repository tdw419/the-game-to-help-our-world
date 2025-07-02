# PXThoughtPlayer.gd
# This script enables PXOS to "replay" its introspection history automatically.
# It iterates through the entries stored in PXIntrospectionMemory.gd,
# displaying them one by one (or in chunks) on the PXThoughtTimeline.gd,
# allowing for automated review of past cognitive states.

extends Node

# --- Configuration ---
# How often the player advances to the next introspection entry (in seconds).
@export var playback_interval_sec: float = 1.0

# Whether the player should loop back to the beginning when it reaches the end of history.
@export var loop_playback: bool = true

# --- Dependencies ---
@onready var px_introspection_memory: PXIntrospectionMemory = get_node_or_null("../PXIntrospectionMemory") # To read introspection history
@onready var px_thought_timeline: PXThoughtTimeline = get_node_or_null("../PXThoughtTimeline") # To control the timeline's scroll
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging player activity

# --- Internal State ---
var current_playback_index: int = 0 # The index of the introspection entry currently being "played"
var is_playing: bool = false
var time_since_last_playback: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_introspection_memory or not px_thought_timeline or not px_scroll_log:
        print_err("PXThoughtPlayer: Essential dependencies missing. Playback disabled.")
        set_process(false)
        return

    print("PXThoughtPlayer: Initialized. Ready for playback.")

func _process(delta):
    if is_playing:
        time_since_last_playback += delta
        if time_since_last_playback >= playback_interval_sec:
            time_since_last_playback = 0.0
            _play_next_entry()

# --- Playback Control API ---

func start_playback():
    """Starts the automatic playback of introspection history."""
    if is_playing:
        print_warn("PXThoughtPlayer: Playback already active.")
        return

    is_playing = true
    current_playback_index = 0 # Start from the beginning
    _log_player_activity("Playback started.")
    print("PXThoughtPlayer: Starting playback.")
    _play_next_entry() # Play the very first entry immediately

func stop_playback():
    """Stops the automatic playback."""
    if not is_playing:
        print_warn("PXThoughtPlayer: Playback not active.")
        return

    is_playing = false
    _log_player_activity("Playback stopped.")
    print("PXThoughtPlayer: Playback stopped.")

func _play_next_entry():
    """
    Advances the playback to the next introspection entry and updates the timeline.
    """
    var history = px_introspection_memory.get_introspection_history()
    if history.is_empty():
        _log_player_activity("History empty. Stopping playback.")
        stop_playback()
        return

    if current_playback_index >= history.size():
        if loop_playback:
            _log_player_activity("End of history. Looping back.")
            current_playback_index = 0 # Loop back to start
        else:
            _log_player_activity("End of history. Playback complete.")
            stop_playback()
            return

    var entry_to_play = history[current_playback_index]
    _log_player_activity("Playing: " + entry_to_play.explanation.left(20) + "...")

    # Instruct PXThoughtTimeline to scroll to this entry
    # This requires PXThoughtTimeline to have a method to scroll to a specific index.
    # We will assume PXThoughtTimeline.scroll_to_index(index) exists.
    # Since PXThoughtTimeline displays in reverse order (most recent at top),
    # we need to calculate the correct scroll_offset_y for it.
    var display_index_in_timeline = (history.size() - 1) - current_playback_index # Convert to timeline's internal index
    px_thought_timeline.scroll_to_index(display_index_in_timeline)

    current_playback_index += 1

# --- Logging ---

func _log_player_activity(message: String):
    """
    Helper function to log player activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PLAYER: " + message)
    else:
        print("PXThoughtPlayer (Console Log): ", message)

