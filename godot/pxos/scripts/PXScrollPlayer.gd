# PXScrollPlayer.gd
# This module enables PXOS to "replay" previously recorded RRE scrolls.
# It reads a scroll (a sequence of glyph-based commands) from memory,
# and then injects its steps, one by one, into a target agent's region
# for execution, simulating a playback.

extends Node

# --- Configuration ---
# Delay in seconds between injecting each step of the scroll during playback.
@export var playback_step_delay_sec: float = 0.5

# --- Dependencies ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To read scrolls from memory
@onready var px_roadmap_injector: PXRoadmapInjector = get_node_or_null("../PXRoadmapInjector") # To inject steps into agent
@onready var px_agent_reflex_bridge: PXAgentReflexBridge = get_node_or_null("../PXAgentReflexBridge") # To get agent regions
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging player activity

# --- Internal State ---
var current_scroll_to_play: Array[String] = [] # The scroll steps currently being played
var current_playback_agent_id: String = ""
var current_step_index: int = -1
var is_playing: bool = false
var time_since_last_step_injection: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_ztxt_memory or not px_roadmap_injector or not px_agent_reflex_bridge or not px_scroll_log:
        print_err("PXScrollPlayer: Essential dependencies missing. Player disabled.")
        set_process(false)
        return

    print("PXScrollPlayer: Initialized. Ready to replay scrolls.")

func _process(delta):
    if is_playing:
        time_since_last_step_injection += delta
        if time_since_last_step_injection >= playback_step_delay_sec:
            time_since_last_step_injection = 0.0
            _inject_next_step()

# --- Core Playback API ---

func play_recorded_scroll(agent_id: String, scroll_name: String, source_region: Rect2) -> bool:
    """
    Initiates playback of a recorded scroll.
    It reads the scroll from the specified source_region in memory,
    and then injects its steps into the target agent.

    Args:
        agent_id (String): The ID of the agent that will execute the scroll.
        scroll_name (String): The name of the scroll (for logging/identification).
        source_region (Rect2): The memory region where the recorded scroll is stored.

    Returns:
        bool: True if playback started successfully, false otherwise.
    """
    if is_playing:
        _log_player_activity("Player already busy. Cannot start new playback.")
        return false

    var agent_node = px_agent_reflex_bridge.registered_agents.get(agent_id)
    if not agent_node or not agent_node is PXAgentNode:
        _log_player_activity("ERROR: Agent '" + agent_id + "' not found or not a PXAgentNode.")
        return false

    # Read the scroll content from memory
    var full_scroll_content_ztxt = px_ztxt_memory.read_ztxt(source_region)
    if full_scroll_content_ztxt.is_empty():
        _log_player_activity("ERROR: No scroll found in region " + str(source_region))
        return false

    # Parse the scroll content (remove headers/footers, split into steps)
    var lines = full_scroll_content_ztxt.split("\n", false)
    current_scroll_to_play.clear()
    var in_content_section = false
    for line in lines:
        var trimmed_line = line.strip_edges()
        if trimmed_line.begins_with("# RECORDED_SCROLL:"):
            in_content_section = true
            continue
        if trimmed_line.begins_with("# END_RECORDING"):
            in_content_section = false
            break
        if in_content_section and not trimmed_line.is_empty():
            current_scroll_to_play.append(trimmed_line)

    if current_scroll_to_play.is_empty():
        _log_player_activity("ERROR: Recorded scroll '" + scroll_name + "' is empty or malformed.")
        return false

    current_playback_agent_id = agent_id
    current_step_index = 0
    is_playing = true
    time_since_last_step_injection = 0.0 # Inject first step immediately
    _log_player_activity("Starting playback of '" + scroll_name + "' for '" + agent_id + "' (" + str(current_scroll_to_play.size()) + " steps).")
    print("PXScrollPlayer: Starting playback of '", scroll_name, "' for '", agent_id, "'.")

    _inject_next_step() # Inject the first step

    return true

func stop_playback():
    """Stops the current scroll playback."""
    if not is_playing:
        print_warn("PXScrollPlayer: Playback not active.")
        return

    is_playing = false
    current_scroll_to_play.clear()
    current_step_index = -1
    _log_player_activity("Playback stopped.")
    print("PXScrollPlayer: Playback stopped.")

func _inject_next_step():
    """Injects the next step of the current scroll into the agent's region."""
    if current_step_index >= current_scroll_to_play.size():
        _log_player_activity("End of scroll. Playback complete.")
        stop_playback()
        return

    var step_command = current_scroll_to_play[current_step_index]
    var agent_node = px_agent_reflex_bridge.registered_agents.get(current_playback_agent_id)

    if agent_node and agent_node is PXAgentNode:
        # Inject the single step command into the agent's region
        # This relies on PXAgentNode's RRE logic to pick up the command.
        # We need to ensure the agent's region is clear to receive the command.
        # The agent's RRE logic should clear its region after processing a command.
        if px_ztxt_memory.write_ztxt(agent_node.agent_region_rect, step_command):
            _log_player_activity("Injected step " + str(current_step_index) + ": " + step_command.left(15) + " to '" + current_playback_agent_id + "'.")
            current_step_index += 1
        else:
            _log_player_activity("ERROR: Failed to inject step to agent. Stopping playback.")
            stop_playback()
    else:
        _log_player_activity("ERROR: Target agent not found during playback. Stopping.")
        stop_playback()


# --- Logging ---

func _log_player_activity(message: String):
    """
    Helper function to log player activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PLAYER: " + message)
    else:
        print("PXScrollPlayer (Console Log): ", message)

