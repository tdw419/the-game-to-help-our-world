# PXGoalAdvisor.gd
# This module acts as a decision-support system for PXOS's goal-setting.
# It analyzes the historical data in PXGoalMemory.gd to provide advice
# on whether a specific goal should be attempted, based on factors like
# recent execution, past failures, or stagnation.

extends Node

# --- Configuration ---
# Default cooldown period (in seconds) before a goal of the same type can be re-attempted.
@export var default_cooldown_sec: float = 30.0

# Threshold for considering a goal "stagnant" (e.g., how many recent failures indicate stagnation).
@export var stagnation_failure_threshold: int = 3

# --- Dependencies ---
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # Reference to the goal history
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging advice

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_goal_memory:
        print_err("PXGoalAdvisor: PXGoalMemory node not found. Advisor capabilities disabled.")
        set_process(false) # Disable _process if essential dependency is missing
        return
    if not px_scroll_log:
        print_warn("PXGoalAdvisor: PXScrollLog not found. Advisor logs will go to console.")

    print("PXGoalAdvisor: Initialized. Ready to provide goal advice.")

# --- Core Advisory API ---

func should_attempt_goal(goal_type: String, custom_cooldown_sec: float = -1.0) -> bool:
    """
    Advises whether PXOS should attempt a specific goal based on its history.

    Args:
        goal_type (String): The type of goal to check (e.g., "EXPLORE").
        custom_cooldown_sec (float): Optional. A custom cooldown for this specific check.
                                     If -1.0, uses default_cooldown_sec.

    Returns:
        bool: True if the goal should be attempted, false otherwise.
    """
    _log_advisor_activity("ADVISE: Should attempt '" + goal_type + "'?")

    var cooldown = default_cooldown_sec
    if custom_cooldown_sec >= 0:
        cooldown = custom_cooldown_sec

    # Check if the goal was attempted too recently
    if is_goal_too_recent(goal_type, cooldown):
        _log_advisor_activity("  Reason: Too recent. Skipping.")
        return false

    # Check if the goal is stagnant (repeatedly failing)
    if is_goal_stagnant(goal_type, stagnation_failure_threshold):
        _log_advisor_activity("  Reason: Stagnant (repeated failures). Skipping.")
        return false

    _log_advisor_activity("  Advice: OK to attempt.")
    return true

func is_goal_too_recent(goal_type: String, cooldown_sec: float) -> bool:
    """
    Checks if a goal of the given type was issued too recently.

    Args:
        goal_type (String): The type of goal to check.
        cooldown_sec (float): The cooldown period in seconds.

    Returns:
        bool: True if the goal was issued within the cooldown period, false otherwise.
    """
    var last_goal_entry = px_goal_memory.get_last_goal_of_type(goal_type)
    if last_goal_entry:
        var time_since_last_attempt = OS.get_unix_time_from_system() - last_goal_entry.timestamp
        if time_since_last_attempt < cooldown_sec:
            print("PXGoalAdvisor: Goal '", goal_type, "' attempted ", time_since_last_attempt, "s ago. Cooldown: ", cooldown_sec, "s.")
            return true
    return false

func is_goal_stagnant(goal_type: String, failure_threshold: int) -> bool:
    """
    Checks if a goal of the given type has repeatedly failed, indicating stagnation.

    Args:
        goal_type (String): The type of goal to check.
        failure_threshold (int): The number of consecutive failures to consider it stagnant.

    Returns:
        bool: True if the goal is considered stagnant, false otherwise.
    """
    var recent_failures = 0
    var history = px_goal_memory.get_goal_history(goal_type) # Get all past attempts of this type

    # Iterate backwards to check for consecutive failures
    for i in range(history.size() - 1, -1, -1):
        var entry = history[i]
        if entry.outcome == "FAILURE":
            recent_failures += 1
        else:
            # If a success or pending is encountered, the streak of failures is broken
            break
        if recent_failures >= failure_threshold:
            print("PXGoalAdvisor: Goal '", goal_type, "' is stagnant (", recent_failures, " consecutive failures).")
            return true
    return false

func get_recent_failures(goal_type: String) -> int:
    """
    Returns the count of consecutive recent failures for a given goal type.
    """
    var failures = 0
    var history = px_goal_memory.get_goal_history(goal_type)
    for i in range(history.size() - 1, -1, -1):
        if history[i].outcome == "FAILURE":
            failures += 1
        else:
            break
    return failures

# --- Logging ---

func _log_advisor_activity(message: String):
    """
    Helper function to log advisor activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("ADVISOR: " + message)
    else:
        print("PXGoalAdvisor (Console Log): ", message)

