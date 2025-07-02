# PXEmotionEngine.gd
# This module simulates internal emotional states for PXOS.
# Emotions (e.g., satisfaction, frustration, fear, joy) change based on
# the outcomes of goals recorded in PXGoalMemory.gd. These emotional states
# can then influence other modules like PXMotivationCore.gd.

extends Node

# --- Configuration ---
# How often the emotion engine evaluates and updates emotional states.
@export var emotion_update_frequency_sec: float = 1.0 # Update emotions every second

# Decay rate for emotions (per second) - emotions naturally fade over time.
@export var emotion_decay_rate: float = 0.05

# --- Emotional State Properties (Ranges from 0.0 to 1.0) ---
var emotions: Dictionary = {
    "satisfaction": 0.0, # Increases with SUCCESS outcomes
    "frustration": 0.0,  # Increases with FAILURE outcomes
    "curiosity_joy": 0.0, # Increases with EXPLORE success
    "fear": 0.0,         # Increases with critical system errors or repeated failures
    "boredom_level": 0.0 # Increases with low activity or repetitive tasks
}

# --- Dependencies ---
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To read goal outcomes
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging emotional changes

# --- Internal State ---
var time_since_last_emotion_update: float = 0.0
var _last_goal_history_size: int = 0 # To detect new goal outcomes

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_goal_memory:
        print_err("PXEmotionEngine: PXGoalMemory node not found. Emotion engine disabled.")
        set_process(false)
        return
    if not px_scroll_log:
        print_warn("PXEmotionEngine: PXScrollLog not found. Emotional logs will go to console.")

    print("PXEmotionEngine: Initialized. Ready to feel.")
    # Initialize _last_goal_history_size with current history size
    _last_goal_history_size = px_goal_memory.get_goal_history().size()

func _process(delta):
    time_since_last_emotion_update += delta
    if time_since_last_emotion_update >= emotion_update_frequency_sec:
        time_since_last_emotion_update = 0.0
        _update_emotions_from_outcomes()
        _decay_emotions()
        _log_current_emotions() # Log current states periodically

# --- Core Emotion Logic ---

func _update_emotions_from_outcomes():
    """
    Scans PXGoalMemory for new goal outcomes and adjusts emotional states.
    """
    var current_history = px_goal_memory.get_goal_history()
    if current_history.size() <= _last_goal_history_size:
        return # No new outcomes to process

    # Process only new outcomes since last check
    for i in range(_last_goal_history_size, current_history.size()):
        var goal_entry = current_history[i]
        _process_goal_outcome(goal_entry)

    _last_goal_history_size = current_history.size() # Update for next check

func _process_goal_outcome(goal_entry: GoalEntry):
    """
    Adjusts emotions based on a single goal's outcome.
    """
    var goal_type = goal_entry.goal_type
    var outcome = goal_entry.outcome

    match outcome:
        "SUCCESS":
            emotions["satisfaction"] = clampf(emotions["satisfaction"] + 0.2, 0.0, 1.0)
            _log_emotion_activity("Satisfaction increased (Goal: " + goal_type + ")")
            if goal_type.begins_with("EXPLORE"):
                emotions["curiosity_joy"] = clampf(emotions["curiosity_joy"] + 0.1, 0.0, 1.0)
                _log_emotion_activity("Curiosity joy increased (Goal: " + goal_type + ")")
        "FAILURE":
            emotions["frustration"] = clampf(emotions["frustration"] + 0.25, 0.0, 1.0)
            _log_emotion_activity("Frustration increased (Goal: " + goal_type + ")")
            if goal_type.begins_with("REPAIR") or goal_type.begins_with("HALT"):
                emotions["fear"] = clampf(emotions["fear"] + 0.15, 0.0, 1.0)
                _log_emotion_activity("Fear increased (Goal: " + goal_type + ")")
        "ABORTED":
            emotions["boredom_level"] = clampf(emotions["boredom_level"] + 0.1, 0.0, 1.0)
            _log_emotion_activity("Boredom increased (Goal: " + goal_type + ")")
        _:
            pass # No specific emotional impact for PENDING or unknown outcomes

func _decay_emotions():
    """
    Gradually reduces emotional levels over time.
    """
    for emotion_name in emotions.keys():
        emotions[emotion_name] = clampf(emotions[emotion_name] - emotion_decay_rate, 0.0, 1.0)

# --- API for Other Modules to Query Emotions ---

func get_emotion_level(emotion_name: String) -> float:
    """
    Returns the current level of a specific emotion (0.0 to 1.0).
    """
    return emotions.get(emotion_name, 0.0)

func get_all_emotions() -> Dictionary:
    """
    Returns a dictionary of all current emotional states.
    """
    return emotions.duplicate(true) # Return a copy

# --- Logging ---

func _log_emotion_activity(message: String):
    """
    Helper function to log emotional activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("EMOTION: " + message)
    else:
        print("PXEmotionEngine (Console Log): ", message)

func _log_current_emotions():
    """Logs the current levels of all emotions."""
    var emotion_str = "EMO_STATE: "
    for emotion_name in emotions.keys():
        emotion_str += emotion_name.left(3).to_upper() + ":" + str(round(emotions[emotion_name] * 100)) + "% "
    _log_emotion_activity(emotion_str)

