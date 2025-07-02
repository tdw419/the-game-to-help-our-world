# main.gd
# This script is the core logic for the PXOS Microkernel.
# It handles the Godot UI, loads/saves all PXOS data from/to assets/8.png.json,
# and contains the chatbot and roadmap execution logic.

extends Control

# --- UI References (assigned in the editor) ---
onready var output_display = $VBoxContainer/OutputDisplay
onready var input_field = $VBoxContainer/InputContainer/InputField
onready var eight_png_display = $VBoxContainer/EightPNGDisplay

# --- File System Paths (relative to res://) ---
var eight_png_data_path = "res://assets/8.png.json"

# --- PXOS State (loaded from/saved to 8.png.json) ---
var pxos_data = {
	"conversation_history": [],
	"current_roadmap": null,
	"current_roadmap_step_index": -1,
	"is_paused": false,
	"pxos_in_memory_files": {}, # Simulates the PXOS file system
	"pending_human_approval_step": null,
	"roadmaps": {} # Stores all loaded roadmaps by name
}

# --- Initialization ---
func _ready():
	_ensure_assets_directory_exists()
	_load_pxos_data()
	
	_log_message("PXOS Microkernel initialized. Type 'Hey PXOSBot, load roadmap initial_boot' to begin.")
	input_field.grab_focus() # Focus input field on start

# --- UI Event Handlers ---
func _on_SendButton_pressed():
	_process_input_from_ui()

func _on_InputField_text_entered(text: String):
	_process_input_from_ui()

func _process_input_from_ui():
	var input_text = input_field.text.strip_edges()
	if input_text.empty():
		return
	
	input_field.clear()
	_process_chatbot_input(input_text)

# --- Internal Helper Functions ---

func _log_message(message: String):
	output_display.append_bbcode("[color=white]" + message + "[/color]\n")
	output_display.scroll_vertical = output_display.get_v_scroll().max_value # Auto-scroll to bottom

func _ensure_assets_directory_exists():
	var dir = Directory.new()
	if not dir.dir_exists("res://assets/"):
		dir.make_dir_recursive("res://assets/")
		_log_message("Created res://assets/ directory.")

func _load_pxos_data():
	var file = File.new()
	if file.file_exists(eight_png_data_path):
		file.open(eight_png_data_path, File.READ)
		var content = file.get_as_text()
		file.close()
		var parse_result = JSON.parse(content)
		if parse_result.error == OK:
			pxos_data = parse_result.result
			_log_message("Loaded PXOS data from: " + eight_png_data_path)
		else:
			_log_message("ERROR: Failed to parse 8.png.json: " + parse_result.error_string + ". Starting fresh.")
			_initialize_default_pxos_data()
	else:
		_log_message("No existing 8.png.json data found. Starting fresh.")
		_initialize_default_pxos_data()

func _initialize_default_pxos_data():
	# Define a basic initial_boot roadmap directly in the default data
	var initial_boot_roadmap = [
		{
			"phase_number": 1,
			"title": "PXOS Initial Boot Sequence",
			"description": "Establishes core system files and welcomes the user.",
			"steps": [
				{
					"type": "create_file",
					"path": "/pxos/config/boot.json",
					"content": "{\"status\": \"booted\", \"timestamp\": \"%s\"}" % OS.get_datetime_string_from_system()
				},
				{
					"type": "pxos_command",
					"command": "log",
					"message": "PXOS core boot files created."
				},
				{
					"type": "gui_update",
					"update_data": {
						"component": "welcome_message",
						"text": "Welcome to PXOS! I am your Microkernel AI."
					}
				}
			],
			"requires_human_approval": false
		},
		{
			"phase_number": 2,
			"title": "Agent System Activation",
			"description": "Activates the initial agent framework.",
			"steps": [
				{
					"type": "create_file",
					"path": "/pxos/agents/pxagent_001.py",
					"content": "# PXAgent-001: Placeholder for agent logic.\n# This file will evolve within PXOS memory."
				},
				{
					"type": "pxos_command",
					"command": "log",
					"message": "PXAgent-001 framework initiated."
				}
			],
			"requires_human_approval": true # This phase will require approval
		}
	]
	
	pxos_data["roadmaps"]["initial_boot"] = initial_boot_roadmap
	pxos_data["conversation_history"] = []
	pxos_data["current_roadmap"] = null
	pxos_data["current_roadmap_step_index"] = -1
	pxos_data["is_paused"] = false
	pxos_data["pxos_in_memory_files"] = {}
	pxos_data["pending_human_approval_step"] = null
	_save_pxos_data() # Save the initialized data

func _save_pxos_data():
	var file = File.new()
	file.open(eight_png_data_path, File.WRITE)
	file.store_string(JSON.print(pxos_data, "\t"))
	file.close()
	_log_message("Saved PXOS data to: " + eight_png_data_path)

# --- PXOS File System (In-Memory, part of 8.png.json) ---

func _pxos_command_create_file(path: String, content: String):
	pxos_data["pxos_in_memory_files"][path] = content
	_save_pxos_data() # Persist changes
	return "PXOS FS: Created in-memory file: " + path

func _pxos_command_read_file(path: String) -> String:
	if pxos_data["pxos_in_memory_files"].has(path):
		return pxos_data["pxos_in_memory_files"][path]
	return ""

func _pxos_command_write_file(path: String, content: String) -> bool:
	pxos_data["pxos_in_memory_files"][path] = content
	_save_pxos_data() # Persist changes
	return true

# --- Roadmap Logic (Integrated) ---

func _execute_phase(phase_data: Dictionary) -> Array:
	var phase_logs = []
	phase_logs.append("RoadmapRunner: Executing phase: " + phase_data.get("title", "Unknown Phase"))

	for step in phase_data.get("steps", []):
		var step_desc = step.get("description", str(step))
		phase_logs.append("  - Step: " + step_desc)

		# Handle different step types
		if step.get("type") == "create_file":
			var log_msg = _pxos_command_create_file(step.get("path"), step.get("content", ""))
			phase_logs.append("    " + log_msg)
		elif step.get("type") == "gui_update":
			# For this minimal setup, just log GUI updates
			phase_logs.append("    GUI Update Requested: " + JSON.print(step.get("update_data")))
			# If it's a welcome message, display it
			if step.get("update_data", {}).get("component") == "welcome_message":
				_log_message("[color=#87CEEB]" + step.get("update_data").get("text", "") + "[/color]")
		elif step.get("type") == "pxos_command":
			var command_type = step.get("command")
			if command_type == "log":
				phase_logs.append("    PXOS Command Log: " + step.get("message"))
			else:
				phase_logs.append("    PXOS Command: Unknown command type: " + command_type)
		
		yield(get_tree().create_timer(0.1), "timeout") # Small delay for readability

	return phase_logs

# --- Chatbot Core Logic ---

func _process_chatbot_input(input_text: String):
	pxos_data["conversation_history"].append({"role": "user", "text": input_text, "timestamp": OS.get_datetime_string_from_system()})
	_log_message("User: " + input_text)
	
	var response = "I'm not sure how to respond to that yet."
	var command_recognized = false
	
	if input_text.to_lower().begins_with("hey pxosbot,"):
		var command = input_text.to_lower().replace("hey pxosbot,", "").strip_edges()
		command_recognized = true

		if command.begins_with("load roadmap"):
			var roadmap_name = command.replace("load roadmap", "").strip_edges()
			if pxos_data["roadmaps"].has(roadmap_name):
				pxos_data["current_roadmap"] = pxos_data["roadmaps"][roadmap_name]
				pxos_data["current_roadmap_step_index"] = -1
				pxos_data["is_paused"] = false
				pxos_data["pending_human_approval_step"] = null
				response = "Loaded roadmap: '" + roadmap_name + "'. It has " + str(pxos_data["current_roadmap"].size()) + " phases."
			else:
				response = "ERROR: Roadmap '" + roadmap_name + "' not found in PXOS memory."
		
		elif command.begins_with("begin executing phase"):
			if pxos_data["current_roadmap"] == null:
				response = "ERROR: No roadmap loaded. Please load a roadmap first."
			else:
				var phase_num_str = command.replace("begin executing phase", "").strip_edges()
				var phase_num = int(phase_num_str) if phase_num_str.is_valid_integer() else -1
				
				var start_step_index = -1
				for i in range(pxos_data["current_roadmap"].size()):
					var phase = pxos_data["current_roadmap"][i]
					if phase.has("phase_number") and phase.phase_number == phase_num:
						start_step_index = i
						break
				
				if start_step_index == -1:
					response = "ERROR: Phase " + str(phase_num) + " not found in the loaded roadmap."
				else:
					pxos_data["current_roadmap_step_index"] = start_step_index
					pxos_data["is_paused"] = false
					pxos_data["pending_human_approval_step"] = null
					response = "Beginning execution from Phase " + str(phase_num) + "."
					_execute_next_roadmap_step() # Execute immediately
		
		elif command == "pause" or command == "pause execution":
			if pxos_data["current_roadmap"] != null:
				pxos_data["is_paused"] = true
				response = "Execution paused. Current step: Phase " + str(pxos_data["current_roadmap"][pxos_data["current_roadmap_step_index"]].phase_number) + "."
			else:
				response = "No roadmap is currently being executed."
		
		elif command == "resume" or command == "resume execution" or command == "approve":
			if pxos_data["current_roadmap"] != null and pxos_data["is_paused"]:
				pxos_data["is_paused"] = false
				pxos_data["pending_human_approval_step"] = null
				response = "Resuming execution."
				_execute_next_roadmap_step() # Continue execution
			else:
				response = "No roadmap is paused or being executed."
		
		elif command.begins_with("execute step"):
			if pxos_data["current_roadmap"] == null:
				response = "ERROR: No roadmap loaded."
			else:
				var step_num_str = command.replace("execute step", "").strip_edges()
				var step_num = int(step_num_str) if step_num_str.is_valid_integer() else -1
				if step_num < 1 || step_num > pxos_data["current_roadmap"].size():
					response = "ERROR: Invalid step number. Roadmap has " + str(pxos_data["current_roadmap"].size()) + " phases."
				else:
					pxos_data["current_roadmap_step_index"] = step_num - 1 # Adjust to 0-based index
					pxos_data["is_paused"] = false
					pxos_data["pending_human_approval_step"] = null
					response = "Executing specific step: Phase " + str(step_num) + "."
					_execute_next_roadmap_step()
		
		elif command.begins_with("skip step"):
			if pxos_data["current_roadmap"] == null:
				response = "ERROR: No roadmap loaded."
			else:
				var step_num_str = command.replace("skip step", "").strip_edges()
				var step_num = int(step_num_str) if step_num_str.is_valid_integer() else -1
				if step_num < 1 || step_num > pxos_data["current_roadmap"].size():
					response = "ERROR: Invalid step number. Roadmap has " + str(pxos_data["current_roadmap"].size()) + " phases."
				elif pxos_data["current_roadmap_step_index"] == step_num - 1:
					pxos_data["current_roadmap_step_index"] += 1 # Move to the next step
					pxos_data["is_paused"] = false
					pxos_data["pending_human_approval_step"] = null
					response = "Skipped step: Phase " + str(step_num) + ". Proceeding to next."
					_execute_next_roadmap_step()
				else:
					response = "ERROR: Cannot skip phase " + str(step_num) + ". Current execution is at phase " + str(pxos_data["current_roadmap_step_index"] + 1) + "."
		
		elif command.begins_with("edit"):
			var file_path = command.replace("edit", "").strip_edges()
			var content = _pxos_command_read_file(file_path)
			if content != "":
				response = "Opened '" + file_path + "' for manual editing. Content preview (first 100 chars):\n" + content.left(100) + "..."
				_log_message("[color=#FFA500]" + response + "[/color]") # Highlight edit message
				response = "File '" + file_path + "' is ready for your manual edits. (Content logged to console)"
			else:
				response = "ERROR: Could not read file '" + file_path + "' or it's empty/does not exist in memory."
		
		elif command == "show 8.png data" or command == "show memory":
			if pxos_data["pxos_in_memory_files"].empty():
				response = "8.png data is currently empty."
			else:
				response = "Current 8.png data:\n" + JSON.print(pxos_data["pxos_in_memory_files"], "\t")
		
		elif command == "save 8.png data" or command == "save memory":
			_save_pxos_data()
			response = "8.png data saved."
		
		else:
			response = "Command not recognized: '" + command + "'."
	
	if not command_recognized:
		response = "I'm not sure how to respond to that yet."
	
	pxos_data["conversation_history"].append({"role": "pxosbot", "text": response, "timestamp": OS.get_datetime_string_from_system()})
	_log_message("PXOSBot: " + response)
	_save_pxos_data() # Save state after bot response

func _execute_next_roadmap_step():
	if pxos_data["current_roadmap"] == null or pxos_data["current_roadmap_step_index"] >= pxos_data["current_roadmap"].size():
		_log_message("Roadmap execution finished or no roadmap loaded.")
		pxos_data["current_roadmap"] = null
		pxos_data["current_roadmap_step_index"] = -1
		pxos_data["is_paused"] = false
		pxos_data["pending_human_approval_step"] = null
		_save_pxos_data()
		return
	
	if pxos_data["is_paused"]:
		_log_message("Execution is paused. Use 'resume' or 'approve' to continue.")
		return
	
	var current_phase = pxos_data["current_roadmap"][pxos_data["current_roadmap_step_index"]]
	_log_message("[color=#6A5ACD]Executing Phase " + str(current_phase.get("phase_number")) + ": " + current_phase.get("title") + "[/color]")
	
	if current_phase.get("requires_human_approval", false):
		pxos_data["is_paused"] = true
		pxos_data["pending_human_approval_step"] = current_phase
		_log_message("[color=#FFD700]PXAgent-001: Phase " + str(current_phase.get("phase_number")) + " '" + current_phase.get("title") + "' requires human approval.[/color]")
		_log_message("[color=#FFD700]PXAgent-001: Here are the steps for this phase:[/color]")
		for step in current_phase.get("steps", []):
			var step_desc = step.get("description", str(step))
			_log_message("[color=#FFD700]  - " + step_desc + " (Type: " + step.get("type") + ")[/color]")
		_log_message("[color=#FFD700]PXAgent-001: Please type 'Hey PXOSBot, resume' or 'Hey PXOSBot, approve' to proceed, or 'Hey PXOSBot, skip step " + str(current_phase.get("phase_number")) + "' to skip this phase.[/color]")
		_save_pxos_data()
		return # Pause here, waiting for user input

	# If not paused or approval not required, execute the phase
	var phase_execution_logs = _execute_phase(current_phase)
	for log_line in phase_execution_logs:
		_log_message(log_line)

	pxos_data["current_roadmap_step_index"] += 1
	_save_pxos_data() # Save state after phase execution

	# Automatically proceed to the next step if not paused and roadmap not finished
	if not pxos_data["is_paused"] and pxos_data["current_roadmap_step_index"] < pxos_data["current_roadmap"].size():
		_log_message("[color=#ADD8E6]PXOSBot: Phase " + str(current_phase.get("phase_number")) + " completed. Automatically proceeding to next phase...[/color]")
		call_deferred("_execute_next_roadmap_step") # Use call_deferred to avoid recursion depth issues
	elif not pxos_data["is_paused"] and pxos_data["current_roadmap_step_index"] >= pxos_data["current_roadmap"].size():
		_log_message("[color=#ADD8E6]PXOSBot: All roadmap phases completed.[/color]")
		pxos_data["current_roadmap"] = null
		pxos_data["current_roadmap_step_index"] = -1
		_save_pxos_data()
