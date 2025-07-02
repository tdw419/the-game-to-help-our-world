# Call this to parse actual ISO directory entries
func _execute_px_scan_iso_dir_real(lba: int, size: int, pxram_key: String):
	var offset = lba * 2048
	_execute_px_read_bytes(iso_file_path, offset, size, pxram_key)
	var dir_data = pxram.get(pxram_key)
	if dir_data == null:
		_execute_px_log("[PXBIOS] Failed to read directory block at LBA=%d" % lba)
		return []

	var entries = _parse_iso_directory_entries(dir_data)
	pxram[pxram_key + "_entries"] = entries
	_execute_px_log("[PXBIOS] Parsed %d entries from directory at LBA=%d" % [entries.size(), lba])
	return entries


# Parses ISO9660 directory entries from a raw block
func _parse_iso_directory_entries(data: PoolByteArray) -> Array:
	var entries := []
	var index = 0

	while index < data.size():
		var length = data[index]
		if length <= 0:
			break

		var lba = _read_le_uint32(data, index + 2)
		var file_size = _read_le_uint32(data, index + 10)
		var name_len = data[index + 32]
		var name = data.subarray(index + 33, index + 33 + name_len).get_string_from_ascii()
		name = name.strip_edges(true, true).replace(";", "").replace(".", "").to_lower()

		entries.append({
			"name": name,
			"lba": lba,
			"size": file_size
		})

		index += length
	return entries


# Searches parsed ISO directories for a specific file
func _execute_px_find_in_iso_real(target_filename: String, dir_entries_key: String, offset_key: String, size_key: String):
	var entries = pxram.get(dir_entries_key + "_entries", [])
	for e in entries:
		if e["name"] == target_filename.to_lower():
			var offset = e["lba"] * 2048
			var size = e["size"]
			pxram[offset_key] = offset
			pxram[size_key] = size
			_execute_px_log("[PXBIOS] Found file '%s' at LBA=%d, size=%d" % [target_filename, e["lba"], size])
			return true

	_execute_px_log("[PXBIOS] File '%s' not found in %s." % [target_filename, dir_entries_key])
	pxram[offset_key] = 0
	pxram[size_key] = 0
	return false
