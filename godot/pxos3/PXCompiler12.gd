# PXCompiler.gd - UPDATED

extends Node

func compile(source_code: String) -> Dictionary:
	var lines = source_code.strip_edges().split("\n", false) # Keep empty lines for accurate indexing
	var instructions = []
	var labels = {} # To store label_name: instruction_index

	# --- Pass 1: Collect Labels and Initial Instructions ---
	for i in range(lines.size()):
		var line = lines[i].strip_edges()
		if line.empty() or line.begins_with("#"): # Ignore empty lines and comments
			continue

		if line.begins_with("::"):
			var label_name = line.substr(2).strip_edges()
			if labels.has(label_name):
				return { "error": "Compiler Error: Duplicate label '" + label_name + "'" }
			labels[label_name] = instructions.size() # Store current instruction index for the label
			# Labels themselves do not generate an instruction, they are just markers
		else:
			# For now, just append a placeholder or the raw line, actual parsing in Pass 2
			instructions.append({"raw_line": line})

	# Reset instructions for Pass 2 to fill with actual opcodes
	instructions = []

	# --- Pass 2: Parse Instructions, Resolve Jumps ---
	for i in range(lines.size()):
		var line = lines[i].strip_edges()
		if line.empty() or line.begins_with("#") or line.begins_with("::"):
			continue # Skip empty lines, comments, and labels

		if line.begins_with("print "):
			var msg = line.substr(6).strip_edges().strip_edges("\"")
			instructions.append({ "opcode": "PRINT", "args": [msg] })
		elif line.begins_with("shell "):
			var shell_cmd = line.substr(6)
			instructions.append({ "opcode": "SHELL_COMMAND", "args": [shell_cmd] })
		elif line.begins_with("set_var "):
			var parts = line.substr(8).split(" ", false)
			if parts.size() >= 2:
				# Attempt to convert to int/float if numerical
				var val = parts[1]
				if val.is_valid_integer() or (val.is_valid_float() and val.find(".") != -1):
					val = float(val) if val.find(".") != -1 else int(val)
				instructions.append({ "opcode": "SET_VAR", "args": [parts[0], val] })
		elif line.begins_with("read "):
			var fpath = line.substr(5).strip_edges()
			instructions.append({ "opcode": "READ_FILE", "args": [fpath] })
		elif line == "halt":
			instructions.append({ "opcode": "HALT" })
		elif line.begins_with("jump_if "):
			var parts = line.substr(8).split(" ", false, 3) # Split into [var1, op, var2, ::label]
			if parts.size() == 4 and parts[3].begins_with("::"):
				var var1_name = parts[0]
				var op = parts[1]
				var var2_val = parts[2]
				var target_label = parts[3].substr(2)
				if not labels.has(target_label):
					return { "error": "Compiler Error: Undefined label '" + target_label + "'" }
				instructions.append({ "opcode": "JUMP_IF", "args": [var1_name, op, var2_val, labels[target_label]] })
			else:
				return { "error": "Compiler Error: Invalid jump_if syntax: " + line }
		elif line.begins_with("jump "):
			var target_label = line.substr(5).strip_edges()
			if not target_label.begins_with("::"):
				return { "error": "Compiler Error: Invalid jump target. Must be a label (::label)." }
			target_label = target_label.substr(2)
			if not labels.has(target_label):
				return { "error": "Compiler Error: Undefined label '" + target_label + "'" }
			instructions.append({ "opcode": "JUMP", "args": [labels[target_label]] })
		elif line.begins_with("add ") or line.begins_with("sub ") or \
		     line.begins_with("mul ") or line.begins_with("div "):
			var op_type = line.split(" ", false)[0].to_upper()
			var parts = line.substr(op_type.length() + 1).split(" ", false)
			if parts.size() == 3: # var1 var2 result_var
				instructions.append({ "opcode": op_type, "args": [parts[0], parts[1], parts[2]] })
			else:
				return { "error": "Compiler Error: Invalid arithmetic syntax: " + line }
		else:
			instructions.append({ "opcode": "UNKNOWN", "args": [line] })

	return { "instructions": instructions }