# PXOSUIScreen.gd
# This script manages the visual simulation of a kernel boot process
# and now includes a real-time interactive shell with virtual commands,
# a writable PXRAM-backed file system under /home/, shell navigation,
# command history with up/down arrow recall, background job control,
# built-in 'echo', 'cat', 'ps' commands, virtual disk mounting,
# enhanced scrollback buffer with command history,
# simulated writable filesystem ('touch', 'echo >', and '.pxapp' execution),
# PXFS persistence (save/load), enhanced file management commands (ls, cat, rm, mkdir),
# a graphical PXRAM viewer (Phase 26), and a new 'import' command.

extends Control

@onready var boot_log_label: RichTextLabel = $TerminalContainer/BootLog
@onready var command_input: LineEdit = $TerminalContainer/CommandInput
@onready var boot_log_timer: Timer = $BootLogTimer
# --- Phase 26: PXRAM Viewer Nodes ---
@onready var pxram_viewer_panel: Panel = $PXRAMViewerPanel
@onready var pxram_tree: Tree = $PXRAMViewerPanel/VBoxContainer/pxram_tree
@onready var toggle_pxram_viewer_button: Button = $TerminalContainer/TogglePXRAMViewerButton
# --- NEW: Import FileDialog Node ---
@onready var import_file_dialog: FileDialog = $ImportFileDialog
# --- End NEW ---

# Variable to hold the PXRAM data passed from PXVM.gd
var pxram_data: Dictionary = {}

# --- Phase 12 & 13: PXRAM File Store (now also serves as writable FS) ---
# This simulates a writable file system, starting with /home/
var pxram_fs := {
	"home": {} # Represents the /home/ directory
}
# --- End PXRAM File Store ---

# --- Phase 14: Current Working Directory ---
var current_path: String = "/home" # Initial path after boot
# --- End Phase 14 ---

# --- Phase 17 & 18: Background Job System ---
var background_jobs := [] # Stores dictionaries of active background jobs
var next_job_id := 1 # Counter for unique job IDs
var foreground_job := null # Placeholder for a job brought to foreground (simulated)
# --- End Phase 17 & 18 ---

# --- Phase 19: Virtual File System Map for Built-in 'cat' ---
var pxfs: Dictionary = {
	"/etc/px-release": "PXOS v0.1\nBuilt from pixels and dreams.",
	"/home/tc/readme.txt": "Welcome to PXOS!\nYou are running inside a bootloader shell.",
	"/boot/vmlinuz": "<kernel binary>",
}
# --- End Phase 19 ---

# --- Phase 20: Simulated Disk Content and Mount Points ---
var px_disk_mounts: Dictionary = {} # Tracks mounted devices and their mount points: {"/mnt": {"/readme.txt": "content"}}
var px_virtual_disks: Dictionary = {
	"/dev/px0": { # Content of the virtual disk /dev/px0
		"/readme.txt": "This is PX Disk 0.\nData lives here.",
		"/hello.txt": "PXOS says hello from disk."
	},
	"/dev/px1": { # Another example disk
		"/data.txt": "More data from PX Disk 1."
	}
}
# --- End Phase 20 ---

# --- Phase 24: PXFS Persistence File Path ---
var pxfs_file_path := "user://pxfs.pxdisk"
# --- End Phase 24 ---


# --- Phase 11: Expanded Virtual Command Structure (for /bin commands) ---
# Note: 'echo', 'cat', 'ps', 'ls', 'mount', 'touch', 'run' will now be handled as built-ins before checking this.
var virtual_fs := {
	"/bin/help": "echo Available commands: help, clear, exit, echo, time, cat, mount, ls, mkdir, rm, cd, pwd, run, jobs, fg, kill, touch, save, load, import",
	"/bin/clear": "clear",
	"/bin/echo": "echo", # This entry will now mostly be for 'help' command's listing
	"/bin/exit": "exit",
	"/bin/time": "echo PXOS Time: " + Time.get_time_string_from_system(),
	"/bin/cat": "cat", # This entry will now mostly be for 'help' command's listing
	"/bin/mount": "mount",
	"/bin/ls": "ls",
	"/bin/mkdir": "mkdir",
	"/bin/rm": "rm",
	"/bin/cd": "cd",
	"/bin/pwd": "pwd",
	"/bin/run": "run",
	"/bin/jobs": "jobs",
	"/bin/fg": "fg",
	"/bin/kill": "kill",
	"/bin/touch": "touch", # Added touch to virtual_fs
	"/bin/save": "save", # Added save to virtual_fs
	"/bin/load": "load", # Added load to virtual_fs
	"/bin/import": "import", # Added import to virtual_fs

	# Simulated /proc and /sys files
	"/proc/version": "PXOS v1.0 (Simulated Kernel)",
	"/proc/cpuinfo": "CPU: VirtualPX 1.0\nCores: 2\nClock: 2.40GHz",
	"/sys/meminfo": "MemTotal: 1024kB\nMemFree: 512kB\nPXRAMSize: " + str(0) + " entries" # Placeholder, updated in _ready or set_pxram_data
}
# --- End Phase 11 ---

var boot_messages: Array[String] = [
    "[    0.000000] Linux version 5.10.0-rc1 (build@pxvm) (gcc ...) #1 SMP PREEMPT",
    "[    0.000000] Command line: console=ttyS0",
    "[    0.000000] Initializing cgroup subsys cpuset",
    "[    0.000000] Initializing cgroup subsys cpu",
    "[    0.000000] Initializing cgroup subsys cpuacct",
    "[    0.000000] Linux agpgart interface v0.103",
    "[    0.000000] Memory: 128MB (BIOS detected)",
    "[    0.000000] Kernel/Userland split: 0x0000000080000000 - 0x00000000c0000000",
    "[    000000] Detected 1 CPU cores",
    "[    0.000000] Initializing RAMDISK: %d bytes (simulated)" % 0, # Placeholder for initrd size
    "[    0.000000] VFS: Mounted root (ext2 filesystem) readonly on device 0:0.",
    "[    0.000000] Freeing initrd memory: %dK" % 0,
    "[    0.000000] Run /sbin/init as init process",
    "[    0.000000] systemd 245 (v245.4-1.fc32) running in system mode.",
    "[    0.000000] Welcome to TinyCore Linux!",
    "",
    "pxos@pxcore:~$" # This will be the initial prompt
]
var current_boot_message_index: int = 0
# --- Phase 16 & 21: Command History Variables ---
var command_history: Array[String] = []
var history_index: int = -1 # -1 means no command from history is currently selected / at the end of history
# --- End Phase 16 & 21 ---

func _ready():
    boot_log_label.text = ""
    command_input.hide() # Hide input initially
    command_input.connect("text_submitted", self, "_on_command_entered") # Connect signal
    boot_log_timer.start() # Start the boot log animation
    
    # Update /sys/meminfo with actual pxram_data size if already set
    _update_sys_meminfo()
    
    # --- Phase 21: Optional: Load saved history ---
    _load_history()
    # --- End Phase 21 ---

    # --- Phase 26: PXRAM Viewer Setup ---
    pxram_viewer_panel.visible = false # Ensure it's hidden initially
    toggle_pxram_viewer_button.connect("pressed", Callable(self, "_on_TogglePXRAMViewerButton_pressed"))
    pxram_tree.connect("item_selected", Callable(self, "_on_pxram_tree_item_selected"))
    # PXRAM tree will be populated when pxram_data is set via set_pxram_data()
    # --- End Phase 26 ---

    # --- NEW: Import FileDialog Setup ---
    import_file_dialog.connect("file_selected", Callable(self, "_on_ImportFileDialog_file_selected"))
    # --- End NEW ---


# Method to receive pxram data from PXVM.gd
func set_pxram_data(data: Dictionary):
    pxram_data = data
    _update_sys_meminfo() # Update /sys/meminfo once pxram_data is received
    print(f"PXOSUIScreen: Received pxram_data with {pxram_data.size()} entries.") # For debugging
    
    # --- Phase 26: Populate PXRAM Tree after data is received ---
    _populate_pxram_tree()
    # --- End Phase 26 ---


# Helper to update the /sys/meminfo entry dynamically
func _update_sys_meminfo():
    virtual_fs["/sys/meminfo"] = "MemTotal: 1024kB\nMemFree: 512kB\nPXRAMSize: " + str(pxram_data.size()) + " entries"


func _on_BootLogTimer_timeout():
    if current_boot_message_index < boot_messages.size():
        var message = boot_messages[current_boot_message_index]
        boot_log_label.append_text(message + "\n")
        boot_log_label.scroll_to_line(boot_log_label.get_line_count() - 1) # Auto-scroll
        current_boot_message_index += 1
    else:
        boot_log_timer.stop()
        _show_shell_prompt() # Show the shell prompt and input after boot messages

# Shows the shell prompt and enables input
func _show_shell_prompt():
    # Update the prompt to reflect the current path
    boot_log_label.append_text("pxos@pxcore:" + current_path + "$ ")
    boot_log_label.scroll_to_line(boot_log_label.get_line_count() - 1)
    command_input.show()
    command_input.grab_focus() # Focus the input field so user can type immediately

# Handles command input from the LineEdit
func _on_command_entered(text: String):
    # Echo the command back to the console
    boot_log_label.append_text(text + "\n")
    command_input.clear() # Clear the input field
    
    # --- Phase 16: Add command to history ---
    var command_to_add = text.strip_edges()
    if not command_to_add.empty(): # Only add non-empty commands to history
        command_history.push_back(command_to_add)
    
    history_index = command_history.size() # Reset history index to "after last command"
    # --- End Phase 16 ---

    _process_command(text) # Process the command
    _show_shell_prompt() # Show new prompt

    # --- Phase 26: Update PXRAM Tree after command (if it changes PXRAM) ---
    # This is a conceptual hook. If commands like 'load' or 'save' modify pxram_data,
    # you'd call _populate_pxram_tree() here or within those functions.
    # For now, pxram_data is mostly static after initial boot.
    # _populate_pxram_tree() # Uncomment if commands modify pxram_data directly
    # --- End Phase 26 ---


# --- Phase 17: Main command processing logic with background detection ---
func _process_command(text: String):
    var command_text = text.strip_edges()
    if command_text.empty(): return

    var is_background := command_text.ends_with("&")
    if is_background:
        command_text = command_text.left(command_text.length() - 1).strip_edges()

    if is_background:
        _start_background_job(command_text)
    else:
        _execute_shell_command(command_text) # Execute foreground commands
# --- End Phase 17 ---

# --- Phase 22 & 23: Core command execution with built-ins ---
func _execute_shell_command(cmd_string: String):
	var args = cmd_string.split(" ", false) # Use false to keep empty strings for path parsing
	if args.is_empty(): return

	var cmd = args[0].to_lower()
	
	# --- Built-in Commands (Order matters: more specific first) ---
	match cmd:
		"echo": # --- Phase 22: Built-in echo with write support ---
			# Built-in echo needs to handle redirection
			if ">" in args or ">>" in args:
				var is_append = ">>" in args
				var redirect_char_idx = args.find(">>") if is_append else args.find(">")
				
				if redirect_char_idx >= 1 and redirect_char_idx + 1 < args.size():
					var content_parts = args.slice(1, redirect_char_idx)
					var message = content_parts.join(" ")
					var target_path = _pxfs_normalize_path(args[redirect_char_idx + 1]) # Use normalized path
					
					var [parent_node, file_key] = _pxfs_resolve_parent_and_key(target_path)
					
					if parent_node and typeof(parent_node) == TYPE_DICTIONARY:
						if is_append:
							# Append to existing content, or create if not exists
							parent_node[file_key] = parent_node.get(file_key, "") + message + "\n"
						else:
							# Overwrite
							parent_node[file_key] = message + "\n"
						# boot_log_label.append_text("") # Silent success
					else:
						_append_to_terminal("echo: Write access denied or invalid path: " + target_path)
				else:
					_append_to_terminal("Usage: echo [text] > [filename] or echo [text] >> [filename]")
			else: # Standard echo without redirection
				_append_to_terminal(args.slice(1).join(" "))
			return # Handled, so return
		"cat": # --- Phase 25: Built-in cat ---
			if args.size() > 1:
				_cmd_cat(args) # Call the new _cmd_cat function
			else:
				_append_to_terminal("Usage: cat [file_path]")
			return # Handled, so return
		"ps":
			_execute_ps() # Call the new _execute_ps function
			return # Handled, so return
		"ls": # --- Phase 25: Built-in ls ---
			_cmd_ls(args) # Call the new _cmd_ls function
			return # Handled, so return
		"mount": # --- Phase 20: Built-in mount ---
			if args.size() >= 3:
				_execute_mount(args[1], args[2])
			else:
				_append_to_terminal("Usage: mount <device> <mount_point>")
			return # Handled, so return
		"jobs":
			if background_jobs.size() == 0:
				_append_to_terminal("No background jobs.")
			else:
				_append_to_terminal("ID\tStatus\tCommand")
				for job in background_jobs:
					_append_to_terminal(f"[{job['id']}]\t{job['status']}\t{job['command']}")
			return # Handled, so return
		"fg":
			if args.size() > 1:
				var job_id = args[1].to_int()
				_bring_job_to_foreground(job_id)
			else:
				_append_to_terminal("Usage: fg <job_id>")
			return # Handled, so return
		"kill":
			if args.size() > 1:
				var job_id = args[1].to_int()
				_kill_background_job(job_id)
			else:
				_append_to_terminal("Usage: kill <job_id>")
			return # Handled, so return
		"touch": # --- Phase 22: Built-in touch ---
			if args.size() < 2:
				_append_to_terminal("Usage: touch [filename]")
				return
			var filename = _pxfs_normalize_path(args[1]) # Normalize path
			var [parent_node, file_key] = _pxfs_resolve_parent_and_key(filename)
			
			if parent_node and typeof(parent_node) == TYPE_DICTIONARY:
				parent_node[file_key] = parent_node.get(file_key, "") # Create if not exists, keep content if exists
				# _append_to_terminal("Created " + filename) # Silent success
			else:
				_append_to_terminal("touch: Cannot create file: " + filename)
			return # Handled, so return
		"run": # --- Phase 23: Built-in run for .pxapp ---
			if args.size() < 2:
				_append_to_terminal("Usage: run [filename.pxapp]")
				return
			var filename = _pxfs_normalize_path(args[1]) # Normalize path
			_execute_pxapp_script(filename) # Call the new PXApp execution function
			return # Handled, so return
		"save": # --- Phase 24: Built-in save ---
			_save_pxfs()
			return # Handled, so return
		"load": # --- Phase 24: Built-in load ---
			_load_pxfs()
			return # Handled, so return
		"mkdir": # --- Phase 25: Built-in mkdir ---
			_cmd_mkdir(args) # Call the new _cmd_mkdir function
			return # Handled, so return
		"rm": # --- Phase 25: Built-in rm ---
			_cmd_rm(args) # Call the new _cmd_rm function
			return # Handled, so return
		"import": # --- NEW: Built-in import ---
			_execute_import_command(args)
			return # Handled, so return
	# --- End Built-in Commands ---

	var cmd_path = "/bin/" + cmd
	# Check if the command exists in our virtual /bin
	if virtual_fs.has(cmd_path):
		var simulated_action = virtual_fs[cmd_path]
		
		match simulated_action:
			# These commands are now handled as built-ins above, so these virtual_fs entries
			# mostly serve for the 'help' command's listing.
			# "echo": Handled as built-in
			# "cat": Handled as built-in
			# "ps": Handled as built-in
			# "ls": Handled as built-in
			# "mount": Handled as built-in
			# "jobs": Handled as built-in
			# "fg": Handled as built-in
			# "kill": Handled as built-in
			# "touch": Handled as built-in
			# "run": Handled as built-in
			# "save": Handled as built-in
			# "load": Handled as built-in
			# "mkdir": Handled as built-in
			# "rm": Handled as built-in
			# "import": Handled as built-in
			"clear": # Handle /bin/clear
				boot_log_label.text = ""
			"exit": # Handle /bin/exit
				_append_to_terminal("Shutting down PXOS...")
				yield(get_tree().create_timer(1.0), "timeout")
				get_tree().quit()
			"cd": # --- Phase 14: Handle cd command ---
				var target_path_arg = args.size() > 1 ? args[1] : "/home" # Default to /home
				var resolved_path = _pxfs_normalize_path(target_path_arg)
				var node = _pxfs_resolve_path(resolved_path)
				
				if typeof(node) == TYPE_DICTIONARY: # Check if it's a directory
					current_path = resolved_path
					# Silent success
				else:
					_append_to_terminal("cd: no such directory: " + target_path_arg)
			"pwd": # --- Phase 14: Handle pwd command ---
				_append_to_terminal(current_path)
			"time": # Handle /bin/time
				_append_to_terminal("PXOS Time: " + Time.get_time_string_from_system())
			_: # This should ideally not be reached if all commands are properly handled
				_append_to_terminal("Command not found: %s (from virtual_fs fallback)" % cmd)
	else:
		# Command not found in virtual /bin
		_append_to_terminal("Command not found: %s" % cmd)
# --- End Phase 24 & 25: Core command execution with built-ins ---

# --- Phase 17: Background Job System Functions ---
func _start_background_job(cmd: String):
	var job_id = next_job_id
	next_job_id += 1

	var timer = Timer.new()
	timer.one_shot = true
	timer.wait_time = 2.0 + randf() * 2.0 # Simulated job time: 2–4 sec
	add_child(timer) # Add timer to scene tree so it runs

	var job = {
		"id": job_id,
		"command": cmd,
		"status": "Running",
		"timer": timer
	}
	background_jobs.append(job)

	# Use callable to connect with arguments
	timer.connect("timeout", callable(self, "_on_background_job_complete").bind(job_id))
	timer.start()

	_append_to_terminal(f"[{job_id}] {cmd} &")

func _on_background_job_complete(job_id: int):
	var job_to_remove = -1
	for i in range(background_jobs.size()):
		if background_jobs[i]["id"] == job_id:
			background_jobs[i]["status"] = "Done"
			_append_to_terminal(f"\n[{job_id}] Done\t{background_jobs[i]['command']}")
			# Remove the timer node from the scene tree
			if is_instance_valid(background_jobs[i]["timer"]):
				background_jobs[i]["timer"].queue_free()
			job_to_remove = i
			break
	if job_to_remove != -1:
		background_jobs.remove(job_to_remove)
# --- End Phase 17 ---

# --- Phase 18: Foreground and Kill Job Functions ---
func _bring_job_to_foreground(job_id: int):
	var job_found = false
	for i in range(background_jobs.size()):
		var job = background_jobs[i]
		if job["id"] == job_id:
			job_found = true
			if job["status"] == "Running":
				_append_to_terminal(f"[{job_id}] Brought to foreground: {job['command']}")
				# Simulate job finishing immediately when foregrounded
				job["timer"].stop()
				job["status"] = "Done"
				_on_background_job_complete(job_id) # Call completion handler
				# The job is removed by _on_background_job_complete
			else:
				_append_to_terminal(f"[{job_id}] Already finished.")
			return
	if not job_found:
		_append_to_terminal(f"fg: job {job_id} not found")

func _kill_background_job(job_id: int):
	var job_found = false
	for i in range(background_jobs.size()):
		var job = background_jobs[i]
		if job["id"] == job_id:
			job_found = true
			if job["status"] == "Running":
				job["timer"].stop()
				job["status"] = "Killed"
				_append_to_terminal(f"[{job['id']}] Killed\t{job['command']}")
				# Remove the timer node from the scene tree
				if is_instance_valid(job["timer"]):
					job["timer"].queue_free()
				background_jobs.remove(i)
			else:
				_append_to_terminal(f"[{job['id']}] Cannot kill; already {job['status']}")
			return
	if not job_found:
		_append_to_terminal(f"kill: job {job_id} not found")
# --- End Phase 18 ---

# --- Phase 15: Script Execution Function ---
func _run_script_lines(lines: Array):
	for line in lines:
		var stripped_line = line.strip_edges()
		if stripped_line == "":
			continue
		_append_to_terminal("→ " + stripped_line) # Indicate script execution
		_execute_shell_command(stripped_line) # Use _execute_shell_command for script lines
# --- End Phase 15 ---

# --- Phase 25: Path Resolution Helpers (Refined for null return) ---
# Resolves a full path (e.g., "/home/user/file.txt") to its corresponding node in pxram_fs.
# Returns the node (dictionary for directory, string for file content) or null if path not found.
func _pxfs_resolve_path(path: String) -> Variant: # Variant can be Dictionary or String
	var parts = path.strip_edges(true, true).split("/")
	var current_node = pxram_fs # Start from the root of pxram_fs (which is "home" in our case)
	
	for p in parts:
		if p == "": continue # Skip empty parts from leading/trailing slashes
		
		# If the current node is a dictionary (a directory)
		if typeof(current_node) == TYPE_DICTIONARY and current_node.has(p):
			current_node = current_node[p]
		else:
			# Path segment not found or trying to traverse into a file
			return null # Return null to signify not found
	return current_node

# Resolves a full path to its parent node and the key for the target item.
# Returns an Array [parent_node (Dictionary), key_of_target (String)] or [null, null] if path is invalid.
func _pxfs_resolve_parent_and_key(path: String) -> Array:
	var parts = path.strip_edges(true, true).split("/")
	if parts.size() < 1: # Path must have at least one component (e.g., "home")
		return [null, null]
	
	var key_to_target = parts.pop_back() # The last part is the key of the target item
	
	var parent_path_parts = parts # Remaining parts form the parent path
	var parent_node: Dictionary
	
	if parent_path_parts.empty(): # If parent path is empty, it means target is at the root of pxram_fs (e.g., "home")
		parent_node = pxram_fs
	else:
		# Reconstruct parent path and resolve it
		var resolved_parent_path = "/" + "/".join(parent_path_parts)
		parent_node = _pxfs_resolve_path(resolved_parent_path)
	
	if typeof(parent_node) == TYPE_DICTIONARY:
		return [parent_node, key_to_target]
	else:
		return [null, null] # Parent path not found or not a directory
# --- End Phase 25: Path Resolution Helpers ---

# --- Phase 14: Path Normalization Utility ---
func _pxfs_normalize_path(input_path: String) -> String:
	var parts = []
	var tokens: Array
	
	# Determine if the path is absolute or relative
	if input_path.begins_with("/"):
		tokens = input_path.strip_edges(true, true).split("/")
	else:
		# Start from current_path if relative
		tokens = current_path.strip_edges(true, true).split("/")
		tokens.append_array(input_path.strip_edges(true, true).split("/"))

	for token in tokens:
		match token:
			"", ".":
				continue # Skip empty tokens and current directory
			"..":
				if parts.size() > 0:
					parts.pop_back() # Go up one level
			_:
				parts.append(token) # Add valid directory/file name

	# Reconstruct the normalized path
	if parts.empty():
		return "/" # If all parts resolved to nothing, it's the root
	
	# The _pxfs_resolve_path expects paths relative to pxram_fs's root,
	# so we need to ensure the normalized path is consistent with that.
	# If the input was "/" it should resolve to the pxram_fs root itself.
	# If it's "/home", it should resolve to pxram_fs["home"].
	# For simplicity, let's ensure paths are always absolute from the conceptual root "/"
	# and _pxfs_resolve_path handles the "home" entry.

	var normalized = "/" + "/".join(parts)
	
	# Special handling for the root of our PXRAM FS
	if normalized == "/home" and pxram_fs.has("home"):
		return "/home"
	elif normalized == "/": # If normalized to root, but our FS starts at /home
		return "/" # Conceptual root, not directly resolvable to a dictionary unless we add a top-level.
	
	return normalized
# --- End Phase 14: Path Normalization Utility ---


# Helper function to append text to the terminal output
func _append_to_terminal(text: String):
    boot_log_label.append_text(text + "\n")
    boot_log_label.scroll_to_line(boot_log_label.get_line_count() - 1) # Auto-scroll

# --- Phase 16: Input History (Up/Down Arrow) ---
func _input(event):
    if command_input.has_focus() and event is InputEventKey and event.pressed and not event.echo:
        if event.scancode == KEY_UP:
            if history_index > 0: # Can go back if not at the very first command
                history_index -= 1
                command_input.text = command_history[history_index]
                command_input.caret_column = command_input.text.length()
            get_viewport().set_input_as_handled()

        elif event.scancode == KEY_DOWN:
            if history_index < command_history.size() - 1: # Can go forward if not at the last command
                history_index += 1
                command_input.text = command_history[history_index]
                command_input.caret_column = command_input.text.length()
            else:
                # If at the last command and pressing down, go to empty line
                history_index = command_history.size() # Represents the "new command" empty line
                command_input.text = ""
                command_input.caret_column = command_input.text.length()
            get_viewport().set_input_as_handled()
# --- End Phase 16 ---

# --- Phase 21: Optional: Load saved history ---
func _load_history():
	# Example of pre-loading history for testing
	command_history = [
		"ls",
		"mount /dev/px0 /mnt",
		"cat /mnt/readme.txt",
		"mkdir /home/temp",
		"cd /home/temp",
		"echo Initial content > my_file.txt",
		"cat my_file.txt"
	]
	history_index = command_history.size()
# --- End Phase 21 ---

# --- Phase 24: PXFS Save + Load Implementations ---
func _save_pxfs():
	var file := FileAccess.open(pxfs_file_path, FileAccess.WRITE)
	if file:
		var json = JSON.stringify(pxram_fs) # Serialize the pxram_fs
		file.store_string(json)
		file.close()
		_append_to_terminal("[PXFS] Saved to pxfs.pxdisk")
		# _populate_file_tree() # No file explorer in this scene, so removed
	else:
		_append_to_terminal("[PXFS] ERROR: Could not open pxfs.pxdisk for writing")

func _load_pxfs():
	if not FileAccess.file_exists(pxfs_file_path):
		_append_to_terminal("[PXFS] No saved pxfs.pxdisk found")
		return

	var file := FileAccess.open(pxfs_file_path, FileAccess.READ)
	if file:
		var content := file.get_as_text()
		var parsed := JSON.parse_string(content)
		if typeof(parsed) == TYPE_DICTIONARY:
			pxram_fs = parsed # Load the parsed content into pxram_fs
			_append_to_terminal("[PXFS] Loaded from pxfs.pxdisk")
			# _populate_file_tree() # No file explorer in this scene, so removed
		else:
			_append_to_terminal("[PXFS] ERROR: Malformed JSON in pxfs.pxdisk")
		file.close()
	else:
		_append_to_terminal("[PXFS] ERROR: Could not open pxfs.pxdisk")
# --- End Phase 24 ---

# --- Phase 25: Built-in Command Implementations ---
# _execute_cat, _execute_ps, _execute_mount, _execute_ls are defined below.
# --- End Phase 25 ---

# --- Phase 25: Built-in Command Implementations (Continued) ---
func _cmd_ls(args: Array):
	var dir_path = args.size() > 1 ? _pxfs_normalize_path(args[1]) : current_path # Use normalized path or current_path
	var entries_to_list = []

	# 1. Check pxram_fs (for /home and its subdirectories)
	var node = _pxfs_resolve_path(dir_path)
	if typeof(node) == TYPE_DICTIONARY: # It's a directory in pxram_fs
		for k in node.keys():
			if typeof(node[k]) == TYPE_DICTIONARY:
				entries_to_list.append(k + "/") # Append slash for directories
			else:
				entries_to_list.append(k)
		entries_to_list.sort()
		_append_to_terminal(entries_to_list.join("  "))
		return
	elif typeof(node) == TYPE_STRING: # It's a file in pxram_fs
		_append_to_terminal("ls: " + dir_path + ": Not a directory")
		return

	# 2. Check px_disk_mounts (for mounted devices like /mnt)
	for mount_point in px_disk_mounts.keys():
		if dir_path == mount_point: # Listing the mount point itself
			var disk_content = px_disk_mounts[mount_point]
			for f in disk_content.keys():
				entries_to_list.append(f.lstrip("/")) # Remove leading slash for display
			entries_to_list.sort()
			_append_to_terminal(entries_to_list.join("  "))
			return
		elif dir_path.begins_with(mount_point + "/"):
			# This implies listing a subdirectory *within* a mounted disk.
			# Our px_virtual_disks currently only supports flat files at the root of the disk.
			# To support this, px_virtual_disks would need to be nested dictionaries.
			_append_to_terminal("ls: " + dir_path + ": Subdirectories of mounted disks not yet supported.")
			return

	# 3. Handle root directory listing (ls / or ls with no arg)
	if dir_path == "/" || dir_path == "":
		# Add top-level conceptual directories
		var root_dirs = ["bin/", "boot/", "etc/", "home/", "proc/", "sys/"]
		for dir_name in root_dirs:
			if not entries_to_list.has(dir_name):
				entries_to_list.append(dir_name)
		
		# Add mounted points as directories
		for mp in px_disk_mounts.keys():
			var mp_name = mp.replace("/", "") + "/"
			if not entries_to_list.has(mp_name):
				entries_to_list.append(mp_name)

		# Add top-level files from pxfs (e.g., if /etc/px-release was /px-release)
		# For now, pxfs has full paths, so this isn't strictly necessary unless we change pxfs structure.
		
		entries_to_list.sort()
		_append_to_terminal(entries_to_list.join("  "))
		return

	_append_to_terminal("ls: No such file or directory: " + dir_path)

func _cmd_cat(args: Array):
	if args.size() < 2:
		_append_to_terminal("cat: Usage: cat [file_path]")
		return
	var file_path = _pxfs_normalize_path(args[1]) # Normalize path for lookup

	# First, check the virtual_fs (for /proc, /sys, /etc/px-release etc.)
	if virtual_fs.has(file_path):
		_append_to_terminal(virtual_fs[file_path])
		return

	# Then, check px_disk_mounts (for mounted files)
	for mount_point in px_disk_mounts.keys():
		if file_path.begins_with(mount_point):
			var relative_path = file_path.substr(mount_point.length())
			if not relative_path.begins_with("/"): # Ensure relative path starts with / for disk lookup
				relative_path = "/" + relative_path
			var disk_content = px_disk_mounts[mount_point]
			if disk_content.has(relative_path):
				_append_to_terminal(disk_content[relative_path])
				return

	# Finally, check the pxram_fs (for /home/ files, now including written files)
	if file_path.begins_with("/home/"):
		var node = _pxfs_resolve_path(file_path)
		if typeof(node) == TYPE_STRING: # It's a file (string content)
			_append_to_terminal(node)
			return
		elif typeof(node) == TYPE_DICTIONARY: # It's a directory
			_append_to_terminal("cat: " + file_path + ": Is a directory")
			return

	_append_to_terminal("cat: " + file_path + ": No such file or directory")

func _cmd_rm(args: Array):
	if args.size() < 2:
		_append_to_terminal("rm: Usage: rm /path/to/file")
		return
	var path = _pxfs_normalize_path(args[1]) # Normalize path
	var [parent_node, key_to_remove] = _pxfs_resolve_parent_and_key(path)
	
	if parent_node and parent_node.has(key_to_remove):
		if typeof(parent_node[key_to_remove]) == TYPE_DICTIONARY and not args.has("-r"):
			_append_to_terminal("rm: " + path + ": Is a directory. Use 'rm -r' to remove directories.")
		else:
			parent_node.erase(key_to_remove)
			_append_to_terminal("[rm] Deleted: %s" % path) # Indicate success
	else:
		_append_to_terminal("rm: " + path + ": No such file or directory")

func _cmd_mkdir(args: Array):
	if args.size() < 2:
		_append_to_terminal("mkdir: Usage: mkdir /path/to/newdir")
		return
	var path = _pxfs_normalize_path(args[1]) # Normalize path
	var [parent_node, new_dir_key] = _pxfs_resolve_parent_and_key(path)
	
	if parent_node and typeof(parent_node) == TYPE_DICTIONARY:
		if parent_node.has(new_dir_key):
			_append_to_terminal("mkdir: " + path + ": File exists")
		else:
			parent_node[new_dir_key] = {} # Create new empty dictionary for directory
			_append_to_terminal("[mkdir] Created: %s" % path) # Indicate success
	else:
		_append_to_terminal("mkdir: " + path + ": No such file or directory")

func _execute_ps():
	_append_to_terminal(" PID\tSTATUS\tCOMMAND")
	for job in background_jobs:
		_append_to_terminal(" %03d\t%s\t%s" % [job["id"], job["status"], job["command"]])
	# If there was a foreground job, we'd list it here.
	# In this simulation, foreground jobs complete immediately, so foreground_job will be null.
	# If you implement blocking foreground jobs, you'd add:
	# if foreground_job:
	# 	_append_to_terminal(" %03d\tForeground\t%s" % [foreground_job["id"], foreground_job["command"]])

func _execute_mount(device: String, mount_point: String):
	var normalized_mount_point = _pxfs_normalize_path(mount_point) # Normalize mount point

	if not px_virtual_disks.has(device):
		_append_to_terminal("mount: Unknown device " + device)
		return
	if px_disk_mounts.has(normalized_mount_point):
		_append_to_terminal("mount: Mount point already in use: " + mount_point)
		return
	
	# Check if mount_point is a directory in pxram_fs (optional, for realism)
	var mount_point_node = _pxfs_resolve_path(normalized_mount_point)
	if mount_point_node == null && normalized_mount_point != "/": # If it doesn't exist and isn't root, create it
		# This is a simplification; in a real system, mount points must exist.
		# For this simulation, we'll auto-create if it's a valid path.
		var [parent, key] = _pxfs_resolve_parent_and_key(normalized_mount_point)
		if parent and typeof(parent) == TYPE_DICTIONARY:
			parent[key] = {} # Create it as an empty directory
			_append_to_terminal("mount: Created mount point directory: " + normalized_mount_point)
		else:
			_append_to_terminal("mount: Invalid mount point path: " + mount_point)
			return
	elif typeof(mount_point_node) != TYPE_DICTIONARY: # If it exists but is a file
		_append_to_terminal("mount: Mount point " + mount_point + " is a file, not a directory.")
		return

	px_disk_mounts[normalized_mount_point] = px_virtual_disks[device]
	_append_to_terminal("Mounted " + device + " to " + mount_point)

# --- End Phase 25: Built-in Command Implementations ---

# --- Phase 23: PXApp Execution ---
func _execute_pxapp_script(filename: String):
	# First, check pxram_fs (for /home/ files)
	var app_content: String = ""
	var found_in_pxram_fs = false
	if filename.begins_with("/home/"):
		var node = _pxfs_resolve_path(filename)
		if typeof(node) == TYPE_STRING: # It's a file (string content)
			app_content = node
			found_in_pxram_fs = true
	
	# If not found in pxram_fs, check px_disk_mounts (for mounted files like /mnt/myapp.pxapp)
	if not found_in_pxram_fs:
		for mount_point in px_disk_mounts.keys():
			if filename.begins_with(mount_point):
				var relative_path = filename.substr(mount_point.length())
				if not relative_path.begins_with("/"):
					relative_path = "/" + relative_path
				var disk_content = px_disk_mounts[mount_point]
				if disk_content.has(relative_path):
					app_content = disk_content[relative_path]
					found_in_pxram_fs = true # Re-use flag for clarity, means found in any writable FS
					break
	
	if not found_in_pxram_fs:
		_append_to_terminal("PXApp not found: " + filename)
		return

	var app_code = app_content.split("\n")
	_append_to_terminal("[PXOS] Executing PXApp: " + filename)

	for line in app_code:
		line = line.strip_edges()
		if line.begins_with("log "):
			_append_to_terminal("[PXApp] " + line.replace("log ", ""))
		elif line != "":
			_append_to_terminal("[PXApp] Unknown instruction: " + line)
# --- End Phase 23 ---

# --- Phase 26: PXRAM Viewer Functions ---
func _on_TogglePXRAMViewerButton_pressed():
	pxram_viewer_panel.visible = not pxram_viewer_panel.visible
	if pxram_viewer_panel.visible:
		_populate_pxram_tree() # Refresh content when shown

func _populate_pxram_tree():
	pxram_tree.clear()
	var root = pxram_tree.create_item() # Invisible root
	pxram_tree.set_hide_root(true)
	
	_add_pxram_tree_branch(root, pxram_data, "")

func _add_pxram_tree_branch(parent_item: TreeItem, data: Variant, current_path: String):
	if typeof(data) == TYPE_DICTIONARY:
		var keys = data.keys()
		keys.sort()
		for key in keys:
			var value = data[key]
			var child_item = pxram_tree.create_item(parent_item)
			child_item.set_text(0, str(key)) # Key in first column
			
			var full_path = current_path + "/" + str(key) if current_path else str(key)
			child_item.set_metadata(0, full_path) # Store full path as metadata
			
			if typeof(value) == TYPE_DICTIONARY:
				child_item.set_text(1, "{...}") # Indicate dictionary
				_add_pxram_tree_branch(child_item, value, full_path)
			elif typeof(value) == TYPE_ARRAY:
				child_item.set_text(1, f"Array[{value.size()}]") # Indicate array
				_add_pxram_tree_branch(child_item, value, full_path) # Recursively add array elements
			elif typeof(value) == TYPE_POOL_BYTE_ARRAY:
				child_item.set_text(1, f"PoolByteArray[{value.size()}]") # Indicate PoolByteArray
				# Optionally, add a child for hex/string view of small byte arrays
				if value.size() < 1024: # Limit size for display
					var byte_view_item = pxram_tree.create_item(child_item)
					byte_view_item.set_text(0, "Bytes (Hex)")
					byte_view_item.set_text(1, value.hex_encode())
					byte_view_item.set_metadata(0, full_path + "/_hex_")
					
					var string_view_item = pxram_tree.create_item(child_item)
					string_view_item.set_text(0, "Bytes (String)")
					string_view_item.set_text(1, value.get_string_from_ascii())
					string_view_item.set_metadata(0, full_path + "/_string_")
				else:
					var large_item = pxram_tree.create_item(child_item)
					large_item.set_text(0, "Large Data")
					large_item.set_text(1, "Too large to display")
					large_item.set_metadata(0, full_path + "/_large_")
			else:
				child_item.set_text(1, str(value)) # Display other types directly
	elif typeof(data) == TYPE_ARRAY:
		for i in range(data.size()):
			var value = data[i]
			var child_item = pxram_tree.create_item(parent_item)
			child_item.set_text(0, f"[{i}]") # Array index as key
			
			var full_path = current_path + f"/[{i}]"
			child_item.set_metadata(0, full_path)
			
			if typeof(value) == TYPE_DICTIONARY:
				child_item.set_text(1, "{...}")
				_add_pxram_tree_branch(child_item, value, full_path)
			elif typeof(value) == TYPE_ARRAY:
				child_item.set_text(1, f"Array[{value.size()}]")
				_add_pxram_tree_branch(child_item, value, full_path)
			elif typeof(value) == TYPE_POOL_BYTE_ARRAY:
				child_item.set_text(1, f"PoolByteArray[{value.size()}]")
				if value.size() < 1024:
					var byte_view_item = pxram_tree.create_item(child_item)
					byte_view_item.set_text(0, "Bytes (Hex)")
					byte_view_item.set_text(1, value.hex_encode())
					byte_view_item.set_metadata(0, full_path + "/_hex_")
					
					var string_view_item = pxram_tree.create_item(child_item)
					string_view_item.set_text(0, "Bytes (String)")
					string_view_item.set_text(1, value.get_string_from_ascii())
					string_view_item.set_metadata(0, full_path + "/_string_")
				else:
					var large_item = pxram_tree.create_item(child_item)
					large_item.set_text(0, "Large Data")
					large_item.set_text(1, "Too large to display")
					large_item.set_metadata(0, full_path + "/_large_")
			else:
				child_item.set_text(1, str(value))

func _on_pxram_tree_item_selected():
	var item = pxram_tree.get_selected()
	if item:
		var path = item.get_metadata(0)
		var key = item.get_text(0)
		var value = item.get_text(1)
		_append_to_terminal(f"PXRAM Selected: {path} = {value}")

# --- NEW: Import Command Implementation ---
func _execute_import_command(args: Array):
	if args.size() < 2:
		_append_to_terminal("import: Usage: import [target_path]")
		_append_to_terminal("       Example: import /home/my_file.txt")
		_append_to_terminal("       This will open a file dialog to select a host file.")
		import_file_dialog.popup_centered() # Open dialog even if no path given
		return
	
	var target_path = _pxfs_normalize_path(args[1])
	
	# Store the target path for when the dialog returns
	import_file_dialog.set_meta("target_pxos_path", target_path)
	
	_append_to_terminal(f"import: Select a file from your host system to import to {target_path}")
	import_file_dialog.popup_centered() # Show the file dialog

func _on_ImportFileDialog_file_selected(host_file_path: String):
	var target_pxos_path = import_file_dialog.get_meta("target_pxos_path", "/imported/default_import.txt")
	
	_append_to_terminal(f"import: Host file selected: {host_file_path}")
	
	var file_access = FileAccess.open(host_file_path, FileAccess.READ)
	if file_access:
		var content = file_access.get_as_text()
		file_access.close()
		
		# Save content to pxram_fs at the target_pxos_path
		var [parent_node, file_key] = _pxfs_resolve_parent_and_key(target_pxos_path)
		
		if parent_node and typeof(parent_node) == TYPE_DICTIONARY:
			parent_node[file_key] = content
			_append_to_terminal(f"import: Successfully imported '{host_file_path}' to '{target_pxos_path}'")
			# Refresh PXRAM viewer and File Explorer if they are present and active
			_populate_pxram_tree() # PXRAM contains pxram_fs, so this updates it
			# If you had a separate file explorer for pxram_fs, you'd update it here too.
		else:
			_append_to_terminal(f"import: ERROR: Invalid target path for import: {target_pxos_path}")
	else:
		_append_to_terminal(f"import: ERROR: Could not open host file: {host_file_path}")
		_append_to_terminal(f"import: Error code: {FileAccess.get_open_error()}")
# --- End NEW: Import Command Implementation ---
