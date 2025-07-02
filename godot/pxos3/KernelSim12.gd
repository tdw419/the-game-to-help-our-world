extends Control

@onready var kernel_console := $KernelConsole
@onready var kernel_timer := $KernelTimer

var kernel_log: Array[String] = []
var log_index := 0

# These are injected by PXVM during scene switch
var kernel_data: PoolByteArray
var initrd_data: PoolByteArray

func _ready():
	kernel_console.text = ""
	kernel_log = _generate_kernel_log()
	kernel_timer.start()

func _on_KernelTimer_timeout():
	if log_index < kernel_log.size():
		kernel_console.append_text(kernel_log[log_index] + "\n")
		kernel_console.scroll_to_line(kernel_console.get_line_count() - 1)
		log_index += 1
	else:
		kernel_timer.stop()

func _generate_kernel_log() -> Array:
	var kern_sz = kernel_data.size() if kernel_data else 0
	var initrd_sz = initrd_data.size() if initrd_data else 0
	return [
		"[KERNEL] Decompressing kernel image... (%d bytes)" % kern_sz,
		"[KERNEL] Initializing PXOS kernel subsystems...",
		"[KERNEL] Mounting initrd... (%d bytes)" % initrd_sz,
		"[KERNEL] Creating virtual filesystem in /dev/ram0...",
		"[INIT] Executing /init from initrd...",
		"[INIT] PXOS Boot Sequence Complete.",
		"",
		"pxos@pxcore:~$"
	]
