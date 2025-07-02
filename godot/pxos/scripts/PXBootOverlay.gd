# PXBootOverlay.gd
# This module provides a visual overlay to inform the user that a system is
# being loaded and booted. It displays a "Booting..." message, the file name,
# and a simple animation, then hides itself when the process is complete or times out.

extends Control # Extends Control to be a UI element

# --- Configuration ---
# Duration in seconds before the overlay automatically hides if no session end signal is received.
@export var auto_hide_timeout_seconds: float = 5.0
# The text to display as the main title.
@export var title_text: String = "Booting System..."

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging overlay activity
@onready var px_drop_zone: PXDropZone = get_node_or_null("../PXDropZone") # To show overlay when file is dropped
@onready var px_runtime: PXRuntime = get_node_or_null("../PXRuntime") # To hide overlay when runtime session starts/ends

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
@onready var title_label: Label = get_node_or_null("TitleLabel")
@onready var file_name_label: Label = get_node_or_null("FileNameLabel")
@onready var spinner_animation: AnimationPlayer = get_node_or_null("SpinnerAnimation") # Or a simple Tween/TextureRect for animation

# --- Internal State ---
var _hide_timer: Timer = null

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_drop_zone or not px_runtime:
        print_err("PXBootOverlay: Essential dependencies missing. Overlay may not function correctly.")
        # Do not disable the node entirely, as it can still be manually shown/hidden.

    # Initialize UI elements
    if title_label:
        title_label.text = title_text
    if file_name_label:
        file_name_label.text = "" # Starts empty

    # Connect signals
    if px_drop_zone:
        px_drop_zone.file_dropped.connect(Callable(self, "_on_file_dropped"))
        _log_overlay_activity("Connected to PXDropZone.")
    if px_runtime:
        px_runtime.runtime_session_started.connect(Callable(self, "_on_runtime_session_started"))
        px_runtime.runtime_session_ended.connect(Callable(self, "_on_runtime_session_ended"))
        _log_overlay_activity("Connected to PXRuntime.")

    # Set up the timer for auto-hiding
    _hide_timer = Timer.new()
    add_child(_hide_timer)
    _hide_timer.wait_time = auto_hide_timeout_seconds
    _hide_timer.one_shot = true
    _hide_timer.timeout.connect(Callable(self, "hide_overlay"))

    # Initially hide the overlay
    hide()
    _log_overlay_activity("Initialized and hidden.")

# --- Public Methods ---

func show_overlay(file_name: String = ""):
    """
    Displays the booting overlay with an optional file name.
    Starts the auto-hide timer.
    """
    if file_name_label:
        file_name_label.text = file_name
    
    show()
    _log_overlay_activity("Overlay shown for: " + file_name)
    
    if spinner_animation:
        spinner_animation.play("boot_spinner") # Assuming an animation named "boot_spinner"
    
    _hide_timer.start()

func hide_overlay():
    """
    Hides the booting overlay and stops the timer.
    """
    if is_visible():
        hide()
        _log_overlay_activity("Overlay hidden.")
        if spinner_animation and spinner_animation.is_playing():
            spinner_animation.stop()
        _hide_timer.stop()

# --- Signal Callbacks ---

func _on_file_dropped(file_path: String, file_type: String):
    """
    Callback when a file is dropped into PXDropZone.
    Shows the overlay.
    """
    var base_file_name = file_path.get_file()
    show_overlay(base_file_name)
    _log_overlay_activity("Triggered by file drop: " + base_file_name)

func _on_runtime_session_started(session_id: String, system_name: String):
    """
    Callback when PXRuntime signals a session has started.
    Confirms the boot is in progress, but keeps overlay visible for a bit.
    """
    _log_overlay_activity("Runtime session started: " + session_id + " for " + system_name)
    # You might want to update the message here, e.g., "System running..."
    # For now, we'll let the auto_hide_timeout_seconds handle it, or wait for session_ended.

func _on_runtime_session_ended(session_id: String, outcome: String):
    """
    Callback when PXRuntime signals a session has ended.
    Hides the overlay.
    """
    _log_overlay_activity("Runtime session ended: " + session_id + " with outcome: " + outcome)
    hide_overlay()

# --- Logging ---

func _log_overlay_activity(message: String):
    """
    Helper function to log overlay activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXBOOTOVERLAY: " + message)
    else:
        print("PXBootOverlay (Console Log): ", message)

