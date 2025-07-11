# PXVM.gd
# This script simulates the PXTalk Virtual Machine execution environment
# and now includes functionality for reading real ISO files,
# recursively parsing ISO9660 directory records,
# enhanced filename flexibility (Phase 5), and handoff to PXOSUIScreen (Phase 11).
# It also integrates PX_EXEC_SCRIPT to run an embedded PXTalk boot script.

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

# --- Simulated Embedded PXTalk Boot Script ---
# This simulates the 'boot.pxtalk' file that would be generated by your Python compiler
# and theoretically embedded within the ISO.
# You should replace this string with the actual content of your generated tinycore_boot.pxtalk.
var embedded_pxtalk_boot_script_content: String = """
PX_LOG "[PXBIOS] Embedded boot.pxtalk executing..."

# MBR and PVD checks (conceptual, as PXVM already does this)
PX_READ_BYTES "tinycore.iso" 0 512 -> mbr_data
PX_COMPARE mbr_data 0x1FE 0xAA55 THEN "LABEL MBR_OK" ELSE "PX_HALT"
LABEL MBR_OK
PX_READ_ISO_PVD # This would internally verify CD001 and get root_dir_lba/size
PX_LOG "[PXBIOS] ISO structure validated by embedded script."

# Dynamically discovered kernel and initrd locations (replace with actual values from your compiler output)
PX_SET kernel_offset 1048576
PX_SET kernel_size 8388608
PX_SET initrd_offset 6291456
PX_SET initrd_size 16777216

PX_LOG "[PXBIOS] Found kernel at offset $kernel_offset (size $kernel_size)"
PX_LOG "[PXBIOS] Found initrd at offset $initrd_offset (size $initrd_size)"

# Read kernel and initrd data into PXRAM
PX_READ_BYTES "tinycore.iso" $kernel_offset $kernel_size -> kernel_data
PX_READ_BYTES "tinycore.iso" $initrd_offset $initrd_size -> initrd_data

PX_LOG "[PXBIOS] Kernel and Initrd loaded. Handoff to kernel simulation..."
PX_EXEC_KERNEL
"""
# --- End Simulated Embedded PXTalk Boot Script ---


# -------------------
# SYSTEM INIT
# -------------------

func _ready():
	# Find the PXBootSim instance to send log messages
	px_boot_sim = get_node_or_null("/root/PXBootSimNode")

	if not _open_iso_file(iso_file_path):
		return
	
	# Instead of _execute_pxtalk_script(), we now simulate loading
	# and executing the embedded PXTalk script.
	_execute_px_exec_script(embedded_pxtalk_boot_script_content)


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
# PXTalk Emulation (Now driven by _execute_px_exec_script)
# -------------------

# --- NEW: PX_EXEC_SCRIPT handler ---
func _execute_px_exec_script(script_content: String):
    _execute_px_log("[PXBIOS] Executing embedded PXTalk boot script...")
    var lines = script_content.split("\n")
    var labels = {} # To store LABEL positions for PX_JUMP/THEN

    # First pass: identify labels
    for i in range(lines.size()):
        var line = lines[i].strip_edges()
        if line.begins_with("LABEL "):
            var label_name = line.replace("LABEL ", "").strip_edges()
            labels[label_name] = i
            # print(f"DEBUG: Found LABEL {label_name} at line {i}") # Debugging labels

    var current_line_index = 0
    while current_line_index < lines.size():
        var line = lines[current_line_index].strip_edges()
        if line.empty() or line.begins_with("#") or line.begins_with("LABEL "):
            current_line_index += 1
            continue

        var parts = line.split(" ", false)
        var instruction = parts[0].to_upper()
        var args = parts.slice(1)

        # print(f"DEBUG: Executing line {current_line_index}: {line}") # Debugging execution flow

        match instruction:
            "PX_LOG":
                var message = line.replace("PX_LOG ", "").strip_edges()
                # Replace PXRAM variables like $kernel_offset
                for key in pxram.keys():
                    message = message.replace(f"${key}", str(pxram[key]))
                _execute_px_log(message)
            "PX_READ_BYTES":
                if args.size() >= 4:
                    var source_file = args[0].strip_edges().trim_prefix("\"").trim_suffix("\"")
                    var offset_str = args[1]
                    var length_str = args[2]
                    var target_pxram_key = args[3].trim_prefix("->").strip_edges()

                    var offset = int(offset_str) if not offset_str.begins_with("$") else pxram.get(offset_str.trim_prefix("$"), 0)
                    var length = int(length_str) if not length_str.begins_with("$") else pxram.get(length_str.trim_prefix("$"), 0)

                    _execute_px_read_bytes(source_file, offset, length, target_pxram_key)
                else:
                    _execute_px_log("[PXTalk] ERROR: PX_READ_BYTES: Missing arguments.")
                    return # Halt script execution on error
            "PX_COMPARE":
                if args.size() >= 5: # data_key, offset, expected_value, THEN, LABEL
                    var data_key = args[0]
                    var offset = int(args[1])
                    var expected_value = int(args[2], 0) # Auto-detect base (0x for hex)
                    var then_keyword = args[3].to_upper()
                    var target_label = args[4]

                    var result = _execute_px_compare(data_key, offset, expected_value)
                    if result and then_keyword == "THEN" and labels.has(target_label):
                        current_line_index = labels[target_label] # Jump
                        continue # Continue from new line index
                    elif not result and then_keyword == "ELSE" and labels.has(target_label): # Optional ELSE
                        current_line_index = labels[target_label] # Jump
                        continue # Continue from new line index
                else:
                    _execute_px_log("[PXTalk] ERROR: PX_COMPARE: Missing arguments.")
                    return # Halt script execution on error
            "PX_READ_ISO_PVD":
                if not _execute_px_read_iso_pvd():
                    _execute_px_log("[PXTalk] ERROR: PX_READ_ISO_PVD failed. Halting.")
                    return # Halt script execution on error
            "PX_SET":
                if args.size() >= 2:
                    var var_name = args[0]
                    var value_str = args[1]
                    var value
                    if value_str.begins_with("$"): # If value is another PXRAM variable
                        value = pxram.get(value_str.trim_prefix("$"), 0)
                    elif value_str.begins_with("0x"): # Hex value
                        value = int(value_str, 16)
                    else: # Decimal value
                        value = int(value_str)
                    pxram[var_name] = value
                else:
                    _execute_px_log("[PXTalk] ERROR: PX_SET: Missing arguments.")
                    return # Halt script execution on error
            "PX_EXEC_KERNEL":
                _execute_px_exec_kernel()
                return # Handoff, so script execution ends
            "PX_HALT":
                _execute_px_log("[PXTalk] PX_HALT instruction encountered. Stopping boot.")
                return # Stop script execution
            "PX_JUMP":
                if args.size() >= 1:
                    var target_label = args[0]
                    if labels.has(target_label):
                        current_line_index = labels[target_label]
                        continue # Continue from new line index
                    else:
                        _execute_px_log(f"[PXTalk] ERROR: PX_JUMP: Label '{target_label}' not found.")
                        return # Halt script execution on error
                else:
                    _execute_px_log("[PXTalk] ERROR: PX_JUMP: Missing label argument.")
                    return # Halt script execution on error
            # Add other PXTalk instructions here as needed (PX_FIND_IN_ISO, PX_SCAN_ISO_DIR etc.)
            # For this specific boot script, we only need the ones above.
            _:
                _execute_px_log(f"[PXTalk] ERROR: Unknown PXTalk instruction: {instruction}")
                return # Halt script execution on unknown instruction
        
        current_line_index += 1
    _execute_px_log("[PXBIOS] PXTalk script finished execution.")


# --- Original PXTalk Emulation functions (now called by _execute_px_exec_script) ---

func _execute_pxtalk_script():
    # This function is now effectively replaced by _execute_px_exec_script
    # but kept for reference or if you want to call a hardcoded sequence.
    pass # No longer needed for the new boot flow


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

# --- Real ISO Directory Parsing Functions (Not directly used by the embedded script, but kept for context) ---

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
		
		# Clean up ISO9660 specific naming conventions (Phase 5: Normalize filename lookup)
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

# --- Recursive Directory Scanner (Not directly used by the embedded script, but kept for context) ---
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


# --- ISO Path Navigator (Not directly used by the embedded script, but kept for context) ---
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

	# 1. Exact match
	var entry = pxram["iso_parsed_files"].get(normalized_path)
	if entry:
		_execute_px_log(f"[PXBIOS] Exact match found for: {iso_path}")
		return {
			"offset": entry["lba"] * 2048,
			"size": entry["size"],
			"is_dir": entry["is_dir"]
		}
	
	_execute_px_log(f"[PXBIOS] Exact match not found for: {iso_path}. Attempting fuzzy match...")

	# 2. Fuzzy matching fallback (basename match)
	# Extract the basename from the target path (e.g., "vmlinuz" from "/boot/vmlinuz")
	var path_parts = normalized_path.split("/")
	var target_basename = path_parts[path_parts.size() - 1]
	if target_basename.ends_with("/"): # Remove trailing slash if it's a directory basename
		target_basename = target_basename.left(target_basename.length() - 1)

	var containing_dir_path = ""
	if path_parts.size() > 1:
		containing_dir_path = "/" + "/".join(path_parts.slice(0, path_parts.size() - 1))
		if not containing_dir_path.ends_with("/"):
			containing_dir_path += "/"
	else: # If it's a root-level file, its containing dir is "/"
		containing_dir_path = "/"

	for full_file_path in pxram["iso_parsed_files"]:
		if full_file_path.begins_with(containing_dir_path):
			var file_entry = pxram["iso_parsed_files"][full_file_path]
			if not file_entry["is_dir"]: # Only consider files for fuzzy matching
				var file_basename = full_file_path.split("/").back()
				if file_basename.begins_with(target_basename):
					_execute_px_log(f"[PXBIOS] Fuzzy match found for '{iso_path}': '{full_file_path}'")
					return {
						"offset": file_entry["lba"] * 2048,
						"size": file_entry["size"],
						"is_dir": file_entry["is_dir"]
					}
	
	_execute_px_log(f"[PXBIOS] Path not found in parsed ISO (even with fuzzy match): {iso_path}")
	return {}


# --- Handoff to PXOSUIScreen ---
func _execute_px_exec_kernel():
	_execute_px_log("[PXBIOS] Handoff to PXOSUIScreen (Phase 11)...")
	yield(get_tree().create_timer(1.0), "timeout")
	
	# Load the PXOSUIScreen scene
	var pxos_ui_scene = load("res://PXOSUIScreen.tscn").instantiate()
	get_tree().root.add_child(pxos_ui_scene)
	
	# Pass the entire pxram dictionary to PXOSUIScreen
	if pxos_ui_scene.has_method("set_pxram_data"):
		pxos_ui_scene.set_pxram_data(pxram)
	
	# Hide and free the current scene (PXBootSim)
	if get_tree().current_scene:
		get_tree().current_scene.queue_free()
	# Set the new scene as the current scene
	get_tree().current_scene = pxos_ui_scene


# Utils for reading multi-byte integers from PoolByteArray
func _read_le_uint32(data: PoolByteArray, offset: int) -> int:
	if offset + 4 > data.size(): return 0
	return (data[offset+3] << 24) | (data[offset+2] << 16) | (data[offset+1] << 8) | data[offset]

func _read_be_uint32(data: PoolByteArray, offset: int) -> int:
	if offset + 4 > data.size(): return 0
	return (data[offset] << 24) | (data[offset+1] << 16) | (data[offset+2] << 8) | data[offset+3]

