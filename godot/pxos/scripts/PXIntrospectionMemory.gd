# PXIntrospectionMemory.gd
# This module provides a dedicated, persistent storage for PXOS's
# introspective logs (explanations of its decisions). It acts as a
# "thought trail" or "cognitive journal," allowing for long-term replay,
# debugging, and future training of self-reflection.

extends Node

# --- Configuration ---
# Maximum number of introspection entries to store.
@export var max_introspection_history: int = 500

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging memory activities

# --- Internal State ---
# Stores a list of introspection entries. Each entry could be a dictionary
# containing the explanation, timestamp, and any relevant context.
var introspection_history: Array[Dictionary] = []

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_warn("PXIntrospectionMemory: PXScrollLog not found. Memory logs will go to console.")

    print("PXIntrospectionMemory: Initialized. Ready to store introspection.")

# --- Core Introspection Memory API ---

func record_introspection(explanation: String, timestamp: float, context: Dictionary = {}):
    """
    Records an introspective explanation into the history.

    Args:
        explanation (String): The full explanation string from PXGoalIntrospector.
        timestamp (float): The OS.get_unix_time_from_system() when the explanation was generated.
        context (Dictionary): Optional dictionary for additional context (e.g., goal_type, decision_type).
    """
    var entry = {
        "explanation": explanation,
        "timestamp": timestamp,
        "context": context
    }
    introspection_history.append(entry)

    # Trim history if it exceeds max_introspection_history
    while introspection_history.size() > max_introspection_history:
        introspection_history.pop_front() # Remove the oldest entry

    _log_introspection_memory_activity("RECORD: " + explanation.left(20) + "...")
    print("PXIntrospectionMemory: Recorded introspection entry (Total: ", introspection_history.size(), ").")


func get_introspection_history(filter_decision_type: String = "") -> Array[Dictionary]:
    """
    Retrieves a filtered list of introspection entries from the history.

    Args:
        filter_decision_type (String): Optional. Filter by decision type (e.g., "ISSUED", "SKIPPED").

    Returns:
        Array[Dictionary]: A new array containing the filtered introspection entries.
    """
    var filtered_history: Array[Dictionary] = []
    for entry in introspection_history:
        var decision_type_match = filter_decision_type.is_empty() or \
                                  entry.context.get("decision_type", "") == filter_decision_type
        if decision_type_match:
            filtered_history.append(entry)
    return filtered_history

func get_last_introspection_entry() -> Dictionary:
    """
    Retrieves the most recent introspection entry.

    Returns:
        Dictionary: The most recent entry, or an empty dictionary if history is empty.
    """
    if not introspection_history.is_empty():
        return introspection_history.back()
    return {}

# --- Logging ---

func _log_introspection_memory_activity(message: String):
    """
    Helper function to log introspection memory activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("INTROMEM: " + message)
    else:
        print("PXIntrospectionMemory (Console Log): ", message)

