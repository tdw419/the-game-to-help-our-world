# PXMemoryGlyphEditor.gd
# This script provides an interactive UI for directly editing byte values
# within the PXMemoryRegion. It allows users to click on memory pixels,
# input a byte value (0-255), and see the change reflected immediately.

extends Control # Extends Control to handle UI input (mouse clicks)

# --- Configuration ---
# The Rect2 defining the interactive area for memory editing.
# This should typically align with the PXMemoryRegion's rect.
@export var editable_memory_region: Rect2 = Rect2(45, 0, 15, 64) # Example: Same as memory region

# The frequency at which the editor checks for input (if not using _input directly).
const INPUT_CHECK_FREQUENCY = 0.05 # Check every 0.05 seconds

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # Reference to the PXMemory node

# --- Internal State ---
var current_edit_coord: Vector2 = Vector2.INF # The pixel coordinate currently being edited
var time_since_last_input_check: float = 0.0

# --- UI Elements (Placeholders - you'll need to add these in Godot scene) ---
# A simple message label to show instructions or current value.
@onready var message_label: Label = get_node_or_null("MessageLabel") # Path to a Label node
# A LineEdit for user input of the byte value.
@onready var value_input: LineEdit = get_node_or_null("ValueInput") # Path to a LineEdit node
# A Button to confirm the input.
@onready var confirm_button: Button = get_node_or_null("ConfirmButton") # Path to a Button node

# --- Godot Lifecycle Methods ---

func _ready():
    # Ensure dependencies are available
    if not display_screen:
        print_err("PXMemoryGlyphEditor: 'DisplayScreen' TextureRect not found. Cannot operate.")
        set_process(false)
        return
    if not px_memory:
        print_err("PXMemoryGlyphEditor: 'PXMemory' node (PXMemoryRegion.gd) not found. Cannot edit memory.")
        set_process(false)
        return

    # Set up UI connections
    if value_input:
        value_input.text_submitted.connect(Callable(self, "_on_value_input_submitted"))
        value_input.focus_exited.connect(Callable(self, "_on_value_input_focus_exited"))
        value_input.hide() # Hide initially
    if confirm_button:
        confirm_button.pressed.connect(Callable(self, "_on_confirm_button_pressed"))
        confirm_button.hide() # Hide initially
    if message_label:
        message_label.text = "Click on a memory pixel to edit."

    # Set up mouse input for this Control node
    set_mouse_filter(Control.MOUSE_FILTER_STOP) # Stop mouse events from propagating further
    set_process_input(true) # Enable _input function

    # Make this Control node cover the entire display area (or relevant part)
    # This ensures it captures clicks over the memory region.
    # You might want to adjust its size/position in the editor.
    size = display_screen.size # Assume it covers the display for click detection
    position = display_screen.position

    print("PXMemoryGlyphEditor: Initialized. Ready for memory editing.")

func _process(delta):
    time_since_last_input_check += delta
    if time_since_last_input_check >= INPUT_CHECK_FREQUENCY:
        # You could add periodic checks here if not using _input for all interactions
        time_since_last_input_check = 0.0
        pass

func _input(event):
    # Handle mouse clicks for selecting memory pixels
    if event is InputEventMouseButton and event.pressed:
        if event.button_index == MOUSE_BUTTON_LEFT:
            var local_click_pos = event.position # Position relative to this Control node
            var display_global_pos = display_screen.global_position
            var display_scale = display_screen.get_global_transform().get_scale()

            # Convert click position to pixel coordinate on the DisplayScreen
            var pixel_coord_on_display = (local_click_pos - display_global_pos) / display_scale

            # Check if the click is within the editable memory region
            if editable_memory_region.has_point(pixel_coord_on_display):
                current_edit_coord = Vector2(floor(pixel_coord_on_display.x), floor(pixel_coord_on_display.y))
                print("PXMemoryGlyphEditor: Selected memory pixel at: ", current_edit_coord)
                show_editor_ui()
                # Read current value and pre-fill input
                var current_value = px_memory.read_byte(int(current_edit_coord.x), int(current_edit_coord.y))
                if current_value != -1 and value_input:
                    value_input.text = str(current_value)
                    value_input.grab_focus() # Give focus to the input field
                if message_label:
                    message_label.text = "Editing (" + str(int(current_edit_coord.x)) + "," + str(int(current_edit_coord.y)) + "). Enter byte (0-255):"
            else:
                # Clicked outside editable region, hide UI
                hide_editor_ui()
                if message_label:
                    message_label.text = "Click on a memory pixel to edit."

# --- UI Management ---

func show_editor_ui():
    if value_input: value_input.show()
    if confirm_button: confirm_button.show()
    # Position the UI elements near the clicked pixel or in a fixed spot
    # For simplicity, let's just place them in a fixed spot for now.
    if value_input: value_input.position = Vector2(10, 10) # Example position
    if confirm_button: confirm_button.position = Vector2(10, 40) # Example position

func hide_editor_ui():
    if value_input:
        value_input.release_focus()
        value_input.hide()
    if confirm_button: confirm_button.hide()
    current_edit_coord = Vector2.INF # Reset selected coordinate
    if message_label:
        message_label.text = "Click on a memory pixel to edit."

# --- UI Callbacks ---

func _on_value_input_submitted(new_text: String):
    # Called when Enter is pressed in the LineEdit
    _write_value_to_memory(new_text)

func _on_confirm_button_pressed():
    # Called when the Confirm button is pressed
    if value_input:
        _write_value_to_memory(value_input.text)

func _on_value_input_focus_exited():
    # Optional: If focus is lost, you might want to hide the UI or auto-confirm
    # For now, let's hide it if no value was submitted.
    if value_input and value_input.text.is_empty():
        hide_editor_ui()

# --- Memory Write Logic ---

func _write_value_to_memory(text_value: String):
    if current_edit_coord == Vector2.INF:
        print_warn("PXMemoryGlyphEditor: No pixel selected for writing.")
        return

    var value_to_write = text_value.to_int()
    if not text_value.is_valid_int() or value_to_write < 0 or value_to_write > 255:
        if message_label:
            message_label.text = "Invalid value! Enter 0-255."
        print_err("PXMemoryGlyphEditor: Invalid input value: '", text_value, "'. Must be 0-255.")
        return

    var success = px_memory.write_byte(int(current_edit_coord.x), int(current_edit_coord.y), value_to_write)
    if success:
        print("PXMemoryGlyphEditor: Wrote ", value_to_write, " to (", int(current_edit_coord.x), ",", int(current_edit_coord.y), ")")
        if message_label:
            message_label.text = "Wrote " + str(value_to_write) + " to (" + str(int(current_edit_coord.x)) + "," + str(int(current_edit_coord.y)) + "). Click another pixel."
        hide_editor_ui() # Hide UI after successful write
    else:
        print_err("PXMemoryGlyphEditor: Failed to write value to memory.")
        if message_label:
            message_label.text = "Write failed. Try again."

