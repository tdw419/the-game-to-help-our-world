# PXVM.gd - UPDATED

extends Node
signal vm_output(text)

var shell_callback := null
var file_system := null
var variables := {}
var program_counter := 0
var instructions := []

func execute(app: Dictionary) -> void:
	if not app.has("instructions"):
		emit_signal("vm_output", "Error: No instructions to execute.")
		return

	instructions = app["instructions"]
	program_counter = 0
	variables = {} # Reset variables for each new execution
	variables["_LAST_RESULT"] = "" # Initialize internal variable

	while program_counter < instructions.size():
		var instr = instructions[program_counter]
		var opcode = instr.get("opcode", "")
		var args = instr.get("args", [])

		var next_pc = program_counter + 1 # Default next instruction

		match opcode:
			"PRINT":
				var msg = args[0]
				# Substitute variables in the message
				if msg.find("$") != -1:
					for key in variables.keys():
						msg = msg.replace("$" + key, str(_get_variable_value(key)))
					msg = msg.replace("$_LAST_RESULT", str(_get_variable_value("_LAST_RESULT")))
				emit_signal("vm_output", msg)
			"SHELL_COMMAND":
				if shell_callback and shell_callback.is_valid():
					emit_signal("vm_output", "[Shell]: " + args[0])
					shell_callback.call_func(args[0])
				else:
					emit_signal("vm_output", "Error: Shell callback not set.")
			"SET_VAR":
				variables[args[0]] = _resolve_arg_value(args[1]) # Resolve value if it's a variable name
			"READ_FILE":
				var path = args[0]
				var file_entry = _pxfs_get_file_content(path) # Helper to get content, not full dict
				if file_entry != null:
					variables["_LAST_RESULT"] = file_entry
				else:
					variables["_LAST_RESULT"] = "[ERR] File not found or empty."
			"ADD", "SUB", "MUL", "DIV":
				if args.size() == 3:
					var val1 = _get_variable_value(args[0])
					var val2 = _get_variable_value(args[1])
					var result_var_name = args[2]

					if typeof(val1) in [TYPE_INT, TYPE_REAL] and typeof(val2) in [TYPE_INT, TYPE_REAL]:
						var result
						match opcode:
							"ADD": result = val1 + val2
							"SUB": result = val1 - val2
							"MUL": result = val1 * val2
							"DIV":
								if val2 != 0:
									result = val1 / val2
								else:
									emit_signal("vm_output", "Error: Division by zero.")
									result = 0 # Or some error state
						variables[result_var_name] = result
					else:
						emit_signal("vm_output", "Error: Arithmetic on non-numeric variables.")
				else:
					emit_signal("vm_output", "Error: Invalid arithmetic args for " + opcode)
			"JUMP":
				var target_index = args[0]
				if target_index >= 0 and target_index < instructions.size():
					next_pc = target_index
				else:
					emit_signal("vm_output", "Error: Invalid jump target.")
					break # Halt on invalid jump
			"JUMP_IF":
				if args.size() == 4:
					var var1_name = args[0]
					var op = args[1]
					var var2_val_raw = args[2] # Can be a variable name or literal
					var target_index = args[3]

					var val1 = _get_variable_value(var1_name)
					var val2 = _resolve_arg_value(var2_val_raw)

					var condition_met = false
					match op:
						"==": condition_met = (val1 == val2)
						"!=": condition_met = (val1 != val2)
						">":  condition_met = (val1 > val2)
						"<":  condition_met = (val1 < val2)
						">=": condition_met = (val1 >= val2)
						"<=": condition_met = (val1 <= val2)
						_:
							emit_signal("vm_output", "Error: Unknown comparison operator: " + op)

					if condition_met:
						if target_index >= 0 and target_index < instructions.size():
							next_pc = target_index
						else:
							emit_signal("vm_output", "Error: Invalid conditional jump target.")
							break
				else:
					emit_signal("vm_output", "Error: Invalid JUMP_IF syntax.")
			"HALT":
				emit_signal("vm_output", "Execution halted.")
				return # Use return to completely stop execution
			_:
				emit_signal("vm_output", "[?] Unknown opcode: " + opcode)
		
		program_counter = next_pc # Update PC for next loop iteration

func _get_variable_value(var_name: String):
	if variables.has(var_name):
		return variables[var_name]
	else:
		# Attempt to treat it as a literal number if it looks like one
		if var_name.is_valid_integer() or (var_name.is_valid_float() and var_name.find(".") != -1):
			return float(var_name) if var_name.find(".") != -1 else int(var_name)
		return null # Or empty string, or raise error

func _resolve_arg_value(arg_raw):
	# If it starts with '$', treat it as a variable name and get its value
	if typeof(arg_raw) == TYPE_STRING and arg_raw.begins_with("$"):
		var_name = arg_raw.substr(1)
		return _get_variable_value(var_name)
	# Otherwise, treat as literal (could be string, int, float)
	# Attempt to convert to int/float if numerical string
	if typeof(arg_raw) == TYPE_STRING:
		if arg_raw.is_valid_integer() or (arg_raw.is_valid_float() and arg_raw.find(".") != -1):
			return float(arg_raw) if arg_raw.find(".") != -1 else int(arg_raw)
	return arg_raw

# Helper function to abstract file system access within PXVM
func _pxfs_get_file_content(path: String):
    # This requires PXVM to have a reference to PXOSUIScreen's _pxfs_resolve_parent_and_key
    # For now, it will use file_system, which should be the root of pxram_fs
    var parts = path.split("/")
    var current_node = file_system # Start from the root of pxram_fs

    for i in range(parts.size()):
        var part = parts[i]
        if part.empty(): continue # Skip initial empty part from /root/path

        if current_node is Dictionary and current_node.has(part):
            current_node = current_node[part]
        else:
            return null # Path not found

    # If it's a file dictionary, return its content
    if current_node is Dictionary and current_node.has("content"):
        return current_node["content"]
    elif current_node is String or current_node is Image: # Raw content
        return current_node
    
    return null # It's a directory or empty