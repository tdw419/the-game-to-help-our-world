# PXDigestLoader.gd
# This module is responsible for loading and parsing .pxdigest files,
# specifically designed to recognize and extract embedded ISO payloads.
# It acts as a bridge to allow PXOS to boot external systems encapsulated
# within its native .pxdigest format.

extends Node

# --- Configuration ---
# Prefix for temporary files extracted from digests.
@export var temp_file_prefix: String = "px_digest_temp_"
# Directory to store extracted temporary files (e.g., ISOs).
@export var temp_extract_dir: String = "user://temp_digests/"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging loader activity
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read .pxdigest file content
@onready var px_digest_inspector: PXDigestInspector = get_node_or_null("../PXDigestInspector") # To leverage its parsing capabilities
@onready var px_runtime: PXRuntime = get_node_or_null("../PXRuntime") # To pass extracted ISOs for launching

# Signals for other modules to react to digest loading events
signal digest_loaded(digest_path: String, metadata: Dictionary)
signal iso_payload_extracted(iso_path: String, digest_path: String)
signal digest_load_failed(digest_path: String, error_message: String)

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_fs_reader or not px_digest_inspector or not px_runtime:
        print_err("PXDigestLoader: Essential dependencies missing. Digest loading limited.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Ensure the temporary directory exists
    _ensure_temp_directory()
    _log_loader_activity("Initialized. Temp extract directory: " + temp_extract_dir)

# --- Core Digest Loading Functions ---

func load_digest(digest_path: String) -> Dictionary:
    """
    Loads and processes a .pxdigest file.
    If an ISO payload is detected, it attempts to extract and launch it.
    Returns parsed digest data.
    """
    _log_loader_activity("Loading digest: " + digest_path)

    var digest_content = px_fs_reader.read_file_by_name(digest_path)
    if digest_content.is_empty():
        var error_msg = "Failed to read .pxdigest file: " + digest_path
        _log_loader_activity("Error: " + error_msg)
        emit_signal("digest_load_failed", digest_path, error_msg)
        return {}

    var parsed_data = px_digest_inspector._parse_pxdigest_content(digest_content)
    var metadata = parsed_data.get("metadata", {})
    var pixel_data = parsed_data.get("pixel_data", []) # Raw pixel data (not used for ISO extraction directly)

    emit_signal("digest_loaded", digest_path, metadata)
    _log_loader_activity("Digest '%s' loaded. Metadata: %s" % [digest_path.get_file(), str(metadata)])

    # Check for ISO payload reference in metadata
    var payload_ref = metadata.get("payload", "")
    if payload_ref.begins_with("/boot/") and payload_ref.ends_with(".iso"):
        _log_loader_activity("ISO payload reference detected: " + payload_ref)
        # Assuming for this scaffold that the ISO data is directly encoded
        # within a specific part of the .pxdigest or referenced by path within the digest's structure.
        # For a real implementation, you'd need a robust way to extract binary data from a text-based .pxdigest.
        # For now, we'll simulate extraction by looking for a specific marker and data.

        var iso_data_marker = "--- ISO_PAYLOAD_START ---"
        var iso_data_end_marker = "--- ISO_PAYLOAD_END ---"
        
        var iso_start_pos = digest_content.find(iso_data_marker)
        var iso_end_pos = digest_content.find(iso_data_end_marker)

        if iso_start_pos != -1 and iso_end_pos != -1 and iso_end_pos > iso_start_pos:
            var raw_iso_base64 = digest_content.substr(iso_start_pos + iso_data_marker.length(), iso_end_pos - (iso_start_pos + iso_data_marker.length())).strip_edges()
            _log_loader_activity("Found ISO payload data within digest. Attempting to decode and extract.")
            
            var decoded_iso_data = Marshalls.base64_to_raw(raw_iso_base64.to_utf8())
            if decoded_iso_data.size() > 0:
                var temp_iso_file_name = temp_file_prefix + digest_path.get_file().replace(".pxdigest", "") + ".iso"
                var temp_iso_path = temp_extract_dir + temp_iso_file_name

                var file = FileAccess.open(temp_iso_path, FileAccess.WRITE)
                if file:
                    file.store_buffer(decoded_iso_data)
                    file.close()
                    _log_loader_activity("ISO payload extracted to: " + temp_iso_path)
                    emit_signal("iso_payload_extracted", temp_iso_path, digest_path)
                    
                    # Automatically pass to PXRuntime for launching (M8)
                    if px_runtime:
                        _log_loader_activity("Routing extracted ISO to PXRuntime for launch.")
                        px_runtime._on_iso_file_dropped(temp_iso_path) # Directly call the ISO handler
                    else:
                        _log_loader_activity("Error: PXRuntime not available to launch extracted ISO.")
                else:
                    var extract_error = "Failed to write extracted ISO to: " + temp_iso_path
                    _log_loader_activity("Error: " + extract_error)
                    emit_signal("digest_load_failed", digest_path, extract_error)
            else:
                var decode_error = "Failed to decode ISO payload from base64."
                _log_loader_activity("Error: " + decode_error)
                emit_signal("digest_load_failed", digest_path, decode_error)
        else:
            _log_loader_activity("ISO payload reference found, but no embedded ISO data marker in digest.")
            # This could be a digest that just points to an external ISO, not embeds it.
            # Handle that case if needed.
    else:
        _log_loader_activity("No ISO payload reference found in digest metadata.")

    return parsed_data

func _ensure_temp_directory():
    """Ensures the temporary extraction directory exists."""
    var dir = DirAccess.open("user://")
    if dir and not dir.dir_exists(temp_extract_dir.replace("user://", "")):
        dir.make_dir(temp_extract_dir.replace("user://", ""))
        _log_loader_activity("Created temporary directory: " + temp_extract_dir)

# --- Utility Functions ---

func cleanup_temp_files():
    """Removes temporary files extracted by the loader."""
    var dir = DirAccess.open(temp_extract_dir)
    if dir:
        dir.list_dir_begin()
        var file_name = dir.get_next()
        while file_name != "":
            if not dir.current_is_dir() and file_name.begins_with(temp_file_prefix):
                var file_path = temp_extract_dir + file_name
                dir.remove(file_path)
                _log_loader_activity("Cleaned up temporary file: " + file_path)
            file_name = dir.get_next()
        dir.list_dir_end()
    _log_loader_activity("Temporary files cleanup complete.")

# --- Logging ---

func _log_loader_activity(message: String):
    """
    Helper function to log loader activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXDIGEST_LOADER: " + message)
    else:
        print("PXDigestLoader (Console Log): ", message)

