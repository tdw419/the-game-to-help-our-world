# PXLogTerminal.gd
# Simulated log terminal panel for PXRuntime shell output and boot feedback

extends Control

# --- Dependencies ---
@onready var log_display: RichTextLabel = $LogDisplay

# --- Config ---
@export var typing_speed_chars_per_second: float = 120.0
var _typing_queue: Array[String] = []
var _current_line: String = ""
var _last_add_time := 0.0
var _typing_in_progress := false

# --- Lifecycle ---
func _ready():
    clear_log()
    set_process(true)

# --- Public API ---

func add_line(line: String, prefix: String = "", color: Color = Color.WHITE, simulate_typing: bool = false):
    var formatted_line := ""
    if prefix != "":
        formatted_line += "[color=gray][%s][/color] " % prefix

    formatted_line += "[color=#%s]%s[/color]" % [color.to_html(false), line]

    if simulate_typing:
        _typing_queue.append(formatted_line)
    else:
        log_display.append_bbcode(formatted_line + "\n")
        scroll_to_bottom()

func clear_log():
    log_display.clear()

func scroll_to_bottom():
    await get_tree().process_frame
    log_display.scroll_to_line(log_display.get_line_count())

func export_to_file(path: String = "user://terminal_log.txt"):
    var file := FileAccess.open(path, FileAccess.WRITE)
    file.store_string(log_display.text)
    file.close()

func copy_to_clipboard():
    DisplayServer.clipboard_set(log_display.text)

# --- Simulated Typing Update ---
func _process(delta: float):
    if _typing_queue.is_empty(): return

    if OS.get_ticks_msec() - _last_add_time < (1000.0 / typing_speed_chars_per_second):
        return

    var next_line := _typing_queue.pop_front()
    log_display.append_bbcode(next_line + "\n")
    scroll_to_bottom()
    _last_add_time = OS.get_ticks_msec()
