# Inside PXRoadmapExecutor.gd

@onready var px_fs_writer: PXFSWriter = get_node_or_null("../PXFSWriter") # Add this line

# ... (rest of _ready, _process, _execute_current_step) ...

func _execute_command_logic(command: String, arg_text: String, full_step_text: String):
    match command:
        # ... (existing commands) ...
        "WRITE_TO_FS_BLOCK": # NEW COMMAND
            # Format: WRITE_TO_FS_BLOCK:FILENAME:CONTENT:COL:ROW:TYPE_R,G,B:FLAGS_R,G,B:ORIGIN_R,G,B
            var parts = arg_text.split(":", false)
            if parts.size() >= 5: # Filename, Content, Col, Row, Type_Color
                var filename = parts[0]
                var content = parts[1]
                var col = parts[2].to_int()
                var row = parts[3].to_int()
                var type_color_str = parts[4].split(",")
                var type_color = Color(type_color_str[0].to_float()/255.0, type_color_str[1].to_float()/255.0, type_color_str[2].to_float()/255.0)

                var flags_color = Color(0.2, 0.2, 0.2) # Default
                if parts.size() > 5:
                    var flags_color_str = parts[5].split(",")
                    flags_color = Color(flags_color_str[0].to_float()/255.0, flags_color_str[1].to_float()/255.0, flags_color_str[2].to_float()/255.0)

                var origin_agent_color = Color(0.0, 0.0, 0.0) # Default
                if parts.size() > 6:
                    var origin_agent_color_str = parts[6].split(",")
                    origin_agent_color = Color(origin_agent_color_str[0].to_float()/255.0, origin_agent_color_str[1].to_float()/255.0, origin_agent_color_str[2].to_float()/255.0)

                if px_fs_writer:
                    var success = px_fs_writer.write_file(filename, content, col, row, type_color, flags_color, origin_agent_color)
                    if success:
                        _log_roadmap_activity("FS_WRITER: Wrote '%s' to (%d,%d)." % [filename, col, row])
                    else:
                        _log_roadmap_activity("FS_WRITER: Failed to write '%s'." % filename)
                else:
                    _log_roadmap_activity("FS_WRITER: PXFSWriter not found.")
            else:
                print_warn("PXRoadmapExecutor: Invalid WRITE_TO_FS_BLOCK format: ", arg_text)
        # ... (rest of existing commands) ...