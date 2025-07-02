# PXReflexDaemon.gd
# This module acts as a vigilant daemon that periodically scans a designated
# memory region (runtime_next_region) for pixel-encoded text commands (zTXT).
# Upon detecting specific commands, it triggers corresponding high-level actions
# within PXOS, enabling remote command and control, and automated reflexes.

extends Node

# --- Configuration ---
# How often the daemon scans the runtime_next_region for new commands (in seconds).
@export var scan_frequency_sec: float = 1.0

# --- Dependencies ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory") # To read zTXT commands
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # For commands like CLEAR_MEMORY
@onready var px_directive: PXDirective = get_node_or_null("../PXDirective") # For commands like FORCE_GOAL
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging daemon activity
@onready var px_roadmap_auto_loop: Node = get_node_or_null("../PXRoadmapAutoLoop") # For STOP_LOOP/START_LOOP
@onready var px_digest_exporter: Node = get_node_or_null("../PXDigestExporter") # NEW: For EXPORT_STATE (placeholder for future module)

# --- Internal State ---
var time_since_last_scan: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_ztxt_memory or not px_memory or not px_directive or not px_scroll_log:
        print_err("PXReflexDaemon: Essential dependencies missing. Daemon disabled.")
        set_process(false) # Disable _process if dependencies are not met
        return

    print("PXReflexDaemon: Initialized. Ready to scan for reflexes.")

func _process(delta):
    time_since_last_scan += delta
    if time_since_last_scan >= scan_frequency_sec:
        time_since_last_scan = 0.0
        _scan_and_execute_commands()

# --- Core Daemon Logic ---

func _scan_and_execute_commands():
    """
    Scans the runtime_next_region for commands and executes them.
    Commands are consumed by clearing the region after execution.
    """
    var commands_raw_text = px_ztxt_memory.read_ztxt(px_ztxt_memory.runtime_next_region).strip_edges()

    if commands_raw_text.is_empty():
        # print("PXReflexDaemon: No new commands in runtime_next_region.") # Too chatty
        return

    _log_daemon_activity("Detected command(s): '" + commands_raw_text.left(20) + "'")
    print("PXReflexDaemon: Processing commands from runtime_next_region: '", commands_raw_text, "'")

    # Clear the region immediately to consume the commands, preventing re-execution
    px_ztxt_memory.write_ztxt(px_ztxt_memory.runtime_next_region, "") # Clear the region

    var commands = commands_raw_text.split("\n", false) # Split by newline for multiple commands

    for command_line in commands:
        var trimmed_command = command_line.strip_edges()
        if trimmed_command.is_empty():
            continue

        _execute_daemon_command(trimmed_command)

func _execute_daemon_command(command: String):
    """
    Parses and executes a single command received by the daemon.
    """
    var parts = command.split(":", false, 1) # Split only on the first colon
    var cmd_name = parts[0].to_upper()
    var cmd_arg = ""
    if parts.size() > 1:
        cmd_arg = parts[1].strip_edges()

    _log_daemon_activity("Executing: " + cmd_name + ((" " + cmd_arg) if not cmd_arg.is_empty() else ""))

    match cmd_name:
        "RESET_ALL":
            # Clears all memory and potentially resets other modules
            if px_memory:
                px_memory.clear_region(px_memory.memory_region_rect)
                _log_daemon_activity("Memory cleared.")
            # You might add calls to reset other modules here (e.g., px_emotion_engine.reset_emotions())
        "FORCE_GOAL":
            # Forces PXDirective to issue a specific goal
            if px_directive and not cmd_arg.is_empty():
                # Note: This bypasses PXMotivationCore and PXGoalAdvisor for direct control.
                # You might want to pass a specific GoalEntry if you want it tracked.
                px_directive.issue_directive(cmd_arg, px_scroll_log.add_line("FORCE_GOAL: " + cmd_arg)) # Simplified logging
                _log_daemon_activity("Forced goal: " + cmd_arg)
            else:
                _log_daemon_activity("FORCE_GOAL: Invalid arg or PXDirective missing.")
        "LOG_DAEMON":
            # Logs a custom message from the daemon
            _log_daemon_activity("Custom Daemon Log: " + cmd_arg)
        "STOP_LOOP":
            # Stops the PXRoadmapAutoLoop
            if px_roadmap_auto_loop:
                px_roadmap_auto_loop.stop_loop()
                _log_daemon_activity("Roadmap AutoLoop stopped.")
            else:
                _log_daemon_activity("STOP_LOOP: PXRoadmapAutoLoop not found.")
        "START_LOOP":
            # Starts the PXRoadmapAutoLoop
            if px_roadmap_auto_loop:
                px_roadmap_auto_loop.start_loop()
                _log_daemon_activity("Roadmap AutoLoop started.")
            else:
                _log_daemon_activity("START_LOOP: PXRoadmapAutoLoop not found.")
        "EXPORT_STATE": # NEW COMMAND
            # Triggers a state export (e.g., to .pxdigest)
            if px_digest_exporter:
                # Assuming PXDigestExporter has an export_state method
                px_digest_exporter.export_state(cmd_arg if not cmd_arg.is_empty() else "default_snapshot")
                _log_daemon_activity("State export triggered: " + (cmd_arg if not cmd_arg.is_empty() else "default_snapshot"))
            else:
                _log_daemon_activity("EXPORT_STATE: PXDigestExporter not found.")
        "INJECT_CODE": # NEW COMMAND (Conceptual)
            # Simulates injecting new GDScript code or modules at runtime.
            # In a real Godot project, this is highly complex and usually involves
            # custom class loaders or plugin systems. For this scaffold, it's a conceptual trigger.
            _log_daemon_activity("INJECT_CODE: Conceptual code injection for: " + cmd_arg)
            print("PXReflexDaemon: Conceptual code injection requested for: ", cmd_arg)
            # You would implement actual code loading/execution logic here if feasible.
        "RESTART_OS": # NEW COMMAND
            # Reloads the current scene, effectively restarting the PXOS.
            _log_daemon_activity("RESTART_OS: Initiating system restart.")
            print("PXReflexDaemon: Initiating PXOS system restart (reloading scene).")
            get_tree().reload_current_scene()
        "PRINT": # NEW COMMAND
            # Directly prints a message to the PXScrollLog.
            if px_scroll_log:
                px_scroll_log.add_line("DAEMON_PRINT: " + cmd_arg)
                _log_daemon_activity("Printed to scroll log: " + cmd_arg)
            else:
                _log_daemon_activity("PRINT: PXScrollLog not found.")
        _:
            _log_daemon_activity("UNKNOWN CMD: " + command)
            print_warn("PXReflexDaemon: Unknown command received: '", command, "'")

# --- Logging ---

func _log_daemon_activity(message: String):
    """
    Helper function to log daemon activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("DAEMON: " + message)
    else:
        print("PXReflexDaemon (Console Log): ", message)

