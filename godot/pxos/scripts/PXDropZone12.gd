# PXDropZone.gd
# This module creates a UI area that detects drag-and-drop file operations.
# It emits specific signals when supported file types (like .iso) are dropped,
# allowing PXRuntime or other modules to process the incoming file.

extends Control # Extends Control to be a UI element

# --- Configuration ---
# List of file extensions (without the dot) that this drop zone will accept.
@export var accepted_file_types: Array[String] = ["iso", "img", "elf", "txt", "zTXT"]

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging drop zone activity

# Signals for other PXOS modules to connect to
signal file_dropped(file_path: String, file_type: String) # Generic signal for any accepted file type
signal iso_file_dropped(path: String) # Specific signal for .iso files (M1 of PXRUNTIME_BOOT_ISO_V1)

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log:
        print_err("PXDropZone: PXScrollLog dependency missing. Drop zone logging disabled.")
        # Do not disable the node entirely, as it can still detect drops.

    _log_drop_zone_activity("Initialized. Accepting types: " + str(accepted_file_types))
    
    # Ensure the control node can receive input events
    set_process_input(true)
    set_mouse_filter(Control.MOUSE_FILTER_PASS) # Allows input events to pass through to children if any

func _can_drop_data(at_position: Vector2, data: Variant) -> bool:
    """
    Godot's built-in callback to check if the dropped data is acceptable.
    This is where we filter by file type and provide visual feedback.
    """
    if data is Dictionary and data.has("files"):
        var files = data["files"]
        if files.is_empty():
            modulate = Color.WHITE # Reset color if no files
            return false
        
        var file_path = files[0]
        var file_extension = file_path.get_extension().to_lower()
        
        if accepted_file_types.has(file_extension):
            # Visually indicate that a drop is possible
            modulate = Color.web_color("40C0FF", 0.5) # Light blue with transparency
            return true
    
    modulate = Color.WHITE # Reset color if not accepted
    return false

func _drop_data(at_position: Vector2, data: Variant):
    """
    Godot's built-in callback for when data is actually dropped.
    Emits specific signals based on file type.
    """
    modulate = Color.WHITE # Reset color after drop attempt

    if data is Dictionary and data.has("files"):
        var files = data["files"]
        if files.is_empty():
            _log_drop_zone_activity("No files found in dropped data.")
            return

        var dropped_file_path = files[0]
        var dropped_file_extension = dropped_file_path.get_extension().to_lower()

        if accepted_file_types.has(dropped_file_extension):
            _log_drop_zone_activity("File dropped: %s (Type: %s)" % [dropped_file_path, dropped_file_extension])
            
            # Emit generic signal
            emit_signal("file_dropped", dropped_file_path, dropped_file_extension)

            # Emit specific ISO signal if applicable
            if dropped_file_extension == "iso":
                _log_drop_zone_activity("ISO file detected, emitting iso_file_dropped signal.")
                emit_signal("iso_file_dropped", dropped_file_path)
        else:
            _log_drop_zone_activity("Dropped file type '%s' not accepted." % dropped_file_extension)
    else:
        _log_drop_zone_activity("Dropped data is not a recognized file type.")

func _gui_input(event: InputEvent):
    """
    Handles GUI input events, specifically for drag-and-drop visual feedback.
    """
    if event is InputEventMouse:
        if event.is_released():
            modulate = Color.WHITE # Reset color if mouse is released anywhere after a drag (even outside drop zone)

# --- Logging ---

func _log_drop_zone_activity(message: String):
    """
    Helper function to log drop zone activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXDROPZONE: " + message)
    else:
        print("PXDropZone (Console Log): ", message)

