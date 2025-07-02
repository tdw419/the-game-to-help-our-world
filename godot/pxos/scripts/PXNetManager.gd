# scripts/PXNetManager.gd
extends Node

class_name PXNetManager

@export var net_bus_width: int = 4 # e.g., 4 pixels wide for messages
@export var net_bus_height: int = 4 # e.g., 4 pixels high for messages

var net_bus_image: Image # The backing image for the PXNet SubViewport's sprite
var net_bus_texture: ImageTexture # The texture that is rendered into the SubViewport

@onready var pxnet_viewport: SubViewport = $"../PXGPUDriver/Viewport_PXNet" # Assumes sibling of PXDisplayNode, child of PXGPUDriver

func _ready():
	_setup_net_bus()
	set_process(true) # Or set_process_mode(Node.PROCESS_MODE_DISABLED) if only external writes

func _setup_net_bus():
	if pxnet_viewport:
		pxnet_viewport.size = Vector2i(net_bus_width, net_bus_height)
		pxnet_viewport.render_target_update_mode = SubViewport.RENDER_TARGET_UPDATE_ALWAYS
		pxnet_viewport.disable_3d = true
		pxnet_viewport.transparent_bg = true # Important if overlaying on another display

		net_bus_image = Image.create(net_bus_width, net_bus_height, false, Image.FORMAT_RGBA8)
		net_bus_image.fill(Color(0,0,0,0)) # Start fully transparent
		net_bus_texture = ImageTexture.create_from_image(net_bus_image)

		var net_bus_sprite = Sprite2D.new()
		net_bus_sprite.texture = net_bus_texture
		net_bus_sprite.centered = false
		pxnet_viewport.add_child(net_bus_sprite)
	else:
		push_error("PXNetManager: Viewport_PXNet not found!")

# --- PXNet API for Sending/Writing Messages ---
# Messages are single pixels for now. More complex messages would involve
# writing patterns/multiple pixels to the net_bus_image.
func send_pixel_message(x: int, y: int, message_pixel_color: Color):
	if net_bus_image and x >= 0 and x < net_bus_width and y >= 0 and y < net_bus_height:
		net_bus_image.lock()
		net_bus_image.set_pixel(x, y, message_pixel_color)
		net_bus_image.unlock()
		net_bus_texture.update(net_bus_image)
		# print("PXNet: Sent message pixel at (%d,%d): %s" % [x,y, message_pixel_color.to_html(false)])
	else:
		push_error("PXNet: Failed to send message (out of bus bounds or not initialized).")

# --- PXNet API for Receiving/Reading Messages ---
# This would be used by agents or a central PXNet processing unit
func read_pixel_message(x: int, y: int) -> Color:
	if net_bus_image and x >= 0 and x < net_bus_width and y >= 0 and y < net_bus_height:
		net_bus_image.lock()
		var color = net_bus_image.get_pixel(x, y)
		net_bus_image.unlock()
		return color
	return Color(0,0,0,0) # Return transparent if out of bounds or not initialized

# Utility to clear the bus (e.g., after a frame or message read)
func clear_net_bus():
	if net_bus_image:
		net_bus_image.lock()
		net_bus_image.fill(Color(0,0,0,0))
		net_bus_image.unlock()
		net_bus_texture.update(net_bus_image)

# This _process can be used for conceptual "network latency" or periodic clearing
func _process(delta):
	# Example: Clear the bus every few seconds to simulate message transmission
	# This can be disabled if messages are persistent until explicitly read/overwritten.
	# For simplicity, we'll clear it when a message is "received" by the shader,
	# or rely on agents to clear it.
	pass