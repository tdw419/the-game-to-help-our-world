# PXRoadmapRegistry.gd
# This module acts as a persistent registry for all completed roadmap executions.
# It stores metadata and fitness scores for each run, enabling PXOS to
# learn from past performance, track strategy effectiveness, and inform
# future roadmap selection.

extends Node

# --- Configuration ---
# The filename within PXFS where the roadmap execution results will be stored.
@export var registry_filename: String = "roadmap_registry.json"

# --- Dependencies ---
@onready var px_fs_writer: PXFSWriter = get_node_or_null("../PXFSWriter") # To write to PXFS
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read from PXFS
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging registry activity

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_fs_writer or not px_fs_reader or not px_scroll_log:
        print_err("PXRoadmapRegistry: Essential dependencies missing. Registry disabled.")
        set_process(false)
        return

    print("PXRoadmapRegistry: Initialized. Ready to register roadmap results.")
    # Ensure the registry file exists or is initialized as an empty JSON array
    _ensure_registry_file_exists()

# --- Core Registry API ---

func register_roadmap_result(
    roadmap_name: String,
    goal_entry: GoalEntry, # The GoalEntry associated with this roadmap execution
    score: float,
    duration: float,
    steps: int,
    mutations: int
):
    """
    Registers the result of a completed roadmap execution into the persistent registry.

    Args:
        roadmap_name (String): The name of the roadmap that was executed.
        goal_entry (GoalEntry): The GoalEntry object for this execution.
        score (float): The fitness score calculated for this execution.
        duration (float): The time taken for the roadmap to execute.
        steps (int): The number of steps in the roadmap.
        mutations (int): The number of mutations applied to this roadmap or its variant.
    """
    _log_registry_activity("REGISTER: " + roadmap_name + " (Score: " + str(snapped(score, 0.01)) + ")")

    var entry = {
        "roadmap": roadmap_name,
        "goal_type": goal_entry.goal_type,
        "outcome": goal_entry.outcome,
        "score": score,
        "duration": duration,
        "steps": steps,
        "mutations": mutations,
        "timestamp": OS.get_unix_time_from_system(),
        "details": goal_entry.details # Include any extra goal details
    }

    # Read current registry, append new entry, and write back
    var current_registry_content = _read_registry_content()
    var registry_array = []
    if not current_registry_content.is_empty():
        # Attempt to parse as JSON array
        var parse_result = JSON.parse_string(current_registry_content)
        if parse_result is Array:
            registry_array = parse_result
        else:
            print_err("PXRoadmapRegistry: Existing registry file is not a valid JSON array. Overwriting.")

    registry_array.append(entry)

    var json_content = JSON.stringify(registry_array, "\t") # Pretty print for readability
    
    # Write the updated JSON content back to PXFS
    var success = px_fs_writer.write_file_auto(registry_filename, json_content, Color(0.8, 0.5, 0.0), Color(0.0, 0.0, 1.0), Color(0.5, 0.0, 0.5)) # Orange=Registry, Blue=Data, Purple=System
    if success:
        _log_registry_activity("Registry updated in PXFS.")
    else:
        _log_registry_activity("ERROR: Failed to update registry in PXFS.")


func get_all_roadmap_results() -> Array[Dictionary]:
    """
    Retrieves all recorded roadmap execution results from the registry.

    Returns:
        Array[Dictionary]: An array of dictionaries, each representing a roadmap run.
    """
    var content = _read_registry_content()
    if content.is_empty():
        return []

    var parse_result = JSON.parse_string(content)
    if parse_result is Array:
        return parse_result
    else:
        print_err("PXRoadmapRegistry: Registry file content is not a valid JSON array.")
        return []

func _read_registry_content() -> String:
    """Reads the raw content of the registry file from PXFS."""
    return px_fs_reader.read_file_by_name(registry_filename)

func _ensure_registry_file_exists():
    """Ensures the registry file exists in PXFS, creating it if necessary."""
    var content = px_fs_reader.read_file_by_name(registry_filename)
    if content.is_empty() or JSON.parse_string(content) == null: # Check if empty or invalid JSON
        _log_registry_activity("Registry file not found or invalid. Creating new one.")
        px_fs_writer.write_file_auto(registry_filename, "[]", Color(0.8, 0.5, 0.0), Color(0.0, 0.0, 1.0), Color(0.5, 0.0, 0.5))


# --- Logging ---

func _log_registry_activity(message: String):
    """
    Helper function to log registry activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("REGISTRY: " + message)
    else:
        print("PXRoadmapRegistry (Console Log): ", message)

