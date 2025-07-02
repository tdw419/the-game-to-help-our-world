# PXAgentReflexBridge.gd
# This module acts as a bridge between the PXReflexDaemon and individual PXAgentNode instances.
# It allows the daemon to route specific commands to named agents, enabling granular control
# and orchestration of the multi-agent system within PXOS.

extends Node

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging bridge activity

# --- Internal State ---
# A dictionary to hold references to active PXAgentNode instances, mapped by their agent_id.
# Agents will register themselves with this bridge.
var registered_agents: Dictionary = {} # { "agent_id": PXAgentNode_instance }

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_warn("PXAgentReflexBridge: PXScrollLog not found. Bridge logs will go to console.")

    print("PXAgentReflexBridge: Initialized. Ready to route commands to agents.")

# --- API for Agents to Register ---

func register_agent(agent_id: String, agent_node: Node):
    """
    PXAgentNode instances call this to register themselves with the bridge.

    Args:
        agent_id (String): The unique ID of the agent.
        agent_node (Node): A reference to the PXAgentNode instance.
    """
    if registered_agents.has(agent_id):
        print_warn("PXAgentReflexBridge: Agent ID '", agent_id, "' already registered. Overwriting.")
    registered_agents[agent_id] = agent_node
    _log_bridge_activity("Agent '", agent_id, "' registered.")
    print("PXAgentReflexBridge: Agent '", agent_id, "' registered.")

func unregister_agent(agent_id: String):
    """
    PXAgentNode instances call this to unregister themselves.
    """
    if registered_agents.has(agent_id):
        registered_agents.erase(agent_id)
        _log_bridge_activity("Agent '", agent_id, "' unregistered.")
        print("PXAgentReflexBridge: Agent '", agent_id, "' unregistered.")

# --- API for Daemon to Route Commands ---

func route_command_to_agent(agent_id: String, agent_command: String) -> bool:
    """
    Routes a specific command to a named PXAgentNode.
    This is called by PXReflexDaemon.

    Args:
        agent_id (String): The ID of the target agent.
        agent_command (String): The command string for the agent (e.g., "CONFIRM_STATE", "PREPARE_SNAPSHOT").

    Returns:
        bool: True if the command was successfully routed, false otherwise.
    """
    if not registered_agents.has(agent_id):
        _log_bridge_activity("ERROR: Agent '", agent_id, "' not found for command '", agent_command, "'.")
        print_err("PXAgentReflexBridge: Agent '", agent_id, "' not found for command '", agent_command, "'.")
        return false

    var target_agent = registered_agents[agent_id]

    # --- Execute Agent-Specific Command ---
    # This is where you define what commands agents can respond to.
    # Agents should have public methods to handle these commands.
    var command_parts = agent_command.split(":", false, 1)
    var cmd_name = command_parts[0].to_upper()
    var cmd_arg = ""
    if command_parts.size() > 1:
        cmd_arg = command_parts[1].strip_edges()

    var success = false
    match cmd_name:
        "CONFIRM_STATE":
            if target_agent.has_method("confirm_state"): # Agents need to implement this
                target_agent.confirm_state(cmd_arg)
                success = true
        "PREPARE_SNAPSHOT":
            if target_agent.has_method("prepare_snapshot"): # Agents need to implement this
                target_agent.prepare_snapshot(cmd_arg)
                success = true
        "SET_MOOD": # Example: Daemon can directly set an agent's mood
            if target_agent.has_method("set_mood") and not cmd_arg.is_empty():
                target_agent.set_mood(cmd_arg)
                success = true
        "LOG_AGENT": # Example: Agent logs a message
            if target_agent.has_method("log_agent_message") and not cmd_arg.is_empty():
                target_agent.log_agent_message(cmd_arg)
                success = true
        _:
            _log_bridge_activity("UNKNOWN CMD for Agent '", agent_id, "': '", agent_command, "'.")
            print_warn("PXAgentReflexBridge: Unknown command '", agent_command, "' for agent '", agent_id, "'.")
            return false

    if success:
        _log_bridge_activity("Routed '", agent_command, "' to '", agent_id, "'.")
    else:
        _log_bridge_activity("Failed to route '", agent_command, "' to '", agent_id, "'.")
    return success

# --- Logging ---

func _log_bridge_activity(message: String):
    """
    Helper function to log bridge activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("AGENT_BR: " + message)
    else:
        print("PXAgentReflexBridge (Console Log): ", message)

