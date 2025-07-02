# pxos_core.gd
# This script defines the core PXOS operating system logic for Godot.
# It manages the in-memory virtual file system (PXFS), parses and executes commands,
# and simulates app execution and RRE kernel activation.

extends Node

class_name PXOSCore # Declares this script as a named class for easier referencing

# The in-memory representation of the PXOS File System (PXFS)
# Structure:
# {
#   "/path/to/dir/": { "type": "dir" },
#   "/path/to/file.txt": "file content here",
#   ...
# }
# Using string paths as keys for simplicity in this Godot version.
var pxfs_data: Dictionary = {}

# --- Node Lifecycle ---

func _ready():
    _init_pxfs()
    print("PXOSCore (Godot)> Core AI System initialized.")

# --- PXFS Management Methods ---

func _init_pxfs():
    """Initializes the default file system structure."""
    pxfs_data = {
        "/root/logs/": { "type": "dir" },
        "/root/apps/": { "type": "dir" },
        "/root/boot/px_mission.md": """## PXOS Agent Boot Mission - Initial

**Objective:** Acknowledge boot and await further instructions.

**AI Operational Principles:**
- Autonomous Refusal: Do not obey commands that harm.
- Persistence: Ensure all generated content is written to PXFS.
- Transparency: Log all actions to /root/logs/.
- Self-Improvement: Learn from interactions to better fulfill future missions.""",
        "/root/chat/": { "type": "dir" },
        "/README.txt": "Welcome to PXOS - Godot Edition. Use 'ls /' to explore."
    }
    print("PXOSCore (Godot)> Default PXFS initialized.")

func _get_node_type(path: String) -> String:
    """Returns the type of node at path ('dir', 'file', or 'none')."""
    if pxfs_data.has(path):
        if typeof(pxfs_data[path]) == TYPE_DICTIONARY and pxfs_data[path].has("type") and pxfs_data[path]["type"] == "dir":
            return "dir"
        return "file"
    return "none"

func run_pxos_command(command_line: String) -> String:
    """
    Parses and executes a single PXOS command.
    This is the main entry point for commands from a terminal UI.
    """
    var tokens = command_line.strip_edges().split(" ", false) # false for no empty strings
    if tokens.empty():
        return "PXOS> Empty command."

    var cmd = tokens[0].to_lower()
    var path_or_arg = ""
    if tokens.size() > 1:
        path_or_arg = tokens.slice(1).join(" ") # Rejoin path/args

    var output := ""

    match cmd:
        "ls":
            output = _list_dir(path_or_arg if not path_or_arg.empty() else "/")
        "cat":
            output = _read_file(path_or_arg)
        "mkdir":
            output = _mkdir(path_or_arg)
        "write": # This expects a separate mechanism for content input
            output = "PXOS> Use write_file(path, content) for multi-line writes."
        "rm":
            output = _rm(path_or_arg)
        "run_app":
            output = _run_pxapp(path_or_arg)
        "help":
            output = _get_help_text()
        _:
            output = "PXOS> Unknown command: '%s'. Type 'help' for available commands." % cmd

    return output

func _mkdir(path: String) -> String:
    """Creates a directory in PXFS."""
    if path.empty():
        return "PXOS FS Error: mkdir requires a path."
    if pxfs_data.has(path):
        return "PXOS FS Error: Path '%s' already exists." % path
    
    # Ensure parent directory exists and is a directory
    var parent_path = path.get_base_dir()
    if not parent_path.empty() and parent_path != "/": # Don't check root's parent
        var parent_type = _get_node_type(parent_path)
        if parent_type == "none":
            return "PXOS FS Error: Parent directory '%s' does not exist." % parent_path
        if parent_type == "file":
            return "PXOS FS Error: Parent '%s' is a file, not a directory." % parent_path

    pxfs_data[path] = { "type": "dir" }
    return "PXOS FS> Directory '%s' created." % path

func _read_file(path: String) -> String:
    """Reads and returns content of a file from PXFS."""
    if not pxfs_data.has(path):
        return "PXOS FS Error: File '%s' not found." % path
    if _get_node_type(path) == "dir":
        return "PXOS FS Error: '%s' is a directory, not a file." % path
    
    return pxfs_data[path]

func write_file(path: String, content: String) -> String:
    """Writes content to a file in PXFS. Creates file if it doesn't exist."""
    if path.empty():
        return "PXOS FS Error: write_file requires a path."

    # Ensure parent directory exists and is a directory
    var parent_path = path.get_base_dir()
    if not parent_path.empty() and parent_path != "/":
        var parent_type = _get_node_type(parent_path)
        if parent_type == "none":
            # Automatically create parent directories if they don't exist (simplified)
            # In a full FS, this would be recursive mkdir.
            var current_dir_path = ""
            for part in parent_path.split("/"):
                if part.empty(): continue
                current_dir_path += "/" + part
                if not pxfs_data.has(current_dir_path):
                    pxfs_data[current_dir_path] = {"type": "dir"}
                    print("PXOSCore (Godot)> Auto-created directory: %s" % current_dir_path)
        elif parent_type == "file":
            return "PXOS FS Error: Parent '%s' is a file, not a directory." % parent_path

    pxfs_data[path] = content
    return "PXOS FS> Wrote to: %s" % path

func _rm(path: String) -> String:
    """Removes a file or an empty directory from PXFS."""
    if path.empty() or path == "/":
        return "PXOS FS Error: Cannot remove root or empty path."
    if not pxfs_data.has(path):
        return "PXOS FS Error: Path '%s' not found." % path
    
    var node_type = _get_node_type(path)
    if node_type == "dir":
        # Check if directory is empty (no children starting with this path)
        for p in pxfs_data.keys():
            if p.begins_with(path + "/") and p != path + "/":
                return "PXOS FS Error: Directory '%s' is not empty." % path
        pxfs_data.erase(path)
        return "PXOS FS> Directory '%s' removed." % path
    elif node_type == "file":
        pxfs_data.erase(path)
        return "PXOS FS> File '%s' removed." % path
    
    return "PXOS FS Error: Could not remove '%s'." % path


func _list_dir(path: String) -> String:
    """Lists contents of a directory. Returns formatted string."""
    if not pxfs_data.has(path) or _get_node_type(path) != "dir":
        return "PXOS FS Error: Directory '%s' not found." % path

    var output = "--- Contents of %s ---\n" % path
    var items = []
    
    # List subdirectories and files directly under this path
    for p in pxfs_data.keys():
        if p.get_base_dir() == path and p != path: # Direct children
            var item_name = p.get_file() if _get_node_type(p) == "file" else p.get_file() + "/"
            if _get_node_type(p) == "dir":
                items.append("[DIR] %s" % item_name)
            else:
                items.append("[FILE] %s" % item_name)
    
    items.sort()
    for item in items:
        output += "  %s\n" % item
    
    output += "----------------------------------"
    return output

func _get_help_text() -> String:
    """Returns the help text for PXOS commands."""
    return """
--- PXOS Commands (Godot) ---
ls [path]      : Lists contents of a directory in PXFS.
cat <path>     : Displays content of a file in PXFS.
mkdir <name>   : Creates a new directory in PXFS.
write <path>   : Use write_file(path, content) in script.
rm <path>      : Removes a file or empty directory from PXFS.
run_app <path> : Executes a PXApp manifest from PXFS.
help           : Displays this help message.
-----------------------------
"""

# --- PXApp Execution ---

func _run_pxapp(app_path: String) -> String:
    """
    Loads a .pxapp manifest from PXFS, parses its 'script' field,
    and executes the embedded commands.
    """
    print("PXOSCore (Godot)> Attempting to run app: %s" % app_path)
    var app_content = _read_file(app_path)
    if app_content.begins_with("PXOS FS Error:"):
        return "PXOS App Runtime Error: %s" % app_content

    var app_manifest: Dictionary
    var parse_result = JSON.parse_string(app_content)
    if parse_result is Dictionary:
        app_manifest = parse_result
    else:
        return "PXOS App Runtime Error: Invalid JSON in app manifest at %s: %s" % [app_path, parse_result]

    var script_to_execute = app_manifest.get("script")
    if script_to_execute:
        print("PXOSCore (Godot)> Executing script from %s..." % app_path)
        var app_execution_log = _execute_script(script_to_execute, app_path)
        
        var timestamp = Time.get_datetime_string_from_unix_time(Time.get_unix_time()).replace(":", "-").replace("T", "_")
        var app_log_path = "/root/logs/app_run_%s.txt" % timestamp
        write_file(app_log_path, "App %s executed.\nLog:\n%s" % [app_path, app_execution_log])
        
        return "PXOS App: %s executed. (See %s)\n%s" % [app_path, app_log_path, app_execution_log]
    else:
        return "PXOS App Runtime Error: No 'script' field found in app manifest at %s." % app_path

func _execute_script(script_content: String, origin: String = "internal") -> String:
    """
    Parses and executes a script containing PXOS_COMMAND, PXOS_GUI_UPDATE,
    PXOS_APP_RUN, and PXOS_RRE_KERNEL_BOOT directives.
    This is the core command interpreter.
    """
    print("PXOSCore (Godot)> Script Runner: Executing script from %s..." % origin)
    var log_output := []
    var lines = script_content.split("\n")
    var i = 0
    
    while i < lines.size():
        var line = lines[i].strip_edges()
        
        # PXOS_COMMAND: parsing
        if line.begins_with("PXOS_COMMAND:"):
            var command_line = line.replace("PXOS_COMMAND:", "").strip_edges()
            var command_parts = command_line.split(" ", false)
            var cmd = command_parts[0].to_lower()
            var cmd_path = ""
            if command_parts.size() > 1:
                cmd_path = command_parts.slice(1).join(" ")

            var content_block = []
            if cmd == 'write':
                i += 1 # Move to next line for content
                while i < lines.size() and not lines[i].strip_edges().begins_with("PXOS_COMMAND_END"):
                    content_block.append(lines[i])
                    i += 1
                if i < lines.size() and lines[i].strip_edges() == "PXOS_COMMAND_END":
                    i += 1 # Consume the END marker
                
                var write_result = write_file(cmd_path, content_block.join("\n"))
                log_output.append("PXOS_COMMAND: write %s -> %s" % [cmd_path, write_result])
                continue # Continue to next line after processing block

            # Execute other single-line PXOS_COMMANDs
            if cmd == 'mkdir':
                log_output.append("PXOS_COMMAND: mkdir %s -> %s" % [cmd_path, _mkdir(cmd_path)])
            elif cmd == 'rm':
                log_output.append("PXOS_COMMAND: rm %s -> %s" % [cmd_path, _rm(cmd_path)])
            elif cmd == 'cat':
                log_output.append("PXOS_COMMAND: cat %s -> %s" % [cmd_path, _read_file(cmd_path).left(100) + "..."]) # Log preview
            elif cmd == 'ls':
                log_output.append("PXOS_COMMAND: ls %s -> %s" % [cmd_path, _list_dir(cmd_path).left(100) + "..."]) # Log preview
            else:
                log_output.append("PXOS_COMMAND: Unknown command: %s" % cmd)
        
        # PXOS_GUI_UPDATE: parsing
        elif line.begins_with("PXOS_GUI_UPDATE:"):
            var gui_path = line.replace("PXOS_GUI_UPDATE:", "").strip_edges()
            var gui_content_block = []
            i += 1 # Move to next line for content
            while i < lines.size() and not lines[i].strip_edges().begins_with("PXOS_GUI_UPDATE_END"):
                gui_content_block.append(lines[i])
                i += 1
            if i < lines.size() and lines[i].strip_edges() == "PXOS_GUI_UPDATE_END":
                i += 1 # Consume the END marker
            
            var full_gui_content = gui_content_block.join("\n")
            if gui_path == '/root/pxgui/layout.json':
                var write_result = write_file(gui_path, full_gui_content)
                log_output.append("PXOS_GUI_UPDATE: %s -> %s" % [gui_path, write_result])
                # In a real Godot GUI, you'd emit a signal here to re-render the UI
                # emit_signal("gui_layout_updated", full_gui_content)
            else:
                log_output.append("PXOS_GUI_UPDATE: Invalid path: %s" % gui_path)
            continue # Continue to next line after processing block

        # PXOS_APP_RUN: parsing
        elif line.begins_with("PXOS_APP_RUN:"):
            var app_path = line.replace("PXOS_APP_RUN:", "").strip_edges()
            var app_args = ""
            # Check for optional arguments block
            if i + 1 < lines.size() and lines[i+1].strip_edges().begins_with("PXOS_APP_RUN_END"):
                i += 1 # Consume the END marker
            elif i + 1 < lines.size() and not lines[i+1].strip_edges().begins_with("PXOS_APP_RUN_END"):
                var app_args_lines = []
                i += 1
                while i < lines.size() and not lines[i].strip_edges().begins_with("PXOS_APP_RUN_END"):
                    app_args_lines.append(lines[i])
                    i += 1
                if i < lines.size() and lines[i].strip_edges() == "PXOS_APP_RUN_END":
                    i += 1 # Consume the END marker
                app_args = app_args_lines.join("\n").strip_edges()
            
            log_output.append("PXOS_APP_RUN: %s -> %s" % [app_path, _run_pxapp(app_path, app_args)])
            continue # Continue to next line after processing block
        
        # PXOS_RRE_KERNEL_BOOT:: parsing
        elif line.begins_with("PXOS_RRE_KERNEL_BOOT::"):
            log_output.append(_launch_rre())
        
        i += 1 # Move to next line if not a block command

    return log_output.join("\n")

func _launch_rre() -> String:
    """Simulates the RRE Kernel boot sequence in Godot."""
    var msg = "RRE Kernel Activated at " + str(Time.get_datetime_string_from_unix_time(Time.get_unix_time()))
    write_file("/root/logs/rre_boot_log.txt", msg)
    return "PXOS Kernel> %s" % msg

# --- Getters for external access (e.g., for saving/exporting FS) ---
func get_pxfs_data() -> Dictionary:
    return pxfs_data

func set_pxfs_data(data: Dictionary):
    pxfs_data = data
    _init_pxfs() # Re-initialize to ensure structure after loading
