# PXGoalMutationEngine.gd
# This module enables PXOS to adapt its goals (directives) based on past outcomes,
# particularly when a goal is identified as stagnant (repeatedly failing).
# It can suggest mutated versions of goals or trigger fallback strategies.

extends Node

# --- Configuration ---
# How many times a goal should be mutated before considering a different strategy (e.g., fallback).
@export var max_mutations_per_goal: int = 3

# --- Dependencies ---
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To read goal history
@onready var px_roadmap_generator: PXRoadmapGenerator = get_node_or_null("../PXRoadmapGenerator") # To generate new roadmaps for mutated goals
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging mutation activities

# --- Internal State ---
# Tracks mutation count for each goal type to know when to suggest a fallback.
var goal_mutation_counts: Dictionary = {} # { "GOAL_TYPE": current_mutation_count }

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_goal_memory:
        print_err("PXGoalMutationEngine: PXGoalMemory node not found. Mutation engine disabled.")
        set_process(false)
        return
    if not px_roadmap_generator:
        print_err("PXGoalMutationEngine: PXRoadmapGenerator node not found. Cannot generate mutated roadmaps.")
        set_process(false)
        return
    if not px_scroll_log:
        print_warn("PXGoalMutationEngine: PXScrollLog not found. Mutation logs will go to console.")

    print("PXGoalMutationEngine: Initialized. Ready to mutate goals.")

# --- Core Mutation API ---

func get_mutated_goal(original_goal_type: String, failure_count: int) -> String:
    """
    Suggests a mutated version of an original goal based on its failure count.
    This is where the "adaptive" logic resides.

    Args:
        original_goal_type (String): The goal type that has been failing.
        failure_count (int): The number of consecutive failures for this goal.

    Returns:
        String: A new, mutated goal string, or a fallback goal if max mutations reached.
    """
    _log_mutation_activity("MUTATE: Attempting to mutate goal '" + original_goal_type + "' (Failures: " + str(failure_count) + ")")

    # Increment mutation count for this goal type
    goal_mutation_counts[original_goal_type] = goal_mutation_counts.get(original_goal_type, 0) + 1
    var current_mutations = goal_mutation_counts[original_goal_type]

    if current_mutations >= max_mutations_per_goal:
        # If max mutations reached, suggest a fallback strategy
        _log_mutation_activity("  Max mutations reached for '" + original_goal_type + "'. Suggesting fallback.")
        # Reset mutation count for this goal type if we're falling back
        goal_mutation_counts[original_goal_type] = 0
        return _get_fallback_goal(original_goal_type)
    else:
        # Otherwise, suggest a specific mutation
        _log_mutation_activity("  Applying mutation #" + str(current_mutations) + " for '" + original_goal_type + "'.")
        return _apply_specific_mutation(original_goal_type, current_mutations)

func reset_mutation_count(goal_type: String):
    """
    Resets the mutation count for a specific goal type (e.g., when it finally succeeds).
    """
    if goal_mutation_counts.has(goal_type):
        goal_mutation_counts[goal_type] = 0
        _log_mutation_activity("RESET MUTATION COUNT for '" + goal_type + "'.")

# --- Mutation Strategies (Internal) ---

func _apply_specific_mutation(goal_type: String, mutation_num: int) -> String:
    """
    Applies a specific mutation strategy based on the goal type and mutation number.
    This is a simplified example; real mutations would be more complex.
    """
    match goal_type:
        "EXPLORE":
            match mutation_num:
                1: return "EXPLORE_DEEPER" # Try exploring more intensely
                2: return "EXPLORE_RANDOM" # Try exploring a random area
                _: return "EXPLORE" # Default
        "REPAIR_SYSTEM":
            match mutation_num:
                1: return "REPAIR_DIAGNOSE" # Add a diagnostic step
                2: return "REPAIR_RESET" # Try a hard reset
                _: return "REPAIR_SYSTEM" # Default
        "ACQUIRE_RESOURCES":
            match mutation_num:
                1: return "ACQUIRE_FAST" # Try a faster acquisition method
                2: return "ACQUIRE_SAFE" # Try a safer acquisition method
                _: return "ACQUIRE_RESOURCES" # Default
        "CREATE_NEW_PLAN":
            match mutation_num:
                1: return "CREATE_PLAN_COMPLEX" # Try generating a more complex plan
                2: return "CREATE_PLAN_SIMPLE" # Try generating a simpler plan
                _: return "CREATE_NEW_PLAN" # Default
        _:
            # For unknown goals, just return the original or a generic fallback
            return goal_type + "_MUTATED"

func _get_fallback_goal(original_goal_type: String) -> String:
    """
    Provides a fallback goal when a specific goal has failed too many times.
    """
    match original_goal_type:
        "EXPLORE": return "REST" # If exploring fails, maybe rest
        "REPAIR_SYSTEM": return "REPORT_ERROR" # If repair fails, report it
        "ACQUIRE_RESOURCES": return "REQUEST_HELP" # If acquiring fails, ask for help
        "CREATE_NEW_PLAN": return "DEFAULT_ACTION" # If plan creation fails, do a default action
        _: return "HALT_SYSTEM" # Generic critical fallback

# --- Logging ---

func _log_mutation_activity(message: String):
    """
    Helper function to log mutation activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MUTATOR: " + message)
    else:
        print("PXGoalMutationEngine (Console Log): ", message)

