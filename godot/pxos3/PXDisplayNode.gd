# scripts/PXDisplayNode.gd
extends Control

class_name PXDisplayNode

@export var canvas_width: int = 64
@export var canvas_height: int = 64
@export var pixel_size: int = 8

@onready var gpu_driver: PXGPUDriver = $PXGPUDriver
@onready var texture_rect_display: TextureRect = $PXGPUDriver/Texture_Rect_Display
@onready var app_builder: PXAppBuilder = $AppBuilderPanel
@onready var pxnet_manager: PXNetManager = $"../PXNetManager"
@onready var pxnet_claim_manager: PXNetClaimManager = $"../PXNetClaimManager"

@export var planet_3d_scene_res: PackedScene

var debugger: Node # Set to PXDebugger instance in _ready()
var px_agent: PXAgent 

var show_grid: bool = false
var planet_3d_instance: Node3D = null
var show_3d_view: bool = false

func _ready():
	debugger = get_parent().find_child("PXDebugger") # Ensure this gets the PXDebugger instance
	if not debugger:
		print("Warning: PXDebugger node not found as a sibling.")
		return
	
	set_process_input(true)
	set_process(true)

	px_agent = PXAgent.new()
	px_agent.agent_id = 1
	px_agent.agent_color = Color(1.0, 1.0, 0.0, 1.0)
	px_agent.gpu_driver = gpu_driver
	px_agent.pxnet_manager = pxnet_manager
	add_child(px_agent)

	if app_builder:
		app_builder.gpu_driver = gpu_driver
		app_builder.parent_display_node = self
		app_builder.display_node = self
		app_builder.pxnet_claim_manager = pxnet_claim_manager

	if planet_3d_scene_res:
		planet_3d_instance = planet_3d_scene_res.instantiate()
		add_child(planet_3d_instance)
		
		planet_3d_instance.position = Vector3(100, 0, -200)
		planet_3d_instance.visible = show_3d_view
		
		gpu_driver.set_planet_3d_instance(planet_3d_instance)
	else:
		push_error("PXDisplayNode: planet_3d_scene_res is not assigned in the Inspector!")

func _input(event):
	if event is InputEventKey:
		if event.is_pressed():
			var key_code_val = event.unicode.ord() if event.unicode.is_ascii() and event.unicode.length() == 1 else 0
			if key_code_val > 0:
				gpu_driver.set_persistent_data_pixel(gpu_driver.KEYBOARD_BUFFER_X, gpu_driver.KEYBOARD_BUFFER_Y, gpu_driver._int_to_color(key_code_val))
				print("Keyboard input: '%s' (Code: %d) written to buffer." % [event.unicode, key_code_val])
			else:
				gpu_driver.set_persistent_data_pixel(gpu_driver.KEYBOARD_BUFFER_X, gpu_driver.KEYBOARD_BUFFER_Y, Color(0,0,0,1))
		elif event.is_released():
			gpu_driver.set_persistent_data_pixel(gpu_driver.KEYBOARD_BUFFER_X, gpu_driver.KEYBOARD_BUFFER_Y, Color(0,0,0,1))
		
		pass 
	
	var rect = Rect2(texture_rect_display.global_position, texture_rect_display.size)
	if not rect.has_point(event.position) and not (event is InputEventKey):
		return

	if event.is_action_pressed("ui_graph_next"):
		show_3d_view = not show_3d_view
		texture_rect_display.visible = not show_3d_view
		if planet_3d_instance:
			planet_3d_instance.visible = show_3d_view
		print("Toggled 3D view: %s" % show_3d_view)
		get_viewport().set_input_as_handled()
		return

	if not show_3d_view:
		if event is InputEventMouseButton:
			var local_pos_on_canvas = (event.position - texture_rect_display.global_position) / pixel_size
			var px_x = int(local_pos_on_canvas.x)
			var px_y = int(local_pos_on_canvas.y)
				
			if px_x >= 0 and px_x < canvas_width and px_y >= 0 and px_y < canvas_height:
				if event.is_pressed():
					if event.button_index == MOUSE_BUTTON_RIGHT:
						var pixel_color = gpu_driver.get_opcode_pixel(px_x, px_y)
						debugger.show_pixel_info(px_x, px_y, pixel_color)
						print("Data at (%d,%d): %s" % [px_x, px_y, gpu_driver.get_data_pixel(px_x, px_y).to_html(false)])
						print("Elevation: %.2f" % gpu_driver.get_elevation_pixel(px_x, px_y))
						get_viewport().set_input_as_handled()
					elif event.button_index == MOUSE_BUTTON_LEFT:
						var paint_opcode_color = app_builder.get_paint_opcode_color(px_x, px_y)
						gpu_driver.set_persistent_pixel_opcode(px_x, px_y, paint_opcode_color)
						print("Painted opcode at (%d,%d): %s" % [px_x, px_y, paint_opcode_color.to_html(false)])
						get_viewport().set_input_as_handled()
				if event.is_action_pressed("click") and event.button_index == MOUSE_BUTTON_LEFT:
					var paint_opcode_color = app_builder.get_paint_opcode_color(px_x, px_y)
					gpu_driver.set_persistent_pixel_opcode(px_x, px_y, paint_opcode_color)
					get_viewport().set_input_as_handled()

		elif event is InputEventMouseMotion:
			var local_pos_on_canvas = (event.position - texture_rect_display.global_position) / pixel_size
			var px_x = int(local_pos_on_canvas.x)
			var px_y = int(local_pos_on_canvas.y)
			
			if px_x >= 0 and px_x < canvas_width and px_y >= 0 and px_y < canvas_height:
				var pixel_color = gpu_driver.get_opcode_pixel(px_x, px_y)
				debugger.update_hover_info(px_x, px_y, pixel_color)
				
				if event.button_mask & MOUSE_BUTTON_MASK_LEFT:
					var paint_opcode_color = app_builder.get_paint_opcode_color(px_x, px_y)
					gpu_driver.set_persistent_pixel_opcode(px_x, px_y, paint_opcode_color)
					get_viewport().set_input_as_handled()
	
	if event.is_action_pressed("ui_accept"):
		var rand_x = randi() % canvas_width
		var rand_y = randi() % canvas_height
		var random_color = Color(randf(), randf(), randf(), 1.0)
		var injected_opcode = Color(1.0/255.0, random_color.g, random_color.b, 1.0) 
		gpu_driver.inject_pixel_opcode(rand_x, rand_y, injected_opcode)
		print("Injected (transient) PX_DRAW_PIXEL at (%d, %d)." % [rand_x, rand_y, ])

	if event.is_action_pressed("ui_text_submit"):
		var rand_x = randi() % (canvas_width - int(PXOpcodes.FONT_CHAR_WIDTH))
		var rand_y = randi() % (canvas_height - int(PXOpcodes.FONT_CHAR_HEIGHT))
		var char_g_opcode = Color(2.0/255.0, 71.0/255.0, 0.0, 1.0)
		gpu_driver.inject_pixel_opcode(rand_x, rand_y, char_g_opcode)
		print("Injected (transient) PX_DRAW_CHAR 'G' at (%d, %d)." % [rand_x, rand_y, ])

	if event.is_action_pressed("ui_select"):
		var start_x = randi() % canvas_width
		var start_y = randi() % canvas_height
		var dx = randi() % (int(PXOpcodes.MAX_LINE_OFFSET) + 1)
		var dy = randi() % (int(PXOpcodes.MAX_LINE_OFFSET) + 1)
		start_x = min(start_x, canvas_width - int(PXOpcodes.MAX_LINE_OFFSET) - 1)
		start_y = min(start_y, canvas_height - int(PXOpcodes.MAX_LINE_OFFSET) - 1)
		var line_opcode = Color(3.0/255.0, dx / 255.0, dy / 255.0, 1.0)
		gpu_driver.inject_pixel_opcode(start_x, start_y, line_opcode)
		print("Injected (transient) PX_DRAW_LINE_SEGMENT from (%d,%d) to (%d,%d)." % [start_x, start_y, start_x + dx, start_y + dy, ])

	if event.is_action_pressed("ui_page_up"):
		var start_x = randi() % canvas_width
		var start_y = randi() % canvas_height
		var dx = randi() % (int(PXOpcodes.MAX_LINE_OFFSET) + 1)
		var dy = randi() % (int(PXOpcodes.MAX_LINE_OFFSET) + 1)
		start_x = min(start_x, canvas_width - int(PXOpcodes.MAX_LINE_OFFSET) - 1)
		start_y = min(start_y, canvas_height - int(PXOpcodes.MAX_LINE_OFFSET) - 1)
		var line_opcode = Color(3.0/255.0, dx / 255.0, dy / 255.0, 1.0)
		gpu_driver.set_persistent_pixel_opcode(start_x, start_y, line_opcode)
		print("Persistently set PX_DRAW_LINE_SEGMENT from (%d,%d) to (%d,%d)." % [start_x, start_y, start_x + dx, start_y + dy, ])

	if event.is_action_pressed("ui_left"):
		var start_x = randi() % canvas_width
		var start_y = randi() % canvas_height
		var width = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) + 1)
		var height = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) + 1)
		start_x = min(start_x, canvas_width - int(PXOpcodes.MAX_RECT_DIMENSION) - 1)
		start_y = min(start_y, canvas_height - int(PXOpcodes.MAX_RECT_DIMENSION) - 1)
		var rect_opcode = Color(4.0/255.0, width / 255.0, height / 255.0, 1.0)
		gpu_driver.inject_pixel_opcode(start_x, start_y, rect_opcode)
		print("Injected (transient) PX_DRAW_RECT at (%d,%d) size (%d,%d)." % [start_x, start_y, width, height, ])

	if event.is_action_pressed("ui_right"):
		var start_x = randi() % canvas_width
		var start_y = randi() % canvas_height
		var width = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) + 1)
		var height = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) + 1)
		start_x = min(start_x, canvas_width - int(PXOpcodes.MAX_RECT_DIMENSION) - 1)
		start_y = min(start_y, canvas_height - int(PXOpcodes.MAX_RECT_DIMENSION) - 1)
		var rect_opcode = Color(4.0/255.0, width / 255.0, height / 255.0, 1.0)
		gpu_driver.set_persistent_pixel_opcode(start_x, start_y, rect_opcode)
		print("Persistently set PX_DRAW_RECT at (%d,%d) size (%d,%d)." % [start_x, start_y, width, height, ])

	if event.is_action_pressed("ui_text_caret_right"):
		var dest_x = randi() % canvas_width
		var dest_y = randi() % canvas_height
		var src_offset_x = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) * 2 + 1) - int(PXOpcodes.MAX_RECT_DIMENSION)
		var src_offset_y = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) * 2 + 1) - int(PXOpcodes.MAX_RECT_DIMENSION)
		dest_x = min(dest_x, canvas_width - int(PXOpcodes.COPY_REGION_WIDTH) - 1)
		dest_y = min(dest_y, canvas_height - int(PXOpcodes.COPY_REGION_HEIGHT) - 1)
		var encoded_src_offset_x = (float(src_offset_x) + float(PXOpcodes.MAX_RECT_DIMENSION)) / (2.0 * float(PXOpcodes.MAX_RECT_DIMENSION)) * 255.0
		var encoded_src_offset_y = (float(src_offset_y) + float(PXOpcodes.MAX_RECT_DIMENSION)) / (2.0 * float(PXOpcodes.MAX_RECT_DIMENSION)) * 255.0
		var copy_opcode = Color(5.0/255.0, encoded_src_offset_x / 255.0, encoded_src_offset_y / 255.0, 1.0)
		gpu_driver.inject_pixel_opcode(dest_x, dest_y, copy_opcode)
		print("Injected (transient) PX_COPY_REGION at dest (%d,%d) from offset (%d,%d)." % [dest_x, dest_y, src_offset_x, src_offset_y, ])

	if event.is_action_pressed("ui_text_caret_left"):
		var dest_x = randi() % canvas_width
		var dest_y = randi() % canvas_height
		var src_offset_x = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) * 2 + 1) - int(PXOpcodes.MAX_RECT_DIMENSION)
		var src_offset_y = randi() % (int(PXOpcodes.MAX_RECT_DIMENSION) * 2 + 1) - int(PXOpcodes.MAX_RECT_DIMENSION)
		dest_x = min(dest_x, canvas_width - int(PXOpcodes.COPY_REGION_WIDTH) - 1)
		dest_y = min(dest_y, canvas_height - int(PXOpcodes.COPY_REGION_HEIGHT) - 1)
		var encoded_src_offset_x = (float(src_offset_x) + float(PXOpcodes.MAX_RECT_DIMENSION)) / (2.0 * float(PXOpcodes.MAX_RECT_DIMENSION)) * 255.0
		var encoded_src_offset_y = (float(src_offset_y) + float(PXOpcodes.MAX_RECT_DIMENSION)) / (2.0 * float(PXOpcodes.MAX_RECT_DIMENSION)) * 255.0
		var copy_opcode = Color(5.0/255.0, encoded_src_offset_x / 255.0, encoded_src_offset_y / 255.0, 1.0)
		gpu_driver.set_persistent_pixel_opcode(dest_x, dest_y, copy_opcode)
		print("Persistently set PX_COPY_REGION at dest (%d,%d) from offset (%d,%d)." % [dest_x, dest_y, src_offset_x, src_offset_y, ])

	if event.is_action_pressed("ui_down"):
		var rand_x = randi() % canvas_width
		var rand_y = randi() % canvas_height
		var read_data_opcode = Color(6.0/255.0, 0.0, 0.0, 1.0)
		gpu_driver.inject_pixel_opcode(rand_x, rand_y, read_data_opcode)
		print("Injected (transient) PX_READ_DATA_TO_COLOR at (%d, %d)." % [rand_x, rand_y, ])

	if event.is_action_pressed("ui_up"):
		var rand_x = randi() % canvas_width
		var rand_y = randi() % canvas_height
		var random_color = Color(randf(), randf(), randf(), 1.0)
		gpu_driver.set_persistent_data_pixel(rand_x, rand_y, random_color)
		print("Persistently set data pixel at (%d, %d) with %s." % [rand_x, rand_y, random_color.to_html(false), ])

	if event.is_action_pressed("ui_home"):
		gpu_driver.pc_active = not gpu_driver.pc_active
		print("PC Active: %s" % str(gpu_driver.pc_active))
		if gpu_driver.pc_active:
			gpu_driver.set_persistent_pixel_opcode(gpu_driver.PC_PIXEL_X, gpu_driver.PC_PIXEL_Y,
													Color(PXOpcodes.PX_BOOT_CONTROL_ID, 1.0/255.0, 1.0/255.0, 1.0))
			print("PC reset to (1,1) and activated.")

	if event.is_action_pressed("ui_page_down"):
		gpu_driver.load_qr_boot_block("res://boot_blocks/qr_boot_map_package.png")
		get_viewport().set_input_as_handled()
		print("Attempting to load QR Boot Block.")


func _process(delta):
	queue_redraw()

func toggle_grid_overlay(enable: bool):
	show_grid = enable
	queue_redraw()

func _draw():
	if show_grid and not show_3d_view:
		var line_color = Color(0.5, 0.5, 0.5, 0.5)
		
		var display_rect_global_pos = texture_rect_display.global_position
		var display_rect_size = texture_rect_display.get_rect().size

		for i in range(canvas_width + 1):
			var x = display_rect_global_pos.x + i * pixel_size
			draw_line(Vector2(x, display_rect_global_pos.y), Vector2(x, display_rect_global_pos.y + display_rect_size.y), line_color)
		
		for i in range(0, canvas_height + 1, 1):
			var y = display_rect_global_pos.y + i * pixel_size
			draw_line(Vector2(display_rect_global_pos.x, y), Vector2(display_rect_global_pos.x + display_rect_size.x, y), line_color)

	# NEW: Draw PC highlight
	if debugger and debugger.is_pc_active_for_highlight() and not show_3d_view:
		var pc_coords = debugger.get_pc_highlight_coords()
		if pc_coords.x != -1: # Valid coordinates
			var highlight_rect = Rect2(texture_rect_display.global_position.x + pc_coords.x * pixel_size,
									   texture_rect_display.global_position.y + pc_coords.y * pixel_size,
									   pixel_size, pixel_size)
			draw_rect(highlight_rect, Color(1, 0, 0, 0.5), true) # Red, semi-transparent
			draw_rect(highlight_rect, Color(1, 0, 0, 1), false, 2.0) # Red border

func load_universe_map(boot_pixel_rgb: Color, external_elevation_path: String = ""):
	gpu_driver.load_map_from_boot_pixel(boot_pixel_rgb, external_elevation_path)

func set_pixel_opcode(x: int, y: int, color: Color):
	gpu_driver.set_persistent_pixel_opcode(x, y, color)

func get_pixel_opcode(x: int, y: int) -> Color:
	return gpu_driver.get_pixel_data_from_gpu(x, y)
