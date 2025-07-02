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
@onready var px_qemu_launcher: PXQEMULauncher = get_node_or_null("../PXQEMULauncher") # To launch QEMU processes
@onready var px_drop_zone: PXDropZone = get_node_or_null("../PXDropZone") # To handle drag-and-drop file inputs
# @onready var px_shell_ui: Control = get_node_or_null("../PXShell") # Future: Reference to the main shell UI for panel integration

# Signals for other PXOS modules to connect to
signal runtime_session_started(session_id: String, system_name: String)
signal runtime_session_ended(session_id: String, outcome: String)
signal file_loaded_into_runtime(file_path: String, file_type: String)

# --- Internal State ---
var _current_session_id: String = ""
var _active_runtime_process: OS.ProcessID = 0 # Stores the OS process ID if an external process is running
var _loaded_file_path: String = ""
var _loaded_file_type: String = "" # e.g., "iso", "img", "elf"

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_qemu_launcher or not px_drop_zone:
        print_err("PXRuntime: Essential dependencies missing. Runtime disabled.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Connect to PXDropZone's signal for file loading
    if px_drop_zone:
        px_drop_zone.file_dropped.connect(Callable(self, "_on_file_dropped_into_dropzone"))
        _log_runtime_activity("Connected to PXDropZone for file loading.")

    _log_runtime_activity("Initialized with mode: " + runtime_mode)

# --- Core Runtime Functions ---

func _on_file_dropped_into_dropzone(file_path: String, file_type: String):
    """
    Callback for when a file is dropped into the PXDropZone.
    Initiates the process of loading and preparing the file for execution.
    """
    _log_runtime_activity("Received file via DropZone: %s (Type: %s)" % [file_path, file_type])
    
    _loaded_file_path = file_path
    _loaded_file_type = file_type
    
    emit_signal("file_loaded_into_runtime", file_path, file_type)
    
    # Automatically attempt to launch if it's a recognized bootable type
    if file_type == "iso" or file_type == "img":
        _log_runtime_activity("Attempting to launch bootable image...")
        launch_system(file_path, file_type)
    else:
        _log_runtime_activity("File type '%s' loaded, but not automatically launched. Manual launch required." % file_type)


func launch_system(system_path: String, system_type: String, args: Array[String] = []):
    """
    Launches an external system based on the configured runtime mode.
    Currently focuses on external execution via PXQEMULauncher.
    """
    if _active_runtime_process != 0:
        _log_runtime_activity("Error: Another system is already running. Please stop it first.")
        return

    _current_session_id = generate_session_id()
    _log_runtime_activity("Starting new runtime session: " + _current_session_id + " for " + system_path)
    emit_signal("runtime_session_started", _current_session_id, system_path)

    match runtime_mode:
        "external_exec":
            _launch_external_executable(system_path, system_type, args)
        "internal_emu":
            _log_runtime_activity("Internal emulator mode not yet implemented.")
            emit_signal("runtime_session_ended", _current_session_id, "FAILED_NOT_IMPLEMENTED")
        _:
            _log_runtime_activity("Unknown runtime mode: " + runtime_mode)
            emit_signal("runtime_session_ended", _current_session_id, "FAILED_UNKNOWN_MODE")

func _launch_external_executable(system_path: String, system_type: String, extra_args: Array[String]):
    """
    Uses PXQEMULauncher to start an external QEMU process.
    """
    if not px_qemu_launcher:
        _log_runtime_activity("Error: PXQEMULauncher not available to launch external executable.")
        emit_signal("runtime_session_ended", _current_session_id, "FAILED_NO_LAUNCHER")
        return

    var qemu_args = []
    # Basic QEMU arguments based on file type
    if system_type == "iso":
        qemu_args.append("-cdrom")
        qemu_args.append(ProjectSettings.globalize_path(system_path)) # Ensure absolute path for external process
    elif system_type == "img":
        qemu_args.append("-hda")
        qemu_args.append(ProjectSettings.globalize_path(system_path))
    
    # Add common QEMU args and any extra args provided
    qemu_args.append("-m")
    qemu_args.append("512M") # Default 512MB RAM
    qemu_args.append("-no-reboot") # Prevent QEMU from rebooting automatically
    qemu_args.append("-display")
    qemu_args.append("sdl") # Use SDL display for QEMU, or "none" for headless
    
    for arg in extra_args:
        qemu_args.append(arg)

    _log_runtime_activity("Calling PXQEMULauncher to start QEMU with: " + str(qemu_args))
    
    var process_id = px_qemu_launcher.launch_qemu(qemu_args)
    if process_id != 0:
        _active_runtime_process = process_id
        _log_runtime_activity("QEMU process started with PID: " + str(_active_runtime_process))
        # In a real scenario, you'd monitor this PID for completion/errors
        # For now, we assume it runs and log its start.
    else:
        _log_runtime_activity("Failed to launch QEMU process.")
        emit_signal("runtime_session_ended", _current_session_id, "FAILED_LAUNCH")

func stop_current_system():
    """
    Attempts to stop the currently running external system process.
    """
    if _active_runtime_process != 0:
        _log_runtime_activity("Attempting to terminate QEMU process (PID: " + str(_active_runtime_process) + ")...")
        OS.kill(_active_runtime_process) # Send terminate signal
        _active_runtime_process = 0
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

