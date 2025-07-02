# pxos_feature_debugger.gd
extends Control

# ... (existing @export variables, @onready vars, _pxos_constants, _log_file, etc.) ...

# --- New UI Element for Hover Display ---
@onready var _hover_display_label = $"HoverDisplayLabel" as Label # Add a Label node to your scene for this

# --- New File Access for Sending Signals to PXOS ---
const PXOS_INTERACTION_FILE_PATH = "user://pxos_interaction_signal.log"


func _ready():
	# ... (existing _load_pxos_constants, _init_logs, _fetch_pxos_ram_dump, _update_visuals) ...

	# Connect mouse input for the memory heatmap
	_memory_heatmap_texture.gui_input.connect(_on_memory_heatmap_gui_input)

	_init_interaction_file() # New: Initialize the interaction file

	set_process(true)


func _init_interaction_file():
	# Ensure the interaction file exists and is empty or readable
	var file = FileAccess.open(PXOS_INTERACTION_FILE_PATH, FileAccess.WRITE)
	if file:
		file.close()
	else:
		push_error("Could not create PXOS interaction file: " + PXOS_INTERACTION_FILE_PATH)


func _on_memory_heatmap_gui_input(event: InputEvent):
	if event is InputEventMouseMotion:
		# Hover highlight
		var local_pos = _memory_heatmap_texture.get_local_mouse_position()
		_update_hover_display(local_pos)
	elif event is InputEventMouseButton:
		if event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			# Click detection
			var local_pos = _memory_heatmap_texture.get_local_mouse_position()
			_send_click_signal_to_pxos(local_pos)
			# Accept event to prevent it from propagating further
			get_viewport().set_input_as_handled()


func _update_hover_display(local_pos: Vector2):
	# Convert local pixel position on TextureRect to memory address
	var mem_addr = _pixel_to_memory_address(local_pos)
	if mem_addr != -1 and not _pxos_ram_data.empty() and mem_addr < _pxos_ram_data.size():
		var byte_value = _pxos_ram_data[mem_addr]
		_hover_display_label.text = "Addr: 0x%X, Val: 0x%X" % [mem_addr, byte_value]
		_hover_display_label.set_position(get_global_mouse_position() + Vector2(10,10)) # Display near mouse
	else:
		_hover_display_label.text = ""


func _send_click_signal_to_pxos(local_pos: Vector2):
	var clicked_addr = _pixel_to_memory_address(local_pos)
	if clicked_addr != -1:
		var signal_type = "CLICK"
		# Format: "TYPE:ADDRESS:VALUE"
		var signal_data = "%s:0x%X:0x%X" % [signal_type, clicked_addr, _pxos_ram_data[clicked_addr]]

		# Append to a file that pxos_host_runtime.py monitors
		var file = FileAccess.open(PXOS_INTERACTION_FILE_PATH, FileAccess.WRITE)
		if file:
			file.seek_end() # Append to end of file
			file.store_line(signal_data)
			file.close()
			push_warning("Sent signal to PXOS: " + signal_data) # Use warning for visible log
		else:
			push_error("Could not write to PXOS interaction file!")


func _pixel_to_memory_address(pixel_pos: Vector2) -> int:
	# Assuming your heatmap is 256x256 pixels representing 64KB RAM (256*256 = 65536)
	# Scale pixel pos relative to TextureRect size if it's not 256x256
	var x = int(pixel_pos.x)
	var y = int(pixel_pos.y)

	if x < 0 or x >= 256 or y < 0 or y >= 256:
		return -1 # Out of bounds

	return y * 256 + x


# --- Update _update_visuals to clear _highlight_regions more carefully if needed ---
# If you want persistent highlights, manage _highlight_regions lifecycle
# based on explicit calls to add/remove, not clearing every frame.

# You will need to add _hover_display_label to your @onready var list.
