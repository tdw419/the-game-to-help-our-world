# PXMutantExplorer.gd
# This module provides a visual interface for exploring and comparing
# mutated roadmap variants stored in PXFS. It displays their fitness,
# lineage (conceptual), and allows for visual inspection of their content.

extends Control # Extends Control for GUI elements

# --- Configuration ---
# The Rect2 defining the panel's position and size on the display.
@export var panel_region_rect: Rect2 = Rect2(0, 0, 128, 128) # Example: Full screen or large area

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging panel activity
@onready var px_scroll_library: PXScrollLibrary = get_node_or_null("../PXScrollLibrary") # To get available scrolls
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read roadmap content from PXFS
@onready var px_roadmap_registry: PXRoadmapRegistry = get_node_or_null("../PXRoadmapRegistry") # To get fitness scores
# @onready var px_roadmap_lineage_logger: Node = null # Future: For actual lineage data

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var roadmap_list_dropdown: OptionButton = get_node_or_null("RoadmapListDropdown")
@onready var load_button: Button = get_node_or_null("LoadButton")
@onready var content_display_label: Label = get_node_or_null("ContentDisplayLabel")
@onready var metadata_label: Label = get_node_or_null("MetadataLabel")
@onready var panel_title_label: Label = get_node_or_null("PanelTitleLabel")

# --- Internal State ---
var _loaded_roadmap_name: String = ""
var _loaded_roadmap_content: Array[String] = []
var _loaded_roadmap_metadata: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    # Set panel position and size
    position = panel_region_rect.position
    size = panel_region_rect.size

    # Check for essential dependencies
    if not px_scroll_log or not px_scroll_library or not px_fs_reader or not px_roadmap_registry:
        print_err("PXMutantExplorer: Essential dependencies missing. Panel disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        hide()
        return

    # Set up UI connections
    if roadmap_list_dropdown:
        roadmap_list_dropdown.item_selected.connect(Callable(self, "_on_roadmap_selected"))
    if load_button:
        load_button.pressed.connect(Callable(self, "_on_load_button_pressed"))
    if panel_title_label:
        panel_title_label.text = "PX Mutant Explorer"

    _populate_roadmap_list()
    _log_explorer_activity("Initialized.")

func _populate_roadmap_list():
    """Populates the dropdown with available roadmaps from PXScrollLibrary."""
    if roadmap_list_dropdown:
        roadmap_list_dropdown.clear()
        var roadmap_names = px_scroll_library.get_available_scroll_names()
        roadmap_names.sort()
        for name in roadmap_names:
            roadmap_list_dropdown.add_item(name)
        if not roadmap_names.is_empty():
            roadmap_list_dropdown.select(0)
            _on_roadmap_selected(0) # Select first by default

# --- UI Callbacks ---

func _on_roadmap_selected(index: int):
    _loaded_roadmap_name = roadmap_list_dropdown.get_item_text(index)
    _log_explorer_activity("Selected roadmap: " + _loaded_roadmap_name)
    _display_roadmap_info() # Update info immediately on selection

func _on_load_button_pressed():
    """Loads and displays the selected roadmap's content and metadata."""
    if _loaded_roadmap_name.is_empty():
        _log_explorer_activity("No roadmap selected to load.")
        return

    _log_explorer_activity("Loading roadmap: " + _loaded_roadmap_name)
    var roadmap_content_ztxt = px_fs_reader.read_file_by_name(_loaded_roadmap_name)
    
    if not roadmap_content_ztxt.is_empty():
        _loaded_roadmap_content = roadmap_content_ztxt.split("\n").filter(func(step): return not step.strip_edges().is_empty() and not step.strip_edges().begins_with("#"))
        _loaded_roadmap_metadata = _get_roadmap_metadata(_loaded_roadmap_name)
        _display_roadmap_info()
        _log_explorer_activity("Roadmap loaded successfully.")
    else:
        _log_explorer_activity("Failed to load roadmap content for: " + _loaded_roadmap_name)
        _loaded_roadmap_content = ["ERROR: Could not load content."]
        _loaded_roadmap_metadata = {}
        _display_roadmap_info()

# --- Display Logic ---

func _display_roadmap_info():
    """Updates the UI labels with roadmap content and metadata."""
    if content_display_label:
        content_display_label.text = "\n".join(_loaded_roadmap_content)
    
    if metadata_label:
        var metadata_text = "Name: " + _loaded_roadmap_name + "\n"
        var registry_results = px_roadmap_registry.get_all_roadmap_results()
        var relevant_runs = []
        for run in registry_results:
            if run.roadmap == _loaded_roadmap_name:
                relevant_runs.append(run)
        
        if not relevant_runs.is_empty():
            var total_score = 0.0
            var success_count = 0
            var failure_count = 0
            var total_duration = 0.0
            var total_steps = 0
            var total_mutations = 0
            
            for run in relevant_runs:
                total_score += run.score
                total_duration += run.duration
                total_steps += run.steps
                total_mutations += run.mutations
                if run.outcome == "SUCCESS": success_count += 1
                elif run.outcome == "FAILURE": failure_count += 1
            
            var avg_score = total_score / relevant_runs.size()
            var avg_duration = total_duration / relevant_runs.size()
            var avg_steps = total_steps / relevant_runs.size()
            
            metadata_text += "Runs: " + str(relevant_runs.size()) + "\n"
            metadata_text += "Avg Score: " + str(snapped(avg_score, 0.01)) + "\n"
            metadata_text += "Success: " + str(success_count) + " / " + str(relevant_runs.size()) + "\n"
            metadata_text += "Avg Duration: " + str(snapped(avg_duration, 0.1)) + "s\n"
            metadata_text += "Avg Steps: " + str(snapped(avg_steps, 0.1)) + "\n"
            metadata_text += "Total Mutations: " + str(total_mutations) + "\n"
            
            # Add lineage info conceptually (needs PXRoadmapLineageLogger)
            # metadata_text += "Parent: " + _loaded_roadmap_metadata.get("parent_id", "N/A") + "\n"
            # metadata_text += "Mutated From: " + _loaded_roadmap_metadata.get("mutated_from", "N/A") + "\n"
            
        else:
            metadata_text += "No execution history found.\n"
        
        metadata_label.text = metadata_text

func _get_roadmap_metadata(roadmap_name: String) -> Dictionary:
    """Retrieves metadata for a roadmap (e.g., from PXScrollLibrary or PXFS header)."""
    # This is a placeholder. In a real system, metadata like parent ID, mutation reason
    # might be stored in the scroll header itself or in PXScrollLibrary's index.
    var metadata = {}
    var scroll_entry = px_scroll_library.scroll_index.get(roadmap_name)
    if scroll_entry and scroll_entry.has("metadata"):
        metadata = scroll_entry.metadata
    
    # You might also read the first few lines of the roadmap content for # GOAL: tags
    var content = px_fs_reader.read_file_by_name(roadmap_name)
    if not content.is_empty():
        var lines = content.split("\n")
        for line in lines:
            if line.begins_with("# GOAL:"):
                metadata["goal"] = line.replace("# GOAL:", "").strip_edges()
            if line.begins_with("# STRATEGY:"):
                metadata["strategy"] = line.replace("# STRATEGY:", "").strip_edges()
            # Add more metadata parsing as needed
            if not line.begins_with("#"): break # Stop after headers
    
    return metadata

# --- Logging ---

func _log_explorer_activity(message: String):
    """
    Helper function to log explorer activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("EXPLORER: " + message)
    else:
        print("PXMutantExplorer (Console Log): ", message)

