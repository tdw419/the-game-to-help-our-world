# PXOSUIScreen.gd
# This script manages the visual simulation of a kernel boot process.

extends Control

@onready var boot_log_label: RichTextLabel = $BootLog
@onready var boot_log_timer: Timer = $BootLogTimer
@onready var cursor_blink_timer: Timer = $CursorBlinkTimer

var boot_messages: Array[String] = [
    "[ OK ] Started systemd-udevd.service - Unified Device Event Manager.",
    "[ OK ] Finished Load Kernel Modules.",
    "[ OK ] Finished Apply Kernel Variables.",
    "[ OK ] Reached target Local File Systems (Pre).",
    "[ OK ] Finished Create Static Device Nodes in /dev.",
    "[ OK ] Finished Coldplug All Block Devices.",
    "[ OK ] Reached target Local File Systems.",
    "[ OK ] Started Hostname Service.",
    "[ OK ] Started Network Manager.",
    "[ OK ] Started WPA supplicant.",
    "[ OK ] Reached target Network.",
    "[ OK ] Started Login Service.",
    "[ OK ] Reached target Multi-User System.",
    "[ OK ] Reached target Graphical Interface.",
    "TinyCore Linux (tty1)",
    "",
    "tc@box:~$"
]
var current_message_index: int = 0
var cursor_visible: bool = true

func _ready():
    boot_log_label.text = ""
    boot_log_timer.start() # Start the boot log animation

func _on_BootLogTimer_timeout():
    if current_message_index < boot_messages.size():
        var message = boot_messages[current_message_index]
        boot_log_label.append_text(message + "\n")
        boot_log_label.scroll_to_line(boot_log_label.get_line_count() - 1) # Auto-scroll
        current_message_index += 1
    else:
        boot_log_timer.stop()
        # Once all messages are displayed, ensure cursor blinking starts/continues
        if not cursor_blink_timer.is_stopped():
            _on_CursorBlinkTimer_timeout() # Ensure cursor is visible initially
            cursor_blink_timer.start()


func _on_CursorBlinkTimer_timeout():
    if current_message_index >= boot_messages.size(): # Only blink cursor after all messages
        var current_text = boot_log_label.text
        if current_text.ends_with("_"):
            boot_log_label.text = current_text.left(current_text.length() - 1)
        else:
            boot_log_label.append_text("_")
        cursor_visible = not cursor_visible

