# Inside PXReflexDaemon.gd

@onready var px_roadmap_watcher: PXRoadmapWatcher = get_node_or_null("../PXRoadmapWatcher") # Add this line

# ... (rest of _ready, _process, _scan_and_execute_commands) ...

func _execute_daemon_command(command: String):
    # ... (existing commands) ...

    match cmd_name:
        # ... (existing commands) ...
        "INJECT_WATCHED_ROADMAP": # NEW COMMAND
            # Format: INJECT_WATCHED_ROADMAP:ROADMAP_NAME
            # This will write a predefined roadmap into the watcher's region.
            var roadmap_name = cmd_arg.strip_edges()
            # For simplicity, let's use a predefined roadmap from PXScrollLoader
            var roadmap_content_array = get_node_or_null("../PXScrollLoader").predefined_scrolls.get(roadmap_name)

            if roadmap_content_array and px_roadmap_watcher and px_ztxt_memory:
                var success = px_ztxt_memory.write_ztxt(px_roadmap_watcher.watched_roadmap_region, "\n".join(roadmap_content_array))
                if success:
                    _log_daemon_activity("Injected roadmap '%s' into watcher region." % roadmap_name)
                else:
                    _log_daemon_activity("Failed to write roadmap to watcher region.")
            else:
                _log_daemon_activity("INJECT_WATCHED_ROADMAP: Roadmap or dependencies not found.")
        _:
            _log_daemon_activity("UNKNOWN CMD: " + command)
            print_warn("PXReflexDaemon: Unknown command received: '", command, "'")