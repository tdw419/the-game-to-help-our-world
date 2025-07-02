# PXAgentNode.gd
# This script represents an autonomous agent within the PXOS.
# Each agent operates within a defined visual territory (Rect2) on the display,
# observes pixel patterns (opcodes and glyphs), reacts to them, and
# can write new pixel data (mutations, glyphs) back to the canvas.

extends Node2D # Extends Node2D as agents will have a visual position/territory

# --- Configuration ---
# The frequency at which this agent will perform its observation and reaction cycle.
const AGENT_CYCLE_FREQUENCY = 30 # Runs twice per second at 60 FPS

# --- Agent Properties ---
@export var agent_id: String = "Agent_001" # Unique identifier for this agent
@export var agent_region_rect: Rect2 = Rect2(0, 0, 10, 10) # The visual territory this agent observes and operates within

# --- Internal State ---
var local_state: Dictionary = {
    "mood": "neutral",
    "last_message_received": "",
    "response_count": 0
}

# --- Dependencies ---
# References to the display screen (TextureRect) and utility scripts
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
var glyph_reader: PXGlyphReader = null
var glyph_compiler: PXGlyphCompiler = null

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# A simple frame counter for the agent's cycle
var frame_counter = 0

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies and agent state
    glyph_reader = PXGlyphReader.new()
    glyph_compiler = PXGlyphCompiler.new()

    if display_screen:
        # Get the initial image data from the display screen
        if display_screen.texture:
            display_image = display_screen.texture.get_data()
            if display_image:
                display_image.lock() # Lock the image for pixel access
                print("PXAgentNode '", agent_id, "': Initialized. Operating in region: ", agent_region_rect)
            else:
                print_err("PXAgentNode '", agent_id, "': Could not get image data from display_screen texture.")
        else:
            print_err("PXAgentNode '", agent_id, "': DisplayScreen has no texture. Ensure PXBootPainter runs first.")
    else:
        print_err("PXAgentNode '", agent_id, "': 'DisplayScreen' TextureRect not found. Cannot operate.")

    # Set the agent's position to the top-left of its region for visual debugging if needed
    self.position = agent_region_rect.position

func _process(delta):
    # Only run the agent's main loop if it's properly initialized
    if display_image and display_image.is_locked():
        frame_counter += 1
        if frame_counter >= AGENT_CYCLE_FREQUENCY:
            frame_counter = 0 # Reset counter

            print("\n--- PXAgentNode '", agent_id, "' Cycle Start ---")
            observe_region()
            react_to_observations()
            mutate_region()
            update_local_state() # Update internal state after actions
            print("--- PXAgentNode '", agent_id, "' Cycle End ---\n")

func _exit_tree():
    # Unlock the image when the agent is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXAgentNode '", agent_id, "': Cleaned up image lock.")

# --- Agent Core Logic ---

func observe_region():
    # This function scans the agent's defined region for opcodes and glyphs.
    if not display_image or not display_image.is_locked():
        print_err("PXAgentNode '", agent_id, "': Display image not available or locked for observation.")
        return

    print("PXAgentNode '", agent_id, "': Observing region ", agent_region_rect)

    # --- Read Glyphs from Agent's Region ---
    # This assumes glyphs might be written in the agent's region
    var message_read = glyph_reader.read_glyphs_from_image(display_image, agent_region_rect)
    if message_read:
        local_state["last_message_received"] = message_read
        print("  [Observation] Detected glyph message: '", message_read, "'")
    else:
        local_state["last_message_received"] = ""
        print("  [Observation] No recognizable glyph messages.")

    # --- Read Opcodes (simplified for now, can use PXReflexKernel's opcode_map) ---
    # For a full implementation, you'd replicate or share the opcode_map from PXReflexKernel
    # For now, let's just check for a specific color as an "opcode"
    var detected_opcode_color = display_image.get_pixel(
        int(agent_region_rect.position.x), int(agent_region_rect.position.y)
    )
    if detected_opcode_color.is_equal_approx(Color(1.0, 0.0, 0.0)): # Assuming PXL_HALT from kernel
        print("  [Observation] Detected HALT opcode at (", int(agent_region_rect.position.x), ",", int(agent_region_rect.position.y), ")")
        local_state["mood"] = "alert"
    else:
        local_state["mood"] = "neutral"


func react_to_observations():
    # This function contains the agent's decision-making logic based on its observations.
    print("PXAgentNode '", agent_id, "': Reacting to observations...")

    if local_state["last_message_received"].find("HI") != -1:
        local_state["mood"] = "friendly"
        print("  [Reaction] Detected 'HI'. Setting mood to friendly.")
    elif local_state["last_message_received"].find("JUMP") != -1:
        print("  [Reaction] Detected 'JUMP'. Preparing to jump (conceptually).")
        # In a visual system, "jumping" could mean moving its own visual representation
        # or writing a "JUMP_ACK" message.
    elif local_state["mood"] == "alert":
        print("  [Reaction] Mood is alert. Considering a response.")

    # Example: If the agent is friendly, it might decide to respond.
    if local_state["mood"] == "friendly" and local_state["response_count"] == 0:
        local_state["response_count"] += 1
        print("  [Reaction] Responding to 'HI' for the first time.")
        # This will trigger a visual mutation in mutate_region()

func mutate_region():
    # This function allows the agent to write new pixel data back to the canvas.
    # It can write opcodes, glyphs, or simple data pixels.

    if not display_image or not display_image.is_locked():
        print_err("PXAgentNode '", agent_id, "': Display image not available or locked for mutation.")
        return
    if not display_screen:
        print_err("PXAgentNode '", agent_id, "': 'DisplayScreen' TextureRect not found for visual mutation.")
        return

    print("PXAgentNode '", agent_id, "': Mutating region...")

    # Example 1: Agent writes a pixel based on its mood
    var mood_color = Color(0.0, 0.0, 0.0)
    if local_state["mood"] == "friendly":
        mood_color = Color(0.0, 0.8, 0.0) # Bright green for friendly
    elif local_state["mood"] == "alert":
        mood_color = Color(0.8, 0.8, 0.0) # Yellow for alert
    else:
        mood_color = Color(0.5, 0.5, 0.5) # Grey for neutral

    # Write a small status pixel in its region (e.g., top-right corner of its region)
    var status_pixel_x = int(agent_region_rect.position.x + agent_region_rect.size.x - 1)
    var status_pixel_y = int(agent_region_rect.position.y)
    if display_image.get_width() > status_pixel_x and display_image.get_height() > status_pixel_y:
        display_image.set_pixel(status_pixel_x, status_pixel_y, mood_color)
        print("  [Mutation] Wrote mood pixel (", mood_color, ") at (", status_pixel_x, ",", status_pixel_y, ")")

    # Example 2: Agent responds with a glyph message if friendly and hasn't responded yet
    if local_state["mood"] == "friendly" and local_state["response_count"] == 1:
        var response_message = "HI BACK!"
        var response_start_pos = Vector2(agent_region_rect.position.x, agent_region_rect.position.y + GLYPH_HEIGHT + GLYPH_SPACING_Y)
        if glyph_compiler.compile_text_to_image(display_image, response_message, response_start_pos, true):
            print("  [Mutation] Agent '", agent_id, "' responded with glyph message: '", response_message, "'")
            # Increment response count to avoid spamming
            local_state["response_count"] += 1
        else:
            print_err("  [Mutation] Failed to compile agent response message.")

    # After all mutations, update the display
    var new_texture = ImageTexture.new()
    new_texture.create_from_image(display_image, 0)
    display_screen.texture = new_texture


func update_local_state():
    # This function updates the agent's internal state variables.
    # For now, it's mostly driven by reactions, but could involve more complex logic.
    print("PXAgentNode '", agent_id, "': Local state updated. Current mood: ", local_state["mood"])


