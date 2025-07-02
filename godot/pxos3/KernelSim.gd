extends Control

@onready var kernel_console := $KernelConsole
@onready var kernel_timer := $KernelTimer

var kernel_log: Array[String] = []
var kernel_data: PoolByteArray
var initrd_data: PoolByteArray
var log_index := 0

func _ready():
	kernel_console.text = ""
	kernel_log = [
		"[KERNEL] Decompressing kernel image...",
		"[KERNEL] Initializing PXOS subsystems...",
		"[KERNEL] Mounting initrd as root...",
		"[KERNEL] Executing /init...",
		"[INIT] Boot complete. Launching PXShell...",
		"",
		"pxos@pxcore:~$"
	]
	kernel_timer.start()

func _on_KernelTimer_timeout():
	if log_index < kernel_log.size():
		kernel_console.append_text(kernel_log[log_index] + "\n")
		kernel_console.scroll_to_line(kernel_console.get_line_count() - 1)
		log_index += 1
	else:
		kernel_timer.stop()
