# PXOSHost.gd
# PXOS GPU Host Runtime - Godot 4.x
# Executes PXTalk pixel instructions from pxboot.png

extends Node2D

@onready var pxboot_texture := preload("res://pxboot.png")
var px_image : Image
var px_texture : ImageTexture
var px_vm_state = {}  # Internal PXTalk VM state map (e.g., R0–R5, PC, FLAGS)

func _ready():
    load_pxboot()
    setup_display()
    print("PXOS Host Initialized")

func load_pxboot():
    px_image = pxboot_texture.get_image()
    px_image.lock()
    px_texture = ImageTexture.create_from_image(px_image)

func setup_display():
    var sprite = Sprite2D.new()
    sprite.texture = px_texture
    sprite.scale = Vector2(2, 2)  # Scale up for visibility
    add_child(sprite)

func _process(delta):
    px_talk_tick()
    px_texture.update(px_image)

# PXTalk Instruction Runner (Prototype)
func px_talk_tick():
    var width = px_image.get_width()
    var height = px_image.get_height()
    for y in height:
        for x in width:
            var color = px_image.get_pixel(x, y)
            run_px_instruction(x, y, color)

# Run a single PXTalk instruction based on pixel color
func run_px_instruction(x: int, y: int, color: Color):
    # Example prototype logic:
    # Toggle pixel: if red > 0.5 → set to black; if red == 0 → set to red
    if color.r > 0.5:
        px_image.set_pixel(x, y, Color(0, 0, 0))
    elif color.r == 0:
        px_image.set_pixel(x, y, Color(1, 0, 0))
    
    # Extend here:
    # - Interpret RGB as opcode
    # - Add register simulation
    # - Simulate instruction pointer / memory cursor
    # - Integrate zTXt metadata interpreter

# Reset function (optional)
func reset_px_image():
    px_image.unlock()
    load_pxboot()
    px_texture.update(px_image)
