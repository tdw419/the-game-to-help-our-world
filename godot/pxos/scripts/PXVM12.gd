# PXVM.gd (Partial Example)
# This script would simulate the PXTalk Virtual Machine execution environment.

extends Node

# Dictionary to simulate PXRAM, storing variables and their values
var pxram: Dictionary = {
    "kernel_offset": 0,  # Initialize to 0 (not found)
    "initrd_offset": 0,  # Initialize to 0 (not found)
    "kernel_data": null, # To store simulated kernel binary data
    "initrd_data": null  # To store simulated initrd binary data
}

# Simulated ISO file offset map for testing
# In a real scenario, this would come from a .pxboot config or a more complex ISO parser.
var simulated_iso_offsets: Dictionary = {
    "tinycore.iso": {
        "/boot/vmlinuz": 1048576, # Example offset for kernel
        "/boot/core.gz": 6291456  # Example offset for initrd
    }
}

# Simulated file sizes for kernel and initrd
# These would typically be determined during the ISO parsing phase in a real system.
var simulated_file_sizes: Dictionary = {
    "tinycore.iso": {
        "/boot/vmlinuz": 8388608, # Example: 8 MB kernel
        "/boot/core.gz": 16777216 # Example: 16 MB initrd
    }
}

# Reference to the PXBootSim for logging (adjust path as needed)
@onready var px_boot_sim = null # Will be assigned in _ready() or via dependency injection

func _ready():
    # Find the PXBootSim instance to send log messages
    px_boot_sim = get_node_or_null("/root/PXBootSimNode") # Adjust path to your PXBootSim node

    # For testing, directly inject offsets and sizes into pxram here,
    # or load them from a configuration file.
    if simulated_iso_offsets.has("tinycore.iso"):
        var iso_data = simulated_iso_offsets["tinycore.iso"]
        if iso_data.has("/boot/vmlinuz"):
            pxram["kernel_offset"] = iso_data["/boot/vmlinuz"]
        if iso_data.has("/boot/core.gz"):
            pxram["initrd_offset"] = iso_data["/boot/core.gz"]

    # Example: Start PXTalk execution (this would be part of your main PXVM loop)
    # For demonstration, we'll call it directly here.
    _execute_pxtalk_script()


# Function to simulate the PX_LOG instruction
func _execute_px_log(message: String):
    print("PX_LOG: ", message) # Print to console for debugging
    if px_boot_sim:
        px_boot_sim._process_px_log_message(message)

# Function to simulate the PX_FIND_IN_ISO instruction
func _execute_px_find_in_iso(iso_name: String, path: String, target_var: String):
    var found_offset = 0
    if simulated_iso_offsets.has(iso_name):
        var iso_data = simulated_iso_offsets[iso_name]
        if iso_data.has(path):
            found_offset = iso_data[path]
    
    # Store the found offset (or 0 if not found) in PXRAM
    pxram[target_var] = found_offset
    print(f"PX_FIND_IN_ISO: {iso_name}, Path: {path}, Result: {target_var}={found_offset}")

# Function to simulate the PX_READ_BYTES instruction
# In a real scenario, this would read from a file stream or memory-mapped ISO image.
# Here, we simulate by creating a dummy PoolByteArray of the specified length.
func _execute_px_read_bytes(source_file: String, offset_var: String, length_var: String, target_pxram_key: String):
    var offset = pxram.get(offset_var, 0)
    var length = simulated_file_sizes.get(source_file, {}).get(length_var, 0) # Get length from simulated sizes

    if offset == 0 || length == 0:
        _execute_px_log(f"[PXBIOS] Error: Cannot read {target_pxram_key}. Offset or length is zero.")
        pxram[target_pxram_key] = null # Ensure target is null if read fails
        return

    # Simulate reading bytes by creating a dummy byte array
    var dummy_data = PoolByteArray()
    dummy_data.resize(length)
    # Optionally, fill with some dummy data for more realism (e.g., sequential bytes)
    for i in range(length):
        dummy_data[i] = i % 256 # Fill with some pattern

    pxram[target_pxram_key] = dummy_data
    _execute_px_log(f"[PXBIOS] Read {length} bytes for {target_pxram_key} from offset {offset}.")
    print(f"PX_READ_BYTES: Source: {source_file}, Offset: {offset}, Length: {length}, Target: {target_pxram_key}. Data size: {dummy_data.size()}")


# Simplified PXTalk instruction execution loop (conceptual)
# In reality, this would parse your .px script line by line and execute instructions.
func _execute_pxtalk_script():
    _execute_px_log("[PXBIOS] Scanning ISO directory for boot files...")

    # Simulate PX_FIND_IN_ISO calls
    _execute_px_find_in_iso("tinycore.iso", "/boot/vmlinuz", "kernel_offset")
    _execute_px_find_in_iso("tinycore.iso", "/boot/core.gz", "initrd_offset")

    # Simulate PX_IF conditions for kernel
    if pxram["kernel_offset"] != 0:
        _execute_px_log(f"[PXBIOS] Found kernel at offset {pxram['kernel_offset']}")
    else:
        _execute_px_log("[PXBIOS] Kernel not found. Halting.")
        return # Simulate PX_HALT

    # Simulate PX_IF conditions for initrd
    if pxram["initrd_offset"] != 0:
        _execute_px_log(f"[PXBIOS] Found initrd at offset {pxram['initrd_offset']}")
    else:
        _execute_px_log("[PXBIOS] Initrd not found. Halting.")
        return # Simulate PX_HALT

    # Now, simulate PX_READ_BYTES for kernel and initrd
    # We use the actual paths to look up their simulated lengths
    _execute_px_read_bytes("tinycore.iso", "kernel_offset", "/boot/vmlinuz", "kernel_data")
    _execute_px_read_bytes("tinycore.iso", "initrd_offset", "/boot/core.gz", "initrd_data")

    # Check if data was successfully loaded
    if pxram["kernel_data"] and pxram["initrd_data"]:
        _execute_px_log("[PXBIOS] Kernel and Initrd loaded successfully.")
        _execute_px_log("[PXBIOS] Performing PXHandoff to kernel...")
        # At this point, you would trigger the virtual execution of the loaded kernel
        # or transition to a different state in your PXVM.
    else:
        _execute_px_log("[PXBIOS] Failed to load kernel or initrd data. Halting.")
        return # Simulate PX_HALT

