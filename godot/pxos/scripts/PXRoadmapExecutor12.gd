# PXRoadmapExecutor.gd
# This module reads a roadmap (as a sequence of text commands),
# parses its steps, and dispatches them as actions to other PXOS modules.
# It drives the self-evolution of the PXOS system.
#
# UPDATED: Now includes conceptual execution for self-evolution commands.

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
    if not px_scroll_log or not px_condition_checker or not px_roadmap_memory or not px_roadmap_generator or not px_scroll_library:
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
    # This function is now part of PXRoadmapExecutor, but it relies on PXRoadmapMemoryRegion
    # to actually read the roadmap from memory.
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
    _log_roadmap_activity("STEP " + str(current_step_index) + ": " + step_text.left(15)) # Log truncated step

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
        "GENERATE": # NEW COMMAND: To generate a roadmap
            if px_roadmap_generator:
                var generated_roadmap_steps = px_roadmap_generator.generate_roadmap_from_goal(arg_text)
                if not generated_roadmap_steps.is_empty():
                    _log_roadmap_activity("Generated roadmap for: " + arg_text)
                    # You might then write this to memory or execute it directly
                    # For now, just log its generation.
                else:
                    _log_roadmap_activity("Failed to generate roadmap for: " + arg_text)
            else:
                print_err("PXRoadmapExecutor: PXRoadmapGenerator not available for 'GENERATE' command.")

        # --- NEW: Self-Evolution Commands (Conceptual Execution) ---
        "INSTALL":
            _log_roadmap_activity("CONCEPTUAL: INSTALL module: " + arg_text)
            print("PXRoadmapExecutor: Conceptually installing module: ", arg_text)
        "ENABLE":
            _log_roadmap_activity("CONCEPTUAL: ENABLE feature: " + arg_text)
            print("PXRoadmapExecutor: Conceptually enabling feature: ", arg_text)
        "INJECT": # Example: INJECT SELF ROADMAP :: PX_RRE_SELF_EVOLUTION_BOOTSTRAP
            if arg_text.begins_with("SELF ROADMAP :: "):
                var roadmap_name = arg_text.replace("SELF ROADMAP :: ", "").strip_edges()
                _log_roadmap_activity("CONCEPTUAL: INJECTING SELF ROADMAP: " + roadmap_name)
                print("PXRoadmapExecutor: Conceptually injecting self roadmap: ", roadmap_name)
                # In a real scenario, this would trigger PXRoadmapInjector or similar
                # to inject a specific roadmap from a library or generator.
            else:
                _log_roadmap_activity("CONCEPTUAL: INJECT: " + arg_text)
        "RECORD": # Example: RECORD PX_RRE_SELF_EVOLUTION_BOOTSTRAP
            _log_roadmap_activity("CONCEPTUAL: RECORDING: " + arg_text)
            print("PXRoadmapExecutor: Conceptually recording roadmap: ", arg_text)
            # This would trigger PXRoadmapRecorder.start_recording()
        "SAVE": # Example: SAVE PX_RRE_SELF_EVOLUTION_BOOTSTRAP TO SCROLL LIBRARY
            if arg_text.ends_with(" TO SCROLL LIBRARY"):
                var scroll_name = arg_text.replace(" TO SCROLL LIBRARY", "").strip_edges()
                _log_roadmap_activity("CONCEPTUAL: SAVING TO LIBRARY: " + scroll_name)
                print("PXRoadmapExecutor: Conceptually saving to scroll library: ", scroll_name)
                # This would trigger PXScrollLibrary.save_scroll()
            else:
                _log_roadmap_activity("CONCEPTUAL: SAVE: " + arg_text)
        "ACTIVATE": # Example: ACTIVATE PXReflexFeedbackLogger
            _log_roadmap_activity("CONCEPTUAL: ACTIVATING: " + arg_text)
            print("PXRoadmapExecutor: Conceptually activating: ", arg_text)
        "SAVE CURRENT MEMORY SNAPSHOT": # Example: SAVE CURRENT MEMORY SNAPSHOT
            _log_roadmap_activity("CONCEPTUAL: SAVING MEMORY SNAPSHOT")
            print("PXRoadmapExecutor: Conceptually saving current memory snapshot.")
            # This would trigger PXDigestExporter.export_state()
        "DONE": # Example: DONE
            _log_roadmap_activity("Roadmap indicates completion: DONE.")
            print("PXRoadmapExecutor: Roadmap indicates completion: DONE.")
            roadmap_active = false # Stop roadmap execution
        _:
            print_warn("PXRoadmapExecutor: Unknown roadmap command: '", command, "' in step: '", full_step_text, "'")
            _log_roadmap_activity("UNKNOWN CMD: " + command.left(10))


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

