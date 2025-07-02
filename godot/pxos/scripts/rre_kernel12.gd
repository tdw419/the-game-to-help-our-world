extends Node

class_name RREKernel

var active_roadmap := ""
var log := []
var step := 0

func load_roadmap_from_file(path: String, pxfs: Dictionary) -> String:
	if not pxfs.has(path):
		return "RRE Error: Roadmap not found at %s." % path
	active_roadmap = pxfs[path]
	step = 0
	return "RRE: Roadmap loaded from %s" % path

func execute(pxfs: Dictionary) -> String:
	if active_roadmap == "":
		return "RRE Error: No roadmap loaded."

	log.clear()
	var lines := active_roadmap.split("\n")
	var command_buffer := []
	var in_block := false

	for line in lines:
		line = line.strip_edges()

		if line.begins_with(":: EXECUTE"):
			in_block = true
			command_buffer.clear()
		elif line.begins_with(":: COMPLETE"):
			in_block = false
			step += 1
			var cmd = command_buffer.join("\n")
			log.append("RRE Step %d - BEGIN\n%s" % [step, cmd])
			var result := _process_step(cmd, pxfs)
			log.append("RRE Step %d - RESULT\n%s\n" % [step, result])
		elif line.begins_with(":: COMMENT"):
			log.append("[Comment] %s" % line.replace(":: COMMENT", "").strip_edges())
		elif line.begins_with(":: LOG"):
			log.append("[Log Inject] %s" % line.replace(":: LOG", "").strip_edges())
		elif in_block:
			command_buffer.append(line)

	pxfs["/root/logs/rre_last_execution.log"] = log.join("\n")
	return "RRE Kernel: Executed roadmap with %d steps." % step


func _process_step(cmd: String, pxfs: Dictionary) -> String:
	if cmd.find("PXOS_COMMAND:") != -1:
		var path = _extract_path(cmd)
		var content = _extract_content(cmd, "PXOS_COMMAND", "PXOS_COMMAND_END")
		pxfs[path] = content
		return "PXOS_COMMAND: Wrote to %s" % path

	elif cmd.find("PXOS_GUI_UPDATE:") != -1:
		var gui_content = _extract_content(cmd, "PXOS_GUI_UPDATE:", "PXOS_GUI_UPDATE_END")
		pxfs["/root/pxgui/layout.json"] = gui_content
		return "PXOS_GUI_UPDATE: GUI updated."

	elif cmd.find("PXOS_APP_RUN:") != -1:
		var app_path := _extract_app_path(cmd)
		if not pxfs.has(app_path):
			return "PXOS_APP_RUN: App not found at %s" % app_path

		var app_data := JSON.parse_string(pxfs[app_path])
		if app_data.has("script"):
			return _process_step(app_data["script"], pxfs)
		return "PXOS_APP_RUN: App %s has no script." % app_path

	else:
		return "Unhandled command in roadmap."


func _extract_path(cmd: String) -> String:
	for line in cmd.split("\n"):
		if line.begins_with("PXOS_COMMAND: write "):
			return line.replace("PXOS_COMMAND: write ", "").strip_edges()
	return "/unknown"

func _extract_content(cmd: String, start_marker: String, end_marker: String) -> String:
	var lines = cmd.split("\n")
	var recording = false
	var buffer = []

	for line in lines:
		if line.begins_with(start_marker):
			recording = true
		elif line == end_marker:
			recording = false
		elif recording:
			buffer.append(line)
	return buffer.join("\n")

func _extract_app_path(cmd: String) -> String:
	for line in cmd.split("\n"):
		if line.begins_with("PXOS_APP_RUN:"):
			return line.replace("PXOS_APP_RUN:", "").strip_edges()
	return "/apps/unknown.pxapp"
