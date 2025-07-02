# scripts/PXAgent.gd
extends Node

class_name PXAgent

@export var agent_id: int = 0
@export var agent_color: Color = Color(1, 1, 0, 1) # Yellow
@export var movement_speed: float = 1.0 # Pixels per step
@export var action_chance: float = 0.5 # Chance to perform an action each step (when not goal-seeking)
@export var send_message_chance: float = 0.1 # Chance to send a PXNet message

@export var goal_pixel_color: Color = Color(0.0, 1.0, 0.0, 1.0) # Target color for goal (Green)
@export var goal_position: Vector2 = Vector2(50, 50) # Target pixel position for goal

var gpu_driver: PXGPUDriver 
var pxnet_manager: PXNetManager 

var current_pos: Vector2 
var visited_positions: Dictionary = {}

const MEMORY_RETENTION_TIME = 1.0

const COMMAND_INBOX_START_X = 1
const COMMAND_INBOX_START_Y = 0
const COMMAND_INBOX_WIDTH = 4
const COMMAND_INBOX_HEIGHT = 1

const OCEAN_TERRAIN_COLOR = Color(0, 70, 150)
const LAND_TERRAIN_COLOR = Color(50, 150, 50)
const CONTINENT_EDGE_TERRAIN_COLOR = Color(100, 100, 0)
const SUN_CORE_TERRAIN_COLOR = Color(255, 150, 0)


func _ready():
	randomize()
	current_pos = Vector2(randi() % gpu_driver.canvas_width, randi() % gpu_driver.canvas_height)
	set_process(true)

func _process(delta):
	if not gpu_driver: return
	if not pxnet_manager: return 

	_update_memory(delta)

	_scan_command_inbox() # Process commands first

	# 1. Sense the environment (read current pixel from Opcode layer and Data layer, now Elevation)
	var opcode_pixel_at_pos = gpu_driver.get_opcode_pixel(int(current_pos.x), int(current_pos.y))
	var data_pixel_at_pos = gpu_driver.get_data_pixel(int(current_pos.x), int(current_pos.y))
	var current_terrain_type = _get_terrain_type(data_pixel_at_pos)
	var current_elevation = gpu_driver.get_elevation_pixel(int(current_pos.x), int(current_pos.y)) # NEW: Get elevation

	# print("Agent %d at (%d,%d) on %s terrain, elevation %.2f." % [agent_id, int(current_pos.x), int(current_pos.y), current_terrain_type, current_elevation])


	# 2. Decision Making (Goal-directed vs. Wander, terrain-aware, now elevation-aware)
	var new_x = int(current_pos.x)
	var new_y = int(current_pos.y)

	var reached_goal = (distance(current_pos, goal_position) < movement_speed)

	if reached_goal:
		_perform_goal_action(new_x, new_y)
		_pick_new_random_goal() # Pick new goal after reaching
		
		# Move slightly away from goal to avoid immediate re-trigger
		new_x += randi_range(-1, 1) * int(movement_speed)
		new_y += randi_range(-1, 1) * int(movement_speed)
		
	else:
		_move_towards_goal(new_x, new_y, current_terrain_type, current_elevation) # MODIFIED: Pass current_elevation
		
		if opcode_pixel_at_pos.r > PXOpcodes.PX_NO_OP.r + 0.001:
			_react_to_pixel(new_x, new_y, current_terrain_type, current_elevation) # MODIFIED
		else:
			if randf() < action_chance * 0.2:
				_perform_random_action(new_x, new_y, current_terrain_type, current_elevation) # MODIFIED
	
	if randf() < send_message_chance:
		_send_pxnet_message()

	# 3. Update position (clamp to canvas boundaries)
	current_pos.x = clamp(float(new_x), 0.0, float(gpu_driver.canvas_width - 1))
	current_pos.y = clamp(float(new_y), 0.0, float(gpu_driver.canvas_height - 1))
	
	_add_to_memory(current_pos)

	gpu_driver.inject_pixel_opcode(int(current_pos.x), int(current_pos.y), Color(agent_color.r, agent_color.g, agent_color.b, 0.5))

# --- Helper Functions (Modified for Elevation) ---

func _move_towards_goal(inout_x: int, inout_y: int, terrain_type: String, current_elevation: float): # MODIFIED
	var direction = (goal_position - current_pos).normalized()
	var effective_speed = movement_speed

	if terrain_type == "Ocean":
		effective_speed *= 0.5
	elif terrain_type == "SunCore":
		effective_speed *= 0.1
	elif terrain_type == "Coast":
		effective_speed *= 0.8
	
	# NEW: Adjust speed based on elevation
	effective_speed *= (1.0 - current_elevation * 0.5) # Slower at higher elevations (0.0=full speed, 1.0=half speed)

	var step_vector = direction * effective_speed

	var next_x = int(current_pos.x + step_vector.x)
	var next_y = int(current_pos.y + step_vector.y)

	for i in range(3):
		var candidate_x = next_x + randi_range(-1, 1) * (i * int(effective_speed))
		var candidate_y = next_y + randi_range(-1, 1) * (i * int(effective_speed))
		
		candidate_x = clamp(candidate_x, 0, gpu_driver.canvas_width - 1)
		candidate_y = clamp(candidate_y, 0, gpu_driver.canvas_height - 1)

		if not _is_position_remembered(Vector2(candidate_x, candidate_y)):
			inout_x = candidate_x
			inout_y = candidate_y
			return
	
	inout_x = next_x
	inout_y = next_y

func _perform_goal_action(x: int, y: int):
	# ... (no change to goal action itself, but context of decision is elevation-aware)
	var rect_width = 3
	var rect_height = 3
	var rect_opcode = Color(PXOpcodes.PX_DRAW_RECT_ID, float(rect_width)/255.0, float(rect_height)/255.0, 1.0)
	
	rect_opcode.g = goal_pixel_color.r
	rect_opcode.b = goal_pixel_color.g
	rect_opcode.a = goal_pixel_color.b

	gpu_driver.set_persistent_pixel_opcode(x, y, rect_opcode)
	gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_PIXEL, goal_pixel_color.r, goal_pixel_color.g, 1.0))
	print("Agent %d reached goal at (%d,%d) and performed action!" % [agent_id, x, y])

func _react_to_pixel(x: int, y: int, terrain_type: String, current_elevation: float): # MODIFIED
	var char_exclam_opcode = Color(PXOpcodes.PX_DRAW_CHAR, 33.0/255.0, agent_color.b, 1.0)
	gpu_driver.set_persistent_pixel_opcode(x, y, char_exclam_opcode)
	print("Agent %d at (%d,%d) reacted to existing pixel on %s terrain, elevation %.2f!" % [agent_id, x, y, terrain_type, current_elevation])

func _perform_random_action(x: int, y: int, terrain_type: String, current_elevation: float): # MODIFIED
	if terrain_type == "Land":
		# On land, maybe build more complex structure at higher elevations
		if current_elevation > 0.7: # High elevation building
			gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_RECT_ID, 5.0/255.0, 5.0/255.0, 0.7, 1.0)) # A tower
			print("Agent %d at (%d,%d) built a tower on %s (high elevation)." % [agent_id, x, y, terrain_type])
		else: # Normal land building
			gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_PIXEL, 0.5, 0.5, 0.5, 1.0)) # Gray pixel
			print("Agent %d at (%d,%d) built something on %s." % [agent_id, x, y, terrain_type])
	elif terrain_type == "Ocean":
		gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_PIXEL, 0.0, 0.0, 0.8, 1.0))
		print("Agent %d at (%d,%d) deployed something on %s." % [agent_id, x, y, terrain_type])
	elif terrain_type == "SunCore":
		# Agents might draw fiery patterns in Sun Core
		gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_PIXEL, randf(), 0.0, 0.0, 1.0)) # Reddish pixel
		print("Agent %d at (%d,%d) emitting energy on %s." % [agent_id, x, y, terrain_type])
	else:
		if randf() < 0.5:
			gpu_driver.set_persistent_pixel_opcode(x, y, Color(PXOpcodes.PX_DRAW_PIXEL, agent_color.g, agent_color.b, 1.0))
			print("Agent %d at (%d,%d) drew a pixel." % [agent_id, x, y])
		else:
			var char_to_draw = ord(str(agent_id)[0]) if agent_id >= 0 && agent_id <= 9 else ord('?')
			var char_opcode = Color(PXOpcodes.PX_DRAW_CHAR, float(char_to_draw)/255.0, agent_color.g, 1.0)
			gpu_driver.set_persistent_pixel_opcode(x, y, char_opcode)
			print("Agent %d at (%d,%d) drew char '%c'." % [agent_id, x, y, char_to_draw])

func _send_pxnet_message():
	var message_type = PXOpcodes.PXNET_MESSAGE_TYPE_ECHO
	var message_data_x = int(current_pos.x) % pxnet_manager.net_bus_width
	var message_data_y = int(current_pos.y) % pxnet_manager.net_bus_height
	
	var pxnet_message_color = Color(message_type, float(message_data_x)/255.0, float(message_data_y)/255.0, float(agent_id)/255.0)
	pxnet_manager.send_pixel_message(0, 0, pxnet_message_color)

func _pick_new_random_goal():
	goal_position = Vector2(randi() % gpu_driver.canvas_width, randi() % gpu_driver.canvas_height)
	goal_pixel_color = Color(randf(), randf(), randf(), 1.0)
	print("Agent %d picked new goal: Pos (%d,%d), Color %s" % [agent_id, int(goal_position.x), int(goal_position.y), goal_pixel_color.to_html(false)])