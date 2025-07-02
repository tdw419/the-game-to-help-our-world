# PXGoalScorer.gd
# This module aggregates roadmap fitness scores per goal type,
# enabling PXOS to identify and prioritize goals with lowest average scores
# or highest failure counts, guiding improvement efforts.

extends Node

# --- Configuration ---
# Minimum number of results required to calculate a meaningful average score for a goal.
@export var min_results_for_average: int = 3

# --- Dependencies ---
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To read roadmap results
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging scorer activity

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_roadmap_registry or not px_scroll_log:
        print_err("PXGoalScorer: Essential dependencies missing. Scorer disabled.")
        set_process(false)
        return

    print("PXGoalScorer: Initialized. Ready to aggregate goal fitness.")

# --- Core Aggregation API ---

func get_goal_fitness_summary() -> Dictionary:
    """
    Computes and returns a summary of fitness (average score, failure count)
    for each unique goal type found in the roadmap registry.

    Returns:
        Dictionary: A dictionary where keys are goal_types (String) and values are
                    dictionaries like {"avg_score": float, "total_runs": int, "failure_count": int}.
    """
    _log_scorer_activity("Aggregating goal fitness summary...")

    var all_results = px_roadmap_registry.get_all_roadmap_results()
    var goal_data: Dictionary = {} # { "goal_type": { "scores": [], "failures": 0, "total_runs": 0 } }

    for entry in all_results:
        var goal_type = entry.goal_type
        if not goal_data.has(goal_type):
            goal_data[goal_type] = {"scores": [], "failures": 0, "total_runs": 0}
        
        goal_data[goal_type]["scores"].append(entry.score)
        goal_data[goal_type]["total_runs"] += 1
        if entry.outcome == "FAILURE":
            goal_data[goal_type]["failures"] += 1

    var summary: Dictionary = {} # Final summary to return
    for goal_type in goal_data.keys():
        var data = goal_data[goal_type]
        var avg_score = 0.0
        if data.scores.size() >= min_results_for_average:
            var total_score = 0.0
            for score in data.scores:
                total_score += score
            avg_score = total_score / data.scores.size()
            avg_score = snapped(avg_score, 0.01) # Snap to 2 decimal places
        else:
            avg_score = NAN # Not enough data for meaningful average

        summary[goal_type] = {
            "avg_score": avg_score,
            "total_runs": data.total_runs,
            "failure_count": data.failures,
            "success_rate": snapped(float(data.total_runs - data.failures) / data.total_runs, 0.01) if data.total_runs > 0 else NAN
        }
        _log_scorer_activity("  Goal '" + goal_type + "': Avg Score=" + str(summary[goal_type].avg_score) + ", Failures=" + str(summary[goal_type].failure_count))

    _log_scorer_activity("Goal fitness aggregation complete.")
    return summary

# --- Logging ---

func _log_scorer_activity(message: String):
    """
    Helper function to log scorer activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("GOAL_SCORE: " + message)
    else:
        print("PXGoalScorer (Console Log): ", message)

