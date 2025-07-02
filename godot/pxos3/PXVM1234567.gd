# PXVM.gd
# This script simulates the PXTalk Virtual Machine execution environment
# and now includes functionality for reading real ISO files and
# recursively parsing ISO9660 directory records to find kernel and initrd.

extends Node

# Dictionary to simulate PXRAM, storing variables and their values
var pxram: Dictionary = {
	"kernel_offset": 0,
	"kernel_size": 0,
	"initrd_offset": 0,
	"initrd_size": 0,
	"kernel_data": null,
	"initrd_data": null,
	"root_dir_lba": 0,   # LBA of the root directory (from PVD)
	"root_dir_size": 0,  # Size of the root directory (from PVD)
	"iso_parsed_files": {}, # Stores dynamically parsed file/directory info: { "full/path/to/file": { "lba": X, "size": Y, "is_dir": bool } }
	"iso_dir_map": {} # Stores metadata for directories: { "path_key": { "lba": X, "size": Y } }
}

# Path to the ISO file to be loaded.
# For testing, place tinycore.iso in your project's 'res://' directory
# (e.g., res://tinycore.iso) or a subfolder like 'res://iso/tinycore.iso'.
var iso_file_path: String = "res://tinycore.iso" # <<< CONFIGURE YOUR ISO PATH HERE

# FileAccess object for reading the ISO
var iso_file_access: FileAccess = null

# Reference to the PXBootSim for logging (adjust path as needed)
@onready var px_boot_sim = null # Will be assigned in _ready() or via dependency injection


# -------------------
# SYSTEM INIT
# -------------------

func _ready():
	# Find the PXBootSim instance to send log messages
	px_boot_sim = get_node_or_null("/root/PXBootSimNode")

	if not _open_iso_file(iso_file_path):
		return
	_execute_pxtalk_script()

func _exit_tree():
	if iso_file_access:
		iso_file_access.close()
		iso_file_access = null

func _open_iso_file(path: String) -> bool:
	if iso_file_access:
		iso_file_access.close()
		iso_file_access = null

	iso_file_access = FileAccess.open(path, FileAccess.READ)
	if iso_file_access == null:
		_execute_px_log(f"[PXBIOS] ERROR: Could not open ISO file: {path}. Error: {FileAccess.get_open_error()}")
		return false
	_execute_px_log(f"[PXBIOS] ISO file opened: {path}")
	return true

# -------------------
# PXTalk Emulation
# -------------------

func _execute_pxtalk_script():
	_execute_px_log("[PXBIOS] Phase 1: Boot + PVD Start")

	# Read MBR (first 512 bytes)
	_execute_px_read_bytes(iso_file_path, 0, 512, "mbr_data")
	var mbr_data: PoolByteArray = pxram.get("mbr_data")

	if mbr_data == null or mbr_data.size() < 512:
		_execute_px_log("[PXBIOS] ERROR: Failed to read MBR. Halting.")
		return

	# Verify MBR boot signature (0xAA55 at offset 0x1FE)
	if not _execute_px_compare("mbr_data", 0x1FE, 0xAA55):
		_execute_px_log("[PXBIOS] Invalid MBR boot sector signature. Halting.")
		return
	_execute_px_log("[PXBIOS] Valid boot sector found.")

	# Read and validate ISO PVD, and extract root directory info
	if not _execute_px_read_iso_pvd():
		_execute_px_log("[PXBIOS] ISO PVD validation failed. Halting.")
		return

	_execute_px_log("[PXBIOS] Phase 1 Complete.")
	_execute_px_log("[PXBIOS] Phase 2: Directory Scan + Extraction Start (Real Parsing)")

	# --- Phase 4: Recursive Directory Traversal ---
	# Initialize the directory map and parsed files storage
	pxram["iso_dir_map"] = {}
	pxram["iso_parsed_files"] = {} # Ensure this is cleared for a fresh scan

	# Recursively scan all directories starting at root
	# The root directory's "key" in iso_dir_map will be "root_dir"
	_scan_and_cache_all_dirs("root_dir", pxram["root_dir_lba"], pxram["root_dir_size"], "/")
	_execute_px_log(f"[PXBIOS] Finished scanning ISO directories. Found {pxram['iso_parsed_files'].size()} total entries.")

	# Locate kernel + initrd using full ISO path
	var kernel_entry = _navigate_iso_path("/boot/vmlinuz")
	var initrd_entry = _navigate_iso_path("/boot/core.gz")

	if kernel_entry.has("offset") and not kernel_entry["is_dir"]:
		pxram["kernel_offset"] = kernel_entry["offset"]
		pxram["kernel_size"] = kernel_entry["size"]
		_execute_px_log("[PXBIOS] Kernel found at offset %d, size %d" % [kernel_entry["offset"], kernel_entry["size"]])
	else:
		_execute_px_log("[PXBIOS] Kernel not found in ISO or is a directory. Halting.")
		return

	if initrd_entry.has("offset") and not initrd_entry["is_dir"]:
		pxram["initrd_offset"] = initrd_entry["offset"]
		pxram["initrd_size"] = initrd_entry["size"]
		_execute_px_log("[PXBIOS] Initrd found at offset %d, size %d" % [initrd_entry["offset"], initrd_entry["size"]])
	else:
		_execute_px_log("[PXBIOS] Initrd not found in ISO or is a directory. Halting.")
		return

	# Extract files
	_execute_px_read_bytes(iso_file_path, pxram["kernel_offset"], pxram["kernel_size"], "kernel_data")
	_execute_px_read_bytes(iso_file_path, pxram["initrd_offset"], pxram["initrd_size"], "initrd_data")

	if pxram["kernel_data"] and pxram["initrd_data"]:
		_execute_px_log("[PXBIOS] Kernel and Initrd loaded successfully.")
		_execute_px_log("[PXBIOS] Phase 2, 3 & 4 Complete.")
		_execute_px_exec_kernel()
	else:
		_execute_px_log("[PXBIOS] Failed to extract kernel or initrd. Halting.")
		return

# -------------------
# PXTalk Commands
# -------------------

func _execute_px_log(message: String):
	print(message) # Print to Godot console for debugging
	if px_boot_sim:
		px_boot_sim._process_px_log_message(message)

func _execute_px_compare(data_key: String, offset: int, expected_value: int) -> bool:
	var data: PoolByteArray = pxram.get(data_key)
	if not data or offset + 2 > data.size():
		_execute_px_log(f"[PXBIOS] ERROR: Compare data '{data_key}' not available or too small.")
		return false
	var val = (data[offset+1] << 8) | data[offset] # Read as little-endian 16-bit
	if val == expected_value:
		_execute_px_log(f"[PXBIOS] Verified {data_key} signature: 0x{expected_value:X}")
		return true
	else:
		_execute_px_log(f"[PXBIOS] ERROR: {data_key} signature mismatch: 0x{val:X} (expected 0x{expected_value:X}).")
		return false

func _execute_px_read_bytes(source_file: String, offset: int, length: int, target_pxram_key: String):
	if not iso_file_access or iso_file_access.get_path() != source_file:
		_execute_px_log(f"[PXBIOS] ERROR: ISO file '{source_file}' not open or incorrect for PX_READ_BYTES.")
		pxram[target_pxram_key] = null
		return

	if offset < 0 or length <= 0:
		_execute_px_log(f"[PXBIOS] ERROR: Invalid offset ({offset}) or length ({length}) for PX_READ_BYTES.")
		pxram[target_pxram_key] = null
		return

	# Seek to the specified offset
	iso_file_access.seek(offset)
	
	# Read the bytes
	var data = iso_file_access.get_buffer(length)
	
	if data.size() != length:
		_execute_px_log(f"[PXBIOS] WARNING: Read {data.size()} bytes, expected {length} for {target_pxram_key}. Partial read.")
		# Even if partial, store what was read. In a real scenario, this might be a PX_HALT.

	pxram[target_pxram_key] = data
	_execute_px_log(f"[PXBIOS] Read {data.size()} bytes for {target_pxram_key} from offset {offset}.")


func _execute_px_read_iso_pvd() -> bool:
	var pvd_offset = 0x8000 # Standard PVD location (sector 16 * 2048 bytes/sector)
	var pvd_length = 2048   # Standard PVD size (one sector)

	_execute_px_read_bytes(iso_file_path, pvd_offset, pvd_length, "pvd_data")
	var pvd_data: PoolByteArray = pxram.get("pvd_data")
	if pvd_data == null or pvd_data.size() < 156: # Need enough bytes for CD001 and root dir record
		_execute_px_log("[PXBIOS] ERROR: Failed to read PVD or PVD too small.")
		return false

	# Check for 'CD001' signature at byte 1
	var identifier_string = pvd_data.slice(1, 6).get_string_from_ascii()

	if identifier_string == "CD001":
		_execute_px_log("[PXBIOS] ISO9660 structure detected: CD001")
		
		# Extract Root Directory Record LBA (Little-endian at offset 156, 4 bytes)
		# and size (Little-endian at offset 164, 8 bytes)
		pxram["root_dir_lba"] = _read_le_uint32(pvd_data, 158) # LBA is at offset 158 (4 bytes)
		pxram["root_dir_size"] = _read_le_uint32(pvd_data, 166) # Size is at offset 166 (4 bytes, for simplicity)

		_execute_px_log(f"[PXBIOS] Root Directory at LBA: {pxram['root_dir_lba']} (Size: {pxram['root_dir_size']} bytes)")
		return true
	else:
		_execute_px_log(f"[PXBIOS] ERROR: Invalid ISO9660 PVD signature: '{identifier_string}' (expected 'CD001').")
		return false

# --- Real ISO Directory Parsing Functions ---

# Reads a raw directory block from the ISO and parses its entries.
# Stores the raw data in pxram[pxram_key] and parsed entries in pxram[pxram_key + "_entries"].
func _execute_px_scan_iso_dir_real(lba: int, size: int, pxram_key: String):
	var offset = lba * 2048
	# Read the raw directory block data into pxram[pxram_key]
	_execute_px_read_bytes(iso_file_path, offset, size, pxram_key)
	var dir_data = pxram.get(pxram_key)
	if dir_data == null:
		_execute_px_log("[PXBIOS] Failed to read directory block at LBA=%d" % lba)
		pxram[pxram_key + "_entries"] = [] # Ensure entries list is empty on failure
		return

	# Parse the raw directory data into a list of entries
	var entries = _parse_iso_directory_entries(dir_data)
	pxram[pxram_key + "_entries"] = entries # Store the parsed entries in PXRAM
	_execute_px_log("[PXBIOS] Parsed %d entries from directory at LBA=%d" % [entries.size(), lba])


# Parses ISO9660 directory entries from a raw block (PoolByteArray)
# Returns an Array of dictionaries, each representing a file/directory entry.
func _parse_iso_directory_entries(data: PoolByteArray) -> Array:
	var entries := []
	var index = 0

	while index < data.size():
		var length = data[index] # Length of the current directory record
		if length <= 0: # End of records in this block (or invalid record)
			break

		var lba = _read_le_uint32(data, index + 2) # Location of extent (LBA)
		var file_size = _read_le_uint32(data, index + 10) # Data length (file size)
		var flags = data[index + 25] # File Flags (bit 1 is directory)
		var name_len = data[index + 32] # Length of File Identifier

		# File Identifier (name) starts at offset + 33
		var name_bytes = data.slice(index + 33, index + 33 + name_len)
		var name = name_bytes.get_string_from_ascii()
		
		# Clean up ISO9660 specific naming conventions
		if name.contains(";"): # Remove version number (e.g., ";1")
			name = name.split(";")[0]
		if name.ends_with("."): # Remove trailing '.' for files (common in ISO9660)
			name = name.left(name.length() - 1)
		name = name.to_lower() # Convert to lowercase for easier comparison

		var is_dir = (flags & 0x02) != 0 # Check if the directory flag is set

		# Skip special directory entries: '.' (current dir) and '..' (parent dir)
		# These are represented by single byte 0x00 and 0x01 names respectively.
		if name_len == 1 and (name_bytes[0] == 0x00 or name_bytes[0] == 0x01):
			pass # Skip these special entries
		else:
			entries.append({
				"name": name,
				"lba": lba,
				"size": file_size,
				"is_dir": is_dir
			})

		index += length # Move to the next record

	return entries

# --- NEW: Recursive Directory Scanner ---
# Recursively parses all directories starting from a given LBA/size and path.
# Populates pxram["iso_parsed_files"] with all found files and directories.
# Populates pxram["iso_dir_map"] with directory metadata for traversal.
func _scan_and_cache_all_dirs(dir_pxram_key: String, lba: int, size: int, current_path_prefix: String):
	# Read and parse the current directory block
	_execute_px_scan_iso_dir_real(lba, size, dir_pxram_key)
	var entries = pxram.get(dir_pxram_key + "_entries", [])

	if entries.empty():
		_execute_px_log(f"[PXBIOS] No entries found for directory: {current_path_prefix}")
		return

	# Store this directory's metadata in iso_dir_map
	pxram["iso_dir_map"][dir_pxram_key] = {
		"lba": lba,
		"size": size,
		"path": current_path_prefix # Store the actual path for reference
	}

	for e in entries:
		var name = e["name"]
		# Special entries '.' and '..' are already skipped by _parse_iso_directory_entries
		# but an extra check here doesn't hurt if this function were used differently.
		if name == "." or name == "..":
			continue

		var full_path = current_path_prefix + name
		if e["is_dir"]:
			full_path += "/" # Add trailing slash for directories

		# Store the full path entry in the global parsed files map
		pxram["iso_parsed_files"][full_path] = {
			"lba": e["lba"],
			"size": e["size"],
			"is_dir": e["is_dir"]
		}
		# _execute_px_log(f"[PXBIOS] Cached entry: {full_path}") # Too verbose, uncomment for deep debug

		if e["is_dir"]:
			# Construct a unique key for the subdirectory's entries in PXRAM
			var sub_dir_pxram_key = dir_pxram_key + "_" + name
			# Recursively scan this subdirectory
			_scan_and_cache_all_dirs(sub_dir_pxram_key, e["lba"], e["size"], full_path)


# --- NEW: ISO Path Navigator ---
# Tries to find a file or directory at a given ISO-style path like "/boot/vmlinuz"
# Returns a dictionary with "offset", "size", "is_dir" if found, empty dict otherwise.
func _navigate_iso_path(iso_path: String) -> Dictionary:
	# Normalize the path to match how it's stored in iso_parsed_files
	var normalized_path = iso_path.to_lower()
	# Ensure directories end with a slash for consistent lookup in iso_parsed_files
	if not normalized_path.ends_with("/") and not normalized_path.contains("."):
		# This heuristic assumes if it doesn't have an extension and no trailing slash, it's a directory.
		# This might need refinement for edge cases.
		normalized_path += "/"

	var entry = pxram["iso_parsed_files"].get(normalized_path)
	if entry:
		return {
			"offset": entry["lba"] * 2048,
			"size": entry["size"],
			"is_dir": entry["is_dir"]
		}
	_execute_px_log(f"[PXBIOS] Path not found in parsed ISO: {iso_path}")
	return {}


# Final handoff
func _execute_px_exec_kernel():
	_execute_px_log("[PXBIOS] Handoff to Kernel at 0x100000...")
	yield(get_tree().create_timer(1.0), "timeout")
	get_tree().change_scene_to_file("res://PXOSUIScreen.tscn")

# Utils for reading multi-byte integers from PoolByteArray
func _read_le_uint32(data: PoolByteArray, offset: int) -> int:
	if offset + 4 > data.size(): return 0
	return (data[offset+3] << 24) | (data[offset+2] << 16) | (data[offset+1] << 8) | data[offset]

func _read_be_uint32(data: PoolByteArray, offset: int) -> int:
	if offset + 4 > data.size(): return 0
	return (data[offset] << 24) | (data[offset+1] << 16) | (data[offset+2] << 8) | data[offset+3]

