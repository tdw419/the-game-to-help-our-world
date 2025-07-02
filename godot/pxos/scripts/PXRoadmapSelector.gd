# PXRoadmapSelector.gd
# This module is responsible for selecting the "best" roadmap to execute
# for a given goal. It queries the PXRoadmapRegistry for past execution results,
# aggregates scores, and prioritizes roadmaps based on fitness and goal relevance.

extends Node

# --- Configuration ---
# Minimum score for a roadmap to be considered "good" for selection.
@export var minimum_selection_score: float = 3.0

# --- Dependencies ---
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To get roadmap results
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging selector activity

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_roadmap_registry or not px_scroll_log:
        print_err("PXRoadmapSelector: Essential dependencies missing. Selector disabled.")
        set_process(false)
        return

    print("PXRoadmapSelector: Initialized. Ready to select roadmaps.")

# --- Core Selector API ---

func select_best_roadmap_for_goal(goal_type: String) -> String:
    """
    Selects the best roadmap from the registry that aligns with a given goal type.
    Prioritizes successful and high-scoring roadmaps.

    Args:
        goal_type (String): The goal type (e.g., "BOOT_OPTIMIZATION", "EXPLORE").

    Returns:
        String: The name of the best roadmap, or an empty string if no suitable roadmap is found.
    """
    _log_selector_activity("SELECT: Best roadmap for goal '" + goal_type + "'...")

    var all_results = px_roadmap_registry.get_all_roadmap_results()
    var roadmap_scores: Dictionary = {} # { "roadmap_name": [score1, score2, ...] }
    var roadmap_metadata: Dictionary = {} # { "roadmap_name": { "last_run_ts": ..., "goal_type": ... } }

    for entry in all_results:
        # Filter by goal type (conceptual match for now)
        if entry.goal_type == goal_type and entry.outcome == "SUCCESS":
            roadmap_scores[entry.roadmap] = roadmap_scores.get(entry.roadmap, []) + [entry.score]
            # Update metadata (e.g., last run timestamp)
            var current_ts = roadmap_metadata.get(entry.roadmap, {}).get("last_run_ts", 0)
            if entry.timestamp > current_ts:
                roadmap_metadata[entry.roadmap] = {
                    "last_run_ts": entry.timestamp,
                    "goal_type": entry.goal_type # Ensure goal type is stored
                }
        elif entry.goal_type == goal_type and entry.outcome == "FAILURE":
            # Penalize or just ignore failed attempts for "best" selection
            # For simplicity, we only consider successful runs for "best" selection.
            pass

    var best_roadmap_name = ""
    var highest_avg_score = -INF

    for roadmap_name in roadmap_scores.keys():
        var scores_for_roadmap = roadmap_scores[roadmap_name]
        if scores_for_roadmap.is_empty(): continue

        var total_score = 0.0
        for score in scores_for_roadmap:
            total_score += score
        var avg_score = total_score / scores_for_roadmap.size()

        # Apply selection criteria: minimum score, then highest average
        if avg_score >= minimum_selection_score and avg_score > highest_avg_score:
            highest_avg_score = avg_score
            best_roadmap_name = roadmap_name

    if best_roadmap_name.is_empty():
        _log_selector_activity("  No suitable roadmap found for goal '" + goal_type + "'.")
    else:
        _log_selector_activity("  Selected '" + best_roadmap_name + "' (Avg Score: " + str(snapped(highest_avg_score, 0.01)) + ")")

    return best_roadmap_name

# --- Logging ---

func _log_selector_activity(message: String):
    """
    Helper function to log selector activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("SELECTOR: " + message)
    else:
        print("PXRoadmapSelector (Console Log): ", message)

