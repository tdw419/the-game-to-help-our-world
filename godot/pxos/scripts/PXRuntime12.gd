# PXRuntime.gd
# This module serves as the primary host shell for PXOS, responsible for
# managing the loading, launching, and observation of external systems
# (like QEMU with ISOs, or future custom emulators).
# It acts as the bridge between PXOS's internal logic and external execution environments.

extends Node

# --- Configuration ---
# Defines the operational mode of the runtime.
# "external_exec": For launching external binaries (e.g., QEMU).
# "internal_emu": For future custom, in-Godot emulators.
@export var runtime_mode: String = "external_exec"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging runtime activity
@onready var px_qemu_launcher: PXQemuLauncher = get_node_or_null("../PXQemuLauncher") # To launch QEMU processes
@onready var px_drop_zone: PXDropZone = get_node_or_null("../PXDropZone") # To handle drag-and-drop file inputs
# @onready var px_shell_ui: Control = get_node_or_null("../PXShell") # Future: Reference to the main shell UI for panel integration

# Signals for other PXOS modules to connect to
signal runtime_session_started(session_id: String, system_name: String)
signal runtime_session_ended(session_id: String, outcome: String)
signal file_loaded_into_runtime(file_path: String, file_type: String)

# --- Internal State ---
var _current_session_id: String = ""
var _active_runtime_process_pid: int = 0 # Stores the OS process ID if an external process is running
var _loaded_file_path: String = ""
var _loaded_file_type: String = "" # e.g., "iso", "img", "elf"

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_qemu_launcher or not px_drop_zone:
        print_err("PXRuntime: Essential dependencies missing. Runtime disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Connect to PXDropZone's signals for file loading
    if px_drop_zone:
        px_drop_zone.file_dropped.connect(Callable(self, "_on_file_dropped_into_dropzone"))
        px_drop_zone.iso_file_dropped.connect(Callable(self, "_on_iso_file_dropped")) # Connect to new ISO specific signal
        _log_runtime_activity("Connected to PXDropZone for file loading (generic and ISO specific).")

    _log_runtime_activity("Initialized with mode: " + runtime_mode)

# --- Core Runtime Functions ---

func _on_file_dropped_into_dropzone(file_path: String, file_type: String):
    """
    Callback for when a file is dropped into the PXDropZone.
    This is a generic handler, specific types like ISO are handled by their own signals.
    """
    _log_runtime_activity("Received generic file via DropZone: %s (Type: %s)" % [file_path, file_type])
    
    _loaded_file_path = file_path
    _loaded_file_type = file_type
    
    emit_signal("file_loaded_into_runtime", file_path, file_type)
    
    # If it's not an ISO (which has its own handler), consider other auto-launch logic here
    if file_type != "iso":
        _log_runtime_activity("File type '%s' loaded, but not automatically launched by generic handler." % file_type)

func _on_iso_file_dropped(iso_path: String):
    """
    Callback for when an ISO file is dropped into the PXDropZone.
    Triggers the QEMU launcher for ISOs.
    (M2 of PXRUNTIME_BOOT_ISO_V1 roadmap)
    """
    _log_runtime_activity("ISO file detected via DropZone: " + iso_path)
    
    if _active_runtime_process_pid != 0:
        _log_runtime_activity("Error: Another system is already running. Please stop it first.")
        return

    _current_session_id = generate_session_id()
    _log_runtime_activity("Starting new runtime session for ISO: " + _current_session_id + " for " + iso_path)
    emit_signal("runtime_session_started", _current_session_id, iso_path)

    if px_qemu_launcher:
        _log_runtime_activity("Passing ISO to PXQemuLauncher: " + iso_path)
        var pid = px_qemu_launcher.launch_iso(iso_path)
        if pid != 0:
            _active_runtime_process_pid = pid
            _log_runtime_activity("QEMU ISO boot initiated with PID: %d." % _active_runtime_process_pid)
        else:
            _log_runtime_activity("Failed to initiate QEMU ISO boot.")
            emit_signal("runtime_session_ended", _current_session_id, "FAILED_LAUNCH_ISO")
    else:
        _log_runtime_activity("Error: PXQemuLauncher not available to boot ISO.")
        emit_signal("runtime_session_ended", _current_session_id, "FAILED_NO_LAUNCHER")


func launch_system(system_path: String, system_type: String, args: Array[String] = []):
    """
    Launches an external system based on the configured runtime mode.
    This function can be used for explicit launches, complementing the drop zone.
    """
    if _active_runtime_process_pid != 0:
        _log_runtime_activity("Error: Another system is already running. Please stop it first.")
        return

    _current_session_id = generate_session_id()
    _log_runtime_activity("Starting new runtime session: " + _current_session_id + " for " + system_path)
    emit_signal("runtime_session_started", _current_session_id, system_path)

    match runtime_mode:
        "external_exec":
            # For ISOs, we now prefer the dedicated launch_iso
            if system_type == "iso" and px_qemu_launcher:
                var pid = px_qemu_launcher.launch_iso(system_path)
                if pid != 0:
                    _active_runtime_process_pid = pid
                    _log_runtime_activity("QEMU ISO boot initiated via launch_system with PID: %d." % _active_runtime_process_pid)
                else:
                    _log_runtime_activity("Failed to initiate QEMU ISO boot via launch_system.")
                    emit_signal("runtime_session_ended", _current_session_id, "FAILED_LAUNCH_ISO")
            else:
                _log_runtime_activity("External executable launch for non-ISO types not fully implemented yet.")
                emit_signal("runtime_session_ended", _current_session_id, "FAILED_NOT_IMPLEMENTED_EXTERNAL")
        "internal_emu":
            _log_runtime_activity("Internal emulator mode not yet implemented.")
            emit_signal("runtime_session_ended", _current_session_id, "FAILED_NOT_IMPLEMENTED_INTERNAL")
        _:
            _log_runtime_activity("Unknown runtime mode: " + runtime_mode)
            emit_signal("runtime_session_ended", _current_session_id, "FAILED_UNKNOWN_MODE")

func stop_current_system():
    """
    Attempts to stop the currently running external system process.
    """
    if _active_runtime_process_pid != 0:
        _log_runtime_activity("Attempting to terminate QEMU process (PID: " + str(_active_runtime_process_pid) + ")...")
        if px_qemu_launcher:
            px_qemu_launcher.terminate_qemu_process() # Call launcher's terminate method
        else:
            OS.kill(_active_runtime_process_pid) # Fallback if launcher isn't available
        _active_runtime_process_pid = 0
        _log_runtime_activity("QEMU process terminated.")
        emit_signal("runtime_session_ended", _current_session_id, "STOPPED")
    else:
        _log_runtime_activity("No active system to stop.")

# --- Utility Functions ---

func generate_session_id() -> String:
    """Generates a unique session ID."""
    return "session_" + str(Time.get_unix_time_from_system()) + "_" + str(randi() % 10000)

# --- Logging ---

func _log_runtime_activity(message: String):
    """
    Helper function to log runtime activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXRUNTIME: " + message)
    else:
        print("PXRuntime (Console Log): ", message)

