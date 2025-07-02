# PXRoadmapExecutor.gd
# This module reads a roadmap (as a sequence of text commands),
# parses its steps, and dispatches them as actions to other PXOS modules.
# It drives the self-evolution of the PXOS system.
#
# UPDATED: Now includes conceptual execution for new commands from the
# 'RRE System Evolution v3.0' roadmap, including 'ENABLE GOAL MODE' logic.

extends Node

# --- Configuration ---
# Delay in seconds between executing each step of the roadmap.
@export var step_execution_delay: float = 1.0

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging roadmap activity
@onready var px_glyph_compiler: PXGlyphCompiler = null # Will be initialized for PXAgentMemoryCoder
@onready var px_agent_memory_coder: PXAgentMemoryCoder = null # To write commands to PXScroll region
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # For commands that interact with memory
@onready var px_condition_checker: PXRoadmapConditionChecker = get_node_or_null("../PXRoadmapConditionChecker") # For IF commands
@onready var px_roadmap_memory: PXRoadmapMemoryRegion = get_node_or_null("../PXRoadmapMemory") # To load roadmaps from memory
@onready var px_roadmap_generator: PXRoadmapGenerator = get_node_or_null("../PXRoadmapGenerator") # For GENERATE command
@onready var px_scroll_library: PXScrollLibrary = get_node_or_null("../PXScrollLibrary") # For SAVE TO SCROLL LIBRARY
@onready var px_roadmap_recorder: PXRoadmapRecorder = get_node_or_null("../PXRoadmapRecorder") # For RECORD command
@onready var px_digest_exporter: PXDigestExporter = get_node_or_null("../PXDigestExporter") # For EXPORT command
@onready var px_fs_writer: PXFSWriter = get_node_or_null("../PXFSWriter") # For writing files to PXFS
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # For reading files from PXFS
@onready var px_roadmap_mutator: PXRoadmapMutator = get_node_or_null("../PXRoadmapMutator") # For mutating roadmaps
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # For goal memory access

# --- Internal State ---
var current_roadmap: Array[String] = [] # The list of steps in the active roadmap
var current_step_index: int = -1       # Index of the current step being executed
var roadmap_active: bool = false       # Flag to indicate if a roadmap is currently running

var time_since_last_step: float = 0.0  # Timer for step execution delay

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize PXGlyphCompiler. It's a RefCounted utility, so we instantiate it.
    px_glyph_compiler = PXGlyphCompiler.new()
    if not px_glyph_compiler:
        print_err("PXRoadmapExecutor: Failed to initialize PXGlyphCompiler. Cannot proceed.")
        set_process(false)
        return

    # Get the display image data and initialize PXAgentMemoryCoder
    if display_screen and display_screen.texture:
        var display_image = display_screen.texture.get_data()
        if display_image:
            px_agent_memory_coder = PXAgentMemoryCoder.new(display_image, px_glyph_compiler, display_screen)
            if not px_agent_memory_coder:
                print_err("PXRoadmapExecutor: Failed to initialize PXAgentMemoryCoder.")
                set_process(false)
                return
        else:
            print_err("PXRoadmapExecutor: Could not get display image data for PXAgentMemoryCoder.")
            set_process(false)
            return
    else:
        print_err("PXRoadmapExecutor: 'DisplayScreen' TextureRect or its texture not found. Cannot proceed.")
        set_process(false)
        return

    # Check other dependencies
    if not px_scroll_log or not px_condition_checker or not px_roadmap_memory or \
       not px_roadmap_generator or not px_scroll_library or not px_roadmap_recorder or \
       not px_digest_exporter or not px_fs_writer or not px_fs_reader or not px_roadmap_mutator or not px_goal_memory:
        print_warn("PXRoadmapExecutor: Some optional dependencies are missing. Some roadmap commands may not function.")

    print("PXRoadmapExecutor: Initialized.")

func _process(delta):
    # Only execute roadmap steps if a roadmap is active and there are steps left
    if roadmap_active and current_step_index < current_roadmap.size():
        time_since_last_step += delta
        if time_since_last_step >= step_execution_delay:
            _execute_current_step()
            time_since_last_step = 0.0 # Reset timer for the next step
            advance_roadmap_step()
    elif roadmap_active and current_step_index >= current_roadmap.size():
        # Roadmap has finished
        _log_roadmap_activity("Roadmap complete.")
        roadmap_active = false


# --- Roadmap Management API ---

func execute_roadmap(roadmap_steps: Array[String]):
    """
    Loads and starts the execution of a new roadmap.

    Args:
        roadmap_steps (Array[String]): An array of strings, where each string is a roadmap step command.
                                       Examples: "WRITE HELLO", "DELAY 2.0", "LOG Stage 1 Complete"
    """
    current_roadmap = roadmap_steps
    current_step_index = 0
    roadmap_active = true
    time_since_last_step = 0.0 # Ensure first step executes after initial delay
    _log_roadmap_activity("Roadmap started. Steps: " + str(current_roadmap.size()))
    print("PXRoadmapExecutor: Starting roadmap with ", current_roadmap.size(), " steps.")

func load_and_execute_roadmap_from_memory(goal_entry: GoalEntry = null):
    """
    Loads a roadmap from PXRoadmapMemoryRegion and starts its execution.
    """
    if not px_roadmap_memory:
        print_err("PXRoadmapExecutor: PXRoadmapMemoryRegion not found. Cannot load roadmap from memory.")
        if goal_entry:
            px_goal_memory.update_goal_outcome(goal_entry, "FAILURE", {"reason": "NoRoadmapMemory"})
        return

    var loaded_roadmap = px_roadmap_memory.read_roadmap_from_memory()
    if loaded_roadmap.is_empty():
        print_warn("PXRoadmapExecutor: No roadmap found in memory region or it's empty.")
        if goal_entry:
            px_goal_memory.update_goal_outcome(goal_entry, "FAILURE", {"reason": "EmptyRoadmap"})
        return

    execute_roadmap(loaded_roadmap)


func _execute_current_step():
    """
    Executes the command for the current step in the roadmap.
    """
    if current_step_index >= current_roadmap.size():
        return # Should not happen if roadmap_active check is correct

    var step_text = current_roadmap[current_step_index]
    print("PXRoadmapExecutor: Executing step [", current_step_index, "]: '", step_text, "'")
    _log_roadmap_activity("STEP " + str(step_text).left(15)) # Log truncated step

    # Parse the command and its arguments
    var parts = step_text.split(" ", false, 1) # Split only on the first space
    var command = parts[0].to_upper()
    var arg_text = ""
    if parts.size() > 1:
        arg_text = parts[1]

    _execute_command_logic(command, arg_text, step_text)


func _execute_command_logic(command: String, arg_text: String, full_step_text: String):
    """Helper function to execute command logic, used by _execute_current_step and _execute_nested_command."""
    match command:
        "WRITE":
            if px_agent_memory_coder:
                px_agent_memory_coder.write_command(arg_text)
            else:
                print_err("PXRoadmapExecutor: PXAgentMemoryCoder not available for 'WRITE' command.")
        "DELAY":
            if arg_text.is_valid_float():
                step_execution_delay = arg_text.to_float()
                _log_roadmap_activity("Delay set to: " + arg_text + "s")
            else:
                print_warn("PXRoadmapExecutor: Invalid argument for 'DELAY': ", arg_text)
        "LOG":
            _log_roadmap_activity("Log: " + arg_text)
        "TRIGGER":
            print("PXRoadmapExecutor: Conceptual TRIGGER command: ", arg_text)
            _log_roadmap_activity("TRIGGER: " + arg_text)
        "IF":
            if px_condition_checker:
                var if_parts = arg_text.split(" THEN ", false, 1)
                if if_parts.size() == 2:
                    var condition_string = if_parts[0].strip_edges()
                    var then_command_string = if_parts[1].strip_edges()
                    var condition_met = px_condition_checker.evaluate_condition(condition_string)
                    _log_roadmap_activity("IF '" + condition_string + "' -> " + str(condition_met))
                    if condition_met:
                        print("PXRoadmapExecutor: Condition met. Executing THEN command: '", then_command_string, "'")
                        _execute_command_logic(then_command_string.split(" ")[0].to_upper(), then_command_string.split(" ", false, 1)[1] if then_command_string.split(" ", false, 1).size() > 1 else "", then_command_string)
                    else:
                        print("PXRoadmapExecutor: Condition not met. Skipping THEN command.")
                else:
                    print_warn("PXRoadmapExecutor: Invalid 'IF' command format: ", full_step_text)
            else:
                print_err("PXRoadmapExecutor: PXRoadmapConditionChecker not available for 'IF' command.")
        "GENERATE": # To generate a roadmap
            if px_roadmap_generator:
                var generated_roadmap_steps = px_roadmap_generator.generate_roadmap_from_goal(arg_text)
                if not generated_roadmap_steps.is_empty():
                    _log_roadmap_activity("Generated roadmap for: " + arg_text)
                else:
                    _log_roadmap_activity("Failed to generate roadmap for: " + arg_text)
            else:
                print_err("PXRoadmapExecutor: PXRoadmapGenerator not available for 'GENERATE' command.")
        "WRITE_TO_FS_BLOCK": # Existing command, now with auto-injection logic
            # Format: WRITE_TO_FS_BLOCK:FILENAME:CONTENT:COL:ROW:TYPE_R,G,B:FLAGS_R,G,B:ORIGIN_R,G,B
            # This command is now handled by _execute_file_write_command
            _execute_file_write_command(arg_text, full_step_text)
        "WRITE_FILE_AUTO": # NEW command: Automatically finds slot and writes file
            # Format: WRITE_FILE_AUTO:FILENAME:CONTENT[:TYPE_R,G,B][:FLAGS_R,G,B][:ORIGIN_R,G,B]
            var parts = arg_text.split(":", false)
            if parts.size() >= 2:
                var filename = parts[0]
                var content = parts[1]
                var type_color = Color(0.0, 0.0, 1.0) # Default: Blue = Code
                var flags_color = Color(0.2, 0.2, 0.2) # Default: Grey = none
                var origin_color = Color(0.0, 0.0, 0.0) # Default: Black = system

                if parts.size() > 2:
                    var c = parts[2].split(",")
                    if c.size() == 3: type_color = Color(c[0].to_float()/255.0, c[1].to_float()/255.0, c[2].to_float()/255.0)
                if parts.size() > 3:
                    var f = parts[3].split(",")
                    if f.size() == 3: flags_color = Color(f[0].to_float()/255.0, f[1].to_float()/255.0, f[2].to_float()/255.0)
                if parts.size() > 4:
                    var o = parts[4].split(",")
                    if o.size() == 3: origin_color = Color(o[0].to_float()/255.0, o[1].to_float()/255.0, o[2].to_float()/255.0)

                if px_fs_writer:
                    var success = px_fs_writer.write_file_auto(filename, content, type_color, flags_color, origin_color)
                    if success:
                        _log_roadmap_activity("FS_WRITER: Auto-wrote file '%s'." % filename)
                    else:
                        _log_roadmap_activity("FS_WRITER: Failed to auto-write file '%s'." % filename)
                else:
                    _log_roadmap_activity("FS_WRITER: PXFSWriter not found for WRITE_FILE_AUTO.")
            else:
                print_warn("PXRoadmapExecutor: Invalid WRITE_FILE_AUTO format: ", arg_text)


        # --- Existing Self-Evolution Commands (Conceptual Execution) ---
        "INSTALL":
            _log_roadmap_activity("CONCEPTUAL: INSTALL module: " + arg_text)
            print("PXRoadmapExecutor: Conceptually installing module: ", arg_text)
        "ENABLE":
            _log_roadmap_activity("CONCEPTUAL: ENABLE feature: " + arg_text)
            print("PXRoadmapExecutor: Conceptually enabling feature: ", arg_text)
        "UPGRADE":
            _log_roadmap_activity("CONCEPTUAL: UPGRADE module: " + arg_text)
            print("PXRoadmapExecutor: Conceptually upgrading module: ", arg_text)
        "ADD":
            _log_roadmap_activity("CONCEPTUAL: ADD feature: " + arg_text)
            print("PXRoadmapExecutor: Conceptually adding feature: ", arg_text)
        "CREATE":
            _log_roadmap_activity("CONCEPTUAL: CREATE module: " + arg_text)
            print("PXRoadmapExecutor: Conceptually creating module: ", arg_text)
        "VERIFY":
            _log_roadmap_activity("CONCEPTUAL: VERIFY module: " + arg_text)
            print("PXRoadmapExecutor: Conceptually verifying module: ", arg_text)
        "INJECT":
            if arg_text.begins_with("SELF ROADMAP :: "):
                var roadmap_name = arg_text.replace("SELF ROADMAP :: ", "").strip_edges()
                _log_roadmap_activity("CONCEPTUAL: INJECTING SELF ROADMAP: " + roadmap_name)
                print("PXRoadmapExecutor: Conceptually injecting self roadmap: ", roadmap_name)
            else:
                _log_roadmap_activity("CONCEPTUAL: INJECT: " + arg_text)
        "RECORD":
            if px_roadmap_recorder:
                px_roadmap_recorder.start_recording("RRE_Executor_Recording")
                _log_roadmap_activity("CONCEPTUAL: RECORDING: " + arg_text)
                print("PXRoadmapExecutor: Conceptually recording roadmap: ", arg_text)
            else:
                print_err("PXRoadmapExecutor: PXRoadmapRecorder not available for 'RECORD' command.")
        "SAVE":
            if arg_text.ends_with(" TO SCROLL LIBRARY"):
                var scroll_name = arg_text.replace(" TO SCROLL LIBRARY", "").strip_edges()
                if px_scroll_library:
                    _log_roadmap_activity("CONCEPTUAL: SAVING TO LIBRARY: " + scroll_name)
                    print("PXRoadmapExecutor: Conceptually saving to scroll library: ", scroll_name)
                else:
                    print_err("PXRoadmapExecutor: PXScrollLibrary not available for 'SAVE' command.")
            else:
                _log_roadmap_activity("CONCEPTUAL: SAVE: " + arg_text)
        "ACTIVATE":
            _log_roadmap_activity("CONCEPTUAL: ACTIVATING: " + arg_text)
            print("PXRoadmapExecutor: Conceptually activating: ", arg_text)
        "SAVE CURRENT MEMORY SNAPSHOT":
            if px_digest_exporter:
                px_digest_exporter.export_state("RRE_Auto_Snapshot_" + str(OS.get_unix_time_from_system()))
                _log_roadmap_activity("CONCEPTUAL: SAVING MEMORY SNAPSHOT")
                print("PXRoadmapExecutor: Conceptually saving current memory snapshot.")
            else:
                print_err("PXRoadmapExecutor: PXDigestExporter not available for 'SAVE CURRENT MEMORY SNAPSHOT' command.")
        "DONE":
            _log_roadmap_activity("Roadmap indicates completion: DONE.")
            print("PXRoadmapExecutor: Roadmap indicates completion: DONE.")
            roadmap_active = false # Stop roadmap execution
        "EXPORT":
            if px_digest_exporter:
                px_digest_exporter.export_state(arg_text if not arg_text.is_empty() else "RRE_Export_Snapshot")
                _log_roadmap_activity("CONCEPTUAL: EXPORTING: " + arg_text)
                print("PXRoadmapExecutor: Conceptually exporting: ", arg_text)
            else:
                print_err("PXDigestExporter: PXDigestExporter not available for 'EXPORT' command.")
        "ARCHIVE_ROADMAP": # NEW COMMAND
            if current_roadmap.size() > 0:
                var filename = arg_text.strip_edges()
                if filename == "":
                    filename = "archived_roadmap_" + str(OS.get_unix_time_from_system()) + ".txt"

                var roadmap_content = current_roadmap.join("\n")
                var type_color = Color(0.0, 0.5, 1.0) # Cyan = roadmap
                var flags_color = Color(0.1, 0.1, 0.1) # Dim gray = archived
                var origin_color = Color(1.0, 0.8, 0.2) # Amber = RRE

                if px_fs_writer:
                    var success = px_fs_writer.write_file_auto(filename, roadmap_content, type_color, flags_color, origin_color)
                    if success:
                        _log_roadmap_activity("ARCHIVE_ROADMAP: Saved current roadmap as '%s'." % filename)
                    else:
                        _log_roadmap_activity("ARCHIVE_ROADMAP: Failed to save roadmap as '%s'." % filename)
                else:
                    _log_roadmap_activity("ARCHIVE_ROADMAP: PXFSWriter not found.")
            else:
                _log_roadmap_activity("ARCHIVE_ROADMAP: No active roadmap to archive.")
        "LOAD_ROADMAP_FROM_FS": # NEW COMMAND
            # Format: LOAD_ROADMAP_FROM_FS:FILENAME
            if px_fs_reader:
                var filename = arg_text.strip_edges()
                var file_content = px_fs_reader.read_file_by_name(filename)
                if not file_content.is_empty():
                    var roadmap_steps = file_content.split("\n")
                    # Filter out empty lines or comment lines that might be in the file content
                    roadmap_steps = roadmap_steps.filter(func(step): return not step.strip_edges().is_empty() and not step.strip_edges().begins_with("#"))
                    if not roadmap_steps.is_empty():
                        execute_roadmap(roadmap_steps) # Execute the loaded roadmap
                        _log_roadmap_activity("Loaded and executing roadmap '%s' from PXFS." % filename)
                    else:
                        _log_roadmap_activity("LOAD_ROADMAP_FROM_FS: Loaded roadmap '%s' from PXFS is empty or malformed." % filename)
                else:
                    _log_roadmap_activity("LOAD_ROADMAP_FROM_FS: Failed to load roadmap from PXFS: '%s' (file not found or empty)." % filename)
            else:
                _log_roadmap_activity("LOAD_ROADMAP_FROM_FS: PXFSReader not found.")
        "MUTATE_ROADMAP": # NEW COMMAND
            # Format: MUTATE_ROADMAP:FILENAME[:CONTEXT_KEY=VALUE]
            if px_roadmap_mutator and px_fs_reader and px_fs_writer:
                var parts = arg_text.split(":", false, 1) # Split filename from context
                var filename = parts[0].strip_edges()
                var context_str = ""
                if parts.size() > 1:
                    context_str = parts[1].strip_edges()

                var original_roadmap_content = px_fs_reader.read_file_by_name(filename)
                if not original_roadmap_content.is_empty():
                    var original_roadmap_steps = original_roadmap_content.split("\n").filter(func(step): return not step.strip_edges().is_empty() and not step.strip_edges().begins_with("#"))
                    
                    var mutation_context = {}
                    # Parse context_str (simple key=value pairs)
                    for item in context_str.split("&"):
                        var kv = item.split("=")
                        if kv.size() == 2:
                            mutation_context[kv[0].strip_edges()] = kv[1].strip_edges()

                    var mutated_roadmap_steps = px_roadmap_mutator.mutate_roadmap(original_roadmap_steps, mutation_context)
                    
                    var new_filename = "mutated_" + filename.replace(".txt", "").replace(".roadmap", "") + "_" + str(OS.get_unix_time_from_system()) + ".txt"
                    var type_color = Color(0.0, 0.5, 1.0) # Cyan = roadmap
                    var flags_color = Color(0.8, 0.5, 0.0) # Orange = mutated
                    var origin_color = Color(1.0, 0.8, 0.2) # Amber = RRE

                    var success = px_fs_writer.write_file_auto(new_filename, "\n".join(mutated_roadmap_steps), type_color, flags_color, origin_color)
                    if success:
                        _log_roadmap_activity("MUTATE_ROADMAP: Mutated '%s' to '%s' and saved to PXFS." % [filename, new_filename])
                    else:
                        _log_roadmap_activity("MUTATE_ROADMAP: Failed to save mutated roadmap '%s'." % new_filename)
                else:
                    _log_roadmap_activity("MUTATE_ROADMAP: Original roadmap '%s' not found or empty in PXFS." % filename)
            else:
                _log_roadmap_activity("MUTATE_ROADMAP: PXRoadmapMutator, PXFSReader, or PXFSWriter not found.")
        _:
            print_warn("PXRoadmapExecutor: Unknown roadmap command: '", command, "' in step: '", full_step_text, "'")
            _log_roadmap_activity("UNKNOWN CMD: " + command.left(10))

# --- Helper for File Write Commands ---
func _execute_file_write_command(arg_text: String, full_step_text: String):
    """
    Helper to parse and execute WRITE_TO_FS_BLOCK command.
    """
    var parts = arg_text.split(":", false)
    if parts.size() >= 5: # Filename, Content, Col, Row, Type_Color
        var filename = parts[0]
        var content = parts[1]
        var col = parts[2].to_int()
        var row = parts[3].to_int()
        var type_color_str = parts[4].split(",")
        var type_color = Color(type_color_str[0].to_float()/255.0, type_color_str[1].to_float()/255.0, type_color_str[2].to_float()/255.0)
        
        var flags_color = Color(0.2, 0.2, 0.2) # Default
        if parts.size() > 5:
            var flags_color_str = parts[5].split(",")
            flags_color = Color(flags_color_str[0].to_float()/255.0, flags_color_str[1].to_float()/255.0, flags_color_str[2].to_float()/255.0)

        var origin_agent_color = Color(0.0, 0.0, 0.0) # Default
        if parts.size() > 6:
            var origin_agent_color_str = parts[6].split(",")
            origin_agent_color = Color(origin_agent_color_str[0].to_float()/255.0, origin_agent_color_str[1].to_float()/255.0, origin_agent_color_str[2].to_float()/255.0)

        if px_fs_writer:
            var success = px_fs_writer.write_file(filename, content, col, row, type_color, flags_color, origin_agent_color)
            if success:
                _log_roadmap_activity("FS_WRITER: Wrote '%s' to (%d,%d)." % [filename, col, row])
            else:
                _log_roadmap_activity("FS_WRITER: Failed to write '%s'." % filename)
        else:
            _log_roadmap_activity("FS_WRITER: PXFSWriter not found.")
    else:
        print_warn("PXRoadmapExecutor: Invalid WRITE_TO_FS_BLOCK format: ", arg_text)


func advance_roadmap_step():
    """
    Advances the roadmap to the next step.
    """
    current_step_index += 1
    if current_step_index < current_roadmap.size():
        print("PXRoadmapExecutor: Advancing to step ", current_step_index, ": '", current_roadmap[current_step_index], "'")
    else:
        print("PXRoadmapExecutor: All roadmap steps processed.")


# --- Logging ---

func _log_roadmap_activity(message: String):
    """
    Helper function to log roadmap activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("RMAP: " + message)
    else:
        print("PXRoadmapExecutor (Console Log): ", message)

