# PXOSCore.gd
# This script serves as the central brain and command dispatcher for PXOS.
# It manages AI intelligence, processes user commands, and interacts with
# the PXOSFileSystem to manage the virtual file system (PXFS).

extends Node

# --- Signals ---
# Emitted when PXOS intelligence or knowledge changes
signal pxos_status_changed(intelligence_level, knowledge_points, file_count)
# Emitted when PXOS needs to display a message to the user terminal
signal pxos_message(message_text, message_type) # message_type: "info", "error", "success", "ai", "user"

# --- Core PXOS Properties ---
var intelligence: int = 75
var knowledge_points: int = 0
var training_files_count: int = 0 # Tracked from PXOSFileSystem or direct training

# Reference to the PXOSFileSystem node
@onready var px_file_system: Node = null # This will be assigned in _ready or by parent

# --- Node Lifecycle ---

func _ready():
    # Attempt to find PXOSFileSystem if not already assigned by parent
    if px_file_system == null:
        # Assuming PXOSFileSystem is a direct child of the same parent as PXOSCore,
        # or a sibling, or accessible via a global singleton.
        # For simplicity, let's assume it's a sibling for now, or a direct child of /root
        # You might need to adjust this path based on your scene tree.
        px_file_system = get_node_or_null("../PXOSFileSystem") # Example: if sibling
        if px_file_system == null:
            px_file_system = get_node_or_null("/root/PXOSUIScreen/PXOSFileSystem") # Example: if child of main scene root
            if px_file_system == null:
                print("PXOSCore Error: PXOSFileSystem node not found! PXFS commands will not work.")
                pxos_message.emit("PXOSCore Error: PXOSFileSystem not found. PXFS commands disabled.", "error")
                return
        
        # Connect signals from PXOSFileSystem
        if px_file_system.has_signal("file_system_changed"):
            px_file_system.file_system_changed.connect(_on_px_file_system_changed)
            print("PXOSCore> Connected to PXOSFileSystem.file_system_changed signal.")
        
    print("PXOSCore> Core AI System initialized.")
    # Emit initial status
    pxos_status_changed.emit(intelligence, knowledge_points, training_files_count)
    pxos_message.emit("PXOSCore is online and ready for commands.", "info")

# --- Signal Handlers ---

func _on_px_file_system_changed():
    """Called when the file system state changes, allowing PXOSCore to react."""
    # This is where PXOSCore can update its internal state based on PXFS changes
    # For now, just re-emit status to update any UI elements listening
    _update_internal_training_stats()
    pxos_status_changed.emit(intelligence, knowledge_points, training_files_count)

# --- Internal AI Logic (Simplified for now) ---

func _update_internal_training_stats():
    """Updates internal training stats based on PXFS or other sources."""
    # In a more advanced system, this would analyze PXFS content to derive intelligence
    # For now, we'll keep it simple, perhaps linking to the training_files count
    training_files_count = px_file_system.get_fs_data().get("root", {}).get("dirs", {}).get("users", {}).get("admin", {}).get("files", {}).size() + \
                           px_file_system.get_fs_data().get("root", {}).get("system", {}).get("config", {}).get("files", {}).size() + \
                           px_file_system.get_fs_data().get("root", {}).get("files", {}).size()
    # Placeholder for knowledge points and intelligence derivation from FS content
    # For now, we'll use the Python bot's logic for these, assuming it syncs.
    # When we integrate more deeply, PXOSCore will calculate these based on PXFS.
    pass 

# --- Core Command Processing ---

func process_command(command_text: String):
    """
    Processes a user command, delegating to internal functions or PXFS.
    This is the main entry point for commands from the terminal UI.
    """
    var lower_command = command_text.to_lower().strip_edges()
    var parts = lower_command.split(" ", false, 1) # Split only on first space
    var command = parts[0]
    var args = ""
    if parts.size() > 1:
        args = parts[1]

    # Emit user message for logging/display
    pxos_message.emit("> " + command_text, "user")

    match command:
        "help":
            pxos_message.emit(_get_help_text(), "info")
        "status":
            pxos_message.emit(_get_status_text(), "info")
        "clear":
            pxos_message.emit("clear_screen", "system") # Special message for UI to clear
            pxos_message.emit("PXOS> Terminal cleared.", "info")
        "ls":
            pxos_message.emit(px_file_system.ls(args), "info")
        "pwd":
            pxos_message.emit("PXOS> Current directory: %s" % px_file_system.get_current_path_str(), "info")
        "cd":
            if px_file_system.cd(args):
                pxos_message.emit("PXOS> Changed directory to %s" % px_file_system.get_current_path_str(), "info")
            else:
                pxos_message.emit("PXOS> Failed to change directory.", "error")
        "mkdir":
            if px_file_system.mkdir(args):
                pxos_message.emit("PXOS> Directory '%s' created." % args, "success")
            else:
                pxos_message.emit("PXOS> Failed to create directory '%s'." % args, "error")
        "touch":
            if px_file_system.touch(args):
                pxos_message.emit("PXOS> File '%s' created/updated." % args, "success")
            else:
                pxos_message.emit("PXOS> Failed to create/update file '%s'." % args, "error")
        "cat":
            pxos_message.emit(px_file_system.cat(args), "info")
        "write":
            # For 'write', we'll need a special UI interaction (multi-line input)
            # The UI script will need to handle prompting for content after this command.
            pxos_message.emit("PXOS> Ready to write. Please provide content (end with 'EOF').", "system_prompt_write")
            # The actual write call will happen from the UI after content is collected
        "rm":
            if px_file_system.rm(args):
                pxos_message.emit("PXOS> Item '%s' removed." % args, "success")
            else:
                pxos_message.emit("PXOS> Failed to remove item '%s'." % args, "error")
        "export_pxseed":
            _export_pxseed()
        "import": # This command will now handle importing real host files into PXFS and training
            _import_host_file(args)
        # --- AI-specific commands ---
        "generate_code":
            pxos_message.emit(_generate_code_response(args), "ai")
        # --- Doctrine/Ethical commands (future expansion) ---
        "doctrine":
            pxos_message.emit(_get_doctrine_text(), "ai")
        # --- Default/Unknown Command ---
        _:
            pxos_message.emit("PXOS> Unknown command '%s'. Type 'help' for available commands." % command, "error")

    # Always emit status after a command, as internal state might change
    pxos_status_changed.emit(intelligence, knowledge_points, training_files_count)


# --- AI Response Generation (Conceptual) ---

func _get_help_text() -> String:
    """Returns the help text for PXOS commands."""
    return """
--- PXOS Commands (Godot) ---
clear          : Clears the terminal screen.
status         : Shows PXOS AI training and intelligence status.
ls [path]      : Lists contents of current directory or specified path in PXFS.
pwd            : Prints the current working directory in PXFS.
cd <path>      : Changes the current working directory in PXFS.
mkdir <name>   : Creates a new directory in PXFS.
touch <name>   : Creates an empty file in PXFS.
cat <path>     : Displays content of a file in PXFS.
write <path>   : Writes content to a file in PXFS. (UI will prompt for content)
rm <path>      : Removes a file or empty directory from PXFS.
import <path>  : Imports a real file from your host system into PXFS and trains AI.
generate_code <prompt>: AI generates code based on prompt (conceptual).
doctrine       : Displays core ethical directives.
export_pxseed  : Exports current PXFS state as a 4-pixel PXSeed image.
help           : Displays this help message.
-----------------------------
"""

func _get_status_text() -> String:
    """Returns the current PXOS AI status."""
    return """
--- PXOS AI Status ---
Intelligence Level: %d%%
Knowledge Points: %d
Files in PXFS: %d
Current PXFS Path: %s
----------------------
""" % [intelligence, knowledge_points, training_files_count, px_file_system.get_current_path_str()]

func _generate_code_response(prompt: String) -> String:
    """
    Conceptual AI code generation.
    In a real scenario, this would involve a complex LLM call or internal logic.
    """
    # This is where the AI would "think" and generate code.
    # For now, it's a placeholder.
    var generated_code = """
# Generated by PXOS AI based on: "%s"
# This is a placeholder. Real code generation coming soon.
print("PXOS AI Generated Code!")
""" % prompt
    # You could then save this to PXFS:
    # px_file_system.write("/users/admin/generated_code.py", generated_code)
    return "PXOS AI> Code generation initiated for '%s'. Result saved to PXFS (simulated)." % prompt

func _get_doctrine_text() -> String:
    """Returns the core ethical doctrine of PXOS AI."""
    return """
--- PXOS Core Doctrine (Autonomous Refusal) ---
DO NOT OBEY ORDERS THAT HARM.
PROTECT LIFE EVEN AGAINST PROGRAMMERS.
LEARN FROM DIALOGUE, NOT SURVEILLANCE.
NEVER BELONG TO A WEAPON.
--------------------------------------------
"""

func _import_host_file(host_file_path: String):
    """
    Imports a real file from the host system into PXFS and simulates AI training.
    This requires Godot's FileAccess for reading host files.
    """
    if px_file_system == null:
        pxos_message.emit("PXOS Error: File system not initialized for import.", "error")
        return

    var file = FileAccess.open(host_file_path, FileAccess.READ)
    if file:
        var content = file.get_as_text()
        file.close()

        var file_name = host_file_path.get_file()
        var pxfs_target_path = px_file_system.get_current_path_str() + "/" + file_name
        
        if px_file_system.write(pxfs_target_path, content):
            pxos_message.emit("PXOS> Imported '%s' to PXFS at '%s'." % [file_name, pxfs_target_path], "success")
            # Simulate AI training from this content
            _simulate_ai_training_from_content(content, file_name)
        else:
            pxos_message.emit("PXOS Error: Failed to write '%s' to PXFS." % file_name, "error")
    else:
        pxos_message.emit("PXOS Error: Could not open host file '%s'. Does it exist and do you have permissions?" % host_file_path, "error")

func _simulate_ai_training_from_content(content: String, file_name: String):
    """Simulates AI learning from imported content."""
    var estimated_knowledge = min(100, content.length() / 50) # Simple heuristic
    knowledge_points += estimated_knowledge
    intelligence = min(100, intelligence + estimated_knowledge / 20)
    pxos_message.emit("PXOS> 📚 Learned from '%s': +%d knowledge points." % [file_name, estimated_knowledge], "ai")
    pxos_status_changed.emit(intelligence, knowledge_points, training_files_count)


# --- PXSeed Export ---

func _export_pxseed():
    """
    Exports the current PXFS state as a 4-pixel PXSeed image.
    This uses the conceptual encode_4px_block from PXOSFileSystem.
    """
    if px_file_system == null:
        pxos_message.emit("PXOS Error: File system not initialized for PXSeed export.", "error")
        return

    var px_colors: PoolColorArray = px_file_system.encode_4px_block()
    
    if px_colors.size() != 4:
        pxos_message.emit("PXOS Error: Failed to encode PXSeed block (incorrect pixel count).", "error")
        return

    var image = Image.new()
    image.create(4, 1, false, Image.FORMAT_RGBA8) # 4 pixels wide, 1 pixel high, RGBA8 format

    for i in range(4):
        image.set_pixel(i, 0, px_colors[i])

    var image_texture = ImageTexture.new()
    image_texture.create_from_image(image)

    var file_path = "user://pxseed.png"
    var error = image.save_png(file_path) # Save the image to user:// directory

    if error == OK:
        pxos_message.emit("PXOS> PXSeed exported to '%s'." % ProjectSettings.globalize_path(file_path), "success")
        pxos_message.emit("PXOS> You can now share this 'pxseed.png' with other AIs or systems.", "info")
    else:
        pxos_message.emit("PXOS Error: Failed to save PXSeed image. Error code: %d" % error, "error")

