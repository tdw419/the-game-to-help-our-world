# PXSimPanel.gd
# This module provides a UI panel for visualizing the real-time progress and
# results of .pxdigest simulations performed by PXDigestPreviewRuntime.gd.
# It displays simulated logs, memory state, and predicted outcomes.

extends Control # Extends Control to be a UI element

# --- Configuration ---
@export var panel_region_rect: Rect2 = Rect2(0, 0, 1024, 768) # Default size for the simulation panel
@export var title_text: String = "PX Digest Simulation Panel"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging panel activity
@onready var px_digest_preview_runtime: PXDigestPreviewRuntime = get_node_or_null("../PXDigestPreviewRuntime") # To receive simulation signals
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # For exporting simulated logs

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var panel_title_label: Label = get_node_or_null("PanelTitleLabel")
@onready var simulation_status_label: Label = get_node_or_null("SimulationStatusLabel")
@onready var digest_name_label: Label = get_node_or_null("DigestNameLabel")
@onready var simulated_logs_display: RichTextLabel = get_node_or_null("SimulatedLogsDisplay")
@onready var simulated_memory_label: Label = get_node_or_null("SimulatedMemoryLabel") # For displaying memory state
@onready var predicted_outcome_label: Label = get_node_or_null("PredictedOutcomeLabel")
@onready var simulate_again_button: Button = get_node_or_null("SimulateAgainButton")
@onready var export_logs_button: Button = get_node_or_null("ExportLogsButton")
@onready var close_button: Button = get_node_or_null("CloseButton")

# --- Internal State ---
var _current_simulated_digest_path: String = ""
var _last_simulation_outcome: Dictionary = {}

# --- Godot Lifecycle Methods ---

func _ready():
    # Set panel position and size
    position = panel_region_rect.position
    size = panel_region_rect.size

    # Check for essential dependencies
    if not px_scroll_log or not px_digest_preview_runtime or not px_fs_reader:
        print_err("PXSimPanel: Essential dependencies missing. Simulation panel disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        hide()
        return

    # Initialize UI elements
    if panel_title_label:
        panel_title_label.text = title_text
    _clear_display()

    # Connect signals from PXDigestPreviewRuntime
    if px_digest_preview_runtime:
        px_digest_preview_runtime.simulation_started.connect(Callable(self, "_on_simulation_started"))
        px_digest_preview_runtime.simulation_step_completed.connect(Callable(self, "_on_simulation_step_completed"))
        px_digest_preview_runtime.simulation_completed.connect(Callable(self, "_on_simulation_completed"))
        px_digest_preview_runtime.simulation_failed.connect(Callable(self, "_on_simulation_failed"))
        _log_panel_activity("Connected to PXDigestPreviewRuntime signals.")

    # Connect UI button signals
    if simulate_again_button:
        simulate_again_button.pressed.connect(Callable(self, "_on_simulate_again_pressed"))
    if export_logs_button:
        export_logs_button.pressed.connect(Callable(self, "_on_export_logs_pressed"))
    if close_button:
        close_button.pressed.connect(Callable(self, "hide_panel"))

    # Initially hide the panel
    hide()
    _log_panel_activity("Initialized and hidden.")

# --- Public Methods ---

func show_panel(digest_path: String):
    """
    Displays the simulation panel and initiates a simulation for the given digest.
    """
    _current_simulated_digest_path = digest_path
    _clear_display()
    
    if digest_name_label:
        digest_name_label.text = "Digest: " + digest_path.get_file()

    show()
    _log_panel_activity("Panel shown for digest: " + digest_path.get_file())
    
    # Trigger simulation from here, or assume it's already triggered by PXDigestInspector
    # For this scaffold, we'll assume PXDigestInspector calls simulate_digest()
    # and this panel just displays the results. If this panel is the trigger,
    # uncomment the line below and ensure PXDigestPreviewRuntime is ready.
    # px_digest_preview_runtime.simulate_digest(digest_path)

func hide_panel():
    """Hides the simulation panel."""
    hide()
    _log_panel_activity("Panel hidden.")
    _clear_display()

# --- Simulation Signal Callbacks ---

func _on_simulation_started(digest_path: String):
    """Callback when a simulation begins."""
    _log_panel_activity("Simulation started for: " + digest_path.get_file())
    if simulation_status_label:
        simulation_status_label.text = "Status: Running..."
        simulation_status_label.modulate = Color.YELLOW
    if simulated_logs_display:
        simulated_logs_display.clear()
        simulated_logs_display.append_text("[b]Simulation Log:[/b]\n")
    if predicted_outcome_label:
        predicted_outcome_label.text = "Predicted Outcome: Analyzing..."
        predicted_outcome_label.modulate = Color.WHITE
    if simulated_memory_label:
        simulated_memory_label.text = "Simulated Memory State: Empty"
        simulated_memory_label.modulate = Color.WHITE

func _on_simulation_step_completed(step_data: Dictionary):
    """Callback for each completed simulation step."""
    # This can be used for real-time updates of a progress bar or step-by-step logs
    if simulated_logs_display and step_data.has("log_entry"):
        simulated_logs_display.append_text(step_data["log_entry"] + "\n")
        simulated_logs_display.scroll_to_line(simulated_logs_display.get_line_count() - 1)
    if simulation_status_label:
        simulation_status_label.text = "Status: Step %d..." % step_data.get("step_count", 0)
    # Update simulated memory display if step_data contains memory changes (M4)

func _on_simulation_completed(digest_path: String, outcome: Dictionary):
    """Callback when a simulation successfully completes."""
    _log_panel_activity("Simulation completed for: " + digest_path.get_file())
    _last_simulation_outcome = outcome
    
    if simulation_status_label:
        simulation_status_label.text = "Status: Completed!"
        simulation_status_label.modulate = Color.GREEN
    
    if simulated_logs_display and outcome.has("simulated_logs"):
        for log_entry in outcome["simulated_logs"]:
            simulated_logs_display.append_text(log_entry + "\n")
        simulated_logs_display.scroll_to_line(simulated_logs_display.get_line_count() - 1)

    if predicted_outcome_label:
        predicted_outcome_label.text = "Predicted Outcome: [b]%s[/b]" % outcome.get("predicted_result", "Unknown")
        predicted_outcome_label.modulate = Color.LIME
        predicted_outcome_label.set_use_bbcode(true)

    if simulated_memory_label and outcome.has("final_memory_state"):
        var mem_state_str = "Simulated Memory State:\n"
        if outcome["final_memory_state"].is_empty():
            mem_state_str += "  (No significant changes)"
        else:
            for key in outcome["final_memory_state"].keys():
                mem_state_str += "  %s: %s\n" % [key, outcome["final_memory_state"][key]]
        simulated_memory_label.text = mem_state_str
        simulated_memory_label.modulate = Color.WHITE

func _on_simulation_failed(digest_path: String, error_message: String):
    """Callback when a simulation fails."""
    _log_panel_activity("Simulation failed for: %s. Error: %s" % [digest_path.get_file(), error_message])
    _last_simulation_outcome = {"status": "FAILED", "reason": error_message}
    
    if simulation_status_label:
        simulation_status_label.text = "Status: Failed!"
        simulation_status_label.modulate = Color.RED
    if predicted_outcome_label:
        predicted_outcome_label.text = "Predicted Outcome: [b]FAILURE[/b]"
        predicted_outcome_label.modulate = Color.RED
        predicted_outcome_label.set_use_bbcode(true)
    if simulated_logs_display:
        simulated_logs_display.append_text("[color=red]SIMULATION FAILED: %s[/color]\n" % error_message)
        simulated_logs_display.scroll_to_line(simulated_logs_display.get_line_count() - 1)

# --- UI Button Callbacks ---

func _on_simulate_again_pressed():
    """Triggers a re-simulation of the current digest."""
    if not _current_simulated_digest_path.is_empty():
        _log_panel_activity("Simulate Again button pressed for: " + _current_simulated_digest_path.get_file())
        px_digest_preview_runtime.simulate_digest(_current_simulated_digest_path)
    else:
        _log_panel_activity("No digest loaded to simulate again.")

func _on_export_logs_pressed():
    """Exports the simulated logs to a .scroll file."""
    if simulated_logs_display and not simulated_logs_display.text.is_empty():
        var file_name = "sim_log_" + _current_simulated_digest_path.get_file().replace(".pxdigest", "") + "_" + str(Time.get_unix_time_from_system()) + ".scroll"
        var file_path = "user://pxlogs/simulation/" + file_name # Example path
        
        var file = FileAccess.open(file_path, FileAccess.WRITE)
        if file:
            file.store_string(simulated_logs_display.text)
            file.close()
            _log_panel_activity("Simulated logs exported to: " + file_path)
        else:
            _log_panel_activity("Error: Could not export logs to: " + file_path)
    else:
        _log_panel_activity("No simulated logs to export.")

# --- Utility Functions ---

func _clear_display():
    """Clears all display labels."""
    if simulation_status_label: simulation_status_label.text = "Status: Idle"
    if digest_name_label: digest_name_label.text = "Digest: None"
    if simulated_logs_display: simulated_logs_display.clear()
    if simulated_memory_label: simulated_memory_label.text = "Simulated Memory State: N/A"
    if predicted_outcome_label: predicted_outcome_label.text = "Predicted Outcome: N/A"

# --- Logging ---

func _log_panel_activity(message: String):
    """
    Helper function to log panel activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXSIM_PANEL: " + message)
    else:
        print("PXSimPanel (Console Log): ", message)

