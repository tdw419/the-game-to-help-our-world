# PXBootSim.gd
# This script manages the visual simulation of the PXBoot process
# and now allows the user to select an ISO file via a UI.

extends Control

@onready var log_output_label: RichTextLabel = $VBoxContainer/LogOutputLabel
@onready var select_iso_button: Button = $VBoxContainer/SelectISOButton
@onready var file_dialog: FileDialog = $FileDialog

var log_messages: Array[String] = []
var current_log_index: int = 0
var animation_speed: float = 0.05 # Seconds per character or per line

var pxvm_instance = null # Reference to the PXVM instance
var selected_iso_path: String = "" # Stores the path selected by the user

func _ready():
    # Initialize the log output area
    log_output_label.text = ""
    _process_px_log_message("[PXBIOS] Welcome to PXBootSim!")
    _process_px_log_message("[PXBIOS] Please select an ISO file to begin.")
    
    # PXVM will be initialized only after an ISO is selected
    # Ensure PXVM.gd is set up to accept the ISO path dynamically.

func _process(delta):
    # This function is now primarily for animating log messages.
    # The PXVM execution is triggered by _on_FileDialog_file_selected.
    if not get_node("LogAnimationTimer").is_stopped():
        if current_log_index < log_messages.size():
            var message_to_display = log_messages[current_log_index]
            log_output_label.append_text(message_to_display + "\n")
            log_output_label.scroll_to_line(log_output_label.get_line_count() - 1) # Auto-scroll
            current_log_index += 1
        else:
            get_node("LogAnimationTimer").stop()

# Call this function from your PXVM simulation whenever a PX_LOG instruction is executed.
func _process_px_log_message(message: String):
    log_messages.append(message)
    # Start animation if not already running
    if get_node("LogAnimationTimer").is_stopped():
        get_node("LogAnimationTimer").start(animation_speed)

# --- NEW: ISO Selection Logic ---
func _on_SelectISOButton_pressed():
    file_dialog.popup_centered()

func _on_FileDialog_file_selected(path: String):
    selected_iso_path = path
    _process_px_log_message(f"[PXBIOS] Selected ISO: {selected_iso_path}")
    select_iso_button.hide() # Hide the button once ISO is selected

    _initialize_pxvm() # Initialize and start PXVM with the selected ISO

func _initialize_pxvm():
    if pxvm_instance:
        pxvm_instance.queue_free() # Remove old instance if any
        pxvm_instance = null

    # Create an instance of PXVM.gd (assuming it's a script that can be instantiated)
    # or add it as a child node in your scene and get its reference.
    # For now, let's assume PXVM.gd is an AutoLoad singleton or a child of this scene.
    # If PXVM.gd is a script, you'd load it like this:
    var PXVM_Script = load("res://PXVM.gd") # Adjust path if PXVM.gd is elsewhere
    if PXVM_Script:
        pxvm_instance = PXVM_Script.new()
        add_child(pxvm_instance) # Add PXVM as a child of PXBootSim

        # Pass the selected ISO path to PXVM
        if pxvm_instance.has_method("set_iso_path"):
            pxvm_instance.set_iso_path(selected_iso_path)
        else:
            _process_px_log_message("[PXBIOS] ERROR: PXVM.gd does not have 'set_iso_path' method!")
            return

        # Pass a reference to PXBootSim itself for logging
        if pxvm_instance.has_method("set_px_boot_sim"):
            pxvm_instance.set_px_boot_sim(self)
        else:
            _process_px_log_message("[PXBIOS] ERROR: PXVM.gd does not have 'set_px_boot_sim' method!")
            return
        
        _process_px_log_message("[PXBIOS] PXVM initialized. Starting boot sequence...")
        # PXVM's _ready() should now trigger the boot sequence using the passed path.
    else:
        _process_px_log_message("[PXBIOS] ERROR: Could not load PXVM.gd script!")

