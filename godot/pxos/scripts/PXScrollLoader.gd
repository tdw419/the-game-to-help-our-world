# PXScrollLoader.gd
# This module manages and delivers scroll-based RRE (Rapid Roadmap Execution)
# programs to PXAgentNode instances. It allows for defining multi-step
# sequences of glyph-based commands and placing them into an agent's
# designated region for execution.

extends Node

# --- Configuration ---
# How often the loader checks for new delivery requests or manages active scrolls.
@export var management_frequency_sec: float = 1.0

# --- Dependencies ---
@onready var px_agent_reflex_bridge: PXAgentReflexBridge = get_node_or_null("../PXAgentReflexBridge") # To get agent regions
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To write scrolls to memory regions
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging loader activity

# --- Internal State ---
# A dictionary to store predefined scrolls (programs).
# Key: scroll_name (String), Value: Array[String] (list of RRE commands)
var predefined_scrolls: Dictionary = {
    "AGENT_BOOT_SEQUENCE": [
        ":: EXECUTE CONFIRM_MOOD",
        ":: EXECUTE PING",
        ":: EXECUTE RANDOMIZE_COLOR",
        ":: EXECUTE LOG_AGENT:Boot Sequence Complete",
        ":: EXECUTE HALT" # Halt the RRE loop after sequence
    ],
    "DIAGNOSTIC_ROUTINE": [
        ":: EXECUTE LOG_AGENT:Running Diagnostics",
        ":: EXECUTE CONFIRM_MOOD",
        ":: EXECUTE LOG_AGENT:Mood Confirmed",
        ":: EXECUTE PX_AGENT:*:CONFIRM_STATE", # Example: broadcast to all agents
        ":: EXECUTE LOG_AGENT:Diagnostics Complete"
    ],
    "EXPLORE_AREA": [
        ":: EXECUTE LOG_AGENT:Starting Exploration",
        ":: EXECUTE MOVE 1 1", # Conceptual move command for agent
        ":: EXECUTE MOVE 2 1",
        ":: EXECUTE MOVE 3 1",
        ":: EXECUTE LOG_AGENT:Exploration Done"
    ]
}

# A queue for delivery requests: [{"agent_id": "JUNIOR", "scroll_name": "AGENT_BOOT_SEQUENCE"}]
var delivery_queue: Array = []

var time_since_last_management: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_agent_reflex_bridge or not px_ztxt_memory or not px_scroll_log:
        print_err("PXScrollLoader: Essential dependencies missing. Loader disabled.")
        set_process(false)
        return

    print("PXScrollLoader: Initialized. Ready to deliver scrolls.")

func _process(delta):
    time_since_last_management += delta
    if time_since_last_management >= management_frequency_sec:
        time_since_last_management = 0.0
        _process_delivery_queue()

# --- Core Scroll Delivery API ---

func request_scroll_delivery(agent_id: String, scroll_name: String) -> bool:
    """
    Adds a request to the queue to deliver a named scroll to a specific agent.

    Args:
        agent_id (String): The ID of the target agent.
        scroll_name (String): The name of the predefined scroll to deliver.

    Returns:
        bool: True if the request was added, false if scroll/agent not found.
    """
    if not predefined_scrolls.has(scroll_name):
        _log_loader_activity("ERROR: Scroll '" + scroll_name + "' not found.")
        print_err("PXScrollLoader: Scroll '" + scroll_name + "' not found.")
        return false

    # We need the agent's region to write the scroll.
    # PXAgentReflexBridge should ideally provide this, or agents register their region.
    # For now, we'll assume agent_id maps to a region that can be inferred or retrieved.
    # A better design would be for PXAgentReflexBridge to store agent regions.
    # For this scaffold, we'll get the agent node and then its region.
    var agent_node = px_agent_reflex_bridge.registered_agents.get(agent_id)
    if not agent_node or not agent_node is PXAgentNode: # Check if it's a valid PXAgentNode
        _log_loader_activity("ERROR: Agent '" + agent_id + "' not found or not a PXAgentNode.")
        print_err("PXScrollLoader: Agent '" + agent_id + "' not found or not a PXAgentNode.")
        return false

    delivery_queue.append({"agent_id": agent_id, "scroll_name": scroll_name, "agent_region": agent_node.agent_region_rect})
    _log_loader_activity("Request added: Deliver '" + scroll_name + "' to '" + agent_id + "'.")
    print("PXScrollLoader: Request added to queue for agent '", agent_id, "': '", scroll_name, "'")
    return true


func _process_delivery_queue():
    """
    Processes pending scroll delivery requests.
    """
    if delivery_queue.is_empty():
        return

    var request = delivery_queue.pop_front()
    var agent_id = request.agent_id
    var scroll_name = request.scroll_name
    var agent_region = request.agent_region

    _log_loader_activity("DELIVERING: '" + scroll_name + "' to '" + agent_id + "'.")
    print("PXScrollLoader: Delivering scroll '", scroll_name, "' to agent '", agent_id, "'.")

    var scroll_content_array = predefined_scrolls[scroll_name]
    var scroll_content_ztxt = "\n".join(scroll_content_array) # Join steps with newlines

    # Write the scroll content to the agent's region using PXZTXTMemory
    if px_ztxt_memory.write_ztxt(agent_region, scroll_content_ztxt):
        _log_loader_activity("Delivered '" + scroll_name + "' to '" + agent_id + "'.")
        # Optionally, tell the agent to start RRE if it's not already
        var agent_node = px_agent_reflex_bridge.registered_agents.get(agent_id)
        if agent_node and agent_node is PXAgentNode:
            agent_node.local_state["rre_active"] = true # Activate agent's RRE loop
            agent_node.local_state["mood"] = "executing_rre" # Update mood
            _log_loader_activity("Activated RRE for '" + agent_id + "'.")
    else:
        _log_loader_activity("FAILED to deliver '" + scroll_name + "' to '" + agent_id + "'.")
        print_err("PXScrollLoader: Failed to deliver scroll '", scroll_name, "' to '", agent_id, "'.")

# --- Logging ---

func _log_loader_activity(message: String):
    """
    Helper function to log loader activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("LOADER: " + message)
    else:
        print("PXScrollLoader (Console Log): ", message)

