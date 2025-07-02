# PXMutantExplorerAI.gd
# This module is responsible for analyzing roadmap mutation data and now,
# also simulation outcomes, to generate hypotheses and insights about
# evolutionary success, failure, and predicted digest behavior.
# It acts as a reasoning layer for the PXMutantExplorer and PXDigestPreviewRuntime.

extends Node

# --- Dependencies ---
# Access to core data sources
@onready var px_scroll_library: PXScrollLibrary = get_node_or_null("../PXScrollLibrary") # To get all roadmap names
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To get fitness and execution data
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read roadmap/digest content for analysis
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging AI insights
@onready var px_digest_preview_runtime: PXDigestPreviewRuntime = get_node_or_null("../PXDigestPreviewRuntime") # To receive simulation outcomes

# Optional: Reference to PXMutantExplorerEnhancer for diffing logic or lineage structure
@onready var px_mutant_explorer_enhancer: PXMutantExplorerEnhancer = get_node_or_null("../PXMutantExplorerEnhancer")
@onready var px_digest_inspector: PXDigestInspector = get_node_or_null("../PXDigestInspector") # For parsing digest content

# Store insight results
var roadmap_insights: Dictionary = {} # roadmap_name → Dictionary (goal, mutation_pattern, success_rate, suggestion, etc.)
var digest_simulation_insights: Dictionary = {} # digest_path -> Dictionary (summary, risks, recommendations)


# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_fs_reader: # px_scroll_library and px_roadmap_registry might not be needed for all functions
        print_err("PXMutantExplorerAI: Essential core dependencies missing. Some AI functions may be limited.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    _log_ai_activity("Initialized. Ready for roadmap and digest analysis.")
    _analyze_existing_mutants() # Initial analysis of roadmaps

    # Connect to PXDigestPreviewRuntime's simulation_completed signal (M3)
    if px_digest_preview_runtime:
        px_digest_preview_runtime.simulation_completed.connect(Callable(self, "on_simulation_outcome"))
        px_digest_preview_runtime.simulation_failed.connect(Callable(self, "on_simulation_outcome")) # Also handle failures
        _log_ai_activity("Connected to PXDigestPreviewRuntime for simulation outcome analysis.")
    else:
        _log_ai_activity("Warning: PXDigestPreviewRuntime not found. Digest outcome analysis will not function.")


# ------------------------------------------------------
# 🧠 Core Reasoning Pipeline (Roadmap Analysis)
# ------------------------------------------------------

func _analyze_existing_mutants():
    # Ensure core dependencies for roadmap analysis are available
    if not px_scroll_library or not px_roadmap_registry:
        _log_ai_activity("Skipping roadmap analysis: PXScrollLibrary or PXRoadmapRegistry not available.")
        return

    _log_ai_activity("Initiating comprehensive roadmap evolution analysis...")
    roadmap_insights.clear()

    var all_names = px_scroll_library.get_available_scroll_names()
    if all_names.is_empty():
        _log_ai_activity("No roadmaps found to analyze.")
        return

    var roadmap_data = _gather_all_roadmap_data(all_names)

    # 1. Identify highest/lowest performing roadmaps
    _identify_performance_extremes(roadmap_data)

    # 2. Analyze parent-child relationships for fitness deltas
    _analyze_lineage_performance(roadmap_data)

    # 3. Look for common patterns in successful mutations (conceptual)
    _identify_successful_mutation_patterns(roadmap_data)

    _log_ai_activity("Roadmap analysis complete. Results stored in roadmap_insights.")
    _report_roadmap_analysis_summary()

func _gather_all_roadmap_data(roadmap_names: Array[String]) -> Dictionary:
    """
    Gathers all necessary data for roadmap analysis: content, metadata, and registry results.
    """
    var data = {}
    var all_registry_results = px_roadmap_registry.get_all_roadmap_results()

    for name in roadmap_names:
        var content_raw = px_fs_reader.read_file_by_name(name)
        var metadata = _parse_roadmap_header_metadata(content_raw)
        
        var runs = []
        for run in all_registry_results:
            if run.roadmap == name:
                runs.append(run)
        
        data[name] = {
            "content": content_raw,
            "metadata": metadata,
            "runs": runs,
            "avg_score": _calculate_avg_score(runs),
            "success_ratio": _calculate_success_ratio(runs)
        }
    return data

func _calculate_avg_score(runs: Array) -> float:
    if runs.is_empty(): return 0.0
    var total_score = 0.0
    for run in runs:
        total_score += run.score
    return total_score / runs.size()

func _calculate_success_ratio(runs: Array) -> float:
    if runs.is_empty(): return 0.0
    var success_count = 0
    for run in runs:
        if run.outcome == "SUCCESS":
            success_count += 1
    return float(success_count) / runs.size()

func _identify_performance_extremes(roadmap_data: Dictionary):
    """Identifies the best and worst performing roadmaps."""
    var best_roadmap = ""
    var highest_score = -1.0
    var worst_roadmap = ""
    var lowest_score = 999999.0

    for name in roadmap_data.keys():
        var avg_score = roadmap_data[name].avg_score
        if avg_score > highest_score:
            highest_score = avg_score
            best_roadmap = name
        if avg_score < lowest_score:
            lowest_score = avg_score
            worst_roadmap = name
    
    if not best_roadmap.is_empty():
        roadmap_insights["highest_performing"] = {
            "name": best_roadmap,
            "score": highest_score,
            "goal": roadmap_data[best_roadmap].metadata.get("goal", "N/A")
        }
    if not worst_roadmap.is_empty():
        roadmap_insights["lowest_performing"] = {
            "name": worst_roadmap,
            "score": lowest_score,
            "goal": roadmap_data[worst_roadmap].metadata.get("goal", "N/A")
        }

func _analyze_lineage_performance(roadmap_data: Dictionary):
    """
    Analyzes fitness deltas across parent-child roadmap chains.
    Hypothesizes about the impact of specific mutations.
    """
    var lineage_insights = []
    for name in roadmap_data.keys():
        var current_roadmap = roadmap_data[name]
        var parent_id = current_roadmap.metadata.get("parent_id", "")

        if not parent_id.is_empty() and roadmap_data.has(parent_id):
            var parent_roadmap = roadmap_data[parent_id]
            var score_delta = current_roadmap.avg_score - parent_roadmap.avg_score
            var success_delta = current_roadmap.success_ratio - parent_roadmap.success_ratio
            var rationale = current_roadmap.metadata.get("rationale", "No specific reason provided.")

            var insight = {
                "mutant": name,
                "parent": parent_id,
                "score_delta": snapped(score_delta, 0.01),
                "success_delta": snapped(success_delta, 0.01),
                "rationale": rationale,
                "hypothesis": ""
            }

            if score_delta > 0.5: # Arbitrary threshold for significant improvement
                insight.hypothesis = "Hypothesis: Mutation led to significant fitness improvement."
            elif score_delta < -0.5: # Arbitrary threshold for significant degradation
                insight.hypothesis = "Hypothesis: Mutation led to significant fitness degradation."
            else:
                insight.hypothesis = "Hypothesis: Mutation had minor impact on fitness."
            
            lineage_insights.append(insight)
    
    roadmap_insights["lineage_insights"] = lineage_insights

func _identify_successful_mutation_patterns(roadmap_data: Dictionary):
    """
    (Conceptual) Analyzes content differences of highly successful mutations
    to identify common patterns or 'winning' changes.
    """
    var successful_patterns = []
    var top_performers = []

    var sorted_roadmaps = roadmap_data.keys().duplicate()
    sorted_roadmaps.sort_custom(func(a, b): return roadmap_data[a].avg_score > roadmap_data[b].avg_score)
    
    var num_to_check = min(5, sorted_roadmaps.size())
    for i in range(num_to_check):
        top_performers.append(roadmap_data[sorted_roadmaps[i]])

    for mutant_data in top_performers:
        var parent_id = mutant_data.metadata.get("parent_id", "")
        if not parent_id.is_empty() and roadmap_data.has(parent_id):
            var parent_data = roadmap_data[parent_id]
            
            var rationale = mutant_data.metadata.get("rationale", "No specific reason provided.")
            var score_delta = mutant_data.avg_score - parent_data.avg_score

            if score_delta > 0:
                successful_patterns.append({
                    "mutant": mutant_data.name,
                    "parent": parent_data.name,
                    "score_improvement": snapped(score_delta, 0.01),
                    "reason_given": rationale,
                    "potential_pattern": "Further analysis needed on content diffs for specific winning patterns."
                })
    
    roadmap_insights["successful_mutation_patterns"] = successful_patterns

func _report_roadmap_analysis_summary():
    """Logs a summary of the roadmap analysis results to PXScrollLog."""
    _log_ai_activity("--- PXMutantExplorerAI Roadmap Analysis Summary ---")

    if roadmap_insights.has("highest_performing"):
        var hp = roadmap_insights["highest_performing"]
        _log_ai_activity("Highest Performing Roadmap: '%s' (Score: %s, Goal: %s)" % [hp.name, str(snapped(hp.score, 0.01)), hp.goal])
    if roadmap_insights.has("lowest_performing"):
        var lp = roadmap_insights["lowest_performing"]
        _log_ai_activity("Lowest Performing Roadmap: '%s' (Score: %s, Goal: %s)" % [lp.name, str(snapped(lp.score, 0.01)), lp.goal])

    if roadmap_insights.has("lineage_insights"):
        _log_ai_activity("Lineage Insights (%d mutations analyzed):" % roadmap_insights["lineage_insights"].size())
        for insight in roadmap_insights["lineage_insights"]:
            _log_ai_activity("  - Mutant: '%s' (Parent: '%s'). Score Delta: %s. %s" % [insight.mutant, insight.parent, str(insight.score_delta), insight.hypothesis])
            if not insight.rationale.is_empty() and insight.rationale != "No specific reason provided.":
                _log_ai_activity("    Reason: %s" % insight.rationale)

    if roadmap_insights.has("successful_mutation_patterns"):
        _log_ai_activity("Potential Successful Mutation Patterns (%d identified):" % roadmap_insights["successful_mutation_patterns"].size())
        for pattern in roadmap_insights["successful_mutation_patterns"]:
            _log_ai_activity("  - Improved mutant '%s' from '%s' by %s score. Reason: '%s'." % [pattern.mutant, pattern.parent, str(pattern.score_improvement), pattern.reason_given])
            _log_ai_activity("    Note: %s" % pattern.potential_pattern)

    _log_ai_activity("--- End of Roadmap Analysis Summary ---")

func get_roadmap_analysis_results() -> Dictionary:
    """Returns the last computed roadmap analysis results."""
    return roadmap_insights

# ------------------------------------------------------
# 🧠 Core Reasoning Pipeline (Digest Simulation Outcome Analysis - M3)
# ------------------------------------------------------

func on_simulation_outcome(digest_path: String, outcome: Dictionary):
    """
    M3: Triggered after a PXDigestPreviewRuntime simulation completes (or fails).
    Analyzes the simulation outcome and provides reflexive commentary.
    """
    _log_ai_activity("--- PXMutantExplorerAI Digest Simulation Analysis ---")
    _log_ai_activity("Analyzing simulation outcome for digest: '%s'" % digest_path.get_file())

    var summary_data = {
        "digest_name": digest_path.get_file(),
        "simulation_status": outcome.get("status", "UNKNOWN"),
        "predicted_result": outcome.get("predicted_result", "N/A"),
        "simulated_logs_count": outcome.get("simulated_logs", []).size(),
        "memory_changes_detected": outcome.get("final_memory_state", {}).size() > 0,
        "risks_flagged": [],
        "recommendation": "Further analysis needed."
    }

    var digest_content_raw = px_fs_reader.read_file_by_name(digest_path)
    var parsed_digest_metadata = {}
    if px_digest_inspector:
        parsed_digest_metadata = px_digest_inspector._parse_pxdigest_content(digest_content_raw).get("metadata", {})

    var ai_commentary_string = "AI Commentary on Simulation: "

    match summary_data.simulation_status:
        "COMPLETED":
            ai_commentary_string += "Simulation completed successfully. "
            if summary_data.predicted_result == "System Initialized":
                ai_commentary_string += "This digest appears to be a system initialization or boot sequence. "
            elif summary_data.predicted_result == "System Upgraded":
                ai_commentary_string += "This digest likely performs a system upgrade. "
            
            if summary_data.memory_changes_detected:
                ai_commentary_string += "Detected changes in simulated memory state. "
                # More detailed memory diff analysis would go here (M4)
            else:
                ai_commentary_string += "No significant memory changes observed in simulation. "
            
            summary_data.recommendation = "Consider executing this digest if predicted outcome aligns with goals."
            
            # Flag risks based on metadata or simulated actions
            if parsed_digest_metadata.get("pxroadmap/status") == "Incomplete":
                summary_data.risks_flagged.append("Metadata flags digest as 'Incomplete'.")
                ai_commentary_string += "[color=orange]WARNING: Digest metadata indicates 'Incomplete' status.[/color] "
                summary_data.recommendation = "Review digest content and metadata before execution."
            
            if parsed_digest_metadata.get("pxnet/role") == "Kernel" and summary_data.memory_changes_detected:
                summary_data.risks_flagged.append("Kernel role with memory changes: potential system-level impact.")
                ai_commentary_string += "[color=red]CRITICAL: Kernel role detected with significant simulated memory changes. Potential for system-level impact. Review carefully.[/color] "
                summary_data.recommendation = "Highly recommend thorough manual review and sandbox testing before live execution."
            
        "FAILED":
            ai_commentary_string += "[color=red]Simulation FAILED.[/color] "
            var reason = outcome.get("reason", "Unknown error.")
            ai_commentary_string += "Reason: '%s'. " % reason
            summary_data.risks_flagged.append("Simulation failure: %s" % reason)
            summary_data.recommendation = "DO NOT EXECUTE. Debug digest content or simulation logic."
            
        _:
            ai_commentary_string += "Simulation outcome unknown. "
            summary_data.recommendation = "Cannot recommend execution. Further investigation needed."

    _log_ai_activity(ai_commentary_string)
    _log_ai_activity("Recommendation: %s" % summary_data.recommendation)
    if not summary_data.risks_flagged.is_empty():
        _log_ai_activity("Risks Flagged: %s" % str(summary_data.risks_flagged))

    digest_simulation_insights[digest_path] = summary_data
    _log_ai_activity("Digest simulation analysis complete for '%s'." % digest_path.get_file())
    _log_ai_activity("--- End of Digest Simulation Analysis ---")

    # You might emit a signal here for PXSimPanel or other UI to display this summary
    # emit_signal("digest_simulation_summary_ready", digest_path, summary_data, ai_commentary_string)

func get_digest_simulation_insights(digest_path: String) -> Dictionary:
    """Returns the last computed simulation insights for a specific digest."""
    return digest_simulation_insights.get(digest_path, {})

# ------------------------------------------------------
# 📦 Utilities
# ------------------------------------------------------

func _parse_roadmap_header_metadata(content: String) -> Dictionary:
    """
    Helper to parse metadata from roadmap headers.
    """
    var metadata = {}
    var lines = content.split("\n")
    for line in lines:
        if line.begins_with("# GOAL:"):
            metadata["goal"] = line.replace("# GOAL:", "").strip_edges()
        elif line.begins_with("# STRATEGY:"):
            metadata["strategy"] = line.replace("# STRATEGY:", "").strip_edges()
        elif line.begins_with("# MUTATED_FROM:"):
            metadata["parent_id"] = line.replace("# MUTATED_FROM:", "").strip_edges()
        elif line.begins_with("# REASON:"):
            metadata["rationale"] = line.replace("# REASON:", "").strip_edges()
        elif line.begins_with("# LINEAGE_ID:"):
            metadata["lineage_id"] = line.replace("# LINEAGE_ID:", "").strip_edges()
        if not line.begins_with("#") and not line.strip_edges().is_empty():
            break
    return metadata

# --- Logging ---

func _log_ai_activity(message: String):
    """
    Helper function to log AI activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXAI: " + message) # Changed tag to PXAI for general AI activity
    else:
        print("PXMutantExplorerAI (Console Log): ", message)

