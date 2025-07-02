# scripts/PXDebugger.gd
extends Control

class_name PXDebugger

@onready var debug_log_label = $VBoxContainer/DebugLogLabel as Label
@onready var pixel_info_label = $VBoxContainer/PixelInfoLabel as Label
@onready var hover_info_label = $VBoxContainer/HoverInfoLabel as Label
@onready var timeline_container = $VBoxContainer/TimelineHBoxContainer/TimelinePanel/TimelineScrollContainer/TimelineGridContainer as GridContainer
@onready var known_claims_label = $VBoxContainer/KnownClaimsLabel as Label

# NEW: Phase 5.5 Debugging UI elements
@onready var debug_mode_toggle_button = $VBoxContainer/DebugControls/DebugModeToggle as Button
@onready var run_pause_button = $VBoxContainer/DebugControls/RunPauseButton as Button
@onready var step_button = $VBoxContainer/DebugControls/StepButton as Button
@onready var breakpoint_x_field = $VBoxContainer/DebugControls/BreakpointCoords/BPX as LineEdit
@onready var breakpoint_y_field = $VBoxContainer/DebugControls/BreakpointCoords/BPY as LineEdit
@onready var set_breakpoint_button = $VBoxContainer/DebugControls/SetBreakpointButton as Button
@onready var clear_breakpoints_button = $VBoxContainer/DebugControls/ClearBreakpointsButton as Button

@onready var pc_label = $VBoxContainer/DebugStatus/PCLabel as Label
@onready var registers_label = $VBoxContainer/DebugStatus/RegistersLabel as Label
@onready var stack_label = $VBoxContainer/DebugStatus/StackLabel as Label

var frame_history: Array = []
const MAX_HISTORY_FRAMES = 100
var current_timeline_view_frame: int = -1

var gpu_driver_ref: PXGPUDriver = null # Reference to the main GPU driver (set by PXDisplayNode)

func _ready():
	debug_log_label.text = "Debug Log:"
	pixel_info_label.text = "Pixel Info: N/A"
	hover_info_label.text = "Hover: N/A"
	known_claims_label.text = "Known Claims:"
    pc_label.text = "PC: (N/A)"
    registers_label.text = "R0:0 R1:0 R2:0 R3:0 (SP:0)" # Updated placeholder
    stack_label.text = "Stack: []"
	
	var style_box = StyleBoxFlat.new()
	style_box.bg_color = Color(0, 0, 0, 0.7)
	style_box.set_corner_radius_all(5)
	add_theme_stylebox_override("panel", style_box)

    # NEW: Connect Debug Controls
    debug_mode_toggle_button.button_pressed = false # Start disabled
    debug_mode_toggle_button.pressed.connect(Callable(self, "_on_debug_mode_toggle_pressed"))
    run_pause_button.pressed.connect(Callable(self, "_on_run_pause_button_pressed"))
    step_button.pressed.connect(Callable(self, "_on_step_button_pressed"))
    set_breakpoint_button.pressed.connect(Callable(self, "_on_set_breakpoint_button_pressed"))
    clear_breakpoints_button.pressed.connect(Callable(self, "_on_clear_breakpoints_button_pressed"))
    
    # Initialize toggle button text
    _update_run_pause_button_text(true) # Initially paused if debug mode off


func _process(delta):
    # Get reference once ready
    if gpu_driver_ref == null:
        var px_display_node = get_parent().find_child("PXDisplayNode")
        if px_display_node and px_display_node.gpu_driver:
            gpu_driver_ref = px_display_node.gpu_driver
        else:
            return

    # Update Debug Status Labels
    var debug_state = gpu_driver_ref.get_debug_state()
    pc_label.text = "PC: (%d,%d) Active: %s" % [debug_state.pc_coords.x, debug_state.pc_coords.y, debug_state.pc_active]
    
    var reg_str = "R0:%d R1:%d R2:%d R3:%d (SP_val:%d)" % [ # Added SP_val to clarify SP is a value
        debug_state.registers[0], debug_state.registers[1], 
        debug_state.registers[2], debug_state.registers[3], # R3 is SP value (Y-offset)
        debug_state.registers[3] # Display raw SP register value
    ]
    registers_label.text = reg_str
    
    var stack_str = "Stack: ["
    for i in range(debug_state.stack.size()):
        stack_str += str(debug_state.stack[i]) # Stack elements are ints
        if i < debug_state.stack.size() - 1:
            stack_str += ", "
    stack_str += "]"
    stack_label.text = stack_str

    _update_run_pause_button_text(debug_state.pause_execution) # Keep button text in sync


func log_frame_data(log_entries: Array):
	frame_history.append(log_entries)
	
	if frame_history.size() > MAX_HISTORY_FRAMES:
		frame_history.pop_front()

	update_timeline_visuals()

func show_pixel_info(x: int, y: int, color: Color):
	pixel_info_label.text = "Pixel Info (Right-Click):\nPos: (%d, %d)\nRGB: (%s)\nOpcode ID: %d" % \
							[x, y, color.to_html(false), int(color.r * 255)]

func update_hover_info(x: int, y: int, color: Color):
	hover_info_label.text = "Hover: (%d, %d) RGB: (%s) Opcode ID: %d" % \
							[x, y, color.to_html(false), int(color.r * 255)]

func update_known_claims_display(claims_dict: Dictionary):
	var claims_text = "Known Claims:\n"
	if claims_dict.is_empty():
		claims_text += "  (None yet)"
	else:
		for agent_id in claims_dict:
			var claim = claims_dict[agent_id]
			claims_text += "  Agent %d: (%d,%d)-(%d,%d) Color: %s\n" % [
				agent_id, 
				int(claim["coords"].x), int(claim["coords"].y),
				int(claim["coords"].z), int(claim["coords"].w),
				claim["color"].to_html(false)
			]
	known_claims_label.text = claims_text

# NEW: Debug Control Callbacks
func _on_debug_mode_toggle_pressed():
    if gpu_driver_ref:
        # Pass the button's toggle state directly
        gpu_driver_ref.set_debug_mode_state(debug_mode_toggle_button.button_pressed)

func _on_run_pause_button_pressed():
    if gpu_driver_ref:
        gpu_driver_ref.toggle_pause_execution()

func _on_step_button_pressed():
    if gpu_driver_ref:
        gpu_driver_ref.step_once()

func _on_set_breakpoint_button_pressed():
    if gpu_driver_ref:
        var bp_x_str = breakpoint_x_field.text
        var bp_y_str = breakpoint_y_field.text
        if not bp_x_str.is_empty() and not bp_y_str.is_empty():
            gpu_driver_ref.set_breakpoint(int(bp_x_str), int(bp_y_str))
        else:
            print("DEBUG: Enter X and Y for breakpoint.")

func _on_clear_breakpoints_button_pressed():
    if gpu_driver_ref:
        gpu_driver_ref.clear_all_breakpoints()

func _update_run_pause_button_text(is_paused: bool):
    run_pause_button.text = "RUN" if is_paused else "PAUSE"
    run_pause_button.button_pressed = is_paused # Keep toggle state in sync (if using toggle button)

# Function to be called by PXDisplayNode for PC visual highlight
func get_pc_highlight_coords() -> Vector2i:
    if gpu_driver_ref:
        return gpu_driver_ref.get_debug_state().pc_coords
    return Vector2i(-1, -1)

func is_pc_active_for_highlight() -> bool:
    if gpu_driver_ref:
        var debug_state = gpu_driver_ref.get_debug_state()
        return debug_state.pc_active and debug_state.debug_mode # Only highlight if active and debug mode is on
    return false