# PXMemoryStateExporter.gd
# This Godot-side module captures the current runtime state of PXOS,
# including emotional levels, goal history, and other relevant data,
# and exports it to a JSON file. This file can then be read by map.py
# to update its canonical PXMemory, enabling bidirectional synchronization.

extends Node

# --- Configuration ---
# The filename for the exported JSON state. This should match map.py's PXMEMORY_EXPORT_FILENAME.
@export var export_filename: String = "user://pxmemory_export.json"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging exporter activity
@onready var px_emotion_engine: PXEmotionEngine = get_node_or_null("../PXEmotionEngine") # To include emotional state
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To include goal history
@onready var px_roadmap_executor: PXRoadmapExecutor = get_node_or_null("../PXRoadmapExecutor") # To include current roadmap state
@onready var px_roadmap_auto_loop: Node = get_node_or_null("../PXRoadmapAutoLoop") # To include auto-loop state (e.g., cycle count)
@onready var px_agent_reflex_bridge: PXAgentReflexBridge = get_node_or_null("../PXAgentReflexBridge") # To include agent states

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_warn("PXMemoryStateExporter: PXScrollLog not found. Exporter logs will go to console.")
    if not px_emotion_engine or not px_goal_memory or not px_roadmap_executor or not px_roadmap_auto_loop or not px_agent_reflex_bridge:
        print_warn("PXMemoryStateExporter: Some core dependencies missing. Exported state may be incomplete.")

    print("PXMemoryStateExporter: Initialized. Ready to export Godot runtime state.")

# --- Core Export API ---

func export_current_state() -> bool:
    """
    Captures the current relevant state from various Godot PXOS modules
    and exports it to a JSON file.
    """
    _log_exporter_activity("Capturing current Godot PXOS state for export...")

    var current_godot_rre_state: Dictionary = {}

    # --- 1. Capture Modules (Conceptual - map.py manages source directly) ---
    # Godot doesn't typically export its own GDScript source code at runtime easily.
    # This part is primarily managed by map.py.
    # We'll just export metadata about them if needed.
    current_godot_rre_state["modules"] = {} # Placeholder for module status/metadata

    # --- 2. Capture Roadmaps ---
    current_godot_rre_state["roadmaps"] = {}
    # Example: Capture the currently executing roadmap
    if px_roadmap_executor.roadmap_active:
        current_godot_rre_state["roadmaps"]["current_executing"] = {
            "name": "active_roadmap", # You might get a name from PXRoadmapMemory if loaded
            "steps": px_roadmap_executor.current_roadmap,
            "current_step_index": px_roadmap_executor.current_step_index,
            "status": "executing"
        }
    # You might also want to capture content from PXRoadmapMemoryRegion here.

    # --- 3. Capture Logs ---
    if px_scroll_log:
        current_godot_rre_state["logs"] = px_scroll_log.get_all_lines_as_string().split("\n") # Export all scroll log lines
        _log_exporter_activity("Captured scroll logs.")

    # --- 4. Capture Active Scroll Name (Conceptual) ---
    # This would be the name of the scroll currently being executed by PXScrollPlayer/PXAgentNode
    current_godot_rre_state["active_scroll"] = "N/A" # Placeholder for now

    # --- 5. Capture Snapshots (Conceptual - map.py manages these) ---
    current_godot_rre_state["snapshots"] = [] # Placeholder for snapshot list/metadata

    # --- 6. Capture Metadata ---
    current_godot_rre_state["metadata"] = {
        "version": "Godot_RRE_Runtime",
        "timestamp": str(OS.get_unix_time_from_system()),
        "last_exported_from_godot": str(datetime.now())
    }

    # --- 7. Capture Specific PXOS Runtime States ---
    if px_emotion_engine:
        current_godot_rre_state["emotions"] = px_emotion_engine.get_all_emotions()
        _log_exporter_activity("Captured emotional state.")

    if px_goal_memory:
        var goal_summary_list = []
        for entry in px_goal_memory.get_goal_history():
            goal_summary_list.append({
                "type": entry.goal_type,
                "outcome": entry.outcome,
                "ts": entry.timestamp
            })
        current_godot_rre_state["goal_history_summary"] = goal_summary_list
        _log_exporter_activity("Captured goal history summary.")

    if px_roadmap_auto_loop:
        current_godot_rre_state["auto_loop_state"] = {
            "running": px_roadmap_auto_loop.running,
            "cycle_count": px_roadmap_auto_loop.cycle_count
        }
        _log_exporter_activity("Captured auto-loop state.")

    if px_agent_reflex_bridge:
        var agent_states = {}
        for agent_id in px_agent_reflex_bridge.registered_agents.keys():
            var agent_node = px_agent_reflex_bridge.registered_agents[agent_id]
            if agent_node and agent_node is PXAgentNode:
                agent_states[agent_id] = {
                    "mood": agent_node.local_state.get("mood", "unknown"),
                    "rre_active": agent_node.local_state.get("rre_active", false),
                    "last_message": agent_node.local_state.get("last_message_received", "")
                }
        current_godot_rre_state["agent_states"] = agent_states
        _log_exporter_activity("Captured agent states.")

    # --- Finalize and Write to JSON ---
    var json_string = JSON.stringify(current_godot_rre_state, "\t")

    var file = FileAccess.open(export_filename, FileAccess.WRITE)
    if file:
        file.store_string(json_string)
        file.close()
        _log_exporter_activity("Successfully exported Godot state to " + export_filename)
        print("PXMemoryStateExporter: Successfully exported Godot state to ", export_filename)
        return true
    else:
        _log_exporter_activity("ERROR: Could not open file for writing: " + export_filename)
        print_err("PXMemoryStateExporter: Could not open file for writing: ", export_filename)
        return false

# --- Logging ---

func _log_exporter_activity(message: String):
    """
    Helper function to log exporter activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("GD_EXPORTER: " + message)
    else:
        print("PXMemoryStateExporter (Console Log): ", message)

