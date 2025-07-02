# PXNetHub.gd
# This script simulates a central networking hub for the PXOS.
# It reads pixel-encoded messages from a shared "inbox" region,
# routes them to designated "outbox" regions (agents' inboxes),
# and logs network activity visually on the display.

extends Node

# --- Configuration ---
# The frequency at which the NetHub will process messages.
const NET_HUB_CYCLE_FREQUENCY = 15 # Runs 4 times per second at 60 FPS

# --- Network Regions (Rect2: x, y, width, height) ---
# These regions define the "ports" for the network hub on the display.
const INBOX_REGION = Rect2(50, 0, 10, 4) # Shared area where agents write messages TO the hub
const OUTBOX_BASE_Y = 10 # Starting Y position for agent-specific outboxes
const OUTBOX_HEIGHT = 4 # Height of each agent's outbox region
const OUTBOX_WIDTH = 10 # Width of each agent's outbox region

# Region for logging network activity
const LOG_REGION = Rect2(60, 0, 4, 64) # Rightmost column for network logs

# --- Message Formatting ---
# Max length of a message (in characters) that can be processed.
# (OUTBOX_WIDTH / (GLYPH_WIDTH + GLYPH_SPACING_X))
const MAX_MESSAGE_LENGTH = 2 # Simplified for small regions, adjust based on glyph size

# --- Internal State ---
var message_queue: Array = [] # Queue of messages to be processed by the hub (e.g., ["TO:Agent_002:HI", "TO:Agent_001:ACK"])
var log_cursor_y = 0 # Tracks the current Y position for writing logs in LOG_REGION

# --- Dependencies ---
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen") # Adjust path as needed
var glyph_reader: PXGlyphReader = null
var glyph_compiler: PXGlyphCompiler = null

# Internal reference to the image data of the display for reading/writing
var display_image: Image = null

# A simple frame counter for the hub's cycle
var frame_counter = 0

# --- Agent Region Mapping (Simulated Directory Service) ---
# In a real system, agents would register their regions or the kernel would provide this.
# For demonstration, we'll hardcode a mapping of agent_id to their designated inbox region.
# Agents will read from these regions. PXNetHub writes to these regions.
var agent_inbox_regions = {
    "Agent_001": Rect2(OUTBOX_BASE_Y, 0, OUTBOX_WIDTH, OUTBOX_HEIGHT), # Example: Agent 001's inbox
    "Agent_002": Rect2(OUTBOX_BASE_Y, OUTBOX_HEIGHT + 1, OUTBOX_WIDTH, OUTBOX_HEIGHT) # Example: Agent 002's inbox
    # Add more agents and their specific inbox regions here
}

# --- Godot Lifecycle Methods ---

func _ready():
    # Initialize dependencies
    glyph_reader = PXGlyphReader.new()
    glyph_compiler = PXGlyphCompiler.new()

    if display_screen:
        if display_screen.texture:
            display_image = display_screen.texture.get_data()
            if display_image:
                display_image.lock() # Lock the image for pixel access
                print("PXNetHub: Initialized. Inbox: ", INBOX_REGION, ", Log: ", LOG_REGION)
                # Clear initial network regions
                clear_region(INBOX_REGION)
                clear_region(LOG_REGION)
                for agent_id in agent_inbox_regions:
                    clear_region(agent_inbox_regions[agent_id])
            else:
                print_err("PXNetHub: Could not get image data from display_screen texture.")
        else:
            print_err("PXNetHub: DisplayScreen has no texture. Ensure PXBootPainter runs first.")
    else:
        print_err("PXNetHub: 'DisplayScreen' TextureRect not found. Cannot operate.")

func _process(delta):
    # Only run the hub's main loop if it's properly initialized
    if display_image and display_image.is_locked():
        frame_counter += 1
        if frame_counter >= NET_HUB_CYCLE_FREQUENCY:
            frame_counter = 0 # Reset counter

            print("\n--- PXNetHub Cycle Start ---")
            read_inbox()
            process_queue()
            update_display() # Update the display after all read/write operations
            print("--- PXNetHub Cycle End ---\n")

func _exit_tree():
    # Unlock the image when the hub is removed from the scene tree
    if display_image and display_image.is_locked():
        display_image.unlock()
    print("PXNetHub: Cleaned up image lock.")

# --- Core Networking Logic ---

func read_inbox():
    # Scans the INBOX_REGION for new glyph messages from agents.
    if not display_image or not display_image.is_locked(): return
    if not glyph_reader: return

    print("PXNetHub: Reading inbox region ", INBOX_REGION)
    var incoming_message = glyph_reader.read_glyphs_from_image(display_image, INBOX_REGION)

    if incoming_message:
        print("  [Inbox] Received: '", incoming_message, "'")
        message_queue.append(incoming_message)
        log_activity("IN: " + incoming_message.left(MAX_MESSAGE_LENGTH)) # Log truncated message
        clear_region(INBOX_REGION) # Clear inbox after reading to signal message consumed
    else:
        print("  [Inbox] No new messages.")

func process_queue():
    # Processes messages in the queue, routing them to target agents.
    if not display_image or not display_image.is_locked(): return
    if not glyph_compiler: return

    if message_queue.is_empty():
        print("PXNetHub: Message queue is empty.")
        return

    print("PXNetHub: Processing message queue (", message_queue.size(), " messages)...")
    var processed_messages = []
    for msg in message_queue:
        # Expected format: "TO:AGENT_ID:MESSAGE_CONTENT"
        var parts = msg.split(":")
        if parts.size() >= 3 and parts[0] == "TO":
            var target_agent_id = parts[1]
            var message_content = parts[2]
            var target_region = agent_inbox_regions.get(target_agent_id)

            if target_region:
                write_outbox(target_region, message_content)
                log_activity("OUT:" + target_agent_id.right(3) + ":" + message_content.left(MAX_MESSAGE_LENGTH))
                processed_messages.append(msg)
                print("  [Routing] Sent '", message_content, "' to '", target_agent_id, "' at ", target_region)
            else:
                print_err("  [Routing Error] Unknown target agent ID: '", target_agent_id, "'")
                log_activity("ERR:UNK:" + target_agent_id.right(3))
        else:
            print_err("  [Parsing Error] Invalid message format: '", msg, "'")
            log_activity("ERR:FMT")

    # Remove processed messages from the queue
    for msg in processed_messages:
        message_queue.erase(msg)

func write_outbox(target_region: Rect2, message: String):
    # Writes a pixel-encoded message to a specific target region (an agent's inbox).
    if not display_image or not display_image.is_locked(): return
    if not glyph_compiler: return

    # Clear the target region before writing to avoid pixel overlap
    clear_region(target_region)

    # Compile and draw the message
    var success = glyph_compiler.compile_text_to_image(display_image, message, target_region.position, false)
    if not success:
        print_err("PXNetHub: Failed to write message '", message, "' to region ", target_region)

func log_activity(log_message: String):
    # Writes a log message as glyphs into the LOG_REGION.
    if not display_image or not display_image.is_locked(): return
    if not glyph_compiler: return

    var log_start_pos = Vector2(LOG_REGION.position.x, LOG_REGION.position.y + log_cursor_y)

    # Clear the line before writing
    for x in range(int(log_start_pos.x), int(log_start_pos.x + LOG_REGION.size.x)):
        for y in range(int(log_start_pos.y), int(log_start_pos.y + glyph_compiler.GLYPH_HEIGHT)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, glyph_compiler.GLYPH_INACTIVE_COLOR)


    var success = glyph_compiler.compile_text_to_image(display_image, log_message, log_start_pos, false)
    if success:
        log_cursor_y += glyph_compiler.GLYPH_HEIGHT + glyph_compiler.GLYPH_SPACING_Y
        # Wrap cursor if it goes beyond the log region
        if log_cursor_y >= LOG_REGION.size.y:
            log_cursor_y = 0
            clear_region(LOG_REGION) # Clear the entire log region when wrapping
    else:
        print_err("PXNetHub: Failed to log activity: '", log_message, "'")

func clear_region(region: Rect2):
    # Helper function to clear a specified region on the display image.
    if not display_image or not display_image.is_locked(): return

    for y in range(int(region.position.y), int(region.position.y + region.size.y)):
        for x in range(int(region.position.x), int(region.position.x + region.size.x)):
            if x >= 0 and x < display_image.get_width() and y >= 0 and y < display_image.get_height():
                display_image.set_pixel(x, y, glyph_compiler.GLYPH_INACTIVE_COLOR) # Use inactive color for clearing


func update_display():
    # Updates the TextureRect with the modified display_image.
    if display_screen:
        var new_texture = ImageTexture.new()
        new_texture.create_from_image(display_image, 0)
        display_screen.texture = new_texture
    else:
        print_err("PXNetHub: 'DisplayScreen' TextureRect not found for display update.")

