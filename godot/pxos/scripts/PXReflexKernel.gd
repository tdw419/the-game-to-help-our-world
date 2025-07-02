# PXReflexKernel.gd
# This script extends PXKernelDisplayReflector.gd, evolving it into a "Reflex Kernel".
# It introduces concepts for a modular opcode registry, visual memory regions,
# and a basic framework for opcode rewriting/visual mutation, allowing the
# kernel to dynamically influence its own visual state and logic.

# Inherit from the base PXKernelDisplayReflector to leverage its core functionalities
# like framebuffer access and basic cycle management.
extends "res://PXKernelDisplayReflector.gd" # Adjust path if your PXKernelDisplayReflector.gd is elsewhere

# --- Modular Opcode Registry ---
# A dynamic dictionary mapping pixel colors (opcodes) to their string representations.
# This makes the opcode interpretation more flexible and extensible.
var opcode_map = {
    PXL_HALT: "HALT",
    PXL_PRINT_HELLO: "PRINT_HELLO",
    PXL_JUMP_TO_X: "JUMP_TO_X",
    # Add more opcodes here as your system evolves
    Color(0.5, 0.0, 0.5): "MUTATE_REGION", # Example: A new opcode for mutation
    Color(0.0, 0.5, 0.5): "LOG_STATE"     # Example: A new opcode for logging kernel state
}

# --- Visual Memory Regions ---
# Define specific areas on the display that serve different purposes.
# These are Rect2 objects (position_x, position_y, width, height).
# Assuming a 64x64 display for now, based on PXBootPainter.gd.
const DISPLAY_WIDTH = 64
const DISPLAY_HEIGHT = 64

const BOOT_CODE_REGION = Rect2(0, 0, 4, 1) # Top-left 4x1 pixels for initial boot code
const KERNEL_OUTPUT_REGION = Rect2(0, 10, 10, 1) # A line for kernel-injected output
const PROGRAM_MEMORY_REGION = Rect2(0, 20, DISPLAY_WIDTH, DISPLAY_HEIGHT - 20 - 5) # Main program area
const DEBUG_LOG_REGION = Rect2(DISPLAY_WIDTH - 1, DISPLAY_HEIGHT - 10, 1, 10) # Rightmost column for debug logs

# --- Internal Kernel State (for reflection) ---
# The kernel can maintain its own internal state, which it might then
# reflect visually onto the display.
var kernel_internal_state: Dictionary = {
    "last_opcode_detected": "NONE",
    "cycle_count": 0,
    "mutation_attempts": 0
}

# --- Godot Lifecycle Methods ---

# _ready from base class will call initialize_kernel.
# We can override _process if needed, but for now, we'll just add
# to the existing logic by calling new functions.

func _process(delta):
    # Call the base class's _process to maintain the core cycle logic.
    super._process(delta)

    # Add Reflex Kernel specific actions within the cycle.
    if ready_to_think and frame_counter == 0: # This runs after base class's analyze/inject
        kernel_internal_state["cycle_count"] += 1
        mutate_display_based_on_rules()
        reflect_kernel_state_visually()


# --- Modular Opcode Interpretation ---

func interpret_opcode(color: Color) -> String:
    # Interprets a given pixel color as an opcode string using the dynamic map.
    for key in opcode_map.keys():
        if color == key:
            return opcode_map[key]
    return "UNKNOWN_OPCODE" # Default for unrecognized colors

func analyze_display_stack():
    # Override the base class's analyze_display_stack to use the modular registry
    # and respect memory regions.

    if not framebuffer_image or not framebuffer_image.is_locked():
        print_err("PXReflexKernel: Framebuffer image not available or not locked for reading.")
        return

    print("PXReflexKernel: Analyzing display stack with modular registry...")
    var instructions_found = 0
    kernel_internal_state["last_opcode_detected"] = "NONE"

    # Iterate through each pixel of the framebuffer.
    # We can optimize this by only scanning relevant regions.
    for y in range(framebuffer_image.get_height()):
        for x in range(framebuffer_image.get_width()):
            var current_pixel_pos = Vector2(x, y)
            var color = framebuffer_image.get_pixel(x, y)
            var opcode_name = interpret_opcode(color)

            if opcode_name != "UNKNOWN_OPCODE":
                instructions_found += 1
                kernel_internal_state["last_opcode_detected"] = opcode_name
                print("  [Opcode] ", opcode_name, " detected at (", x, ", ", y, ")")

                # Handle region-specific interpretation or logging
                if BOOT_CODE_REGION.has_point(current_pixel_pos):
                    print("    (In BOOT_CODE_REGION)")
                elif KERNEL_OUTPUT_REGION.has_point(current_pixel_pos):
                    print("    (In KERNEL_OUTPUT_REGION)")
                elif PROGRAM_MEMORY_REGION.has_point(current_pixel_pos):
                    print("    (In PROGRAM_MEMORY_REGION)")
                elif DEBUG_LOG_REGION.has_point(current_pixel_pos):
                    print("    (In DEBUG_LOG_REGION)")

                # Specific opcode handling (e.g., JUMP_TO_X argument reading)
                if opcode_name == "JUMP_TO_X":
                    if x + 1 < framebuffer_image.get_width():
                        var arg_pixel = framebuffer_image.get_pixel(x + 1, y)
                        var jump_x_val = int(arg_pixel.r * 255.0)
                        print("  [Argument] JUMP_TO_X argument (X=", jump_x_val, ") at (", x + 1, ", ", y, ")")
                    else:
                        print_err("  [Error] JUMP_TO_X at (", x, ", ", y, ") missing argument pixel.")

    if instructions_found == 0:
        print("  No known opcodes detected in the current display state.")
    else:
        print("  Total known opcodes detected: ", instructions_found)


func inject_logic():
    # Override the base class's inject_logic to also respect memory regions.
    # We'll still do the base injection, but can add more nuanced logic here.

    super.inject_logic() # Call base class's injection for its default behavior

    # Example: Inject a new pixel into the KERNEL_OUTPUT_REGION
    if KERNEL_OUTPUT_REGION.size.x > 0 and KERNEL_OUTPUT_REGION.size.y > 0:
        var output_x = KERNEL_OUTPUT_REGION.position.x + (kernel_internal_state["cycle_count"] % KERNEL_OUTPUT_REGION.size.x)
        var output_y = KERNEL_OUTPUT_REGION.position.y
        if output_x < kernel_output_image.get_width() and output_y < kernel_output_image.get_height():
            kernel_output_image.set_pixel(output_x, output_y, Color(randf(), randf(), randf())) # Random color for output
            print("  Injected random pixel into KERNEL_OUTPUT_REGION at (", output_x, ", ", output_y, ")")


# --- Opcode Rewriting and Visual Mutation ---

func mutate_display_based_on_rules():
    # This function embodies the "Reflex" aspect: the kernel actively
    # modifies the display based on its internal rules or observed patterns.

    if not kernel_output_image or not kernel_output_image.is_locked():
        print_err("PXReflexKernel: Kernel output image not available or not locked for mutation.")
        return

    print("PXReflexKernel: Mutating display based on rules...")
    kernel_internal_state["mutation_attempts"] += 1

    # Rule 1: If "HALT" was detected in the last cycle, try to replace it with "PRINT_HELLO"
    if kernel_internal_state["last_opcode_detected"] == "HALT":
        # Find the HALT pixel (assuming it's at (0,0) from bootloader for this example)
        var halt_pos = Vector2(0, 0)
        if BOOT_CODE_REGION.has_point(halt_pos) and \
           halt_pos.x < kernel_output_image.get_width() and \
           halt_pos.y < kernel_output_image.get_height():
            kernel_output_image.set_pixel(halt_pos.x, halt_pos.y, PXL_PRINT_HELLO)
            print("  [Mutation] Replaced HALT at (0,0) with PRINT_HELLO.")
            # Also log this mutation in the debug region
            log_to_debug_region(Color(0.0, 1.0, 0.0)) # Green for "mutation success"

    # Rule 2: Periodically inject a new "MUTATE_REGION" opcode
    if kernel_internal_state["cycle_count"] % 5 == 0: # Every 5 cycles
        var mutate_x = PROGRAM_MEMORY_REGION.position.x + 5
        var mutate_y = PROGRAM_MEMORY_REGION.position.y + 5
        if PROGRAM_MEMORY_REGION.has_point(Vector2(mutate_x, mutate_y)) and \
           mutate_x < kernel_output_image.get_width() and \
           mutate_y < kernel_output_image.get_height():
            kernel_output_image.set_pixel(mutate_x, mutate_y, Color(0.5, 0.0, 0.5)) # MUTATE_REGION color
            print("  [Mutation] Injected MUTATE_REGION opcode at (", mutate_x, ", ", mutate_y, ").")
            log_to_debug_region(Color(0.5, 0.0, 0.5)) # Purple for "mutation injected"

    # After mutations, update the display
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(kernel_output_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXReflexKernel: 'DisplayScreen' TextureRect not found for visual mutation.")


# --- Kernel State Reflection ---

func reflect_kernel_state_visually():
    # This function visually represents the kernel's internal state on the display.
    # For example, by changing a pixel in the DEBUG_LOG_REGION.

    if not kernel_output_image or not kernel_output_image.is_locked():
        print_err("PXReflexKernel: Kernel output image not available for state reflection.")
        return

    print("PXReflexKernel: Reflecting kernel state visually...")

    # Example: Change a pixel in the DEBUG_LOG_REGION based on the last opcode detected.
    var debug_x = DEBUG_LOG_REGION.position.x
    var debug_y = DEBUG_LOG_REGION.position.y + (kernel_internal_state["cycle_count"] % DEBUG_LOG_REGION.size.y)

    if DEBUG_LOG_REGION.has_point(Vector2(debug_x, debug_y)) and \
       debug_x < kernel_output_image.get_width() and \
       debug_y < kernel_output_image.get_height():

        var state_color = Color(0, 0, 0) # Default to black
        match kernel_internal_state["last_opcode_detected"]:
            "HALT": state_color = Color(1.0, 0.0, 0.0) # Red
            "PRINT_HELLO": state_color = Color(0.0, 1.0, 0.0) # Green
            "JUMP_TO_X": state_color = Color(0.0, 0.0, 1.0) # Blue
            "MUTATE_REGION": state_color = Color(0.5, 0.0, 0.5) # Purple
            "LOG_STATE": state_color = Color(0.0, 0.5, 0.5) # Teal
            _: state_color = Color(0.5, 0.5, 0.5) # Grey for other/none

        kernel_output_image.set_pixel(debug_x, debug_y, state_color)
        print("  Reflected last opcode '", kernel_internal_state["last_opcode_detected"], "' as color ", state_color, " at (", debug_x, ", ", debug_y, ") in debug log.")

    # After reflection, update the display
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(kernel_output_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXReflexKernel: 'DisplayScreen' TextureRect not found for visual state reflection.")

func log_to_debug_region(color_to_log: Color):
    # A helper function to write a specific color into the debug log region.
    # This simulates the kernel writing a log entry.
    if not kernel_output_image or not kernel_output_image.is_locked():
        print_err("PXReflexKernel: Kernel output image not available for debug logging.")
        return

    var debug_x = DEBUG_LOG_REGION.position.x
    # Advance the Y position in the debug log region for new entries
    var debug_y = DEBUG_LOG_REGION.position.y + (kernel_internal_state["mutation_attempts"] % DEBUG_LOG_REGION.size.y)

    if DEBUG_LOG_REGION.has_point(Vector2(debug_x, debug_y)) and \
       debug_x < kernel_output_image.get_width() and \
       debug_y < kernel_output_image.get_height():
        kernel_output_image.set_pixel(debug_x, debug_y, color_to_log)
        print("  Logged color ", color_to_log, " to debug region at (", debug_x, ", ", debug_y, ").")


# --- Cleanup ---
func _exit_tree():
    # Ensure base class cleanup is also called.
    super._exit_tree()
