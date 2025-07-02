# PXDigestExporter.gd
# This module enables PXOS to capture and export a snapshot of its entire
# visual memory (the DisplayScreen) and potentially other key system states
# into a storable format (conceptual .pxdigest file). This is crucial for
# persistence, debugging, and later analysis of system evolution.

extends Node

# --- Configuration ---
# How often the exporter will log its status (if active).
@export var export_log_frequency_sec: float = 5.0

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # The source of visual memory
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging exporter activity
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # To get underlying image data
@onready var px_emotion_engine: PXEmotionEngine = get_node_or_null("../PXEmotionEngine") # To include emotional state
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To include goal history

# --- Internal State ---
var time_since_last_log: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    if not display_screen or not px_scroll_log or not px_memory:
        print_err("PXDigestExporter: Essential dependencies missing. Exporter disabled.")
        set_process(false)
        return

    print("PXDigestExporter: Initialized. Ready to export snapshots.")

func _process(delta):
    # This module doesn't run continuous _process logic by default,
    # it's triggered by external commands (e.g., from PXReflexDaemon).
    # This _process is just for optional periodic logging.
    time_since_last_log += delta
    if time_since_last_log >= export_log_frequency_sec:
        time_since_last_log = 0.0
        # _log_exporter_activity("Exporter active, awaiting command.") # Too chatty
        pass

# --- Core Export API ---

func export_state(snapshot_name: String = "default_snapshot") -> bool:
    """
    Captures the current state of PXOS (visual memory + key system states)
    and conceptually saves it as a .pxdigest snapshot.

    Args:
        snapshot_name (String): A name for the snapshot.

    Returns:
        bool: True if the export was conceptually successful, false otherwise.
    """
    _log_exporter_activity("Initiating export for snapshot: '" + snapshot_name + "'...")
    print("PXDigestExporter: Capturing state for snapshot: ", snapshot_name)

    if not display_screen or not display_screen.texture:
        _log_exporter_activity("ERROR: Display screen not ready for snapshot.")
        print_err("PXDigestExporter: Display screen not ready for snapshot.")
        return false

    var display_image = display_screen.texture.get_data()
    if not display_image:
        _log_exporter_activity("ERROR: Could not get display image data.")
        print_err("PXDigestExporter: Could not get display image data.")
        return false

    # --- 1. Capture Visual Memory (DisplayScreen Pixels) ---
    # In a real Godot app, you would save this Image to a file.
    # Example: display_image.save_png("user://pxos_snapshots/" + snapshot_name + "_display.png")
    # For this conceptual RRE, we'll just acknowledge capture.
    _log_exporter_activity("Captured display image (conceptual .png).")

    # --- 2. Capture Key System States (as JSON string) ---
    var system_state_data: Dictionary = {
        "snapshot_name": snapshot_name,
        "timestamp": OS.get_unix_time_from_system(),
        "display_dimensions": {
            "width": display_image.get_width(),
            "height": display_image.get_height()
        },
        "emotions": {}, # Placeholder
        "goal_history_summary": [], # Placeholder
        # Add other relevant states here (e.g., agent moods, current roadmap steps, etc.)
    }

    if px_emotion_engine:
        system_state_data["emotions"] = px_emotion_engine.get_all_emotions()
        _log_exporter_activity("Captured emotional state.")

    if px_goal_memory:
        # Get a summary or a subset of goal history to avoid huge files
        var recent_goals = px_goal_memory.get_goal_history() # Get all for simplicity
        var goal_summary_list = []
        for goal_entry in recent_goals:
            goal_summary_list.append({
                "type": goal_entry.goal_type,
                "outcome": goal_entry.outcome,
                "ts": goal_entry.timestamp
            })
        system_state_data["goal_history_summary"] = goal_summary_list
        _log_exporter_activity("Captured goal history summary.")

    # Convert the system state data to a JSON string
    var system_state_json = JSON.stringify(system_state_data, "\t") # Pretty print with tabs
    # Example: FileAccess.open("user://pxos_snapshots/" + snapshot_name + "_state.json", FileAccess.WRITE).store_string(system_state_json)
    _log_exporter_activity("Captured system state (conceptual .json).")

    # --- 3. Conceptual Storage ---
    # In a real Godot app, you'd save these to disk.
    # For RRE, we acknowledge the conceptual "save".
    _log_exporter_activity("Snapshot '" + snapshot_name + "' conceptually saved.")
    print("PXDigestExporter: Snapshot '", snapshot_name, "' conceptually exported.")

    return true

# --- Logging ---

func _log_exporter_activity(message: String):
    """
    Helper function to log exporter activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("EXPORTER: " + message)
    else:
        print("PXDigestExporter (Console Log): ", message)

