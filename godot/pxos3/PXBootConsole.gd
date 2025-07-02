# PXBootConsole.gd
# Displays boot messages and handles post-boot UI transitions

extends Control

@export var auto_scroll: bool = true
@onready var label_log := $BootLogLabel
@onready var scroll_container := $ScrollContainer
@onready var enter_prompt := $PressEnterLabel

signal user_pressed_enter()

var is_boot_complete := false

func _ready():
    label_log.text = ""
    enter_prompt.visible = false
    set_process_input(true)

func add_log_line(line: String):
    label_log.text += line + "\n"
    if auto_scroll:
        await get_tree().process_frame
        scroll_container.scroll_vertical = scroll_container.get_v_scroll_bar().max_value

func on_cpu_halted():
    is_boot_complete = true
    enter_prompt.visible = true
    add_log_line("[PXBootConsole] Boot complete. Press Enter to continue...")

func _input(event):
    if is_boot_complete and event is InputEventKey and event.pressed and event.keycode == KEY_ENTER:
        emit_signal("user_pressed_enter")
