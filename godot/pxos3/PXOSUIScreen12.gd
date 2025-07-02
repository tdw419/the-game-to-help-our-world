extends Control

@onready var boot_log := $BootLog
@onready var boot_log_timer := $BootLogTimer
@onready var cursor_timer := $CursorBlinkTimer

var log_messages: Array[String] = []
var current_log_index := 0
var cursor_visible := true
var cursor_symbol := "_"

func _ready():
    boot_log.text = ""
    log_messages = [
        "[ OK ] PXOS bootloader initialized...",
        "[ OK ] Kernel image located at 0x00100000",
        "[ OK ] Initrd image located at 0x00600000",
        "[ OK ] PXRAM initialized.",
        "[ OK ] Mounting PXFS...",
        "[ OK ] PXFS mounted at /",
        "[ OK ] Starting init process...",
        "[PXOS] Welcome to PXOS Runtime v1.0",
        "",
        "root@pxos:~#"
    ]
    boot_log_timer.start()

func _on_BootLogTimer_timeout():
    if current_log_index < log_messages.size():
        boot_log.append_text(log_messages[current_log_index] + "\n")
        boot_log.scroll_to_line(boot_log.get_line_count())
        current_log_index += 1
    elif not boot_log.text.ends_with(cursor_symbol):
        boot_log.append_text(cursor_symbol)

func _on_CursorBlinkTimer_timeout():
    if boot_log.text.ends_with(cursor_symbol):
        boot_log.text = boot_log.text.substr(0, boot_log.text.length() - 1)
    else:
        boot_log.append_text(cursor_symbol)
