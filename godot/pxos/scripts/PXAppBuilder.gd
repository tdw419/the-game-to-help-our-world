# scripts/PXAppBuilder.gd
extends Control

class_name PXAppBuilder

@onready var gpu_driver: PXGPUDriver
@onready var parent_display_node: PXDisplayNode
@onready var opcode_buttons_vbox = $VBoxContainer/OpcodeButtons as VBoxContainer
@onready var color_picker_button = $VBoxContainer/ColorPickerButton as ColorPickerButton
@onready var grid_toggle_checkbox = $VBoxContainer/GridToggle as CheckBox

@onready var map_boot_color_picker_button = $VBoxContainer/MapBootSection/MapBootColorPickerButton as ColorPickerButton
@onready var boot_map_button = $VBoxContainer/MapBootSection/BootMapButton as Button
@onready var external_elevation_path_line_edit = $VBoxContainer/MapBootSection/ExternalElevationPath as LineEdit

@onready var agent_command_buttons_vbox = $VBoxContainer/AgentCommandSection/AgentCommandButtons as VBoxContainer
@onready var agent_command_target_pos_line_edit_x = $VBoxContainer/AgentCommandSection/AgentCommandTargetPos/TargetX as LineEdit
@onready var agent_command_target_pos_line_edit_y = $VBoxContainer/AgentCommandSection/AgentCommandTargetPos/TargetY as LineEdit
@onready var agent_command_paint_button = $VBoxContainer/AgentCommandSection/PaintAgentCommandButton as Button
@onready var agent_command_target_color_picker_button = $VBoxContainer/AgentCommandSection/AgentCommandTargetColor/AgentCommandTargetColorPickerButton as ColorPickerButton

@onready var toggle_3d_view_button = $VBoxContainer/ViewModeSection/Toggle3DViewButton as Button

@export var pxseed_devtool_scene: PackedScene
var pxseed_devtool_instance: PXSeedDevtool = null

var pxnet_claim_manager: PXNetClaimManager = null

@onready var generate_claimed_map_button = $VBoxContainer/PXNetClaimSection/GenerateClaimedMapButton as Button
@onready var claim_name_line_edit = $VBoxContainer/PXNetClaimSection/ClaimDetails/ClaimName as LineEdit
@onready var claim_x1_line_edit = $VBoxContainer/PXNetClaimSection/ClaimCoords/ClaimX1 as LineEdit
@onready var claim_y1_line_edit = $VBoxContainer/PXNetClaimSection/ClaimCoords/ClaimY1 as LineEdit
@onready var claim_x2_line_edit = $VBoxContainer/PXNetClaimSection/ClaimCoords/ClaimX2 as LineEdit
@onready var claim_y2_line_edit = $VBoxContainer/PXNetClaimSection/ClaimCoords/ClaimY2 as LineEdit
@onready var claim_color_picker_button = $VBoxContainer/PXNetClaimSection/ClaimColor/ClaimColorPickerButton as ColorPickerButton
@onready var claim_icon_char_line_edit = $VBoxContainer/PXNetClaimSection/ClaimIcon/ClaimIconChar as LineEdit

# NEW: Direct Territory Claim UI elements
@onready var direct_claim_x1_line_edit = $VBoxContainer/DirectClaimSection/DirectClaimCoords/X1 as LineEdit
@onready var direct_claim_y1_line_edit = $VBoxContainer/DirectClaimSection/DirectClaimCoords/Y1 as LineEdit
@onready var direct_claim_x2_line_edit = $VBoxContainer/DirectClaimSection/DirectClaimCoords/X2 as LineEdit
@onready var direct_claim_y2_line_edit = $VBoxContainer/DirectClaimSection/DirectClaimCoords/Y2 as LineEdit
@onready var direct_claim_color_picker_button = $VBoxContainer/DirectClaimSection/DirectClaimColor/DirectClaimColorPickerButton as ColorPickerButton
@onready var perform_direct_claim_button = $VBoxContainer/DirectClaimSection/PerformDirectClaimButton as Button


var current_selected_opcode_id: float = PXOpcodes.PX_DRAW_PIXEL.r
var current_selected_color: Color = Color.WHITE

var opcode_button_map: Dictionary = {}
var agent_command_opcode_map: Dictionary = {}


func _ready():
	color_picker_button.color = current_selected_color
	color_picker_button.pressed.connect(Callable(self, "_on_color_picker_button_pressed"))
	
	grid_toggle_checkbox.button_pressed.connect(Callable(self, "_on_grid_toggle_toggled"))
	
	_create_opcode_buttons()
	_select_opcode_button(opcode_button_map[PXOpcodes.PX_DRAW_PIXEL.r])

	# Initialize Map Booting UI
	map_boot_color_picker_button.color = Color(200.0/255.0, 50.0/255.0, 0.0/255.0, 1.0)
	map_boot_color_picker_button.pressed.connect(Callable(self, "_on_map_boot_color_picker_button_pressed"))
	boot_map_button.pressed.connect(Callable(self, "_on_boot_map_button_pressed"))

	# Initialize Agent Command UI
	_create_agent_command_buttons()
	agent_command_paint_button.pressed.connect(Callable(self, "_on_paint_agent_command_button_pressed"))
	agent_command_target_color_picker_button.color = Color.RED
	agent_command_target_color_picker_button.pressed.connect(Callable(self, "_on_agent_command_target_color_picker_button_pressed"))

	# Initialize 3D View Toggle
	toggle_3d_view_button.pressed.connect(Callable(self, "_on_toggle_3d_view_button_pressed"))

    # Instantiate PXSeed Devtool
    if pxseed_devtool_scene:
        pxseed_devtool_instance = pxseed_devtool_scene.instantiate()
        $VBoxContainer.add_child(pxseed_devtool_instance)
        pxseed_devtool_instance.gpu_driver = gpu_driver

    # Connect PXNet Claim UI signals
    generate_claimed_map_button.pressed.connect(Callable(self, "_on_generate_claimed_map_button_pressed"))
    claim_color_picker_button.pressed.connect(Callable(self, "_on_claim_color_picker_button_pressed"))
    claim_color_picker_button.color = Color.WHITE

    # NEW: Connect Direct Claim UI signals
    perform_direct_claim_button.pressed.connect(Callable(self, "_on_perform_direct_claim_button_pressed"))
    direct_claim_color_picker_button.pressed.connect(Callable(self, "_on_direct_claim_color_picker_button_pressed"))
    direct_claim_color_picker_button.color = Color(0, 1, 1, 1) # Default cyan for direct claims


# ... (rest of existing helper functions and callbacks) ...

# NEW: Callback for Perform Direct Claim button
func _on_perform_direct_claim_button_pressed():
    var x1_str = direct_claim_x1_line_edit.text
    var y1_str = direct_claim_y1_line_edit.text
    var x2_str = direct_claim_x2_line_edit.text
    var y2_str = direct_claim_y2_line_edit.text

    if x1_str.is_empty() or y1_str.is_empty() or x2_str.is_empty() or y2_str.is_empty():
        print("Error: Direct claim coordinates must be set.")
        return
    
    var x1 = int(x1_str)
    var y1 = int(y1_str)
    var x2 = int(x2_str)
    var y2 = int(y2_str)
    var claim_color = direct_claim_color_picker_button.color

    _draw_direct_territory_claim(x1, y1, x2, y2, claim_color)

func _on_direct_claim_color_picker_button_pressed():
    direct_claim_color_picker_button.get_picker().color_changed.connect(Callable(self, "_on_direct_claim_color_picker_changed"))

func _on_direct_claim_color_picker_changed(color: Color):
    direct_claim_color_picker_button.color = color
    print("Selected Direct Claim Color: %s" % color.to_html(false))

# NEW: Function to draw the direct territory claim
func _draw_direct_territory_claim(x1: int, y1: int, x2: int, y2: int, color: Color):
    # Clamp coordinates to canvas boundaries
    x1 = clamp(x1, 0, gpu_driver.canvas_width - 1)
    y1 = clamp(y1, 0, gpu_driver.canvas_height - 1)
    x2 = clamp(x2, 0, gpu_driver.canvas_width - 1)
    y2 = clamp(y2, 0, gpu_driver.canvas_height - 1)

    # Ensure coordinates are min <= max
    var draw_x1 = min(x1, x2)
    var draw_y1 = min(y1, y2)
    var draw_x2 = max(x1, x2)
    var draw_y2 = max(y1, y2)

    # Use set_persistent_data_pixel to draw directly onto the data layer
    # This emulates the PIL draw.rectangle(fill=color) logic
    for y_coord in range(draw_y1, draw_y2 + 1):
        for x_coord in range(draw_x1, draw_x2 + 1):
            gpu_driver.set_persistent_data_pixel(x_coord, y_coord, color)
    
    print("Performed direct territory claim at (%d,%d)-(%d,%d) with color %s" % [draw_x1, draw_y1, draw_x2, draw_y2, color.to_html(false)])