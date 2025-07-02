# PXRoadmapTrialManager.gd
# This module manages the trial execution of roadmaps, particularly
# mutated or previously failed ones. It orchestrates retries and
# idle-time experimentation, allowing PXOS to test alternate strategies
# and reinforce learning.

extends Node

# --- Configuration ---
# How often the trial manager checks for roadmaps to trial (in seconds).
@export var trial_check_frequency_sec: float = 15.0

# Maximum number of trials for a single roadmap variant before giving up or escalating.
@export var max_trials_per_roadmap_variant: int = 3

# --- Dependencies ---
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To get roadmap results
@onready var px_scroll_library: PXScrollLibrary = get_node_or_null("../PXScrollLibrary") # To load roadmaps
@onready var px_roadmap_executor: PXRoadmapExecutor = get_node_or_null("../PXRoadmapExecutor") # To execute roadmaps
@onready var px_roadmap_selector: PXRoadmapSelector = get_node_or_null("../PXRoadmapSelector") # To select roadmaps
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging trial activity

# --- Internal State ---
var time_since_last_trial_check: float = 0.0
# Dictionary to track trials: { "roadmap_name": { "trial_count": int, "last_trial_timestamp": float } }
var _roadmap_trial_data: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_roadmap_registry or not px_scroll_library or not px_roadmap_executor or not px_roadmap_selector or not px_scroll_log:
        print_err("PXRoadmapTrialManager: Essential dependencies missing. Trial Manager disabled.")
        set_process(false)
        return

    print("PXRoadmapTrialManager: Initialized. Ready to manage roadmap trials.")

func _process(delta):
    time_since_last_trial_check += delta
    if time_since_last_trial_check >= trial_check_frequency_sec:
        time_since_last_trial_check = 0.0
        _evaluate_and_queue_trials()

# --- Core Trial Management Logic ---

func _evaluate_and_queue_trials():
    """
    Evaluates which roadmaps need trial runs (e.g., recently mutated,
    previously failed, or low-performing ones) and queues them for execution.
    """
    _log_trial_activity("Evaluating roadmaps for trial runs...")

    var all_roadmap_names = px_scroll_library.get_available_scroll_names()
    var candidates_for_trial: Array[String] = []

    for roadmap_name in all_roadmap_names:
        var last_run_result = _get_last_run_outcome(roadmap_name)
        var trial_count = _roadmap_trial_data.get(roadmap_name, {}).get("trial_count", 0)

        # Condition 1: Recently mutated roadmaps (no recent successful trial)
        # This requires PXScrollLibrary to store mutation metadata.
        # For now, we'll conceptually mark a roadmap as "mutated" if its name contains "_mutated_".
        if roadmap_name.find("_mutated_") != -1 and last_run_result != "SUCCESS" and trial_count < max_trials_per_roadmap_variant:
            candidates_for_trial.append(roadmap_name)
            _log_trial_activity("  Candidate (Mutated): " + roadmap_name + " (Trials: " + str(trial_count) + ")")
            continue # Move to next candidate

        # Condition 2: Roadmaps that previously failed and haven't reached max trials
        if last_run_result == "FAILURE" and trial_count < max_trials_per_roadmap_variant:
            candidates_for_trial.append(roadmap_name)
            _log_trial_activity("  Candidate (Failed): " + roadmap_name + " (Trials: " + str(trial_count) + ")")
            continue

        # Condition 3: Idle-time experimentation (select a low-performing but not stagnant roadmap)
        # Only if executor is not active and no other critical trials are pending
        if not px_roadmap_executor.roadmap_active and candidates_for_trial.is_empty():
            # This would involve PXGoalScorer to find low-performing goals/roadmaps
            # For now, let's just pick a random one if nothing else is critical.
            pass # Implement more complex idle logic here

    _queue_and_execute_trials(candidates_for_trial)


func _queue_and_execute_trials(roadmap_names: Array[String]):
    """
    Queues and executes trial runs for the given roadmaps.
    Prioritizes based on internal logic (e.g., most recent failure, or random).
    """
    if roadmap_names.is_empty():
        _log_trial_activity("No roadmaps queued for trial.")
        return

    # Simple prioritization: pick the first one.
    # More advanced: sort by last failure time, lowest score, etc.
    var roadmap_to_trial = roadmap_names[0]

    if px_roadmap_executor.roadmap_active:
        _log_trial_activity("Executor busy. Will retry trial later.")
        return

    _log_trial_activity("Executing trial for: '" + roadmap_to_trial + "'.")

    var loaded_steps = px_scroll_library.load_scroll(roadmap_to_trial)
    if loaded_steps.is_empty():
        _log_trial_activity("ERROR: Failed to load roadmap '" + roadmap_to_trial + "' for trial.")
        return

    # Update trial data
    _roadmap_trial_data[roadmap_to_trial] = _roadmap_trial_data.get(roadmap_to_trial, {"trial_count": 0})
    _roadmap_trial_data[roadmap_to_trial]["trial_count"] += 1
    _roadmap_trial_data[roadmap_to_trial]["last_trial_timestamp"] = OS.get_unix_time_from_system()

    # Execute the roadmap (ensure PXRoadmapExecutor can handle GoalEntry for tracking)
    # This requires a conceptual GoalEntry for trial runs.
    var trial_goal_entry = GoalEntry.new(roadmap_to_trial, OS.get_unix_time_from_system(), {"trial_run": true, "trial_num": _roadmap_trial_data[roadmap_to_trial]["trial_count"]})
    px_roadmap_executor.load_and_execute_roadmap_from_memory(trial_goal_entry)


# --- Helper Functions ---

func _get_last_run_outcome(roadmap_name: String) -> String:
    """
    Retrieves the outcome of the last execution of a specific roadmap.
    Returns "SUCCESS", "FAILURE", "ABORTED", "PENDING", or "NONE".
    """
    var all_results = px_roadmap_registry.get_all_roadmap_results()
    for i in range(all_results.size() - 1, -1, -1): # Iterate backwards for most recent
        var entry = all_results[i]
        if entry.roadmap == roadmap_name:
            return entry.outcome
    return "NONE" # No previous runs found

# --- Logging ---

func _log_trial_activity(message: String):
    """
    Helper function to log trial manager activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("TRIAL: " + message)
    else:
        print("PXRoadmapTrialManager (Console Log): ", message)

