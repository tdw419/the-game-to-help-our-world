# PXRoadmapFitnessMonitor.gd
# This module continuously monitors the fitness trends of executed roadmaps
# stored in PXRoadmapRegistry.gd. It detects performance degradation, plateaus,
# or stagnation and can emit alerts, triggering further adaptive behaviors.

extends Node

# --- Configuration ---
# How often the monitor evaluates roadmap fitness trends (in seconds).
@export var monitor_frequency_sec: float = 10.0

# Number of recent executions to consider for trend analysis.
@export var history_window_size: int = 5

# Threshold for detecting score degradation (e.g., average score drops by this much).
@export var degradation_threshold: float = -2.0 # Negative value, e.g., -2.0 means score drops by 2 points

# Threshold for detecting a plateau (e.g., average score changes by less than this).
@export var plateau_threshold: float = 0.5 # Positive value, e.g., 0.5 means score changes by less than 0.5

# --- Dependencies ---
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To read roadmap results
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging monitor activity

# --- Internal State ---
var time_since_last_monitor: float = 0.0
# Cache of last known average scores for trend detection: { "roadmap_name": last_avg_score }
var _last_avg_scores: Dictionary = {}
# Cache of last known number of entries in registry to detect new results
var _last_registry_size: int = 0

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_roadmap_registry or not px_scroll_log:
        print_err("PXRoadmapFitnessMonitor: Essential dependencies missing. Monitor disabled.")
        set_process(false)
        return

    print("PXRoadmapFitnessMonitor: Initialized. Ready to monitor roadmap fitness.")
    _last_registry_size = px_roadmap_registry.get_all_roadmap_results().size()

func _process(delta):
    time_since_last_monitor += delta
    if time_since_last_monitor >= monitor_frequency_sec:
        time_since_last_monitor = 0.0
        _evaluate_fitness_trends()

# --- Core Monitoring Logic ---

func _evaluate_fitness_trends():
    """
    Evaluates fitness trends for all roadmaps in the registry.
    Detects degradation, plateaus, or improvements.
    """
    _log_monitor_activity("Evaluating roadmap fitness trends...")

    var all_results = px_roadmap_registry.get_all_roadmap_results()
    if all_results.size() <= _last_registry_size:
        # No new results since last check, or registry is empty
        _log_monitor_activity("  No new roadmap results to evaluate.")
        _last_registry_size = all_results.size() # Update in case it shrunk
        return

    _last_registry_size = all_results.size() # Update to current size

    var roadmap_results_by_name: Dictionary = {} # { "roadmap_name": [entry1, entry2, ...] }
    for entry in all_results:
        roadmap_results_by_name[entry.roadmap] = roadmap_results_by_name.get(entry.roadmap, []) + [entry]

    for roadmap_name in roadmap_results_by_name.keys():
        var results_for_roadmap = roadmap_results_by_name[roadmap_name]
        
        # Only consider recent history for trend analysis
        var recent_results = results_for_roadmap.slice(max(0, results_for_roadmap.size() - history_window_size), results_for_roadmap.size())
        
        if recent_results.size() < 2: # Need at least two results to detect a trend
            # _log_monitor_activity("  Not enough history for '" + roadmap_name + "'.") # Too chatty
            continue

        var current_avg_score = _calculate_average_score(recent_results)
        var last_avg_score = _last_avg_scores.get(roadmap_name, current_avg_score) # Use current if no previous

        var score_change = current_avg_score - last_avg_score

        if score_change <= degradation_threshold:
            _log_monitor_activity("  ALERT: Degradation detected for '" + roadmap_name + "'. Change: " + str(snapped(score_change, 0.01)))
            _emit_fitness_alert(roadmap_name, "DEGRADATION", score_change, current_avg_score)
        elif abs(score_change) <= plateau_threshold:
            _log_monitor_activity("  ALERT: Plateau detected for '" + roadmap_name + "'. Change: " + str(snapped(score_change, 0.01)))
            _emit_fitness_alert(roadmap_name, "PLATEAU", score_change, current_avg_score)
        else:
            # _log_monitor_activity("  '" + roadmap_name + "' is stable/improving. Change: " + str(snapped(score_change, 0.01))) # Too chatty
            pass
        
        _last_avg_scores[roadmap_name] = current_avg_score # Update cache

# --- Helper Functions ---

func _calculate_average_score(results: Array[Dictionary]) -> float:
    """Calculates the average fitness score for a list of roadmap results."""
    if results.is_empty(): return 0.0
    var total_score = 0.0
    for entry in results:
        total_score += entry.score
    return total_score / results.size()

func _emit_fitness_alert(roadmap_name: String, alert_type: String, score_change: float, current_avg_score: float):
    """
    Emits a conceptual alert, which PXDirective or PXMotivationCore can pick up.
    For now, it logs to PXScrollLog.
    """
    _log_monitor_activity("FITNESS_ALERT: " + alert_type + " for '" + roadmap_name + "' (Avg: " + str(snapped(current_avg_score, 0.01)) + ")")
    # In a full system, you might emit a signal here:
    # emit_signal("fitness_alert", roadmap_name, alert_type, score_change, current_avg_score)
    # Or write to a specific zTXT memory region for PXReflexDaemon to pick up.

# --- Logging ---

func _log_monitor_activity(message: String):
    """
    Helper function to log monitor activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MONITOR: " + message)
    else:
        print("PXRoadmapFitnessMonitor (Console Log): ", message)

