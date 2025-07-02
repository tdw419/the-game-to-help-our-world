# PXMutantExplorerEnhancer.gd
# This module provides helper functions and potentially custom UI logic
# to enhance PXMutantExplorer with advanced features like diffing and graph rendering.

extends Node

# --- Dependencies ---
# (Likely connected to PXMutantExplorer for direct UI manipulation or data access)
@onready var px_mutant_explorer: Control = get_node_or_null("../PXMutantExplorer")
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read roadmap content for diffing
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To get detailed run data for graphs

# --- UI Element References (To be set up in Godot scene under PXMutantExplorer) ---
# For LineageTree
@onready var lineage_tree: Tree = get_node_or_null("../PXMutantExplorer/LineageTree")
# For FitnessGraph (could be a custom Drawing Node or GraphEdit)
@onready var fitness_graph_container: Control = get_node_or_null("../PXMutantExplorer/FitnessGraph")
# For RoadmapDiffPanel
@onready var roadmap_diff_panel: Control = get_node_or_null("../PXMutantExplorer/RoadmapDiffPanel")
@onready var original_content_label: Label = get_node_or_null("../PXMutantExplorer/RoadmapDiffPanel/OriginalContentLabel")
@onready var mutated_content_label: Label = get_node_or_null("../PXMutantExplorer/RoadmapDiffPanel/MutatedContentLabel")
@onready var diff_summary_label: Label = get_node_or_null("../PXMutantExplorer/RoadmapDiffPanel/DiffSummaryLabel")


# --- Godot Lifecycle Methods ---

func _ready():
    if not px_mutant_explorer or not px_fs_reader or not px_roadmap_registry:
        print_err("PXMutantExplorerEnhancer: Essential dependencies missing. Enhancer functions may be limited.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Initial setup for UI elements if needed
    if roadmap_diff_panel:
        roadmap_diff_panel.hide() # Initially hidden
    # You might want to connect signals here if this module handles specific UI interactions

# --- Core Enhancement Functions ---

func populate_lineage_tree(root_roadmap_name: String, all_roadmap_names: Array[String]):
    """
    Populates the LineageTree with parent-child relationships.
    Requires parsing # MUTATED_FROM and # LINEAGE_ID from roadmap headers.
    """
    if not lineage_tree:
        return

    lineage_tree.clear()
    var root_item = lineage_tree.create_item()
    root_item.set_text(0, root_roadmap_name)
    # Add icon for original roadmap if desired

    # This is a conceptual implementation. A robust lineage tracking
    # would involve PXRoadmapRegistry or a dedicated lineage logger.
    var lineage_map = {} # {parent_name: [child_names]}
    for name in all_roadmap_names:
        var content = px_fs_reader.read_file_by_name(name)
        var metadata = _parse_roadmap_header_metadata(content)
        var parent_id = metadata.get("mutated_from", "")
        if not parent_id.is_empty():
            if not lineage_map.has(parent_id):
                lineage_map[parent_id] = []
            lineage_map[parent_id].append(name)
        else:
            # Handle root roadmaps or those without explicit parent (initial versions)
            if not name.ends_with(".txt"): # Heuristic for non-mutated, might need refinement
                if not lineage_map.has("ROOTS"): # Use a special key for root roadmaps
                    lineage_map["ROOTS"] = []
                lineage_map["ROOTS"].append(name)


    # Recursively build the tree
    _build_tree_recursive(root_item, root_roadmap_name, lineage_map)

func _build_tree_recursive(parent_tree_item: TreeItem, current_roadmap_name: String, lineage_map: Dictionary):
    """Recursive helper for populate_lineage_tree."""
    var children = lineage_map.get(current_roadmap_name, [])
    for child_name in children:
        var child_item = lineage_tree.create_item(parent_tree_item)
        child_item.set_text(0, child_name)
        # Add metadata to item for selection or tooltips
        var metadata = _parse_roadmap_header_metadata(px_fs_reader.read_file_by_name(child_name))
        child_item.set_metadata(0, metadata)
        _build_tree_recursive(child_item, child_name, lineage_map)

func display_roadmap_diff(mutant_name: String, parent_name: String):
    """
    Compares two roadmap files and displays their differences.
    Highlights added/removed/changed lines.
    """
    if not roadmap_diff_panel:
        print_err("RoadmapDiffPanel not found.")
        return

    roadmap_diff_panel.show()

    var mutant_content = px_fs_reader.read_file_by_name(mutant_name).split("\n", false)
    var parent_content = px_fs_reader.read_file_by_name(parent_name).split("\n", false)

    var diff_result = _compute_line_diff(parent_content, mutant_content)

    var original_display_text = ""
    var mutated_display_text = ""
    var diff_summary = "Changes from " + parent_name + " to " + mutant_name + ":\n"
    var added_lines = 0
    var removed_lines = 0
    var changed_lines = 0

    for i in range(max(diff_result.size(), parent_content.size(), mutant_content.size())):
        var original_line = ""
        if i < parent_content.size():
            original_line = parent_content[i]
        
        var mutated_line = ""
        if i < mutant_content.size():
            mutated_line = mutant_content[i]

        var diff_type = ""
        if i < diff_result.size():
            diff_type = diff_result[i]

        if diff_type == "added":
            mutated_display_text += "[color=green]+" + mutated_line + "[/color]\n"
            original_display_text += "\n" # Placeholder to align lines
            added_lines += 1
        elif diff_type == "removed":
            original_display_text += "[color=red]-" + original_line + "[/color]\n"
            mutated_display_text += "\n" # Placeholder to align lines
            removed_lines += 1
        elif diff_type == "changed": # A line was modified
            original_display_text += "[color=orange]~" + original_line + "[/color]\n"
            mutated_display_text += "[color=orange]~" + mutated_line + "[/color]\n"
            changed_lines += 1
        else: # "unchanged" or outside the calculated diff
            original_display_text += original_line + "\n"
            mutated_display_text += mutated_line + "\n"

    diff_summary += "Added: " + str(added_lines) + " lines\n"
    diff_summary += "Removed: " + str(removed_lines) + " lines\n"
    diff_summary += "Changed: " + str(changed_lines) + " lines\n"

    if original_content_label:
        original_content_label.text = "[b]Parent:[/b]\n" + original_display_text
        original_content_label.set_use_bbcode(true)
    if mutated_content_label:
        mutated_content_label.text = "[b]Mutant:[/b]\n" + mutated_display_text
        mutated_content_label.set_use_bbcode(true)
    if diff_summary_label:
        diff_summary_label.text = diff_summary


func _compute_line_diff(list1: Array[String], list2: Array[String]) -> Array[String]:
    """
    A simplistic line-by-line diff algorithm.
    Returns an array of strings: "added", "removed", "changed", "unchanged" for each line in the longer list.
    This is a basic example; a real diff algorithm (like Longest Common Subsequence) is more complex.
    """
    var diff_result = []
    var ptr1 = 0
    var ptr2 = 0

    while ptr1 < list1.size() or ptr2 < list2.size():
        var line1_exists = ptr1 < list1.size()
        var line2_exists = ptr2 < list2.size()

        if line1_exists and line2_exists:
            if list1[ptr1] == list2[ptr2]:
                diff_result.append("unchanged")
                ptr1 += 1
                ptr2 += 1
            else:
                # Heuristic: if next line in list2 matches current list1, assume deletion
                # if next line in list1 matches current list2, assume insertion
                var assumed_deletion = false
                if ptr2 + 1 < list2.size() and list1[ptr1] == list2[ptr2+1]:
                    diff_result.append("added") # New line in list2
                    ptr2 += 1
                elif ptr1 + 1 < list1.size() and list2[ptr2] == list1[ptr1+1]:
                    diff_result.append("removed") # Line removed from list1
                    ptr1 += 1
                else:
                    diff_result.append("changed") # Line changed
                    ptr1 += 1
                    ptr2 += 1
        elif line1_exists:
            diff_result.append("removed")
            ptr1 += 1
        elif line2_exists:
            diff_result.append("added")
            ptr2 += 1
        else:
            break # Should not happen

    return diff_result

func plot_fitness_graph(roadmap_name: String):
    """
    Renders a fitness graph for a given roadmap.
    This will likely involve custom drawing functions on a Control node or using GraphEdit.
    """
    if not fitness_graph_container:
        print_err("FitnessGraph container not found.")
        return

    # Clear previous drawings if any
    for child in fitness_graph_container.get_children():
        child.queue_free()

    var relevant_runs = []
    for run_data in px_roadmap_registry.get_all_roadmap_results():
        if run_data.roadmap == roadmap_name:
            relevant_runs.append(run_data)

    if relevant_runs.is_empty():
        var no_data_label = Label.new()
        no_data_label.text = "No fitness data available for " + roadmap_name
        fitness_graph_container.add_child(no_data_label)
        return

    # Sort runs by timestamp for chronological plotting
    relevant_runs.sort_custom(func(a, b): return a.timestamp < b.timestamp)

    # Basic plotting: draw lines between points
    var line_2d = Line2D.new()
    line_2d.width = 2.0
    line_2d.default_color = Color.aqua
    fitness_graph_container.add_child(line_2d)

    var max_score = 0.0
    var min_score = 1000.0 # Arbitrarily high
    for run in relevant_runs:
        max_score = max(max_score, run.score)
        min_score = min(min_score, run.score)

    if max_score == min_score: # Prevent division by zero for flat lines
        max_score += 1.0
        min_score -= 1.0


    var plot_width = fitness_graph_container.size.x
    var plot_height = fitness_graph_container.size.y
    var x_step = plot_width / max(1.0, float(relevant_runs.size() - 1))

    for i, run in enumerate(relevant_runs):
        var x_pos = i * x_step
        var y_pos = plot_height - ((run.score - min_score) / (max_score - min_score)) * plot_height # Invert Y for drawing from bottom up
        line_2d.add_point(Vector2(x_pos, y_pos))

    # Add labels for min/max score or axes if desired
    var min_score_label = Label.new()
    min_score_label.text = "Min: " + str(snapped(min_score, 0.01))
    min_score_label.position = Vector2(0, plot_height - 20)
    fitness_graph_container.add_child(min_score_label)

    var max_score_label = Label.new()
    max_score_label.text = "Max: " + str(snapped(max_score, 0.01))
    max_score_label.position = Vector2(0, 0)
    fitness_graph_container.add_child(max_score_label)

func _parse_roadmap_header_metadata(content: String) -> Dictionary:
    """
    Parses # MUTATED_FROM, # REASON, # LINEAGE_ID, etc. from roadmap content.
    This should be called by PXMutantExplorer or this enhancer to enrich metadata.
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
        # Add more metadata parsing as needed
        if not line.begins_with("#") and not line.strip_edges().is_empty():
            break # Stop after header block

    return metadata

# --- Logging ---

func _log_enhancer_activity(message: String):
    """
    Helper function to log enhancer activities to PXScrollLog (if available).
    """
    if px_mutant_explorer and px_mutant_explorer.has_method("_log_explorer_activity"):
        px_mutant_explorer._log_explorer_activity("ENHANCER: " + message)
    else:
        print("PXMutantExplorerEnhancer (Console Log): ", message)