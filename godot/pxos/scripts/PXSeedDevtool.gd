# scripts/PXSeedDevtool.gd
extends Control

class_name PXSeedDevtool

@onready var code_input: LineEdit = $VBoxContainer/CodeLineEdit
@onready var execute_btn: Button = $VBoxContainer/ExecuteButton
@onready var load_bootloader_btn: Button = $VBoxContainer/LoadBootloaderButton # NEW

var gpu_driver: PXGPUDriver = null

func _ready():
    execute_btn.pressed.connect(Callable(self, "_on_ExecuteButton_pressed"))
    load_bootloader_btn.pressed.connect(Callable(self, "_on_LoadBootloaderButton_pressed")) # NEW
    
    code_input.placeholder_text = """# PXSeed VM Program Example (Phase 5.3)
MOV_VAL_TO_REG R0 72 0 0
OUT_CHAR R0 0 0
MOV_VAL_TO_REG R0 101 0 0
OUT_CHAR R0 1 0
MOV_VAL_TO_REG R0 108 0 0
OUT_CHAR R0 2 0
OUT_CHAR R0 3 0
MOV_VAL_TO_REG R0 111 0 0
OUT_CHAR R0 4 0

MOV_VAL_TO_REG R0 32 0 0
OUT_CHAR R0 5 0

MOV_VAL_TO_REG R0 87 0 0
OUT_CHAR R0 6 0
MOV_VAL_TO_REG R0 111 0 0
OUT_CHAR R0 7 0
MOV_VAL_TO_REG R0 114 0 0
OUT_CHAR R0 8 0
MOV_VAL_TO_REG R0 108 0 0
OUT_CHAR R0 9 0
MOV_VAL_TO_REG R0 100 0 0
OUT_CHAR R0 10 0

IN_KEY R1
READ_REG_TO_DISPLAY R1 30 31
HALT
"""

func _on_ExecuteButton_pressed():
    if not gpu_driver:
        print("Error: GPU Driver not assigned to PXSeedDevtool!")
        return
    
    gpu_driver.pc_active = false 
    var empty_opcode_image = Image.create(gpu_driver.canvas_width, gpu_driver.canvas_height, false, Image.FORMAT_RGBA8)
    empty_opcode_image.fill(Color(0,0,0,1)) 
    gpu_driver.opcode_a_initial_texture.update(empty_opcode_image)
    gpu_driver.opcode_b_initial_texture.update(empty_opcode_image)
    
    var empty_data_image = Image.create(gpu_driver.canvas_width, gpu_driver.canvas_height, false, Image.FORMAT_RGBA8)
    empty_data_image.fill(Color(0,0,0,1)) 
    gpu_driver.data_a_initial_texture.update(empty_data_image)
    gpu_driver.data_b_initial_texture.update(empty_data_image)

    gpu_driver.set_persistent_data_pixel(gpu_driver.REG_R0_X, gpu_driver.REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    gpu_driver.set_persistent_data_pixel(gpu_driver.REG_R1_X, gpu_driver.REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    gpu_driver.set_persistent_data_pixel(gpu_driver.REG_R2_X, gpu_driver.REGISTER_LAYER_Y_OFFSET, Color(0,0,0,1))
    gpu_driver.set_persistent_data_pixel(gpu_driver.REG_R3_X, gpu_driver.REGISTER_LAYER_Y_OFFSET, gpu_driver._int_to_color(gpu_driver.STACK_BASE_Y))

    for y in range(gpu_driver.STACK_BASE_Y, gpu_driver.STACK_BASE_Y + gpu_driver.STACK_MAX_SIZE):
        gpu_driver.set_persistent_data_pixel(gpu_driver.STACK_BASE_X, y, Color(0,0,0,1))

    for y in range(gpu_driver.CONSOLE_START_Y, gpu_driver.CONSOLE_START_Y + gpu_driver.CONSOLE_HEIGHT * int(PXOpcodes.FONT_CHAR_HEIGHT)):
        for x in range(gpu_driver.CONSOLE_START_X, gpu_driver.CONSOLE_START_X + gpu_driver.CONSOLE_WIDTH * int(PXOpcodes.FONT_CHAR_WIDTH)):
            gpu_driver.set_persistent_data_pixel(x, y, Color(0,0,0,1))
    gpu_driver.set_persistent_data_pixel(gpu_driver.KEYBOARD_BUFFER_X, gpu_driver.KEYBOARD_BUFFER_Y, Color(0,0,0,1))


    var input_code = code_input.text
    var lines = input_code.strip_edges().split("\n")
    print("\n--- Compiling & Loading PXSeed Program ---")
    
    var current_program_x = 1
    var current_program_y = 1

    for line_idx in range(lines.size()):
        var line = lines[line_idx]
        if line.strip_edges().is_empty() or line.strip_edges().starts_with("#"):
            continue

        var tokens = line.strip_edges().split(" ")
        if tokens.is_empty():
            continue

        var opcode_color_val: Color = PXOpcodes.PX_NO_OP
        var num_pixels_consumed = 1 

        match tokens[0].to_upper():
            "MOV_VAL_TO_REG":
                if tokens.size() == 6:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    var value_r = int(tokens[2])
                    var value_g = int(tokens[3])
                    var value_b = int(tokens[4])
                    var value_24bit_color = Color(float(value_r)/255.0, float(value_g)/255.0, float(value_b)/255.0, 1.0)
                    opcode_color_val = Color(PXOpcodes.PX_MOV_VAL_TO_REG_CMD, _get_reg_id_float(reg_id_val), value_24bit_color.r, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(value_24bit_color.g, value_24bit_color.b, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded MOV_VAL_TO_REG R{reg_id_val}, {value_r} {value_g} {value_b} at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ MOV_VAL_TO_REG: Invalid arguments for line: '{line}'")

            "MOV_REG_TO_REG":
                if tokens.size() == 3:
                    var src_reg_id_val = int(tokens[1].trim_prefix("R"))
                    var dest_reg_id_val = int(tokens[2].trim_prefix("R"))
                    opcode_color_val = Color(PXOpcodes.PX_MOV_REG_TO_REG_CMD, _get_reg_id_float(src_reg_id_val), _get_reg_id_float(dest_reg_id_val), 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded MOV_REG_TO_REG R{src_reg_id_val}, R{dest_reg_id_val} at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ MOV_REG_TO_REG: Invalid arguments for line: '{line}'")

            "ADD_REG":
                if tokens.size() == 4:
                    var reg_a_id_val = int(tokens[1].trim_prefix("R"))
                    var reg_b_id_val = int(tokens[2].trim_prefix("R"))
                    var target_reg_id_val = int(tokens[3].trim_prefix("R"))
                    opcode_color_val = Color(PXOpcodes.PX_ADD_REG_CMD, _get_reg_id_float(reg_a_id_val), _get_reg_id_float(reg_b_id_val), 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(_get_reg_id_float(target_reg_id_val), 0.0, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded ADD_REG R{reg_a_id_val}, R{reg_b_id_val}, R{target_reg_id_val} at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ ADD_REG: Invalid arguments for line: '{line}'")

            "JUMP":
                if tokens.size() == 3:
                    var target_x = int(tokens[1])
                    var target_y = int(tokens[2])
                    opcode_color_val = Color(PXOpcodes.PX_JUMP_CMD, float(target_x)/255.0, float(target_y)/255.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded JUMP to ({target_x},{target_y}) at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ JUMP: Invalid arguments for line: '{line}'")

            "READ_REG_TO_DISPLAY":
                if tokens.size() == 4:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    var display_x = int(tokens[2])
                    var display_y = int(tokens[3])
                    opcode_color_val = Color(PXOpcodes.PX_READ_REG_TO_DISPLAY_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(display_x)/255.0, float(display_y)/255.0, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded READ_REG_TO_DISPLAY R{reg_id_val} at ({display_x},{display_y}) at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ READ_REG_TO_DISPLAY: Invalid arguments for line: '{line}'")
            
            # Phase 5.2 - Advanced Control Flow & Stack Instructions
            "PUSH_REG":
                if tokens.size() == 2:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    opcode_color_val = Color(PXOpcodes.PX_PUSH_REG_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded PUSH_REG R{reg_id_val} at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ PUSH_REG: Invalid arguments for line: '{line}'")

            "POP_REG":
                if tokens.size() == 2:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    opcode_color_val = Color(PXOpcodes.PX_POP_REG_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded POP_REG R{reg_id_val} at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ POP_REG: Invalid arguments for line: '{line}'")

            "JUMP_IF_ZERO":
                if tokens.size() == 4:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    var target_x = int(tokens[2])
                    var target_y = int(tokens[3])
                    opcode_color_val = Color(PXOpcodes.PX_JUMP_IF_ZERO_CMD, _get_reg_id_float(reg_id_val), float(target_y)/255.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, 0.0, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded JUMP_IF_ZERO R{reg_id_val} to ({target_x},{target_y}) at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ JUMP_IF_ZERO: Invalid arguments for line: '{line}'")

            "JUMP_IF_NOT_ZERO":
                if tokens.size() == 4:
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    var target_x = int(tokens[2])
                    var target_y = int(tokens[3])
                    opcode_color_val = Color(PXOpcodes.PX_JUMP_IF_NOT_ZERO_CMD, _get_reg_id_float(reg_id_val), float(target_y)/255.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, 0.0, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded JUMP_IF_NOT_ZERO R{reg_id_val} to ({target_x},{target_y}) at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ JUMP_IF_NOT_ZERO: Invalid arguments for line: '{line}'")

            "CALL":
                if tokens.size() == 3:
                    var target_x = int(tokens[1])
                    var target_y = int(tokens[2])
                    opcode_color_val = Color(PXOpcodes.PX_CALL_CMD, float(target_x)/255.0, float(target_y)/255.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, float(target_y)/255.0, 0.0, 1.0))
                    num_pixels_consumed = 2
                    print(f"  Loaded CALL to ({target_x},{target_y}) at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ CALL: Invalid arguments for line: '{line}'")

            "RET":
                if tokens.size() == 1:
                    opcode_color_val = Color(PXOpcodes.PX_RET_CMD, 0.0, 0.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded RET at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ RET: Invalid arguments for line: '{line}'")


            "HALT":
                if tokens.size() == 1:
                    opcode_color_val = Color(PXOpcodes.PX_HALT_CMD, 0.0, 0.0, 1.0)
                    gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                    print(f"  Loaded HALT at ({current_program_x},{current_program_y})")
                else:
                    print(f"⚠️ HALT: Invalid arguments for line: '{line}'")
            
            "DRAW_PIXEL":
                if tokens.size() == 6:
                    var x = int(tokens[1])
                    var y = int(tokens[2])
                    var r = int(tokens[3])
                    var g = int(tokens[4])
                    var b = int(tokens[5])
                    gpu_driver.set_persistent_pixel_opcode(Vector2(x, y), Color(PXOpcodes.PX_DRAW_PIXEL, r / 255.0, g / 255.0, b / 255.0, 1.0))
                    print(f"  DRAW_PIXEL {x} {y} {r} {g} {b} executed.")
                else:
                    print(f"⚠️ DRAW_PIXEL: Invalid number of arguments for line: '{line}'")
            
            "OUT_CHAR":
                if tokens.size() == 4: # OUT_CHAR RegID ConsoleX ConsoleY
                    var reg_id_val = int(tokens[1].trim_prefix("R"))
                    var console_x = int(