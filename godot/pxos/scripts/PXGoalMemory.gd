# PXGoalMemory.gd
# This module acts as a historical record for PXOS's goals (directives).
# It stores information about each goal issued, including its type,
# timestamp, and eventually, its outcome. This enables long-term learning
# and helps prevent the system from repeating recently satisfied goals.

extends Node

# --- Goal Entry Definition ---
# A custom class to represent a single goal entry in memory.
class_name GoalEntry
var goal_type: String      # The high-level directive (e.g., "EXPLORE", "REPAIR_SYSTEM")
var timestamp: float       # When the goal was issued (OS.get_unix_time_from_system())
var outcome: String = "PENDING" # "PENDING", "SUCCESS", "FAILURE", "ABORTED"
var details: Dictionary = {} # Optional: additional context or parameters for the goal

func _init(_goal_type: String, _timestamp: float, _details: Dictionary = {}):
    goal_type = _goal_type
    timestamp = _timestamp
    details = _details

# --- Configuration ---
# Maximum number of goal entries to store in memory.
@export var max_goal_history: int = 100

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging goal memory activities

# --- Internal State ---
var goal_history: Array[GoalEntry] = [] # Stores the list of GoalEntry objects

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_warn("PXGoalMemory: PXScrollLog not found. Goal memory logs will go to console.")

    print("PXGoalMemory: Initialized. Ready to record goals.")

# --- Core Goal Memory API ---

func record_goal(goal_type: String, details: Dictionary = {}) -> GoalEntry:
    """
    Records a new goal (directive) into the goal history.

    Args:
        goal_type (String): The type of goal being recorded.
        details (Dictionary): Optional dictionary for additional context.

    Returns:
        GoalEntry: The newly created GoalEntry object.
    """
    var new_entry = GoalEntry.new(goal_type, OS.get_unix_time_from_system(), details)
    goal_history.append(new_entry)

    # Trim history if it exceeds max_goal_history
    while goal_history.size() > max_goal_history:
        goal_history.pop_front() # Remove the oldest entry

    _log_goal_memory_activity("RECORD: " + goal_type.left(15) + " (Total: " + str(goal_history.size()) + ")")
    print("PXGoalMemory: Recorded goal: ", goal_type, " at ", new_entry.timestamp)
    return new_entry

func update_goal_outcome(goal_entry: GoalEntry, outcome: String, details: Dictionary = {}):
    """
    Updates the outcome of a previously recorded goal.
    This would typically be called by PXRoadmapExecutor or PXDirective when a plan finishes.

    Args:
        goal_entry (GoalEntry): The GoalEntry object to update.
        outcome (String): The new outcome ("SUCCESS", "FAILURE", "ABORTED").
        details (Dictionary): Optional additional details about the outcome.
    """
    if goal_entry in goal_history:
        goal_entry.outcome = outcome
        goal_entry.details.merge(details, true) # Merge new details
        _log_goal_memory_activity("UPDATE: " + goal_entry.goal_type.left(15) + " -> " + outcome)
        print("PXGoalMemory: Updated goal '", goal_entry.goal_type, "' to outcome: ", outcome)
    else:
        print_warn("PXGoalMemory: Attempted to update non-existent goal entry.")

func get_goal_history(filter_type: String = "", filter_outcome: String = "") -> Array[GoalEntry]:
    """
    Retrieves a filtered list of goal entries from the history.

    Args:
        filter_type (String): Optional. Filter by goal type.
        filter_outcome (String): Optional. Filter by outcome.

    Returns:
        Array[GoalEntry]: A new array containing the filtered GoalEntry objects.
    """
    var filtered_history: Array[GoalEntry] = []
    for entry in goal_history:
        var type_match = filter_type.is_empty() or entry.goal_type == filter_type
        var outcome_match = filter_outcome.is_empty() or entry.outcome == filter_outcome
        if type_match and outcome_match:
            filtered_history.append(entry)
    return filtered_history

func get_last_goal_of_type(goal_type: String) -> GoalEntry:
    """
    Retrieves the most recent goal of a specific type.

    Returns:
        GoalEntry: The most recent GoalEntry of the specified type, or null if not found.
    """
    for i in range(goal_history.size() - 1, -1, -1): # Iterate backwards for most recent
        if goal_history[i].goal_type == goal_type:
            return goal_history[i]
    return null

# --- Logging ---

func _log_goal_memory_activity(message: String):
    """
    Helper function to log goal memory activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("GOALMEM: " + message)
    else:
        print("PXGoalMemory (Console Log): ", message)

