extends Node

var pxram: Dictionary = {
	"kernel_offset": 0,
	"kernel_size": 0,
	"initrd_offset": 0,
	"initrd_size": 0,
	"kernel_data": null,
	"initrd_data": null,
	"root_dir_lba": 0,
	"root_dir_size": 0
}

var iso_file_path: String = "res://tinycore.iso"
var iso_file_access: FileAccess = null

@onready var px_boot_sim = get_node_or_null("/root/PXBootSimNode")

# --- Simulated Directory Structure ---
var simulated_iso_directory := {
	"/": ["/boot"],
	"/boot": ["/boot/vmlinuz", "/boot/core.gz"],
	"/boot/vmlinuz": { "lba": 512, "size": 8388608 },
	"/boot/core.gz": { "lba": 4096, "size": 16777216 }
}

# -------------------
# SYSTEM INIT
# -------------------

func _ready():
	if not _open_iso_file(iso_file_path):
		return
	_execute_pxtalk_script()

func _exit_tree():
	if iso_file_access:
		iso_file_access.close()

func _open_iso_file(path: String) -> bool:
	iso_file_access = FileAccess.open(path, FileAccess.READ)
	if iso_file_access == null:
		_execute_px_log("[PXBIOS] ERROR: Failed to open ISO.")
		return false
	_execute_px_log("[PXBIOS] ISO file opened.")
	return true

# -------------------
# PXTalk Emulation
# -------------------

func _execute_pxtalk_script():
	_execute_px_log("[PXBIOS] Phase 1: Boot + PVD Start")
	_execute_px_read_bytes(iso_file_path, 0, 512, "mbr")
	if not _execute_px_compare("mbr", 510, 0xAA55):
		_execute_px_log("[PXBIOS] Invalid boot sector. Halt.")
		return

	if not _execute_px_read_iso_pvd():
		return

	_execute_px_log("[PXBIOS] Phase 1 Complete.")
	_execute_px_log("[PXBIOS] Phase 2: Directory Scan + Extraction Start")

	_execute_px_scan_iso_dir("/")
	_execute_px_scan_iso_dir("/boot")

	_execute_px_find_in_iso(iso_file_path, "/boot/vmlinuz", "kernel_offset", "kernel_size")
	_execute_px_find_in_iso(iso_file_path, "/boot/core.gz", "initrd_offset", "initrd_size")

	# Read actual data
	if pxram["kernel_offset"] > 0:
		_execute_px_read_bytes(iso_file_path, pxram["kernel_offset"], pxram["kernel_size"], "kernel_data")
	if pxram["initrd_offset"] > 0:
		_execute_px_read_bytes(iso_file_path, pxram["initrd_offset"], pxram["initrd_size"], "initrd_data")

	# Final validation
	if pxram["kernel_data"] and pxram["initrd_data"]:
		_execute_px_log("[PXBIOS] Kernel and Initrd loaded successfully.")
		_execute_px_exec_kernel()
	else:
		_execute_px_log("[PXBIOS] Failed to extract kernel or initrd.")
		return

# -------------------
# PXTalk Commands
# -------------------

func _execute_px_log(message: String):
	print(message)
	if px_boot_sim:
		px_boot_sim._process_px_log_message(message)

func _execute_px_compare(data_key: String, offset: int, expected_value: int) -> bool:
	var data: PoolByteArray = pxram.get(data_key)
	if not data or offset + 2 > data.size():
		return false
	var val = (data[offset+1] << 8) | data[offset]
	return val == expected_value

func _execute_px_read_bytes(path: String, offset: int, length: int, target: String):
	iso_file_access.seek(offset)
	var bytes = iso_file_access.get_buffer(length)
	pxram[target] = bytes
	_execute_px_log("[PXBIOS] Read %d bytes for %s." % [bytes.size(), target])

func _execute_px_read_iso_pvd() -> bool:
	_execute_px_read_bytes(iso_file_path, 0x8000, 2048, "pvd")
	var pvd = pxram.get("pvd")
	if not pvd:
		_execute_px_log("[PXBIOS] ERROR: Failed to read PVD.")
		return false
	var ident = pvd.slice(1, 6).get_string_from_ascii()
	if ident != "CD001":
		_execute_px_log("[PXBIOS] ERROR: Invalid PVD identifier: %s" % ident)
		return false

	# Root Dir record at byte 156
	var lba = _read_le_uint32(pvd, 158)
	var size = _read_le_uint32(pvd, 166)
	pxram["root_dir_lba"] = lba
	pxram["root_dir_size"] = size
	_execute_px_log("[PXBIOS] Root Directory LBA: %d, Size: %d" % [lba, size])
	return true

# Simulated scan
func _execute_px_scan_iso_dir(path: String):
	if simulated_iso_directory.has(path):
		_execute_px_log("[PXBIOS] PX_SCAN_ISO_DIR: Scanned '%s': %s" % [path, simulated_iso_directory[path]])
	else:
		_execute_px_log("[PXBIOS] PX_SCAN_ISO_DIR: '%s' not found." % path)

# Simulated lookup
func _execute_px_find_in_iso(iso: String, file_path: String, offset_key: String, size_key: String):
	if simulated_iso_directory.has(file_path):
		var entry = simulated_iso_directory[file_path]
		var offset = entry["lba"] * 2048
		var size = entry["size"]
		pxram[offset_key] = offset
		pxram[size_key] = size
		_execute_px_log("[PXBIOS] Found '%s' at LBA=%d (Offset=%d), Size=%d" % [file_path, entry["lba"], offset, size])
	else:
		pxram[offset_key] = 0
		pxram[size_key] = 0
		_execute_px_log("[PXBIOS] PX_FIND_IN_ISO: '%s' not found." % file_path)

# Final handoff
func _execute_px_exec_kernel():
	_execute_px_log("[PXBIOS] Handoff to Kernel at 0x100000...")
	yield(get_tree().create_timer(1.0), "timeout")
	get_tree().change_scene_to_file("res://PXOSUIScreen.tscn")

# Utils
func _read_le_uint32(data: PoolByteArray, offset: int) -> int:
	return (data[offset+3] << 24) | (data[offset+2] << 16) | (data[offset+1] << 8) | data[offset]
