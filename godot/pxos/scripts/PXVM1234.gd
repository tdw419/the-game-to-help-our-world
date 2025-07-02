# Utility: Convert 32-bit little-endian bytes to int
func _read_le_uint32(data: PoolByteArray, offset: int) -> int:
    return (data[offset + 3] << 24) | (data[offset + 2] << 16) | (data[offset + 1] << 8) | data[offset]

# Read ISO directory structure and find a file path (e.g., /boot/core.gz)
func _execute_px_find_in_iso_real(iso_path: String, file_path: String, target_var: String):
    # Ensure ISO is loaded
    if not iso_file_access:
        _execute_px_log("[PXBIOS] ERROR: No ISO file open for PX_FIND_IN_ISO.")
        pxram[target_var] = 0
        return

    # Read PVD again to extract root directory info
    _execute_px_read_bytes(iso_path, 0x8000, 2048, "pvd_data")
    var pvd: PoolByteArray = pxram.get("pvd_data")
    if not pvd:
        _execute_px_log("[PXBIOS] ERROR: Could not read PVD for PX_FIND_IN_ISO.")
        pxram[target_var] = 0
        return

    # Root directory record starts at byte 156
    var root_dir_record = pvd.slice(156, 190)
    var root_extent = _read_le_uint32(root_dir_record, 2) # Logical block address
    var root_size = _read_le_uint32(root_dir_record, 10)  # Size in bytes

    var current_extent = root_extent
    var current_data = PoolByteArray()
    var segments = file_path.split("/", false)
    if segments.size() == 0:
        pxram[target_var] = 0
        return

    # Traverse each directory segment
    for i in range(segments.size()):
        var segment = segments[i]
        if segment == "":
            continue
        var found = false
        # Read current directory block
        var dir_offset = current_extent * 2048
        _execute_px_read_bytes(iso_path, dir_offset, 2048, "dir_block")
        var dir_block: PoolByteArray = pxram.get("dir_block")
        if not dir_block:
            _execute_px_log("[PXBIOS] ERROR: Cannot read directory block.")
            break

        var pos = 0
        while pos < dir_block.size():
            var length = dir_block[pos]
            if length == 0:
                break
            var entry = dir_block.slice(pos, pos + length)
            var entry_name_len = entry[32]
            var entry_name = entry.slice(33, 33 + entry_name_len).get_string_from_ascii()
            var entry_extent = _read_le_uint32(entry, 2)
            var is_dir = (entry[25] & 0x02) != 0
            if entry_name == segment:
                current_extent = entry_extent
                found = true
                if i == segments.size() - 1 and not is_dir:
                    pxram[target_var] = current_extent * 2048
                    _execute_px_log("[PXBIOS] PX_FIND_IN_ISO: Found '%s' at offset %d." % [file_path, pxram[target_var]])
                    return
                break
            pos += length
        if not found:
            _execute_px_log("[PXBIOS] PX_FIND_IN_ISO: '%s' not found in ISO." % segment)
            pxram[target_var] = 0
            return

    _execute_px_log("[PXBIOS] PX_FIND_IN_ISO: '%s' appears to be a directory." % file_path)
    pxram[target_var] = 0
