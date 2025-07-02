# PXRoadmapFitnessScorer.gd
# This module assigns a "fitness score" to executed roadmaps based on their
# outcomes, efficiency, and other metrics. This score can then be used by
# other modules (e.g., PXRoadmapSelector, PXRoadmapMutator) to prioritize
# and evolve successful strategies.

extends Node

# --- Configuration ---
# Weights for different scoring components (adjust to prioritize metrics)
@export var success_weight: float = 10.0      # Score for a successful roadmap execution
@export var failure_penalty: float = -5.0     # Penalty for a failed roadmap execution
@export var efficiency_weight: float = 0.1    # Score per step (lower steps = higher efficiency)
@export var speed_weight: float = 0.05        # Score per second (lower time = higher speed)
@export var mutation_penalty_per_mutation: float = -1.0 # Penalty for mutations (to favor stable solutions)

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging scorer activity
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To get goal outcomes (success/failure)

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log or not px_goal_memory:
        print_err("PXRoadmapFitnessScorer: Essential dependencies missing. Scorer disabled.")
        set_process(false)
        return

    print("PXRoadmapFitnessScorer: Initialized. Ready to score roadmaps.")

# --- Core Scoring API ---

func calculate_fitness_score(
    roadmap_name: String,
    goal_entry: GoalEntry, # The GoalEntry associated with this roadmap execution
    execution_duration: float, # Time taken to execute the roadmap
    num_steps_executed: int, # Number of steps in the roadmap
    num_mutations_applied: int = 0 # Number of mutations applied during its execution/generation
) -> float:
    """
    Calculates a fitness score for a roadmap execution.

    Args:
        roadmap_name (String): The name of the roadmap being scored.
        goal_entry (GoalEntry): The GoalEntry object for this execution, containing outcome.
        execution_duration (float): The time taken for the roadmap to execute (in seconds).
        num_steps_executed (int): The total number of steps in the roadmap.
        num_mutations_applied (int): Number of mutations applied to this roadmap or its variant.

    Returns:
        float: The calculated fitness score. Higher is better.
    """
    _log_scorer_activity("Calculating fitness for '" + roadmap_name + "' (Outcome: " + goal_entry.outcome + ")")
    
    var score = 0.0

    # 1. Score based on outcome
    match goal_entry.outcome:
        "SUCCESS": score += success_weight
        "FAILURE": score += failure_penalty
        "ABORTED": score += failure_penalty * 0.5 # Less severe penalty than outright failure
        "PENDING": pass # No score for pending

    # 2. Score based on efficiency (fewer steps are better)
    if num_steps_executed > 0:
        score += efficiency_weight * (1.0 / num_steps_executed) # Inverse relationship
    
    # 3. Score based on speed (lower duration is better)
    if execution_duration > 0:
        score += speed_weight * (1.0 / execution_duration) # Inverse relationship

    # 4. Penalty for mutations (to favor stable solutions, or adjust based on goal)
    score += mutation_penalty_per_mutation * num_mutations_applied

    _log_scorer_activity("  Score for '" + roadmap_name + "': " + str(snapped(score, 0.01)))
    return snapped(score, 0.01) # Snap to 2 decimal places for cleaner logs

# --- Logging ---

func _log_scorer_activity(message: String):
    """
    Helper function to log scorer activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("FITNESS: " + message)
    else:
        print("PXRoadmapFitnessScorer (Console Log): ", message)

