# scripts/PXBootloader.gd
extends Node

class_name PXBootloader

# Define start addresses for each bootloader stage on the opcode layer
const STAGE_1_START_X = 1
const STAGE_1_START_Y = 1 # Overwrites initial hardcoded boot code for PC

const STAGE_2_START_X = 1
const STAGE_2_START_Y = 16 # Start of Stage 2 (after Stage 1's max possible size)

const STAGE_3_START_X = 1
const STAGE_3_START_Y = 32 # Start of Stage 3

const USER_PROGRAM_START_X = 1
const USER_PROGRAM_START_Y = 48 # Where the user's application will be loaded


# --- Define Bootloader Stages as PXTalk-like Instruction Arrays ---
# Each element in the array represents one PXSeed instruction line.
# Format: ["CMD", arg1, arg2, ...]
# Arguments for values (like 24-bit numbers) will follow the command as separate values.
# The `load_stage` function below will convert these into actual pixel opcodes.

var stage1_instructions = [
    ["MOV_VAL_TO_REG", 0, 72, 0, 0], # R0 = ASCII 'H' (for "H"ello)
    ["OUT_CHAR", 0, 0, 0],           # OUT_CHAR R0 to console_x=0, console_y=0 (white)
    ["MOV_VAL_TO_REG", 0, 101, 0, 0],# R0 = 'e'
    ["OUT_CHAR", 1, 0, 0],           # OUT_CHAR R0 to console_x=1, console_y=0
    ["MOV_VAL_TO_REG", 0, 108, 0, 0],# R0 = 'l'
    ["OUT_CHAR", 2, 0, 0],           # OUT_CHAR R0 to console_x=2, console_y=0
    ["OUT_CHAR", 3, 0, 0],           # OUT_CHAR R0 to console_x=3, console_y=0

    ["CALL", STAGE_2_START_X, STAGE_2_START_Y], # Call Stage 2 as subroutine
    ["HALT"] # Should not be reached if CALL works, but good practice.
]

var stage2_instructions = [
    ["MOV_VAL_TO_REG", 0, 32, 0, 0], # R0 = ASCII ' '
    ["OUT_CHAR", 4, 0, 0],           # Output space ' '
    ["MOV_VAL_TO_REG", 0, 87, 0, 0], # R0 = 'W' (for "World")
    ["OUT_CHAR", 5, 0, 0],           # Output 'W'
    ["MOV_VAL_TO_REG", 0, 111, 0, 0],# R0 = 'o'
    ["OUT_CHAR", 6, 0, 0],           # Output 'o'
    ["MOV_VAL_TO_REG", 0, 114, 0, 0],# R0 = 'r'
    ["OUT_CHAR", 7, 0, 0],           # Output 'r'
    
    # Simulate memory setup / program loader: Draw a pixel to signify.
    ["DRAW_PIXEL", 0, 0, 0, 255, 0], # Blue pixel at (0,0) to show Stage 2 loaded
    ["CALL", STAGE_3_START_X, STAGE_3_START_Y], # Call Stage 3
    ["RET"] # Return to caller (Stage 1, then HALT)
]

var stage3_instructions = [
    ["MOV_VAL_TO_REG", 0, 108, 0, 0], # R0 = 'l'
    ["OUT_CHAR", 8, 0, 0],            # Output 'l'
    ["MOV_VAL_TO_REG", 0, 100, 0, 0], # R0 = 'd'
    ["OUT_CHAR", 9, 0, 0],            # Output 'd'
    
    # Now, jump to a conceptual "user program"
    # This user program is just a simple animation loop or a HALT for now.
    ["JUMP", USER_PROGRAM_START_X, USER_PROGRAM_START_Y] # Jump to program start
]

var user_program_instructions = [
    ["MOV_VAL_TO_REG", 0, 0, 255, 0],   # R0 = Green color
    ["MOV_VAL_TO_REG", 1, 0, 0, 0],     # R1 = 0 (loop counter)
    ["LOOP_START_LABEL", 0, 0, 0],      # Just a label for clarity (will not be processed as opcode)
    ["READ_REG_TO_DISPLAY", 0, 5, 5],   # Display R0 (Green) at (5,5)
    ["MOV_VAL_TO_REG", 2, 1, 0, 0],     # R2 = 1
    ["ADD_REG", 1, 2, 1],               # R1 = R1 + R2 (increment loop counter)
    ["MOV_VAL_TO_REG", 2, 10, 0, 0],    # R2 = 10 (loop limit)
    ["JUMP_IF_NOT_ZERO", 1, 1, 0],      # JNZ R1 to (1,0) (label) - will jump back to top (not exact location now)
    ["JUMP", USER_PROGRAM_START_X, USER_PROGRAM_START_Y + 1] # Loop back (simulated)
    # The above loop is for conceptual illustration. Actual JUMP/CALL needs exact pixel coords.
    # For a real loop, you'd calculate exact target pixel for JUMP.
    # For this test, let's make the user program print a final message and halt.

    ["MOV_VAL_TO_REG", 0, ord('D'), 0, 0], # R0 = 'D'
    ["OUT_CHAR", 0, 1, 0],                 # Output 'D' to console row 1, x=0
    ["MOV_VAL_TO_REG", 0, ord('O'), 0, 0], # R0 = 'O'
    ["OUT_CHAR", 1, 1, 0],
    ["MOV_VAL_TO_REG", 0, ord('N'), 0, 0], # R0 = 'N'
    ["OUT_CHAR", 2, 1, 0],
    ["MOV_VAL_TO_REG", 0, ord('E'), 0, 0], # R0 = 'E'
    ["OUT_CHAR", 3, 1, 0],
    ["HALT"]
]


# --- Load Stages into Opcode Memory ---
func load_stage(stage_number: int, gpu_driver: PXGPUDriver):
    var instructions_to_load: Array
    var start_x = 0
    var start_y = 0
    
    match stage_number:
        1:
            instructions_to_load = stage1_instructions
            start_x = STAGE_1_START_X
            start_y = STAGE_1_START_Y
            print("Bootloader: Loading Stage 1...")
        2:
            instructions_to_load = stage2_instructions
            start_x = STAGE_2_START_X
            start_y = STAGE_2_START_Y
            print("Bootloader: Loading Stage 2...")
        3:
            instructions_to_load = stage3_instructions
            start_x = STAGE_3_START_X
            start_y = STAGE_3_START_Y
            print("Bootloader: Loading Stage 3...")
        # NEW: Load the user program as part of the boot process
        "user_program":
            instructions_to_load = user_program_instructions
            start_x = USER_PROGRAM_START_X
            start_y = USER_PROGRAM_START_Y
            print("Bootloader: Loading User Program...")
        _:
            push_error("Bootloader: Invalid stage number: %d" % stage_number)
            return

    # Clear the target region before loading new instructions
    # This is a basic clear. For a full bootloader, a dedicated memory clearer would be needed.
    # For simplicity, we just overwrite.
    
    var current_program_x = start_x
    var current_program_y = start_y

    for line_data in instructions_to_load:
        var cmd = line_data[0]
        var opcode_color_val: Color = PXOpcodes.PX_NO_OP
        var num_pixels_consumed = 1 # Default for most single-pixel opcodes

        match cmd:
            "MOV_VAL_TO_REG":
                var reg_id_val = line_data[1]
                var value_r = line_data[2]
                var value_g = line_data[3]
                var value_b = line_data[4]
                var value_24bit_color = Color(float(value_r)/255.0, float(value_g)/255.0, float(value_b)/255.0, 1.0)
                opcode_color_val = Color(PXOpcodes.PX_MOV_VAL_TO_REG_CMD, _get_reg_id_float(reg_id_val), value_24bit_color.r, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(value_24bit_color.g, value_24bit_color.b, 0.0, 1.0))
                num_pixels_consumed = 2

            "MOV_REG_TO_REG":
                var src_reg_id_val = line_data[1]
                var dest_reg_id_val = line_data[2]
                opcode_color_val = Color(PXOpcodes.PX_MOV_REG_TO_REG_CMD, _get_reg_id_float(src_reg_id_val), _get_reg_id_float(dest_reg_id_val), 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "ADD_REG":
                var reg_a_id_val = line_data[1]
                var reg_b_id_val = line_data[2]
                var target_reg_id_val = line_data[3]
                opcode_color_val = Color(PXOpcodes.PX_ADD_REG_CMD, _get_reg_id_float(reg_a_id_val), _get_reg_id_float(reg_b_id_val), 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(_get_reg_id_float(target_reg_id_val), 0.0, 0.0, 1.0))
                num_pixels_consumed = 2

            "JUMP":
                var target_x = line_data[1]
                var target_y = line_data[2]
                opcode_color_val = Color(PXOpcodes.PX_JUMP_CMD, float(target_x)/255.0, float(target_y)/255.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "READ_REG_TO_DISPLAY":
                var reg_id_val = line_data[1]
                var display_x = line_data[2]
                var display_y = line_data[3]
                opcode_color_val = Color(PXOpcodes.PX_READ_REG_TO_DISPLAY_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(display_x)/255.0, float(display_y)/255.0, 0.0, 1.0))
                num_pixels_consumed = 2
            
            "PUSH_REG":
                var reg_id_val = line_data[1]
                opcode_color_val = Color(PXOpcodes.PX_PUSH_REG_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "POP_REG":
                var reg_id_val = line_data[1]
                opcode_color_val = Color(PXOpcodes.PX_POP_REG_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "JUMP_IF_ZERO":
                var reg_id_val = line_data[1]
                var target_x = line_data[2]
                var target_y = line_data[3]
                opcode_color_val = Color(PXOpcodes.PX_JUMP_IF_ZERO_CMD, _get_reg_id_float(reg_id_val), float(target_y)/255.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, 0.0, 0.0, 1.0))
                num_pixels_consumed = 2

            "JUMP_IF_NOT_ZERO":
                var reg_id_val = line_data[1]
                var target_x = line_data[2]
                var target_y = line_data[3]
                opcode_color_val = Color(PXOpcodes.PX_JUMP_IF_NOT_ZERO_CMD, _get_reg_id_float(reg_id_val), float(target_y)/255.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, 0.0, 0.0, 1.0))
                num_pixels_consumed = 2

            "CALL":
                var target_x = line_data[1]
                var target_y = line_data[2]
                opcode_color_val = Color(PXOpcodes.PX_CALL_CMD, float(target_x)/255.0, float(target_y)/255.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(target_x)/255.0, float(target_y)/255.0, 0.0, 1.0))
                num_pixels_consumed = 2

            "RET":
                opcode_color_val = Color(PXOpcodes.PX_RET_CMD, 0.0, 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "OUT_CHAR":
                var reg_id_val = line_data[1]
                var console_x = line_data[2]
                var console_y = line_data[3]
                opcode_color_val = Color(PXOpcodes.PX_OUT_CHAR_CMD, _get_reg_id_float(reg_id_val), float(console_x)/255.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)
                gpu_driver.set_persistent_pixel_opcode(current_program_x + 1, current_program_y, Color(float(console_y)/255.0, 0.0, 0.0, 1.0)) # ConsoleY in next pixel R (and color is implicit white for console for now)
                num_pixels_consumed = 2

            "IN_KEY":
                var reg_id_val = line_data[1]
                opcode_color_val = Color(PXOpcodes.PX_IN_KEY_CMD, _get_reg_id_float(reg_id_val), 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "HALT":
                opcode_color_val = Color(PXOpcodes.PX_HALT_CMD, 0.0, 0.0, 1.0)
                gpu_driver.set_persistent_pixel_opcode(current_program_x, current_program_y, opcode_color_val)

            "DRAW_PIXEL": # Direct pixel draw (not a VM instruction, for quick setup)
                var x = line_data[1]
                var y = line_data[2]
                var r = line_data[3]
                var g = line_data[4]
                var b = line_data[5]
                gpu_driver.set_persistent_pixel_opcode(Vector2(x, y), Color(PXOpcodes.PX_DRAW_PIXEL, float(r) / 255.0, float(g) / 255.0, float(b) / 255.0, 1.0))

            _:
                print("Bootloader: Unknown command during load: %s" % cmd)
        
        current_program_y += num_pixels_consumed
    
    # After loading stage, ensure next pixels are cleared to avoid stale instructions
    # (Optional, but good for clean memory)
    # for y in range(current_program_y, start_y + len(instructions_to_load) * 2 + 5): # Clear a bit beyond
    #    gpu_driver.set_persistent_pixel_opcode(current_program_x, y, PXOpcodes.PX_NO_OP)

    print("Bootloader: Stage loaded.")

# Helper to convert integer register ID to float ID for opcode encoding
func _get_reg_id_float(reg_id_int: int) -> float:
    match reg_id_int:
        0: return PXOpcodes.REG_R0_ID
        1: return PXOpcodes.REG_R1_ID
        2: return PXOpcodes.REG_R2_ID
        3: return PXOpcodes.REG_R3_ID
    return -1.0 # Error