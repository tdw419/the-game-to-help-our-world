# scripts/PXGPUDriver.gd
extends Node2D

class_name PXGPUDriver

@export var canvas_width: int = 64
@export var canvas_height: int = 64
@export var pixel_size: int = 8

@onready var viewport_opcode_a: SubViewport = $Viewport_OpcodeA
@onready var viewport_opcode_b: SubViewport = $Viewport_OpcodeB
@onready var viewport_data_a: SubViewport = $Viewport_DataA
@onready var viewport_data_b: SubViewport = $Viewport_DataB
@onready var viewport_injection: SubViewport = $Viewport_Injection
@onready var viewport_pxnet: SubViewport = $Viewport_PXNet
@onready var texture_rect_display: TextureRect = $Texture_Rect_Display

var current_opcode_read_viewport: SubViewport
var current_opcode_write_viewport: SubViewport

var current_data_read_viewport: SubViewport
var current_data_write_viewport: SubViewport

var opcode_a_initial_texture: ImageTexture
var opcode_b_initial_texture: ImageTexture

var data_a_initial_texture: ImageTexture
var data_b_initial_texture: ImageTexture

var injection_image: Image 
var injection_texture: ImageTexture 

var elevation_layer: Image = null

const PC_PIXEL_X = 0
const PC_PIXEL_Y = 0
var pc_active: bool = true

var qr_boot_image: Image = null
var qr_boot_texture: ImageTexture = null

var planet_3d_instance: Node3D = null

@onready var pxnet_claim_manager: PXNetClaimManager = $"../PXNetClaimManager"
@onready var px_bootloader: PXBootloader = $"../PXBootloader" # NEW: Reference to the Bootloader

# Phase 5.1 - Register Locations (within the data_layer)
const REGISTER_LAYER_Y_OFFSET = 0
const REG_R0_X = 1
const REG_R1_X = 2
const REG_R2_X = 3
const REG_R3_X = 4

# Phase 5.2 - Stack Memory Layout (within the data_layer)
const STACK_BASE_X = 5
const STACK_BASE_Y = 0
const STACK_MAX_SIZE = 10

# Phase 5.3 - I/O Device Locations (within the data_layer)
const CONSOLE_START_X = 0
const CONSOLE_START_Y = STACK_BASE_Y + STACK_MAX_SIZE + 1
const CONSOLE_WIDTH = 10
const CONSOLE_HEIGHT = 5

const KEYBOARD_BUFFER_X = 0
const KEYBOARD_BUFFER_Y = STACK_BASE_Y + STACK_MAX_SIZE

var font_image: Image

# Phase 5.5 - Debugging Variables
var debug_mode := false
var pause_execution := false
var single_step_ready := false
var breakpoints: Array[Vector2i] = []
var current_pc_coords: Vector2i = Vector2i(PC_PIXEL_X, PC_PIXEL_Y)

func _get_register_coords(reg_id: float) -> Vector2i:
    match reg_id:
        PXOpcodes.REG_R0_ID: return Vector2i(REG_R0_X, REGISTER_LAYER_Y_OFFSET)
        PXOpcodes.REG_R1_ID: return Vector2i(REG_R1_X, REGISTER_LAYER_Y_OFFSET)
        PXOpcodes.REG_R2_ID: return Vector2i(REG_R2_X, REGISTER_LAYER_Y_OFFSET)
        PXOpcodes.REG_R3_ID: return Vector2i(REG_R3_X, REGISTER_LAYER_Y_OFFSET)
    return Vector2i(-1, -1)

func _color_to_int(color: Color) -> int:
    return (int(round(color.r * 255.0)) << 16) | \
           (int(round(color.g * 255.0)) << 8) | \
           (int(round(color.b * 255.0)))

func _int_to_color(value: int) -> Color:
    var r = float((value >> 16) & 0xFF) / 255.0
    var g = float((value >> 8) & 0xFF) / 255.0
    var b = float(value & 0xFF) / 255.0
    return Color(r, g, b, 1.0)

func _push_stack(value: int):
    var sp_coords = _get_register_coords(PXOpcodes.REG_R3_ID)
    var current_sp_value = _color_to_int(get_data_pixel(sp_coords.x, sp_coords.y))

    if current_sp_value >= STACK_BASE_Y + STACK_MAX_SIZE -1:
        print("STACK OVERFLOW!")
        pc_active = false
        return

    set_persistent_data_pixel(STACK_BASE_X, current_sp_value + 1, _int_to_color(value))
    
    set_persistent_data_pixel(sp_coords.x, sp_coords.y, _int_to_color(current_sp_value + 1))
    print("STACK: PUSHed %d to Y=%d" % [value, current_sp_value + 1])

func _pop_stack() -> int:
    var sp_coords = _get_register_coords(PXOpcodes.REG_R3_ID)
    var current_sp_value = _color_to_int(get_data_pixel(sp_coords.x, sp_coords.y))

    if current_sp_value <= STACK_BASE_Y:
        print("STACK UNDERFLOW!")
        pc_active = false
        return 0

    set_persistent_data_pixel(sp_coords.x, sp_coords.y, _int_to_color(current_sp_value - 1))
    
    var popped_value_color = get_data_pixel(STACK_BASE_X, current_sp_value)
    var popped_value = _color_to_int(popped_value_color)
    
    set_persistent_data_pixel(STACK_BASE_X, current_sp_value, Color(0,0,0,1))
    print("STACK: POPped %d from Y=%d" % [popped_value, current_sp_value])
    return popped_value

func _draw_char_to_console(char_code_int: int, console_x: int, console_y: int, color: Color):
    var char_index = char_code_int
    var char_color = color

    var px_x_start = CONSOLE_START_X + console_x * int(PXOpcodes.FONT_CHAR_WIDTH)
    var px_y_start = CONSOLE_START_Y + console_y * int(PXOpcodes.FONT_CHAR_HEIGHT)

    if font_image == null:
        push_error("Font image not loaded for console output!")
        return
    
    if console_x >= CONSOLE_WIDTH or console_y >= CONSOLE_HEIGHT:
        print("Console: Tried to draw char '%c' out of bounds at (%d,%d)" % [char(char_code_int), console_x, console_y])
        return

    var data_img_a = data_a_initial_texture.get_image()
    var data_img_b = data_b_initial_texture.get_image()

    data_img_a.lock()
    data_img_b.lock()

    PXOpcodes.draw_char_on_image(data_img_a, font_image, px_x_start, px_y_start, char_index, char_color)
    PXOpcodes.draw_char_on_image(data_img_b, font_image, px_x_start, px_y_start, char_index, char_color)
    
    data_img_a.unlock()
    data_img_b.unlock()

    data_a_initial_texture.update(data_img_a)
    data_b_initial_texture.update(data_img_b)
    
func _read_keyboard_buffer() -> int:
    var key_pixel = get_data_pixel(KEYBOARD_BUFFER_X, KEYBOARD_BUFFER_Y)
    var key_code = _color_to_int(key_pixel)
    
    set_persistent_data_pixel(KEYBOARD_BUFFER_X, KEYBOARD_BUFFER_Y, Color(0,0,0,1))
    
    return key_code


func _ready():
    var font_texture_res = preload("res://resources/font_5x5.png") as Texture2D
    if font_texture_res:
        font_image = font_texture_res.get_image()
    else:
        push_error("Font image 'res://resources/font_5x5.png' not found for console output!")

	# --- Initialize Registers ---
    set_persistent_data_pixel(REG_R0_X, REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    set_persistent_data_pixel(REG_R1_X, REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    set_persistent_data_pixel(REG_R2_X, REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    set_persistent_data_pixel(REG_R3_X, REGISTER_LAYER_Y_OFFSET, _int_to_color(STACK_BASE_Y)) 

    # --- Clear Stack Memory Region ---
    for y in range(STACK_BASE_Y, STACK_BASE_Y + STACK_MAX_SIZE):
        set_persistent_data_pixel(STACK_BASE_X, y, Color(0,0,0,1))

    # --- Clear Console and Keyboard Buffer Regions ---
    for y in range(CONSOLE_START_Y, CONSOLE_START_Y + CONSOLE_HEIGHT * int(PXOpcodes.FONT_CHAR_HEIGHT)):
        for x in range(CONSOLE_START_X, CONSOLE_START_X + CONSOLE_WIDTH * int(PXOpcodes.FONT_CHAR_WIDTH)):
            set_persistent_data_pixel(x, y, Color(0,0,0,1))
    set_persistent_data_pixel(KEYBOARD_BUFFER_X, KEYBOARD_BUFFER_Y, Color(0,0,0,1))


    # --- Create Initial Opcode Canvas Data (Bootloader will replace this) ---
    var initial_opcode_data = Image.create(canvas_width, canvas_height, false, Image.FORMAT_RGBA8)
    initial_opcode_data.fill(Color(0, 0, 0, 1))

    # PC starts at (0,0) with BOOT_CONTROL opcode, pointing to Stage 1 default load address
    # This will now be handled by the "Load Bootloader" button in PXSeedDevtool.
    initial_opcode_data.set_pixel(PC_PIXEL_X, PC_PIXEL_Y, Color(PXOpcodes.PX_BOOT_CONTROL_ID, 
                                                                 float(PXBootloader.STAGE_1_START_X)/255.0, 
                                                                 float(PXBootloader.STAGE_1_START_Y)/255.0, 
                                                                 1.0))
                                                                 
	opcode_a_initial_texture = ImageTexture.create_from_image(initial_opcode_data)
	opcode_b_initial_texture = ImageTexture.create_from_image(initial_opcode_data.duplicate())

	var opcode_initial_sprite_a = Sprite2D.new()
	opcode_initial_sprite_a.centered = false
	opcode_initial_sprite_a.texture_filter = TextureRect.TEXTURE_FILTER_NEAREST
	opcode_initial_sprite_a.texture = opcode_a_initial_texture
	viewport_opcode_a.add_child(opcode_initial_sprite_a)

	var opcode_initial_sprite_b = Sprite2D.new()
	opcode_initial_sprite_b.centered = false
	opcode_initial_sprite_b.texture_filter = TextureRect.TEXTURE_FILTER_NEAREST
	opcode_initial_sprite_b.texture = opcode_b_initial_texture
	viewport_opcode_b.add_child(opcode_initial_sprite_b)

    # --- Create Initial Data Canvas Data ---
    var initial_data_data = Image.create(canvas_width, canvas_height, false, Image.FORMAT_RGBA8)
    initial_data_data.fill(Color(0, 0, 0, 1))

    data_a_initial_texture = ImageTexture.create_from_image(initial_data_data)
    data_b_initial_texture = ImageTexture.create_from_image(initial_data_data.duplicate())

    var data_initial_sprite_a = Sprite2D.new()
    data_initial_sprite_a.centered = false
    data_initial_sprite_a.texture_filter = TextureRect.TEXTURE_FILTER_NEAREST
    data_initial_sprite_a.texture = data_a_initial_texture
    viewport_data_a.add_child(data_initial_sprite_a)

    var data_initial_sprite_b = Sprite2D.new()
    data_initial_sprite_b.centered = false
    data_initial_sprite_b.texture_filter = TextureRect.TEXTURE_FILTER_NEAREST
    data_initial_sprite_b.texture = data_b_initial_texture
    viewport_data_b.add_child(data_initial_sprite_b)


	# --- Shader Material Setup ---
	var opcode_shader = load("res://shaders/pxos_opcode_shader.gdshader")
	var font_texture = preload("res://resources/font_5x5.png")

	var material = ShaderMaterial.new()
	material.shader = opcode_shader
	material.set_shader_parameter("pxos_resolution", Vector2(canvas_width, canvas_height))
	material.set_shader_parameter("px_font_atlas", font_texture)
	material.set_shader_parameter("injection_overlay", viewport_injection.get_texture())
	material.set_shader_parameter("px_data_read_buffer", viewport_data_a.get_texture())
	material.set_shader_parameter("pxnet_bus_buffer", viewport_pxnet.get_texture())


	var process_sprite_in_opcode_a = Sprite2D.new()
	process_sprite_in_opcode_a.material = material
	process_sprite_in_opcode_a.texture = viewport_opcode_b.get_texture()
	process_sprite_in_opcode_a.centered = false
	viewport_opcode_a.add_child(process_sprite_in_opcode_a)

	var process_sprite_in_opcode_b = Sprite2D.new()
	process_sprite_in_opcode_b.material = material
	process_sprite_in_opcode_b.texture = viewport_opcode_a.get_texture()
	process_sprite_in_opcode_b.centered = false
	viewport_opcode_b.add_child(process_sprite_in_opcode_b)

    var data_passthrough_shader = load("res://shaders/data_passthrough_shader.gdshader")
    var data_material = ShaderMaterial.new()
    data_material.shader = data_passthrough_shader
    data_material.set_shader_parameter("resolution", Vector2(canvas_width, canvas_height))

    var process_sprite_in_data_a = Sprite2D.new()
    process_sprite_in_data_a.material = data_material
    process_sprite_in_data_a.texture = viewport_data_b.get_texture()
    process_sprite_in_data_a.centered = false
    viewport_data_a.add_child(process_sprite_in_data_a)

    var process_sprite_in_data_b = Sprite2D.new()
    process_sprite_in_data_b.material = data_material
    process_sprite_in_data_b.texture = viewport_data_a.get_texture()
    process_sprite_in_data_b.centered = false
    viewport_data_b.add_child(process_sprite_in_data_b)


	# --- Set Initial Display Texture ---
	texture_rect_display.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	texture_rect_display.texture_filter = TextureRect.TEXTURE_FILTER_NEAREST
	texture_rect_display.custom_minimum_size = Vector2(canvas_width * pixel_size, canvas_height * pixel_size)

	current_opcode_read_viewport = viewport_opcode_a
	current_opcode_write_viewport = viewport_opcode_b
	current_data_read_viewport = viewport_data_a
	current_data_write_viewport = viewport_data_b

	texture_rect_display.texture = current_opcode_read_viewport.get_texture()

	set_process(true)

func _process(delta):
	var global_time = Time.get_ticks_msec() / 1000.0
	
	var opcode_material = (viewport_opcode_a.get_child(1) as Sprite2D).material as ShaderMaterial
	if opcode_material:
		opcode_material.set_shader_parameter("time", global_time)
		opcode_material.set_shader_parameter("injection_overlay", viewport_injection.get_texture())
		opcode_material.set_shader_parameter("px_data_read_buffer", current_data_read_viewport.get_texture())
		opcode_material.set_shader_parameter("pxnet_bus_buffer", viewport_pxnet.get_texture())

    var data_material = (viewport_data_a.get_child(1) as Sprite2D).material as ShaderMaterial
    if data_material:
        data_material.set_shader_parameter("time", global_time)

    if planet_3d_instance != null:
        planet_3d_instance.update_textures(
            current_data_read_viewport.get_texture(),
            ImageTexture.create_from_image(elevation_layer)
        )

	clear_injection_buffer()

    # --- Program Counter Logic (CPU-driven execution) ---
    if pause_execution and not single_step_ready:
        return
    
    if breakpoints.has(current_pc_coords):
        pause_execution = true
        print("DEBUG: Breakpoint hit at (%d,%d)!" % [current_pc_coords.x, current_pc_coords.y])
        return

    if pc_active:
        var pc_pixel_color = get_opcode_pixel(PC_PIXEL_X, PC_PIXEL_Y)
        current_pc_coords = Vector2i(int(round(pc_pixel_color.g * 255.0)), int(round(pc_pixel_color.b * 255.0)))
        
        if pc_pixel_color.r == PXOpcodes.PX_BOOT_CONTROL_ID:
            if pc_pixel_color.a > 0.5:
                var current_ptr_x = current_pc_coords.x
                var current_ptr_y = current_pc_coords.y

                var instruction_opcode_pixel = get_opcode_pixel(current_ptr_x, current_ptr_y)
                var instruction_id = instruction_opcode_pixel.r

                var next_ptr_x = current_ptr_x
                var next_ptr_y = current_ptr_y + 1

                match instruction_id:
                    PXOpcodes.PX_WRITE_TO_DATA_CMD:
                        var target_data_x = int(round(instruction_opcode_pixel.g * 255.0))
                        var target_data_y = int(round(instruction_opcode_pixel.b * 255.0))
                        
                        var data_value_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        set_persistent_data_pixel(target_data_x, target_data_y, data_value_pixel)
                        print("PC: Wrote %s to data at (%d,%d)" % [data_value_pixel.to_html(false), target_data_x, target_data_y])
                        next_ptr_y += 1

                    PXOpcodes.PX_DRAW_CHAR_CMD:
                        var char_target_x = int(round(instruction_opcode_pixel.g * 255.0))
                        var char_target_y = int(round(instruction_opcode_pixel.b * 255.0))

                        var char_value_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        set_persistent_pixel_opcode(char_target_x, char_target_y, Color(PXOpcodes.PX_DRAW_CHAR, char_value_pixel.r, char_value_pixel.b, 1.0))
                        print("PC: Drawing char at (%d,%d) with value from (%d,%d)" % [char_target_x, char_target_y, current_ptr_x + 1, current_ptr_y])
                        next_ptr_y += 1

                    PXOpcodes.PX_MOV_VAL_TO_REG_CMD:
                        var target_reg_id = instruction_opcode_pixel.g
                        var val_byte_r = int(round(instruction_opcode_pixel.b * 255.0))
                        
                        var val_pixel_2 = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var val_byte_g = int(round(val_pixel_2.r * 255.0))
                        var val_byte_b = int(round(val_pixel_2.g * 255.0))
                        
                        var value_24bit = (val_byte_r << 16) | (val_byte_g << 8) | val_byte_b
                        var register_coords = _get_register_coords(target_reg_id)
                        
                        if register_coords.x != -1:
                            set_persistent_data_pixel(register_coords.x, register_coords.y, _int_to_color(value_24bit))
                            print("PC: MOV_VAL_TO_REG R%d, %d" % [_get_reg_id_val(target_reg_id), value_24bit])
                        else:
                            print("PC: MOV_VAL_TO_REG: Invalid register ID %f" % target_reg_id)
                        next_ptr_y += 1

                    PXOpcodes.PX_MOV_REG_TO_REG_CMD:
                        var src_reg_id = instruction_opcode_pixel.g
                        var dest_reg_id = instruction_opcode_pixel.b

                        var src_coords = _get_register_coords(src_reg_id)
                        var dest_coords = _get_register_coords(dest_reg_id)

                        if src_coords.x != -1 and dest_coords.x != -1:
                            var src_value_color = get_data_pixel(src_coords.x, src_coords.y)
                            set_persistent_data_pixel(dest_coords.x, dest_coords.y, src_value_color)
                            print("PC: MOV_REG_TO_REG R%d, R%d" % [_get_reg_id_val(src_reg_id), _get_reg_id_val(dest_reg_id)])
                        else:
                            print("PC: MOV_REG_TO_REG: Invalid register IDs %f, %f" % [src_reg_id, dest_reg_id])

                    PXOpcodes.PX_ADD_REG_CMD:
                        var reg_a_id = instruction_opcode_pixel.g
                        var reg_b_id = instruction_opcode_pixel.b
                        var target_reg_id_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var target_reg_id = target_reg_id_pixel.r
                        
                        var reg_a_coords = _get_register_coords(reg_a_id)
                        var reg_b_coords = _get_register_coords(reg_b_id)
                        var target_coords = _get_register_coords(target_reg_id)

                        if reg_a_coords.x != -1 and reg_b_coords.x != -1 and target_coords.x != -1:
                            var val_a = _color_to_int(get_data_pixel(reg_a_coords.x, reg_a_coords.y))
                            var val_b = _color_to_int(get_data_pixel(reg_b_coords.x, reg_b_coords.y))
                            var result = val_a + val_b
                            set_persistent_data_pixel(target_coords.x, target_coords.y, _int_to_color(result))
                            print("PC: ADD_REG R%d, R%d, R%d (Result: %d)" % [_get_reg_id_val(reg_a_id), _get_reg_id_val(reg_b_id), _get_reg_id_val(target_reg_id), result])
                        else:
                            print("PC: ADD_REG: Invalid register IDs.")
                        next_ptr_y += 1

                    PXOpcodes.PX_JUMP_CMD:
                        var jump_target_x = int(round(instruction_opcode_pixel.g * 255.0))
                        var jump_target_y = int(round(instruction_opcode_pixel.b * 255.0))
                        print("PC: JUMP to (%d,%d)" % [jump_target_x, jump_target_y])
                        next_ptr_x = jump_target_x
                        next_ptr_y = jump_target_y
                        
                    PXOpcodes.PX_READ_REG_TO_DISPLAY_CMD:
                        var src_reg_id = instruction_opcode_pixel.g
                        var display_target_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var display_x = int(round(display_target_pixel.r * 255.0))
                        var display_y = int(round(display_target_pixel.g * 255.0))

                        var src_coords = _get_register_coords(src_reg_id)
                        if src_coords.x != -1:
                            var reg_value_color = get_data_pixel(src_coords.x, src_coords.y)
                            set_persistent_pixel_opcode(display_x, display_y, Color(PXOpcodes.PX_DRAW_PIXEL, reg_value_color.r, reg_value_color.g, reg_value_color.b, 1.0))
                            print("PC: READ_REG_TO_DISPLAY R%d at (%d,%d) (Value: %s)" % [_get_reg_id_val(src_reg_id), display_x, display_y, reg_value_color.to_html(false)])
                        else:
                            print("PC: READ_REG_TO_DISPLAY: Invalid register ID %f" % src_reg_id)
                        next_ptr_y += 1

                    PXOpcodes.PX_PUSH_REG_CMD:
                        var reg_id = instruction_opcode_pixel.g
                        var reg_coords = _get_register_coords(reg_id)
                        if reg_coords.x != -1:
                            var value_to_push = _color_to_int(get_data_pixel(reg_coords.x, reg_coords.y))
                            _push_stack(value_to_push)
                            print("PC: PUSH R%d (Value: %d)" % [_get_reg_id_val(reg_id), value_to_push])
                        else:
                            print("PC: PUSH: Invalid register ID %f" % reg_id)

                    PXOpcodes.PX_POP_REG_CMD:
                        var reg_id = instruction_opcode_pixel.g
                        var reg_coords = _get_register_coords(reg_id)
                        if reg_coords.x != -1:
                            var popped_value = _pop_stack()
                            set_persistent_data_pixel(reg_coords.x, reg_coords.y, _int_to_color(popped_value))
                            print("PC: POP R%d (Value: %d)" % [_get_reg_id_val(reg_id), popped_value])
                        else:
                            print("PC: POP: Invalid register ID %f" % reg_id)

                    PXOpcodes.PX_JUMP_IF_ZERO_CMD:
                        var reg_id = instruction_opcode_pixel.g
                        var jump_target_y = int(round(instruction_opcode_pixel.b * 255.0))
                        var jump_target_x_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var jump_target_x = int(round(jump_target_x_pixel.r * 255.0))

                        var reg_coords = _get_register_coords(reg_id)
                        if reg_coords.x != -1:
                            var reg_value = _color_to_int(get_data_pixel(reg_coords.x, reg_coords.y))
                            if reg_value == 0:
                                next_ptr_x = jump_target_x
                                next_ptr_y = jump_target_y
                                print("PC: JZ R%d is zero. JUMP to (%d,%d)" % [_get_reg_id_val(reg_id), jump_target_x, jump_target_y])
                            else:
                                print("PC: JZ R%d is not zero (%d). No jump." % [_get_reg_id_val(reg_id), reg_value])
                        else:
                            print("PC: JZ: Invalid register ID %f" % reg_id)
                        next_ptr_y += 1

                    PXOpcodes.PX_JUMP_IF_NOT_ZERO_CMD:
                        var reg_id = instruction_opcode_pixel.g
                        var jump_target_y = int(round(instruction_opcode_pixel.b * 255.0))
                        var jump_target_x_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var jump_target_x = int(round(jump_target_x_pixel.r * 255.0))

                        var reg_coords = _get_register_coords(reg_id)
                        if reg_coords.x != -1:
                            var reg_value = _color_to_int(get_data_pixel(reg_coords.x, reg_coords.y))
                            if reg_value != 0:
                                next_ptr_x = jump_target_x
                                next_ptr_y = jump_target_y
                                print("PC: JNZ R%d is not zero (%d). JUMP to (%d,%d)" % [_get_reg_id_val(reg_id), reg_value, jump_target_x, jump_target_y])
                            else:
                                print("PC: JNZ R%d is zero. No jump." % [_get_reg_id_val(reg_id)])
                        else:
                            print("PC: JNZ: Invalid register ID %f" % reg_id)
                        next_ptr_y += 1

                    PXOpcodes.PX_CALL_CMD:
                        var call_target_y = int(round(instruction_opcode_pixel.b * 255.0))
                        var call_target_x_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var call_target_x = int(round(call_target_x_pixel.r * 255.0))

                        var return_addr_x = current_ptr_x
                        var return_addr_y = current_ptr_y + 2
                        
                        _push_stack(_color_to_int(Color(float(return_addr_x)/255.0, float(return_addr_y)/255.0, 0.0, 1.0)))

                        print("PC: CALL to (%d,%d). Pushed return (%d,%d)" % [call_target_x, call_target_y, return_addr_x, return_addr_y])
                        next_ptr_x = call_target_x
                        next_ptr_y = call_target_y
                        next_ptr_y += 1

                    PXOpcodes.PX_RET_CMD:
                        var return_addr_int = _pop_stack()
                        var return_addr_color = _int_to_color(return_addr_int)
                        var return_addr_x = int(round(return_addr_color.r * 255.0))
                        var return_addr_y = int(round(return_addr_color.g * 255.0))
                        print("PC: RET. Popped return (%d,%d)" % [return_addr_x, return_addr_y])
                        next_ptr_x = return_addr_x
                        next_ptr_y = return_addr_y

                    # Phase 5.3 - Basic I/O Device Abstractions
                    PXOpcodes.PX_OUT_CHAR_CMD:
                        var src_reg_id = instruction_opcode_pixel.g
                        var console_x_pos = int(round(instruction_opcode_pixel.b * 255.0))

                        var char_color_pixel = get_opcode_pixel(current_ptr_x + 1, current_ptr_y)
                        var char_color = Color(char_color_pixel.r, char_color_pixel.g, char_color_pixel.b, 1.0)

                        var reg_coords = _get_register_coords(src_reg_id)
                        if reg_coords.x != -1:
                            var char_code_int = _color_to_int(get_data_pixel(reg_coords.x, reg_coords.y))
                            _draw_char_to_console(char_code_int, console_x_pos, 0, char_color)
                            print("PC: OUT_CHAR R%d to console_x=%d (Char: '%c')" % [_get_reg_id_val(src_reg_id), console_x_pos, char(char_code_int)])
                        else:
                            print("PC: OUT_CHAR: Invalid register ID %f" % src_reg_id)
                        next_ptr_y += 1

                    PXOpcodes.PX_IN_KEY_CMD:
                        var dest_reg_id = instruction_opcode_pixel.g
                        var reg_coords = _get_register_coords(dest_reg_id)
                        
                        if reg_coords.x != -1:
                            var key_code = _read_keyboard_buffer()
                            set_persistent_data_pixel(reg_coords.x, reg_coords.y, _int_to_color(key_code))
                            print("PC: IN_KEY R%d (Key: '%s' / %d)" % [_get_reg_id_val(dest_reg_id), char(key_code) if key_code > 0 else "None", key_code])
                        else:
                            print("PC: IN_KEY: Invalid register ID %f" % dest_reg_id)

                    PXOpcodes.PX_HALT_CMD:
                        pc_active = false
                        print("PC: HALT Command. Boot process halted.")
                        
                    _:
                        print("PC: Unrecognized or NO_OP at (%d,%d). Advancing." % [current_ptr_x, current_ptr_y])
                        
                if pc_active:
                    set_persistent_pixel_opcode(PC_PIXEL_X, PC_PIXEL_Y, 
                                                Color(PXOpcodes.PX_BOOT_CONTROL_ID, 
                                                      float(next_ptr_x)/255.0, 
                                                      float(next_ptr_y)/255.0, 
                                                      1.0))
                else:
                    set_persistent_pixel_opcode(PC_PIXEL_X, PC_PIXEL_Y, 
                                                Color(PXOpcodes.PX_BOOT_CONTROL_ID, 
                                                      float(current_ptr_x)/255.0, 
                                                      float(current_ptr_y)/255.0, 
                                                      0.0))
            else:
                pass
        else:
            pass
    
    if debug_mode and pause_execution and not single_step_ready:
        return
    
    if single_step_ready:
        single_step_ready = false

	var temp_opcode_read_viewport = current_opcode_read_viewport
	var temp_opcode_write_viewport = current_opcode_write_viewport
	current_opcode_read_viewport = temp_opcode_write_viewport
	current_opcode_write_viewport = temp_opcode_read_viewport
	
	(viewport_opcode_a.get_child(1) as Sprite2D).texture = viewport_opcode_b.get_texture()
	(viewport_opcode_b.get_child(1) as Sprite2D).texture = viewport_opcode_a.get_texture()

    var temp_data_read_viewport = current_data_read_viewport
    var temp_data_write_viewport = current_data_write_viewport
    current_data_read_viewport = temp_data_write_viewport
    current_data_write_viewport = temp_data_read_viewport

    (viewport_data_a.get_child(1) as Sprite2D).texture = viewport_data_b.get_texture()
    (viewport_data_b.get_child(1) as Sprite2D).texture = viewport_data_a.get_texture()

	texture_rect_display.texture = current_opcode_read_viewport.get_texture()

func get_opcode_pixel(px_x: int, px_y: int) -> Color:
	if px_x < 0 or px_x >= canvas_width or px_y < 0 or px_y >= canvas_height:
		return Color(0,0,0,0)
    var current_image: Image = current_opcode_read_viewport.get_texture().get_image()
    if current_image:
        current_image.lock()
        var color = current_image.get_pixel(px_x, px_y)
        current_image.unlock()
        return color
    return Color(0,0,0,0)

func get_pixel_data_from_gpu(px_x: int, px_y: int) -> Color:
	return get_opcode_pixel(px_x, px_y)

func inject_pixel_opcode(x: int, y: int, opcode_color: Color):
	if x >= 0 and x < canvas_width and y >= 0 and y < canvas_height:
		injection_image.lock()
		injection_image.set_pixel(x, y, opcode_color)
		injection_image.unlock()
		injection_texture.update(injection_image)
	else:
		print("Transient injection pixel out of bounds: (%d, %d)" % [x, y])

func clear_injection_buffer():
	injection_image.lock()
	injection_image.fill(Color(0,0,0,0))
	injection_image.unlock()
	injection_texture.update(injection_image)

func set_persistent_pixel_opcode(x: int, y: int, opcode_color: Color):
	if x < 0 or x >= canvas_width or y < 0 or y >= canvas_height:
		print("Persistent opcode modification out of bounds: (%d, %d)" % [x, y])
		return

    var current_img_a = opcode_a_initial_texture.get_image()
    var current_img_b = opcode_b_initial_texture.get_image()

    current_img_a.lock()
    current_img_a.set_pixel(x, y, opcode_color)
    current_img_a.unlock()
    opcode_a_initial_texture.update(current_img_a)

    current_img_b.lock()
    current_img_b.set_pixel(x, y, opcode_color)
    current_img_b.unlock()
    opcode_b_initial_texture.update(current_img_b)
		
	print("Persistent opcode set at (%d, %d) with %s" % [x, y, opcode_color])

func get_data_pixel(px_x: int, px_y: int) -> Color:
    if px_x < 0 or px_x >= canvas_width or px_y < 0 or px_y >= canvas_height:
        return Color(0,0,0,0)
    
    var current_image: Image = current_data_read_viewport.get_texture().get_image()
    if current_image:
        current_image.lock()
        var color = current_image.get_pixel(px_x, px_y)
        current_image.unlock()
        return color
    return Color(0,0,0,0)

func set_persistent_data_pixel(x: int, y: int, data_color: Color):
    if x < 0 or x >= canvas_width or y < 0 or y >= canvas_height:
        print("Persistent data modification out of bounds: (%d, %d)" % [x, y])
        return
    
    var current_img_a = data_a_initial_texture.get_image()
    var current_img_b = data_b_initial_texture.get_image()

    current_img_a.lock()
    current_img_a.set_pixel(x, y, data_color)
    current_img_a.unlock()
    data_a_initial_texture.update(current_img_a)

    current_img_b.lock()
    current_img_b.set_pixel(x, y, data_color)
    current_img_b.unlock()
    data_b_initial_texture.update(current_img_b)

    print("Persistent data set at (%d, %d) with %s" % [x, y, data_color])

func load_map_from_boot_pixel(boot_pixel_rgb: Color, external_elevation_path: String = ""):
    print("Loading map from boot pixel: %s" % boot_pixel_rgb.to_html(false))
    
    var map_py_path = ProjectSettings.globalize_path("res://map.py")
    var output_png_path = ProjectSettings.globalize_path("user://boot_map_temp.png")

    var args = [
        str(int(boot_pixel_rgb.r * 255)),
        str(int(boot_pixel_rgb.g * 255)),
        str(int(boot_pixel_rgb.b * 255)),
        str(canvas_width),
        str(canvas_height),
        output_png_path
    ]
    if not external_elevation_path.is_empty():
        args.append(ProjectSettings.globalize_path(external_elevation_path))
    
    if pxnet_claim_manager != null:
        var manifest_b64 = pxnet_claim_manager.get_territory_manifest_b64()
        if not manifest_b64.is_empty():
            args.append(manifest_b64)
            print("Passed territory manifest to map.py.")
        else:
            print("No territory manifest found to pass to map.py.")


    var python_executable = "python"
    
    var stdout_arr = []
    var stderr_arr = []
    var exit_code = OS.execute(python_executable, [map_py_path] + args, stdout_arr, stderr_arr, true) 
    
    if exit_code == 0:
        print("map.py executed successfully. stdout: %s" % " ".join(stdout_arr))
        if not stderr_arr.is_empty():
            print("map.py stderr: %s" % " ".join(stderr_arr))

        var generated_image = Image.new()
        var err = generated_image.load(output_png_path)
        if err == OK:
            elevation_layer = Image.create(generated_image.get_width(), generated_image.get_height(), false, Image.FORMAT_L8)
            generated_image.lock()
            elevation_layer.lock()
            for y in range(generated_image.get_height()):
                for x in range(generated_image.get_width()):
                    var rgba_pixel = generated_image.get_pixel(x, y)
                    elevation_layer.set_pixel(x, y, Color(rgba_pixel.a, rgba_pixel.a, rgba_pixel.a, 1.0))
            generated_image.unlock()
            elevation_layer.unlock()
            print("Elevation layer extracted and loaded.")

            var rgb_image = Image.create(generated_image.get_width(), generated_image.get_height(), false, Image.FORMAT_RGB8)
            generated_image.lock()
            rgb_image.lock()
            for y in range(generated_image.get_height()):
                for x in range(generated_image.get_width()):
                    var rgba_pixel = generated_image.get_pixel(x, y)
                    rgb_image.set_pixel(x, y, Color(rgba_pixel.r, rgba_pixel.g, rgba_pixel.b, 1.0))
            generated_image.unlock()
            rgb_image.unlock()

            data_a_initial_texture.update(rgb_image)
            data_b_initial_texture.update(rgb_image)
            print("Successfully loaded map RGB into data layer.")
            
            var empty_opcode_image = Image.create(canvas_width, canvas_height, false, Image.FORMAT_RGBA8)
            empty_opcode_image.fill(Color(0,0,0,1))
            opcode_a_initial_texture.update(empty_opcode_image)
            opcode_b_initial_texture.update(empty_opcode_image)
            
            pc_active = false # PC should be halted after a map load, wait for user to activate/boot
            set_persistent_pixel_opcode(PC_PIXEL_X, PC_PIXEL_Y, Color(PXOpcodes.PX_BOOT_CONTROL_ID, 0.0, 0.0, 0.0)) # PC inactive
            
        else:
            push_error("Error loading generated map PNG: %s" % err)
    else:
        push_error("Error executing map.py (exit code: %d). Stderr: %s" % [exit_code, " ".join(stderr_arr)])

func get_elevation_pixel(x: int, y: int) -> float:
    if elevation_layer == null:
        return 0.0
    x = clamp(x, 0, elevation_layer.get_width() - 1)
    y = clamp(y, 0, elevation_layer.get_height() - 1)
    return elevation_layer.get_pixel(x, y).r

func set_planet_3d_instance(instance: Node3D):
    planet_3d_instance = instance

func get_debug_state() -> Dictionary:
    var registers_val = []
    registers_val.append(_color_to_int(get_data_pixel(REG_R0_X, REGISTER_LAYER_Y_OFFSET)))
    registers_val.append(_color_to_int(get_data_pixel(REG_R1_X, REGISTER_LAYER_Y_OFFSET)))
    registers_val.append(_color_to_int(get_data_pixel(REG_R2_X, REGISTER_LAYER_Y_OFFSET)))
    registers_val.append(_color_to_int(get_data_pixel(REG_R3_X, REGISTER_LAYER_Y_OFFSET)))

    var stack_content = []
    var sp_value = _color_to_int(get_data_pixel(REG_R3_X, REGISTER_LAYER_Y_OFFSET))
    for y_offset in range(STACK_BASE_Y, sp_value):
        stack_content.append(_color_to_int(get_data_pixel(STACK_BASE_X, y_offset)))
    
    stack_content.reverse()

    return {
        "pc_coords": current_pc_coords,
        "pc_active": pc_active,
        "registers": registers_val,
        "stack": stack_content,
        "pause_execution": pause_execution,
        "debug_mode": debug_mode
    }

func set_debug_mode_state(enabled: bool):
    debug_mode = enabled
    pause_execution = enabled
    print("DEBUG MODE: %s" % ("ON" if enabled else "OFF"))

func toggle_pause_execution():
    pause_execution = !pause_execution
    print("EXECUTION PAUSED: %s" % pause_execution)

func step_once():
    single_step_ready = true
    pause_execution = true
    print("DEBUG: Single step requested.")

func set_breakpoint(x: int, y: int):
    var bp_coords = Vector2i(x, y)
    if not breakpoints.has(bp_coords):
        breakpoints.append(bp_coords)
        print("DEBUG: Breakpoint set at (%d,%d)" % [x, y])
    else:
        print("DEBUG: Breakpoint already exists at (%d,%d)" % [x, y])

func clear_all_breakpoints():
    breakpoints.clear()
    print("DEBUG: All breakpoints cleared.")