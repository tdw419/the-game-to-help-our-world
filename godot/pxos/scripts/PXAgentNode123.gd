# PXAgentNode.gd
# This script represents an autonomous agent within the PXOS.
# It defines the base interface for agents and handles their registration
# with the PXAgentReflexBridge.
#
# UPDATED: Now includes Rapid Roadmap Execution (RRE) capabilities,
# allowing agents to execute glyph-based directives from their region.

class_name PXAgentNode # Define this as a base class for other agents to extend
extends Node2D # Extends Node2D as agents will have a visual position/territory

# --- Configuration ---
# The frequency at which this agent will perform its observation and reaction cycle.
const AGENT_CYCLE_FREQUENCY = 30 # Runs twice per second at 60 FPS

# NEW: Enable RRE mode for this agent. If true, the agent will attempt to execute
# directives found in its region, starting with ":: EXECUTE ".
@export var enable_rre_mode: bool = false

# --- Agent Properties ---
@export var agent_id: String = "Agent_Base" # Unique identifier for this agent
@export var agent_region_rect: Rect2 = Rect2(0, 0, 10, 10) # The visual territory this agent observes and operates within

# --- Internal State ---
var local_state: Dictionary = {
    "mood": "neutral",
    "last_message_received": "",
    "response_count": 0,
    "rre_active": false # NEW: Internal flag for RRE loop status
}

# --- Dependencies ---
# References to the display screen (TextureRect) and utility scripts
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
@onready var px_agent_reflex_bridge: PXAgentReflexBridge = get_node_or_null("../PXAgentReflexBridge") # For daemon communication
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # For memory interactions
var glyph_reader: PXGlyphReader = null
var glyph_compiler: PXGlyphCompiler = null
var px_memory_coder: PXAgentMemoryCoder = null # For writing commands to scroll region

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# A simple frame counter for the agent's cycle
var frame_counter = 0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_reader = PXGlyphReader.new()
    glyph_compiler = PXGlyphCompiler.new()

    if display_screen:
        # Get the initial image data from the display screen
        if display_screen.texture:
            display_image = display_screen.texture.get_data()
            if display_image:
                display_image.lock() # Lock the image for pixel access
                # Initialize PXAgentMemoryCoder, passing necessary dependencies
                px_memory_coder = PXAgentMemoryCoder.new(display_image, glyph_compiler, display_screen)
                if not px_memory_coder:
                    print_err("PXAgentNode '", agent_id, "': Failed to initialize PXAgentMemoryCoder.")

                print("PXAgentNode '", agent_id, "': Initialized. Operating in region: ", agent_region_rect)
            else:
                print_err("PXAgentNode '", agent_id, "': Could not get image data from display_screen texture.")
        else:
            print_err("PXAgentNode '", agent_id, "': DisplayScreen has no texture. Ensure PXBootPainter runs first.")
    else:
        print_err("PXAgentNode '", agent_id, "': 'DisplayScreen' TextureRect not found. Cannot operate.")

    # Register with the bridge
    if px_agent_reflex_bridge:
        px_agent_reflex_bridge.register_agent(agent_id, self)
    else:
        print_err("PXAgentNode '", agent_id, "': PXAgentReflexBridge not found. Cannot register.")

    # Initialize RRE state
    local_state["rre_active"] = enable_rre_mode


func _process(delta):
    # Only run the agent's main loop if it's properly initialized
    if display_image and display_image.is_locked():
        frame_counter += 1
        if frame_counter >= AGENT_CYCLE_FREQUENCY:
            frame_counter = 0 # Reset counter

            observe_region()
            react_to_observations() # This will now call execute_rre_step if RRE is active
            mutate_region()
            update_local_state()


func _exit_tree():
    # Unregister when removed from tree
    if px_agent_reflex_bridge:
        px_agent_reflex_bridge.unregister_agent(agent_id)
    # Unlock the image when the agent is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXAgentNode '", agent_id, "': Cleaned up image lock.")

# --- Agent Core Logic (To be overridden by subclasses) ---

func observe_region():
    """Scans the agent's defined region for opcodes and glyphs."""
    # Base implementation (can be extended/overridden)
    if not display_image or not display_image.is_locked(): return
    if not glyph_reader: return

    var message_read = glyph_reader.read_glyphs_from_image(display_image, agent_region_rect)
    if message_read:
        local_state["last_message_received"] = message_read
    else:
        local_state["last_message_received"] = ""

    # (Simplified opcode check - can be expanded)
    # NEW: PXL_HALT recognition for RRE mode
    var detected_opcode_color = display_image.get_pixel(
        int(agent_region_rect.position.x), int(agent_region_rect.position.y)
    )
    if detected_opcode_color.is_equal_approx(Color(1.0, 0.0, 0.0)): # Red pixel = HALT
        if local_state["rre_active"]:
            local_state["mood"] = "halted"
            local_state["rre_active"] = false # Stop RRE loop
            _log_agent_activity("RRE HALTED by red pixel.")
        else:
            local_state["mood"] = "alert" # Still alert if not in RRE mode
    else:
        if local_state["mood"] == "halted" and local_state["rre_active"] == false:
            # If HALT pixel is removed, maybe reactivate or change mood
            local_state["mood"] = "neutral" # Or some other recovery mood
            # local_state["rre_active"] = enable_rre_mode # Option to re-enable RRE if HALT is removed


func react_to_observations():
    """Contains the agent's decision-making logic based on its observations."""
    # Base implementation (can be extended/overridden)
    if local_state["rre_active"]: # NEW: Prioritize RRE execution if active
        execute_rre_step()
        return # Skip other reactions if RRE is handling behavior

    # Existing non-RRE reactions
    if local_state["last_message_received"].find("HI") != -1:
        local_state["mood"] = "friendly"
    elif local_state["last_message_received"].find("JUMP") != -1:
        _log_agent_activity("Reacting to 'JUMP'.")


func mutate_region():
    """Allows the agent to write new pixel data back to the canvas."""
    # Base implementation (can be extended/overridden)
    if not display_image or not display_image.is_locked(): return
    if not display_screen: return

    # Write a small status pixel in its region (e.g., top-right corner of its region)
    var mood_color = Color(0.0, 0.0, 0.0)
    if local_state["mood"] == "friendly": mood_color = Color(0.0, 0.8, 0.0)
    elif local_state["mood"] == "alert": mood_color = Color(0.8, 0.8, 0.0)
    elif local_state["mood"] == "halted": mood_color = Color(1.0, 0.0, 0.0) # Red for halted
    else: mood_color = Color(0.5, 0.5, 0.5)

    var status_pixel_x = int(agent_region_rect.position.x + agent_region_rect.size.x - 1)
    var status_pixel_y = int(agent_region_rect.position.y)
    if display_image.get_width() > status_pixel_x and display_image.get_height() > status_pixel_y:
        display_image.set_pixel(status_pixel_x, status_pixel_y, mood_color)

    # Example: Agent responds with a glyph message if friendly and hasn't responded yet
    if local_state["mood"] == "friendly" and local_state["response_count"] == 1:
        var response_message = "HI BACK!"
        var response_start_pos = Vector2(agent_region_rect.position.x, agent_region_rect.position.y + glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y)
        if px_memory_coder and px_memory_coder.write_command(response_message): # Use coder to write to scroll region
            _log_agent_activity("Responded with glyph message: '" + response_message + "'")
            local_state["response_count"] += 1
        else:
            _log_agent_activity("Failed to write response message.")

    # Update the display
    var new_texture = ImageTexture.new()
    new_texture.create_from_image(display_image, 0)
    display_screen.texture = new_texture


func update_local_state():
    """Updates the agent's internal state variables."""
    # Base implementation (can be extended/overridden)
    pass

# --- NEW: Rapid Roadmap Execution (RRE) Logic ---

func execute_rre_step():
    """
    Executes a single RRE step based on the last message received in the agent's region.
    """
    var current_directive = local_state["last_message_received"]
    if current_directive.is_empty():
        return # No directive to execute

    if current_directive.find(":: EXECUTE ") != -1:
        var action = current_directive.replace(":: EXECUTE ", "").strip_edges()
        _log_agent_activity("RRE: Executing action: " + action)

        # Clear the message in its region to consume the command
        if px_memory_coder:
            px_memory_coder.write_command("") # Write empty string to clear agent's region
            _log_agent_activity("RRE: Consumed directive.")

        # Example: trigger internal response or dispatch
        match action:
            "PING":
                _log_agent_activity("RRE: PING received.")
                if px_memory_coder: px_memory_coder.write_command("PONG") # Respond via coder
            "CONFIRM_MOOD":
                if px_memory_coder: px_memory_coder.write_command("MOOD:" + local_state["mood"].to_upper())
            "RANDOMIZE_COLOR":
                _mutate_color_random()
            "HALT": # Explicit HALT command within RRE
                local_state["mood"] = "halted"
                local_state["rre_active"] = false
                _log_agent_activity("RRE: Explicit HALT command received.")
            _:
                _log_agent_activity("RRE: Unknown action '" + action + "'")
                if px_memory_coder: px_memory_coder.write_command("RRE_ERR:UNKNOWN_ACTION")
    else:
        # If message is not an RRE directive, and RRE is active, it's an error or data
        if local_state["rre_active"]:
            _log_agent_activity("RRE: Non-directive message found: '" + current_directive + "'")


func _mutate_color_random():
    """Helper function to change the agent's region color randomly."""
    if not display_image or not display_image.is_locked(): return
    if not display_screen: return

    var random_color = Color(randf(), randf(), randf(), 1.0)
    for y in range(int(agent_region_rect.position.y), int(agent_region_rect.position.y + agent_region_rect.size.y)):
        for x in range(int(agent_region_rect.position.x), int(agent_region_rect.position.x + agent_region_rect.size.x)):
            if display_image.get_width() > x and display_image.get_height() > y:
                display_image.set_pixel(x, y, random_color)
    _log_agent_activity("RRE: Randomized region color.")
    # Update the display
    var new_texture = ImageTexture.new()
    new_texture.create_from_image(display_image, 0)
    display_screen.texture = new_texture


# --- Public Methods for Daemon Commands (To be implemented by subclasses) ---
# These methods are called by PXAgentReflexBridge.

func confirm_state(message: String = ""):
    """Daemon command: Agent confirms its current state."""
    _log_agent_activity("DAEMON_CMD: Confirming state. Message: " + message)

func prepare_snapshot(name: String = ""):
    """Daemon command: Agent prepares for a system snapshot."""
    _log_agent_activity("DAEMON_CMD: Preparing for snapshot: " + name)

func set_mood(mood_name: String):
    """Daemon command: Agent's mood is set externally."""
    _log_agent_activity("DAEMON_CMD: Setting mood to: " + mood_name)
    local_state["mood"] = mood_name

func log_agent_message(message: String):
    """Daemon command: Agent logs a message directly."""
    _log_agent_activity("DAEMON_CMD: Message: " + message)

# --- Helper for Agent's Own Logging ---
func _log_agent_activity(message: String):
    if px_scroll_log:
        px_scroll_log.add_line("AGENT: " + agent_id + ": " + message)
    else:
        print("PXAgentNode '", agent_id, "' (Console Log): ", message)

