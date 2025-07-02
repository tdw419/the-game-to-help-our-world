# PXTalkVM.gd
# This module acts as the core PXTalk Virtual Machine.
# It interprets and executes PXTalk instructions from .pxtalk files,
# managing simulated memory, logs, and now, visual output to a framebuffer.

extends Node

# --- Configuration ---
@export var default_memory_size: int = 256 # Conceptual memory size in key-value pairs or bytes
@export var instruction_delay_ms: int = 10 # Delay between PXTalk instruction execution for visualization
@export var framebuffer_font_size: int = 8 # Font size for text rendered on framebuffer
@export var framebuffer_line_height: int = 10 # Line height for text rendered on framebuffer

# --- Dependencies ---
@onready var px_fs_reader: PXFsReader = get_node_or_null("../PXFsReader") # To read .pxtalk files
@onready var px_log_terminal: PXLogTerminal = get_node_or_null("../PXLogTerminal") # For PX_LOG output
@onready var px_framebuffer: PXFramebuffer = get_node_or_null("../PXFramebuffer") # For PX_PRINT_STR visual output
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For internal VM logging

# UI Input Field (conceptual, needs to be connected in scene)
@onready var px_terminal_input_field: LineEdit = get_node_or_null("../PXOS_UI/TerminalInputField") # Adjust path as needed

# Signals for PXRuntime or other modules to react to VM state
signal vm_halted(reason: String)
signal vm_ready_for_input() # Emitted when PX_READ_INPUT is encountered

# --- Internal State ---
var _simulated_memory: Dictionary = {} # Simple key-value memory for PXTalk state
var _registers: Dictionary = {} # Conceptual registers (R0, R1, etc.)
var _call_stack: Array = [] # For function/module calls
var _current_module_name: String = ""
var _current_function_name: String = ""
var _current_instructions: Array = []
var _instruction_pointer: int = 0
var _is_running: bool = false
var _waiting_for_input: bool = false
var _input_buffer: String = ""
var _last_instruction_time := 0.0

# Framebuffer text cursor position
var _framebuffer_cursor_x: int = 0
var _framebuffer_cursor_y: int = 0

# --- Godot Lifecycle ---
func _ready():
    _log("PXTalkVM: Initializing.")
    _reset_vm_state()
    
    # Connect input field signal if available
    if px_terminal_input_field:
        px_terminal_input_field.text_submitted.connect(Callable(self, "_on_terminal_input_submitted"))
        _log("PXTalkVM: Connected to terminal input field.")
    else:
        _log("PXTalkVM: Warning: TerminalInputField not found. PX_READ_INPUT will be non-interactive.")

# --- Public API ---

func boot_pxboot_file(boot_file_path: String):
    """
    Initiates the PXTalk VM boot sequence from a .pxboot file.
    """
    if _is_running:
        _log("PXTalkVM: Error: VM is already running. Cannot boot.")
        return

    _reset_vm_state()
    _is_running = true
    _log("PXTalkVM: Starting boot from " + boot_file_path)

    var boot_content = px_fs_reader.read_file_by_name(boot_file_path)
    if boot_content.is_empty():
        _log("PXTalkVM: Error: Failed to read boot.pxboot file.")
        _halt_vm("BOOT_FILE_READ_ERROR")
        return

    # Clear framebuffer at boot
    if px_framebuffer and px_framebuffer.is_initialized:
        px_framebuffer.framebuffer_image.fill(Color.BLACK)
        px_framebuffer.update()
        _framebuffer_cursor_x = 0
        _framebuffer_cursor_y = 0
        _log("PXTalkVM: Framebuffer cleared for boot.")


    # Start execution by calling the interpreter's INIT function
    _log("PXTalkVM: Loading pxbios_interpreter.pxtalk...")
    var interpreter_content = px_fs_reader.read_file_by_name("pxdisk/pxbios_interpreter.pxtalk")
    if interpreter_content.is_empty():
        _log("PXTalkVM: Error: pxbios_interpreter.pxtalk not found.")
        _halt_vm("BIOS_INTERPRETER_MISSING")
        return
    _execute_pxtalk_function(interpreter_content, "BIOS_INTERPRETER", "INIT")
    _log("PXTalkVM: Boot sequence initiated.")

func submit_input(input_text: String):
    """
    Submits user input to the VM when it's waiting for PX_READ_INPUT.
    """
    if _waiting_for_input:
        _input_buffer = input_text
        _waiting_for_input = false
        _log("PXTalkVM: Input received: " + input_text)
        # Resume execution after input
        _process_next_instruction()
    else:
        _log("PXTalkVM: Warning: Input submitted but VM not waiting for input.")

func is_running() -> bool:
    return _is_running

# --- Internal VM Execution Loop ---

func _process(delta: float):
    """
    Godot's process loop, used to drive PXTalk instruction execution.
    """
    if not _is_running or _waiting_for_input:
        return

    # Simulate instruction execution delay
    if OS.get_ticks_msec() - _last_instruction_time < instruction_delay_ms:
        return
    _last_instruction_time = OS.get_ticks_msec()

    _process_next_instruction()

func _process_next_instruction():
    """
    Executes the next instruction in the current function.
    """
    if _instruction_pointer >= _current_instructions.size():
        _log("PXTalkVM: End of function. Returning from call stack.")
        _return_from_call()
        return

    var instruction_line = _current_instructions[_instruction_pointer]
    _instruction_pointer += 1 # Advance IP immediately

    var parts = instruction_line.split(" ", false)
    var command = parts[0]
    var args = parts.slice(1)

    match command:
        "PX_LOG":
            _handle_px_log(args)
        "PX_PRINT_STR":
            _handle_px_print_str(args)
        "PX_HALT":
            _handle_px_halt(args)
        "PX_INIT_REGISTERS":
            _handle_px_init_registers()
        "PX_SET_MEM_PTR":
            _handle_px_set_mem_ptr(args)
        "PX_CLEAR_SCREEN":
            _handle_px_clear_screen(args)
        "PX_LOAD_FILE":
            _handle_px_load_file(args)
        "PX_CALL_MODULE":
            _handle_px_call_module(args)
        "PX_CALL_FUNCTION":
            _handle_px_call_function(args)
        "PX_GET_ARG":
            _handle_px_get_arg(args)
        "PX_SET_VAR":
            _handle_px_set_var(args)
        "PX_READ_MEM":
            _handle_px_read_mem(args)
        "PX_IF_EQ":
            _handle_px_if_eq(args)
        "PX_ELSE":
            _handle_px_else()
        "PX_ELSE_IF_STARTS_WITH":
            _handle_px_else_if_starts_with(args)
        "PX_LOOP":
            _handle_px_loop()
        "PX_BREAK_LOOP":
            _handle_px_break_loop()
        "PX_READ_INPUT":
            _handle_px_read_input(args)
        "PX_GET_SUBSTRING":
            _handle_px_get_substring(args)
        "PX_READ_MEM_RANGE":
            _handle_px_read_mem_range(args)
        "PX_GET_MEM_STATE":
            _handle_px_get_mem_state(args)
        "PX_SET_MEM_STATE":
            _handle_px_set_mem_state(args)
        "PX_RETURN":
            _return_from_call()
        "PX_JUMP":
            _handle_px_jump(args)
        "PX_SPLIT_STRING":
            _handle_px_split_string(args)
        "PX_READ_ISO_PVD":
            _handle_px_read_iso_pvd(args)
        "PX_SCAN_ISO_DIR": # NEW: Handle PX_SCAN_ISO_DIR
            _handle_px_scan_iso_dir(args)
        _:
            _log("PXTalkVM: Unknown instruction: " + instruction_line)
            _halt_vm("UNKNOWN_INSTRUCTION")

func _execute_pxtalk_function(pxtalk_content: String, module_name: String, function_name: String, args: Array = []):
    """
    Parses PXTalk content, finds the specified function, and pushes it to the call stack.
    """
    var lines = pxtalk_content.split("\n")
    var function_start_line = -1
    var function_end_line = -1
    var current_line_num = 0

    for line in lines:
        var trimmed_line = line.strip_edges()
        if trimmed_line.begins_with("PX_FUNCTION " + function_name + ":"):
            function_start_line = current_line_num + 1 # Instructions start on the next line
        elif function_start_line != -1 and trimmed_line.begins_with("PX_FUNCTION"):
            function_end_line = current_line_num - 1
            break
        current_line_num += 1
    
    if function_start_line == -1:
        _log("PXTalkVM: Error: Function '%s' not found in module '%s'." % [function_name, module_name])
        _halt_vm("FUNCTION_NOT_FOUND")
        return

    if function_end_line == -1: # Function goes to end of file
        function_end_line = lines.size() - 1

    var function_instructions = lines.slice(function_start_line, function_end_line + 1)
    
    # Push current state to call stack
    _call_stack.append({
        "module": _current_module_name,
        "function": _current_function_name,
        "instructions": _current_instructions,
        "instruction_pointer": _instruction_pointer,
        "registers": _registers.duplicate(), # Save registers for context
        "args": args # Arguments for the new function
    })

    _current_module_name = module_name
    _current_function_name = function_name
    _current_instructions = function_instructions.filter(func(line): return not line.strip_edges().is_empty() and not line.strip_edges().begins_with("#"))
    _instruction_pointer = 0
    _registers.clear() # Clear registers for new function context (or pass/manage them)
    _log("PXTalkVM: Calling function '%s' in module '%s'." % [function_name, module_name])

func _return_from_call():
    """
    Pops the last state from the call stack and resumes execution.
    """
    if _call_stack.is_empty():
        _log("PXTalkVM: Call stack is empty. Halting VM.")
        _halt_vm("CALL_STACK_EMPTY")
        return

    var previous_state = _call_stack.pop_back()
    _current_module_name = previous_state.module
    _current_function_name = previous_state.function
    _current_instructions = previous_state.instructions
    _instruction_pointer = previous_state.instruction_pointer
    _registers = previous_state.registers # Restore registers
    _log("PXTalkVM: Returning from function '%s' to '%s'." % [previous_state.function, _current_function_name])
    
    # Immediately process the next instruction in the resumed context
    _process_next_instruction()

func _halt_vm(reason: String):
    """Halts the VM execution."""
    _is_running = false
    _waiting_for_input = false
    _log("PXTalkVM: Halted. Reason: " + reason)
    emit_signal("vm_halted", reason)

func _reset_vm_state():
    """Resets all VM internal state variables."""
    _simulated_memory.clear()
    _registers.clear()
    _call_stack.clear()
    _current_module_name = ""
    _current_function_name = ""
    _current_instructions.clear()
    _instruction_pointer = 0
    _is_running = false
    _waiting_for_input = false
    _input_buffer = ""
    _last_instruction_time = 0.0
    _framebuffer_cursor_x = 0
    _framebuffer_cursor_y = 0

# --- PXTalk Instruction Handlers ---

func _handle_px_log(args: Array):
    var message = _resolve_args_to_string(args)
    _log("PX_LOG: " + message)

func _handle_px_print_str(args: Array):
    var message = _resolve_args_to_string(args).replace("\"", "") # Remove quotes
    if px_framebuffer and px_framebuffer.is_initialized:
        # Render text on framebuffer
        var font = px_framebuffer.get_font(framebuffer_font_size) # Conceptual: PXFramebuffer provides font
        var color = Color.LIME_GREEN # Default text color
        
        # Draw string on framebuffer image
        px_framebuffer.draw_string_on_image(message, Vector2(_framebuffer_cursor_x, _framebuffer_cursor_y), font, color)
        px_framebuffer.update() # Update the texture rect
        
        # Advance cursor
        _framebuffer_cursor_y += framebuffer_line_height
        if _framebuffer_cursor_y >= px_framebuffer.framebuffer_height:
            # Simple scroll: clear screen and reset cursor if end of screen
            px_framebuffer.framebuffer_image.fill(Color.BLACK)
            _framebuffer_cursor_y = 0
        
        _log("PX_PRINT_STR (Framebuffer): " + message)
    
    # Also log to terminal for text-based output
    if px_log_terminal:
        px_log_terminal.add_line(message, "PXTERM", Color.LIME_GREEN, true)
    else:
        _log("PX_PRINT_STR: " + message)

func _handle_px_halt(args: Array):
    var reason = _resolve_args_to_string(args) if not args.is_empty() else "GENERIC_HALT"
    _halt_vm(reason)

func _handle_px_init_registers():
    _registers.clear()
    _registers["R0"] = null
    _registers["R1"] = null
    _log("PXTalkVM: Registers initialized.")

func _handle_px_set_mem_ptr(args: Array):
    if args.size() == 1:
        var address = _resolve_arg(args[0])
        _simulated_memory["MEM_PTR"] = address
        _log("PXTalkVM: Memory pointer set to: " + str(address))
    else:
        _log("PXTalkVM: Error: PX_SET_MEM_PTR requires 1 argument (address).")

func _handle_px_clear_screen(args: Array):
    if args.size() == 1:
        var color_hex = _resolve_arg(args[0])
        if px_framebuffer and px_framebuffer.is_initialized:
            px_framebuffer.framebuffer_image.fill(Color.from_html(color_hex))
            px_framebuffer.update()
            _framebuffer_cursor_x = 0
            _framebuffer_cursor_y = 0
            _log("PXTalkVM: Framebuffer cleared with color: " + str(color_hex))
        else:
            _log("PXTalkVM: Error: PXFramebuffer not available or initialized for CLEAR_SCREEN.")
    else:
        _log("PXTalkVM: Error: PX_CLEAR_SCREEN requires 1 argument (color_hex).")

func _handle_px_load_file(args: Array):
    if args.size() >= 2 and args[1] == "AS_MODULE":
        var file_path = _resolve_arg(args[0])
        var module_name = _resolve_arg(args[2])
        _simulated_memory["LOADED_MODULE_" + module_name] = file_path
        _log("PXTalkVM: Simulating LOAD_FILE '%s' AS_MODULE '%s'." % [file_path, module_name])
    else:
        _log("PXTalkVM: Error: PX_LOAD_FILE AS_MODULE requires file_path and module_name.")

func _handle_px_call_module(args: Array):
    if args.size() == 2:
        var module_name = _resolve_arg(args[0])
        var function_name = _resolve_arg(args[1])
        var module_path = _simulated_memory.get("LOADED_MODULE_" + module_name)
        if module_path:
            var module_content = px_fs_reader.read_file_by_name(module_path)
            if not module_content.is_empty():
                _execute_pxtalk_function(module_content, module_name, function_name)
            else:
                _log("PXTalkVM: Error: Module content for '%s' not found." % module_name)
                _halt_vm("MODULE_CONTENT_MISSING")
        else:
            _log("PXTalkVM: Error: Module '%s' not loaded." % module_name)
            _halt_vm("MODULE_NOT_LOADED")
    else:
        _log("PXTalkVM: Error: PX_CALL_MODULE requires module_name and function_name.")

func _handle_px_call_function(args: Array):
    if args.size() >= 1:
        var function_name = _resolve_arg(args[0])
        var function_args = args.slice(1)
        _execute_pxtalk_function(_get_current_module_content(), _current_module_name, function_name, function_args)
    else:
        _log("PXTalkVM: Error: PX_CALL_FUNCTION requires function_name.")

func _handle_px_get_arg(args: Array):
    if args.size() == 2:
        var arg_index = int(_resolve_arg(args[0]))
        var target_register = _resolve_arg(args[1])
        if _call_stack.is_empty():
            _log("PXTalkVM: Error: PX_GET_ARG called outside function context.")
            _registers[target_register] = null
            return

        var current_function_call_state = _call_stack.back()
        var function_args = current_function_call_state.get("args", [])
        
        if arg_index < function_args.size():
            _registers[target_register] = _resolve_arg(function_args[arg_index])
            _log("PXTalkVM: PX_GET_ARG: Arg %d -> %s = %s" % [arg_index, target_register, str(_registers[target_register])])
        else:
            _log("PXTalkVM: Warning: PX_GET_ARG: Argument index %d out of bounds." % arg_index)
            _registers[target_register] = null
    else:
        _log("PXTalkVM: Error: PX_GET_ARG requires arg_index and target_register.")

func _handle_px_set_var(args: Array):
    if args.size() == 2:
        var var_name = _resolve_arg(args[0])
        var value = _resolve_arg(args[1])
        _registers[var_name] = value
        _log("PXTalkVM: PX_SET_VAR: %s = %s" % [var_name, str(value)])
    else:
        _log("PXTalkVM: Error: PX_SET_VAR requires var_name and value.")

func _handle_px_read_mem(args: Array):
    if args.size() == 2:
        var address = _resolve_arg(args[0])
        var target_register = _resolve_arg(args[1])
        _registers[target_register] = _simulated_memory.get(str(address), null)
        _log("PXTalkVM: PX_READ_MEM: Addr %s -> %s = %s" % [str(address), target_register, str(_registers[target_register])])
    else:
        _log("PXTalkVM: Error: PX_READ_MEM requires address and target_register.")

func _handle_px_if_eq(args: Array):
    if args.size() == 3:
        var val1 = _resolve_arg(args[0])
        var val2 = _resolve_arg(args[1])
        var jump_target_label = args[2]
        
        if val1 == val2:
            _log("PXTalkVM: PX_IF_EQ: %s == %s is TRUE. Jumping to %s." % [str(val1), str(val2), jump_target_label])
            _jump_to_label(jump_target_label)
        else:
            _log("PXTalkVM: PX_IF_EQ: %s == %s is FALSE. Continuing." % [str(val1), str(val2)])
    else:
        _log("PXTalkVM: Error: PX_IF_EQ requires 3 arguments (val1, val2, label).")

func _handle_px_else():
    _log("PXTalkVM: PX_ELSE encountered. Executing else block.")
    pass

func _handle_px_else_if_starts_with(args: Array):
    if args.size() == 3:
        var string_var = _resolve_arg(args[0])
        var prefix_val = _resolve_arg(args[1])
        var jump_target_label = args[2]
        
        if typeof(string_var) == TYPE_STRING and string_var.begins_with(prefix_val):
            _log("PXTalkVM: PX_ELSE_IF_STARTS_WITH: '%s' starts with '%s' is TRUE. Jumping to %s." % [string_var, prefix_val, jump_target_label])
            _jump_to_label(jump_target_label)
        else:
            _log("PXTalkVM: PX_ELSE_IF_STARTS_WITH: '%s' does not start with '%s'. Continuing." % [string_var, prefix_val])
    else:
        _log("PXTalkVM: Error: PX_ELSE_IF_STARTS_WITH requires 3 arguments (string_var, prefix, label).")

func _handle_px_loop():
    _call_stack.back()["loop_start_ip"] = _instruction_pointer - 1
    _log("PXTalkVM: PX_LOOP entered. Loop start IP: " + str(_instruction_pointer - 1))

func _handle_px_break_loop():
    var loop_start_ip = -1
    var loop_stack_index = -1
    for i in range(_call_stack.size() - 1, -1, -1):
        if _call_stack[i].has("loop_start_ip"):
            loop_start_ip = _call_stack[i]["loop_start_ip"]
            loop_stack_index = i
            break
    
    if loop_start_ip != -1:
        var loop_end_ip = _find_loop_end_ip(loop_start_ip)
        if loop_end_ip != -1:
            _instruction_pointer = loop_end_ip + 1
            _log("PXTalkVM: PX_BREAK_LOOP executed. Jumping past loop end to IP: " + str(_instruction_pointer))
        else:
            _log("PXTalkVM: Error: Could not find end of loop for PX_BREAK_LOOP.")
            _halt_vm("LOOP_END_NOT_FOUND")
    else:
        _log("PXTalkVM: Error: PX_BREAK_LOOP called outside of a loop.")
        _halt_vm("BREAK_OUTSIDE_LOOP")

func _find_loop_end_ip(loop_start_ip: int) -> int:
    var current_depth = 0
    for i in range(loop_start_ip, _current_instructions.size()):
        var instruction = _current_instructions[i].strip_edges()
        if instruction == "PX_LOOP":
            current_depth += 1
        # Assuming loops are terminated by PX_RETURN for now, or explicit end-loop instruction
        elif instruction == "PX_RETURN":
            if current_depth == 1: # If it's the return of the current loop's function
                return i
            # else if we had PX_END_LOOP, we'd check current_depth == 0 for that.
    return _current_instructions.size() - 1 # Assume loop goes to end of function if no explicit end

func _handle_px_read_input(args: Array):
    if args.size() == 2 && args[0] == "->":
        var target_register = _resolve_arg(args[1])
        _log("PXTalkVM: Waiting for user input for register: " + target_register)
        _waiting_for_input = true
        emit_signal("vm_ready_for_input") # Signal UI to enable input
        
        # Enable the LineEdit for input
        if px_terminal_input_field:
            px_terminal_input_field.editable = true
            px_terminal_input_field.grab_focus()
            px_log_terminal.add_line("Input enabled.", "PXTERM", Color.YELLOW, true)
        
        # Pause execution until input is received via submit_input()
        # The _process loop will return until _waiting_for_input is false.
        _registers[target_register] = _input_buffer # Store received input
        _input_buffer = "" # Clear buffer
    else:
        _log("PXTalkVM: Error: PX_READ_INPUT requires '-> TARGET_REGISTER'.")
        _halt_vm("INVALID_READ_INPUT_SYNTAX")

func _handle_px_get_substring(args: Array):
    if args.size() == 3 && args[1] == "->":
        var source_string = _resolve_arg(args[0])
        var start_index = int(_resolve_arg(args[2]))
        var target_register = _resolve_arg(args[3]) # Assuming 4 args: source, ->, index, target
        
        if typeof(source_string) == TYPE_STRING and start_index >= 0 and start_index < source_string.length():
            _registers[target_register] = source_string.substr(start_index)
            _log("PXTalkVM: PX_GET_SUBSTRING: '%s' from %d -> %s = '%s'" % [source_string, start_index, target_register, _registers[target_register]])
        else:
            _log("PXTalkVM: Error: PX_GET_SUBSTRING invalid arguments or string.")
            _registers[target_register] = null
    elif args.size() == 4 && args[1] == "->":
        var source_string = _resolve_arg(args[0])
        var start_index = int(_resolve_arg(args[2]))
        var length = int(_resolve_arg(args[3]))
        var target_register = _resolve_arg(args[4]) # Assuming 5 args: source, ->, start, length, target

        if typeof(source_string) == TYPE_STRING and start_index >= 0 and length >= 0 and (start_index + length) <= source_string.length():
            _registers[target_register] = source_string.substr(start_index, length)
            _log("PXTalkVM: PX_GET_SUBSTRING: '%s' from %d len %d -> %s = '%s'" % [source_string, start_index, length, target_register, _registers[target_register]])
        else:
            _log("PXTalkVM: Error: PX_GET_SUBSTRING invalid arguments or string.")
            _registers[target_register] = null
    else:
        _log("PXTalkVM: Error: PX_GET_SUBSTRING requires source_string, start_index, [length], ->, target_register.")

func _handle_px_read_mem_range(args: Array):
    if args.size() == 3 && args[2] == "->":
        var start_addr = _resolve_arg(args[0])
        var end_addr = _resolve_arg(args[1])
        var target_register = _resolve_arg(args[3])
        
        var dump_str = ""
        if typeof(start_addr) == TYPE_INT and typeof(end_addr) == TYPE_INT and start_addr <= end_addr:
            for i in range(start_addr, end_addr + 1):
                var val = _simulated_memory.get(str(i), "00") # Default to "00" if not set
                dump_str += str(val) + " "
            _registers[target_register] = dump_str.strip_edges()
            _log("PXTalkVM: PX_READ_MEM_RANGE: %s-%s -> %s = '%s'" % [str(start_addr), str(end_addr), target_register, _registers[target_register]])
        else:
            _log("PXTalkVM: Error: PX_READ_MEM_RANGE invalid address range.")
            _registers[target_register] = null
    else:
        _log("PXTalkVM: Error: PX_READ_MEM_RANGE requires start_addr, end_addr, ->, target_register.")

func _handle_px_get_mem_state(args: Array):
    if args.size() == 2 && args[1] == "->":
        var key = _resolve_arg(args[0])
        var target_register = _resolve_arg(args[2])
        _registers[target_register] = _simulated_memory.get(key, null)
        _log("PXTalkVM: PX_GET_MEM_STATE: Key '%s' -> %s = %s" % [key, target_register, str(_registers[target_register])])
    else:
        _log("PXTalkVM: Error: PX_GET_MEM_STATE requires key, ->, target_register.")

func _handle_px_set_mem_state(args: Array):
    if args.size() == 2:
        var key = _resolve_arg(args[0])
        var value = _resolve_arg(args[1])
        _simulated_memory[key] = value
        _log("PXTalkVM: PX_SET_MEM_STATE: '%s' = '%s'" % [key, value])
    else:
        _log("PXTalkVM: Error: PX_SET_MEM_STATE requires key and value.")

func _handle_px_jump(args: Array):
    if args.size() == 1:
        var jump_target_label = args[0]
        _jump_to_label(jump_target_label)
    else:
        _log("PXTalkVM: Error: PX_JUMP requires 1 argument (label).")

func _handle_px_split_string(args: Array):
    if args.size() == 4 && args[2] == "->":
        var source_string = _resolve_arg(args[0])
        var delimiter = _resolve_arg(args[1])
        var target_register = _resolve_arg(args[3])
        
        if typeof(source_string) == TYPE_STRING and typeof(delimiter) == TYPE_STRING:
            _registers[target_register] = source_string.split(delimiter, false)
            _log("PXTalkVM: PX_SPLIT_STRING: '%s' by '%s' -> %s = %s" % [source_string, delimiter, target_register, str(_registers[target_register])])
        else:
            _log("PXTalkVM: Error: PX_SPLIT_STRING invalid arguments or types.")
            _registers[target_register] = null
    else:
        _log("PXTalkVM: Error: PX_SPLIT_STRING requires source_string, delimiter, ->, target_register.")

func _handle_px_read_iso_pvd(args: Array):
    if args.size() == 3 && args[1] == "TO=":
        var iso_path = _resolve_arg(args[0])
        var target_memory_key = _resolve_arg(args[2])
        
        # Conceptual: In a real scenario, you'd read the actual ISO file
        # and parse its PVD structure (e.g., at sector 16, offset 32768).
        # For this simulation, we'll return a dummy PVD signature.
        
        _log("PXTalkVM: Simulating PX_READ_ISO_PVD for '%s'." % iso_path)
        
        # Dummy PVD data (first few bytes of a PVD should be "CD001")
        var dummy_pvd_signature = "CD001" 
        
        _simulated_memory[target_memory_key] = dummy_pvd_signature
        _log("PXTalkVM: Simulated PVD signature '%s' stored in '%s'." % [dummy_pvd_signature, target_memory_key])
    else:
        _log("PXTalkVM: Error: PX_READ_ISO_PVD requires iso_path TO= target_memory_key.")
        _halt_vm("INVALID_READ_ISO_PVD_SYNTAX")

func _handle_px_scan_iso_dir(args: Array): # NEW: PX_SCAN_ISO_DIR handler
    if args.size() == 4 && args[2] == "FOR":
        var pvd_memory_key = _resolve_arg(args[0])
        var search_filename = _resolve_arg(args[3])
        var target_offset_register = _resolve_arg(args[4]) # Assuming 5 args: pvd_key, FOR, filename, TO=, register

        _log("PXTalkVM: Simulating PX_SCAN_ISO_DIR for '%s' in PVD '%s'." % [search_filename, pvd_memory_key])
        
        # Conceptual: In a real scenario, you'd parse the ISO directory records
        # from the PVD data in memory and find the actual offset.
        # For this simulation, we'll return a dummy offset if "vmlinuz" is searched.
        
        if search_filename == "vmlinuz":
            var dummy_kernel_offset = 1048576 # Example offset (1MB)
            _registers[target_offset_register] = dummy_kernel_offset
            _log("PXTalkVM: Simulated PX_SCAN_ISO_DIR found '%s' at offset %d." % [search_filename, dummy_kernel_offset])
        else:
            _registers[target_offset_register] = null
            _log("PXTalkVM: Simulated PX_SCAN_ISO_DIR did not find '%s'." % search_filename)
    else:
        _log("PXTalkVM: Error: PX_SCAN_ISO_DIR requires pvd_memory_key FOR filename TO= target_register.")
        _halt_vm("INVALID_SCAN_ISO_DIR_SYNTAX")

# --- Helper Functions ---

func _resolve_arg(arg_str: String):
    """
    Resolves an argument string to its actual value (register, literal, memory).
    Handles string literals (e.g., "hello"), integer literals (e.g., 0x7C00, 123),
    and register names (e.g., R0, USER_INPUT).
    """
    # Check if it's a string literal (starts and ends with quotes)
    if arg_str.begins_with("\"") and arg_str.ends_with("\""):
        return arg_str.strip_edges().replace("\"", "")
    
    # Check if it's an integer literal (hex or decimal)
    if arg_str.begins_with("0x"):
        return int(arg_str, 16)
    if arg_str.is_valid_int():
        return int(arg_str)

    # Assume it's a register name or variable
    if _registers.has(arg_str):
        return _registers[arg_str]
    
    # If not found, treat as literal string or null
    _log("PXTalkVM: Warning: Unresolved argument '%s'. Treating as literal string or null." % arg_str)
    return arg_str # Return as is, or null, depending on desired strictness

func _resolve_args_to_string(args: Array) -> String:
    """Helper to resolve an array of arguments into a single string."""
    var resolved_parts = []
    for arg in args:
        resolved_parts.append(str(_resolve_arg(arg)))
    return " ".join(resolved_parts)

func _jump_to_label(label_name: String):
    """
    Finds the instruction pointer for a given label and sets _instruction_pointer.
    Labels are assumed to be lines like 'LABEL_NAME:'
    """
    var target_ip = -1
    for i in range(_current_instructions.size()):
        if _current_instructions[i].strip_edges() == label_name + ":":
            target_ip = i
            break
    
    if target_ip != -1:
        _instruction_pointer = target_ip
        _log("PXTalkVM: Jumped to label '%s' at IP %d." % [label_name, _instruction_pointer])
    else:
        _log("PXTalkVM: Error: Label '%s' not found for jump." % label_name)
        _halt_vm("LABEL_NOT_FOUND")

func _get_current_module_content() -> String:
    """
    Retrieves the raw content of the currently executing module.
    Needed for PX_CALL_FUNCTION to call functions within the same module.
    """
    var module_path = _simulated_memory.get("LOADED_MODULE_" + _current_module_name)
    if module_path:
        return px_fs_reader.read_file_by_name(module_path)
    _log("PXTalkVM: Error: Could not get content for current module '%s'." % _current_module_name)
    return ""

# --- Event Handlers for UI Input ---

func _on_terminal_input_submitted(text: String):
    """
    Callback for when user submits text in the terminal input field.
    """
    if _waiting_for_input:
        submit_input(text)
        if px_terminal_input_field:
            px_terminal_input_field.text = "" # Clear input field after submission
            px_terminal_input_field.editable = false # Disable until next PX_READ_INPUT
    else:
        _log("PXTalkVM: Input submitted but VM not waiting. Text: " + text)

# --- Logging ---

func _log(message: String):
    """
    Helper function for internal VM logging.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXTalkVM: " + message)
    else:
        print("PXTalkVM (Console Log): ", message)

