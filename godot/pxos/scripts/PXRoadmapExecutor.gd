# PXRoadmapExecutor.gd
# This module reads a roadmap (as a sequence of text commands),
# parses its steps, and dispatches them as actions to other PXOS modules.
# It drives the self-evolution of the PXOS system.

extends Node

# --- Configuration ---
# Delay in seconds between executing each step of the roadmap.
@export var step_execution_delay: float = 1.0

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Main display
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging roadmap activity
@onready var px_glyph_compiler: PXGlyphCompiler = null # Will be initialized for PXAgentMemoryCoder

# PXAgentMemoryCoder instance, used to write commands to PXScroll region
var px_agent_memory_coder: PXAgentMemoryCoder = null

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
        # PXAgentMemoryCoder needs the image to be locked for its operations.
        # We'll pass it, and it will handle its own locking/unlocking.
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

    match command:
        "WRITE":
            # Command to write a glyph-based command to PXScroll's region
            if px_agent_memory_coder:
                px_agent_memory_coder.write_command(arg_text)
            else:
                print_err("PXRoadmapExecutor: PXAgentMemoryCoder not available for 'WRITE' command.")
        "DELAY":
            # Command to set a delay before the next step executes
            if arg_text.is_valid_float():
                step_execution_delay = arg_text.to_float()
                _log_roadmap_activity("Delay set to: " + arg_text + "s")
            else:
                print_warn("PXRoadmapExecutor: Invalid argument for 'DELAY': ", arg_text)
        "LOG":
            # Command to log a message to the scroll log
            _log_roadmap_activity("Log: " + arg_text)
        "TRIGGER":
            # This command is for triggering specific events or signals in other modules.
            # For example, triggering a specific stage in PXReflexKernel or an agent behavior.
            # You would implement specific signal emission or method calls here.
            print("PXRoadmapExecutor: Conceptual TRIGGER command: ", arg_text)
            _log_roadmap_activity("TRIGGER: " + arg_text)
            # Example: emit_signal("roadmap_trigger_event", arg_text)
        _:
            print_warn("PXRoadmapExecutor: Unknown roadmap command: '", command, "' in step: '", step_text, "'")
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


func _log_roadmap_activity(message: String):
    """
    Helper function to log messages to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("RMAP: " + message)
    else:
        print("PXRoadmapExecutor (Console Log): ", message)

