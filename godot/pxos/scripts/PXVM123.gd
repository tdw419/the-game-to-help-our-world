# PXVM.gd (Partial Example)
# This script simulates the PXTalk Virtual Machine execution environment
# and now includes functionality for reading real ISO files.

extends Node

# Dictionary to simulate PXRAM, storing variables and their values
var pxram: Dictionary = {
    "kernel_offset": 0,  # Initialize to 0 (not found)
    "initrd_offset": 0,  # Initialize to 0 (not found)
    "kernel_data": null, # To store simulated kernel binary data
    "initrd_data": null  # To store simulated initrd binary data
}

# Path to the ISO file to be loaded.
# For testing, place tinycore.iso in your project's 'res://' directory
# (e.g., res://tinycore.iso) or a subfolder like 'res://iso/tinycore.iso'.
var iso_file_path: String = "res://tinycore.iso" # <<< CONFIGURE YOUR ISO PATH HERE

# FileAccess object for reading the ISO
var iso_file_access: FileAccess = null

# Reference to the PXBootSim for logging (adjust path as needed)
@onready var px_boot_sim = null # Will be assigned in _ready() or via dependency injection

func _ready():
    # Find the PXBootSim instance to send log messages
    px_boot_sim = get_node_or_null("/root/PXBootSimNode") # Adjust path to your PXBootSim node

    # Attempt to open the ISO file
    _open_iso_file(iso_file_path)

    # Start PXTalk execution
    _execute_pxtalk_script()

func _exit_tree():
    # Ensure the file is closed when the scene exits
    if iso_file_access:
        iso_file_access.close()
        iso_file_access = null

# Function to open the ISO file
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

# Function to simulate the PX_LOG instruction
func _execute_px_log(message: String):
    print("PX_LOG: ", message) # Print to console for debugging
    if px_boot_sim:
        px_boot_sim._process_px_log_message(message)

# Function to simulate the PX_READ_BYTES instruction (now reads from actual file)
func _execute_px_read_bytes(source_file: String, offset: int, length: int, target_pxram_key: String):
    if not iso_file_access or iso_file_access.get_path() != source_file:
        _execute_px_log(f"[PXBIOS] ERROR: ISO file '{source_file}' not open or incorrect.")
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
        _execute_px_log(f"[PXBIOS] WARNING: Read {data.size()} bytes, expected {length} for {target_pxram_key}.")
        # Even if partial, store what was read. You might want to PX_HALT here in a real scenario.

    pxram[target_pxram_key] = data
    _execute_px_log(f"[PXBIOS] Read {data.size()} bytes for {target_pxram_key} from offset {offset}.")
    print(f"PX_READ_BYTES: Source: {source_file}, Offset: {offset}, Length: {length}, Target: {target_pxram_key}. Data size: {data.size()}")

# Function to simulate PX_READ_ISO_PVD
# This function will read the Primary Volume Descriptor and check for "CD001".
func _execute_px_read_iso_pvd():
    var pvd_offset = 0x8000 # Standard PVD location
    var pvd_length = 2048   # Standard PVD size (one sector)

    # Read the PVD sector
    _execute_px_read_bytes(iso_file_path, pvd_offset, pvd_length, "pvd_data")

    var pvd_data: PoolByteArray = pxram.get("pvd_data")
    if pvd_data == null or pvd_data.size() < 7: # Need at least 7 bytes for 'CD001' and version
        _execute_px_log("[PXBIOS] ERROR: Failed to read PVD or PVD too small.")
        return false

    # Check for 'CD001' signature at byte 1 (offset 1 from start of PVD)
    # PVD structure: Type (1 byte), Standard Identifier (5 bytes "CD001"), Version (1 byte)
    var identifier_bytes = pvd_data.slice(1, 6) # Bytes from index 1 to 5 (inclusive)
    var identifier_string = identifier_bytes.get_string_from_ascii()

    if identifier_string == "CD001":
        _execute_px_log("[PXBIOS] ISO9660 structure detected: CD001")
        return true
    else:
        _execute_px_log(f"[PXBIOS] ERROR: Invalid ISO9660 PVD signature: '{identifier_string}' (expected 'CD001').")
        return false

# Function to simulate PX_COMPARE (for MBR end signature)
func _execute_px_compare(data_key: String, offset: int, expected_value: int) -> bool:
    var data: PoolByteArray = pxram.get(data_key)
    if data == null or offset + 2 > data.size(): # Need 2 bytes for 0x55AA
        _execute_px_log(f"[PXBIOS] ERROR: Data '{data_key}' not available or too small for compare at offset {offset}.")
        return false

    # Read 2 bytes as a 16-bit little-endian integer
    var value = (data[offset+1] << 8) | data[offset] # Little-endian 0xAA55
    
    if value == expected_value:
        _execute_px_log(f"[PXBIOS] Verified {data_key} signature: 0x{expected_value:X}")
        return true
    else:
        _execute_px_log(f"[PXBIOS] ERROR: {data_key} signature mismatch: 0x{value:X} (expected 0x{expected_value:X}).")
        return false


# New function to simulate PX_EXEC_KERNEL
func _execute_px_exec_kernel():
    _execute_px_log("[PXBIOS] Kernel execution handoff initiated.")
    _execute_px_log("[PXBIOS] Transferring control to kernel at 0x100000...")
    _execute_px_log("[PXBIOS] Setting up boot parameters and registers...")

    # Simulate a brief delay before changing scene
    yield(get_tree().create_timer(1.0), "timeout")

    # Pass PXRAM data to the new scene if needed (e.g., for debugging or displaying info)
    # For now, we'll just change the scene. The PXOSUIScreen will simulate its own boot.
    get_tree().change_scene_to_file("res://PXOSUIScreen.tscn") # Ensure this path is correct


# Simplified PXTalk instruction execution loop (conceptual)
# This now simulates the PXTalk script for Phase 1.
func _execute_pxtalk_script():
    _execute_px_log("[PXBIOS] Starting PXBoot Real ISO Loader...")

    if not iso_file_access:
        _execute_px_log("[PXBIOS] Cannot proceed without ISO file. Halting.")
        return

    # --- Phase 1: Boot Sector & ISO PVD Parser ---

    # Read MBR (first 512 bytes)
    _execute_px_read_bytes(iso_file_path, 0, 512, "mbr_data")
    var mbr_data: PoolByteArray = pxram.get("mbr_data")

    if mbr_data == null or mbr_data.size() < 512:
        _execute_px_log("[PXBIOS] ERROR: Failed to read MBR. Halting.")
        return

    # Verify MBR boot signature (0xAA55 at offset 0x1FE)
    if not _execute_px_compare("mbr_data", 0x1FE, 0xAA55):
        _execute_px_log("[PXBIOS] Invalid MBR boot signature. Halting.")
        return
    _execute_px_log("[PXBIOS] Valid boot sector found.")

    # Read and validate ISO PVD
    if not _execute_px_read_iso_pvd():
        _execute_px_log("[PXBIOS] ISO PVD validation failed. Halting.")
        return

    _execute_px_log("[PXBIOS] Phase 1: Boot Sector & ISO PVD Parser - COMPLETE.")

    # --- Placeholder for Phase 2: Kernel & Initrd Detection + Extraction ---
    # This part will be implemented next, after Phase 1 is solid.
    _execute_px_log("[PXBIOS] Entering Phase 2: Kernel & Initrd Detection + Extraction (Simulated)...")

    # For now, we'll revert to the simulated offsets for kernel/initrd
    # until PX_SCAN_ISO_DIR and PX_FIND_IN_ISO are implemented for real ISOs.
    var simulated_iso_offsets: Dictionary = {
        "res://tinycore.iso": { # Use the actual path for consistency
            "/boot/vmlinuz": 1048576, # Example offset
            "/boot/core.gz": 6291456  # Example offset
        }
    }
    var simulated_file_sizes: Dictionary = {
        "res://tinycore.iso": {
            "/boot/vmlinuz": 8388608, # Example: 8 MB kernel
            "/boot/core.gz": 16777216 # Example: 16 MB initrd
        }
    }

    if simulated_iso_offsets.has(iso_file_path):
        var iso_data = simulated_iso_offsets[iso_file_path]
        pxram["kernel_offset"] = iso_data.get("/boot/vmlinuz", 0)
        pxram["initrd_offset"] = iso_data.get("/boot/core.gz", 0)

    if pxram["kernel_offset"] != 0:
        _execute_px_log(f"[PXBIOS] Found kernel at simulated offset {pxram['kernel_offset']}")
    else:
        _execute_px_log("[PXBIOS] Kernel not found (simulated). Halting.")
        return

    if pxram["initrd_offset"] != 0:
        _execute_px_log(f"[PXBIOS] Found initrd at simulated offset {pxram['initrd_offset']}")
    else:
        _execute_px_log("[PXBIOS] Initrd not found (simulated). Halting.")
        return

    # Now, simulate PX_READ_BYTES for kernel and initrd using real file access
    # but with simulated offsets and lengths for now.
    _execute_px_read_bytes(iso_file_path, pxram["kernel_offset"], simulated_file_sizes[iso_file_path]["/boot/vmlinuz"], "kernel_data")
    _execute_px_read_bytes(iso_file_path, pxram["initrd_offset"], simulated_file_sizes[iso_file_path]["/boot/core.gz"], "initrd_data")

    # Check if data was successfully loaded
    if pxram["kernel_data"] and pxram["initrd_data"]:
        _execute_px_log("[PXBIOS] Kernel and Initrd loaded successfully (simulated extraction).")
        # Trigger the kernel handoff
        _execute_px_exec_kernel()
    else:
        _execute_px_log("[PXBIOS] Failed to load kernel or initrd data. Halting.")
        return

