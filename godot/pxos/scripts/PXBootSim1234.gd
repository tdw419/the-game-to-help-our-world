# PXBootSim.gd
# Full implementation of the PX Boot Simulator panel
# Shows animated PX_LOG output during PXVM boot sequences

extends Control

@onready var log_output_label: RichTextLabel = $LogOutputLabel
@onready var animation_timer: Timer = $LogAnimationTimer

var log_messages: Array[String] = []
var current_log_index: int = 0
var animation_speed: float = 0.1 # Seconds per message
var is_animating: bool = false

func _ready():
    log_output_label.clear()
    animation_timer.wait_time = animation_speed
    animation_timer.connect("timeout", Callable(self, "_on_animation_tick"))
    animation_timer.stop()

func reset_simulator():
    log_messages.clear()
    current_log_index = 0
    is_animating = false
    log_output_label.clear()
    animation_timer.stop()

func _process_px_log_message(message: String):
    log_messages.append(message)
    if not is_animating:
        is_animating = true
        animation_timer.start()

func _on_animation_tick():
    if current_log_index < log_messages.size():
        var line = log_messages[current_log_index]
        log_output_label.append_text(line + "\n")
        log_output_label.scroll_to_line(log_output_label.get_line_count() - 1)
        current_log_index += 1
    else:
        animation_timer.stop()
        is_animating = false

# Optional: Allow fast-forward or immediate dump
func show_all_messages():
    for i in current_log_index : log_messages.size():
        var line = log_messages[i]
        log_output_label.append_text(line + "\n")
    log_output_label.scroll_to_line(log_output_label.get_line_count() - 1)
    animation_timer.stop()
    is_animating = false
