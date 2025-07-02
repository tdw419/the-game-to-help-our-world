# PXRoadmapInjector.gd
# This module provides a programmatic interface to inject glyph-based RRE roadmaps
# directly into a specific PXAgentNode's execution territory (agent_region_rect).
# It allows for dynamic submission of multi-step RRE programs to agents.

extends Node

# --- Configuration ---
# Optional: Delay in seconds after injection before the agent starts executing (gives time for visual update).
@export var injection_delay_sec: float = 0.1

# --- Dependencies ---
@onready var px_agent_reflex_bridge: PXAgentReflexBridge = get_node_or_null("../PXAgentReflexBridge") # To get agent nodes and their regions
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To write scrolls to memory regions
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging injector activity

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_agent_reflex_bridge or not px_ztxt_memory or not px_scroll_log:
        print_err("PXRoadmapInjector: Essential dependencies missing. Injector disabled.")
        set_process(false)
        return

    print("PXRoadmapInjector: Initialized. Ready to inject roadmaps into agents.")

# --- Core Roadmap Injection API ---

func inject_roadmap(agent_id: String, roadmap_steps: Array[String]) -> bool:
    """
    Injects a multi-step, glyph-based RRE roadmap into a target agent's
    execution region. This will activate the agent's RRE mode.

    Args:
        agent_id (String): The ID of the target agent.
        roadmap_steps (Array[String]): An array of RRE commands (e.g., [":: EXECUTE PING", ":: EXECUTE HALT"]).

    Returns:
        bool: True if the roadmap was successfully injected, false otherwise.
    """
    _log_injector_activity("Request to inject roadmap into '" + agent_id + "'.")

    var agent_node = px_agent_reflex_bridge.registered_agents.get(agent_id)
    if not agent_node or not agent_node is PXAgentNode:
        _log_injector_activity("ERROR: Agent '" + agent_id + "' not found or not a PXAgentNode.")
        print_err("PXRoadmapInjector: Agent '" + agent_id + "' not found or not a PXAgentNode.")
        return false

    var agent_region = agent_node.agent_region_rect
    var roadmap_content_ztxt = "\n".join(roadmap_steps) # Join steps with newlines for zTXT

    # Write the roadmap content to the agent's region using PXZTXTMemory
    if px_ztxt_memory.write_ztxt(agent_region, roadmap_content_ztxt):
        _log_injector_activity("Injected roadmap into '" + agent_id + "'.")

        # Activate the agent's RRE loop after a short delay for visual update
        get_tree().create_timer(injection_delay_sec).timeout.connect(
            Callable(self, "_activate_agent_rre").bind(agent_node)
        )
        return true
    else:
        _log_injector_activity("FAILED to inject roadmap into '" + agent_id + "'.")
        print_err("PXRoadmapInjector: Failed to inject roadmap into agent '", agent_id, "'.")
        return false

func _activate_agent_rre(agent_node: PXAgentNode):
    """Activates the agent's RRE mode and sets its mood."""
    if agent_node:
        agent_node.local_state["rre_active"] = true
        agent_node.local_state["mood"] = "executing_rre"
        _log_injector_activity("Activated RRE for '" + agent_node.agent_id + "'.")
        print("PXRoadmapInjector: Activated RRE for agent '", agent_node.agent_id, "'.")
    else:
        print_err("PXRoadmapInjector: Failed to activate RRE for null agent_node.")

# --- Logging ---

func _log_injector_activity(message: String):
    """
    Helper function to log injector activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("INJECTOR: " + message)
    else:
        print("PXRoadmapInjector (Console Log): ", message)

