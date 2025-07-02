# PXVM_MemMap.gd
# Responsible for loading ISO boot components into PXRAM (PXVM memory model)

extends Node

# --- Configuration ---
@export var iso_file_path: String = ""
@export var pxram := {}  # This acts as simulated RAM (you can wire it to a global singleton or PXRAM object)

# PXRAM map layout (adjustable)
const ADDR_KERNEL = 0x00100000  # Start of kernel in RAM (1 MB)
const ADDR_INITRD = 0x00800000  # Start of initrd in RAM (8 MB)

signal memory_mapped(component: String, addr: int, size: int)
signal mapping_failed(reason: String)

func load_boot_components(file_map: Dictionary):
    if iso_file_path == "" or file_map.is_empty():
        emit_signal("mapping_failed", "Missing ISO path or file map.")
        return

    var iso = FileAccess.open(iso_file_path, FileAccess.READ)
    if iso == null:
        emit_signal("mapping_failed", "Cannot open ISO.")
        return

    # Load kernel
    if file_map.has("vmlinuz"):
        var kernel_info = file_map["vmlinuz"]
        var kernel_offset = int(kernel_info["extent"]) * 2048
        var kernel_size = int(kernel_info["size"])

        iso.seek(kernel_offset)
        var kernel_data = iso.get_buffer(kernel_size)
        pxram[ADDR_KERNEL] = kernel_data
        emit_signal("memory_mapped", "vmlinuz", ADDR_KERNEL, kernel_size)
    else:
        emit_signal("mapping_failed", "vmlinuz not found.")
        return

    # Load initrd
    if file_map.has("core.gz"):
        var initrd_info = file_map["core.gz"]
        var initrd_offset = int(initrd_info["extent"]) * 2048
        var initrd_size = int(initrd_info["size"])

        iso.seek(initrd_offset)
        var initrd_data = iso.get_buffer(initrd_size)
        pxram[ADDR_INITRD] = initrd_data
        emit_signal("memory_mapped", "core.gz", ADDR_INITRD, initrd_size)
    else:
        emit_signal("mapping_failed", "core.gz not found.")
        return

    iso.close()
