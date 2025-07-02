extends Control

@export var panel_region_rect: Rect2 = Rect2(0, 0, 800, 480)
@export var simulation_speed_multiplier := 1.0
@export var fade_out_duration := 1.5

@onready var boot_log_display: RichTextLabel = $BootLogDisplay
@onready var framebuffer_texture_rect: TextureRect = $FramebufferTextureRect
@onready var press_enter_label: Label = $PressEnterLabel
@onready var close_button: Button = $CloseButton

var _boot_messages: Array = []
var _msg_index := 0
var _is_running := false

func _ready():
    hide()
    close_button.pressed.connect(_on_close_pressed)
    press_enter_label.hide()

func start_simulation(messages: Array):
    _boot_messages = messages
    _msg_index = 0
    _is_running = true
    show()
    modulate.a = 1.0
    boot_log_display.clear()
    _show_next_message()

func _show_next_message():
    if _msg_index >= _boot_messages.size():
        _end_simulation()
        return

    boot_log_display.append_bbcode("[color=lime]%s[/color]\n" % _boot_messages[_msg_index])
    _msg_index += 1

    await get_tree().create_timer(0.8 / simulation_speed_multiplier).timeout
    _show_next_message()

func _end_simulation():
    press_enter_label.text = "Press Enter to continue..."
    press_enter_label.show()
    await _wait_for_enter()
    _fade_out()

func _wait_for_enter():
    var key_event := InputEventKey.new()
    while true:
        await get_tree().process_frame
        if Input.is_action_just_pressed("ui_accept"):
            break

func _fade_out():
    var tween = get_tree().create_tween()
    tween.tween_property(self, "modulate:a", 0.0, fade_out_duration)
    tween.tween_callback(Callable(self, "hide"))

func _on_close_pressed():
    hide()
