# PXRoadmapRecorder.gd
# This module enables PXOS to "learn by doing" by recording the steps
# of executed RRE roadmaps back into a persistent, pixel-encoded scroll
# in a designated memory region. This creates a library of "learned behaviors."

extends Node

# --- Configuration ---
# The Rect2 defining the area on the canvas where recorded roadmaps will be stored.
# This should be a sub-region within PXMemoryRegion.
@export var recorded_scroll_storage_region: Rect2 = Rect2(0, 0, 40, 60) # Example: Top-left for recorded scrolls

# --- Dependencies ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To write recorded scrolls
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging recorder activity

# --- Internal State ---
# A dictionary to hold currently active recording sessions.
# Key: agent_id, Value: Array[String] (steps recorded so far)
var active_recordings: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_ztxt_memory or not px_scroll_log:
        print_err("PXRoadmapRecorder: Essential dependencies missing. Recorder disabled.")
        set_process(false)
        return

    print("PXRoadmapRecorder: Initialized. Ready to record executed roadmaps.")
    # Clear the storage region at startup
    px_ztxt_memory._clear_region(recorded_scroll_storage_region)

# --- Core Recording API ---

func start_recording(agent_id: String):
    """
    Starts a new recording session for a specific agent.
    Any RRE steps executed by this agent will be captured.

    Args:
        agent_id (String): The ID of the agent whose roadmap execution will be recorded.
    """
    if active_recordings.has(agent_id):
        print_warn("PXRoadmapRecorder: Recording for agent '", agent_id, "' already active. Restarting.")
        active_recordings[agent_id].clear() # Clear existing session
    else:
        active_recordings[agent_id] = []
    _log_recorder_activity("Recording started for agent: '" + agent_id + "'.")
    print("PXRoadmapRecorder: Recording started for agent: ", agent_id)


func record_step(agent_id: String, step_command: String):
    """
    Records a single RRE step command for an active recording session.
    This should be called by the agent itself or a monitor observing its execution.

    Args:
        agent_id (String): The ID of the agent.
        step_command (String): The RRE command that was just executed (e.g., ":: EXECUTE PING").
    """
    if active_recordings.has(agent_id):
        active_recordings[agent_id].append(step_command)
        # _log_recorder_activity("Recorded step for '" + agent_id + "': " + step_command.left(10)) # Too chatty
    else:
        print_warn("PXRoadmapRecorder: No active recording for agent '", agent_id, "'. Step not recorded.")


func stop_recording_and_save(agent_id: String, scroll_name: String):
    """
    Stops the recording session for an agent and saves the recorded roadmap
    to the designated storage region in memory.

    Args:
        agent_id (String): The ID of the agent.
        scroll_name (String): The name to give to the recorded scroll (for identification).

    Returns:
        bool: True if the roadmap was successfully saved, false otherwise.
    """
    if not active_recordings.has(agent_id):
        print_warn("PXRoadmapRecorder: No active recording to stop for agent '", agent_id, "'.")
        return false

    var recorded_roadmap = active_recordings.pop(agent_id) # Get and remove the recording
    if recorded_roadmap.is_empty():
        _log_recorder_activity("Recording for '" + agent_id + "' was empty. Not saving.")
        return false

    # Add a header to the recorded scroll for identification
    var full_scroll_content = ["# RECORDED_SCROLL: " + scroll_name + " by " + agent_id + " @ " + str(OS.get_unix_time_from_system())]
    full_scroll_content.append_array(recorded_roadmap)
    full_scroll_content.append("# END_RECORDING")

    # Write the recorded scroll to the storage region using PXZTXTMemory
    # For simplicity, we'll overwrite the entire region. In a real system,
    # you'd manage multiple recorded scrolls within this region (e.g., by index).
    var success = px_ztxt_memory.write_ztxt(recorded_scroll_storage_region, "\n".join(full_scroll_content))

    if success:
        _log_recorder_activity("Recorded scroll '" + scroll_name + "' saved from '" + agent_id + "'.")
        print("PXRoadmapRecorder: Recorded scroll '", scroll_name, "' saved from agent '", agent_id, "'.")
    else:
        _log_recorder_activity("FAILED to save recorded scroll '" + scroll_name + "' from '" + agent_id + "'.")
        print_err("PXRoadmapRecorder: Failed to save recorded scroll '", scroll_name, "' from agent '", agent_id, "'.")
    return success

# --- Logging ---

func _log_recorder_activity(message: String):
    """
    Helper function to log recorder activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("RECORDER: " + message)
    else:
        print("PXRoadmapRecorder (Console Log): ", message)

