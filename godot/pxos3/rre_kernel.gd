extends Node

class_name RREKernel

var active_roadmap := ""
var log := []

func load_roadmap_from_file(path: String, pxfs: Dictionary) -> String:
    if not pxfs.has(path):
        return "RRE Error: Roadmap not found."
    active_roadmap = pxfs[path]
    return "RRE: Roadmap loaded from %s" % path

func execute(pxfs: Dictionary) -> String:
    if active_roadmap == "":
        return "RRE Error: No roadmap loaded."

    log.clear()
    var lines := active_roadmap.split("\n")
    var in_command := false
    var command_buffer := []
    var step := 0

    for line in lines:
        if line.begins_with(":: EXECUTE "):
            in_command = true
            command_buffer.clear()
        elif line.begins_with(":: COMPLETE"):
            in_command = false
            step += 1
            var cmd = command_buffer.join("\n")
            log.append("Step %d: Executing\n%s" % [step, cmd])
            log.append(_process_step(cmd, pxfs))
        elif in_command:
            command_buffer.append(line)

    pxfs["/root/logs/rre_last_execution.log"] = log.join("\n")
    return "RRE: Executed roadmap with %d steps." % step

func _process_step(cmd: String, pxfs: Dictionary) -> String:
    var response := ""
    if cmd.find("PXOS_COMMAND:") != -1:
        var path = _extract_path_from_command(cmd)
        var content = _extract_content_from_command(cmd)
        pxfs[path] = content
        response = "Wrote file via roadmap: %s" % path
    elif cmd.find("PXOS_GUI_UPDATE:") != -1:
        pxfs["/root/pxgui/layout.json"] = cmd  # Later: extract JSON cleanly
        response = "GUI layout updated via roadmap."
    else:
        response = "Unhandled roadmap command."
    return response

func _extract_path_from_command(cmd: String) -> String:
    for line in cmd.split("\n"):
        if line.begins_with("PXOS_COMMAND: write "):
            return line.replace("PXOS_COMMAND: write ", "").strip_edges()
    return "/unknown"

func _extract_content_from_command(cmd: String) -> String:
    var lines = cmd.split("\n")
    var recording = false
    var buffer = []
    for line in lines:
        if line.begins_with("PXOS_COMMAND: write "):
            recording = true
        elif line == "PXOS_COMMAND_END":
            recording = false
        elif recording:
            buffer.append(line)
    return buffer.join("\n")
