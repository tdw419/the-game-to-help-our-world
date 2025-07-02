# PXQemuLauncher.gd
# This module is responsible for launching external QEMU processes
# specifically configured to boot ISO disk images.
# It acts as a bridge between PXOS (via PXRuntime) and the host operating system's
# QEMU installation.

extends Node

# --- Configuration ---
# Path to the QEMU system executable on the host system.
# IMPORTANT: Adjust this path based on your OS and QEMU installation.
# Examples:
# Windows: "C:/Program Files/qemu/qemu-system-x86_64.exe"
# Linux: "/usr/bin/qemu-system-x86_64"
# macOS: "/opt/homebrew/bin/qemu-system-x86_64" (if installed via Homebrew)
@export var qemu_system_executable_path: String = "/usr/bin/qemu-system-x86_64"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging launcher activity

# --- Internal State ---
var _current_qemu_process_id: int = 0 # Stores the OS process ID if an external process is running

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log:
        print_err("PXQemuLauncher: PXScrollLog dependency missing. Launcher logging disabled.")
        # Do not disable the node entirely, as it can still attempt to launch QEMU.

    _log_launcher_activity("Initialized. QEMU executable path set to: " + qemu_system_executable_path)
    _check_qemu_executable_existence()

func _check_qemu_executable_existence():
    """
    Checks if the specified QEMU executable path exists.
    Logs a warning if not found.
    """
    if not FileAccess.file_exists(qemu_system_executable_path):
        _log_launcher_activity("WARNING: QEMU executable not found at '%s'. Please verify the path." % qemu_system_executable_path)
        _log_launcher_activity("QEMU will not be able to launch until path is corrected.")

# --- Core Launcher Functions ---

func launch_iso(iso_path: String) -> int:
    """
    Launches a QEMU process to boot the specified ISO image.
    Returns the process ID (PID) if successful, 0 otherwise.
    This function attempts a non-blocking launch for GUI responsiveness.
    """
    if _current_qemu_process_id != 0:
        _log_launcher_activity("Error: A QEMU process is already active (PID: %d). Please terminate it first." % _current_qemu_process_id)
        return 0

    if not FileAccess.file_exists(iso_path):
        _log_launcher_activity("Error: ISO file not found at '%s'. Cannot launch." % iso_path)
        return 0

    # Build QEMU command arguments as per roadmap
    var qemu_args: Array[String] = [
        "-cdrom", ProjectSettings.globalize_path(iso_path), # Path to the ISO image
        "-boot", "d",       # Boot from CD-ROM (d)
        "-m", "2048",       # Allocate 2048MB (2GB) RAM
        "-enable-kvm",      # Enable KVM for hardware virtualization (Linux only, for performance)
        "-smp", "2",        # Use 2 CPU cores
        "-display", "sdl",  # Use SDL for QEMU's graphical output (opens a new window)
        "-no-reboot"        # Prevent QEMU from rebooting automatically on guest shutdown
    ]

    _log_launcher_activity("Preparing to launch QEMU: %s %s" % [qemu_system_executable_path, " ".join(qemu_args)])

    var process_id = 0
    # OS.create_process is the preferred method for non-blocking external processes.
    # It returns a ProcessID if successful.
    var error_code = OS.create_process(qemu_system_executable_path, qemu_args, &process_id)

    if error_code == OK:
        _current_qemu_process_id = process_id
        _log_launcher_activity("QEMU process launched successfully with PID: %d." % _current_qemu_process_id)
        return _current_qemu_process_id
    else:
        _log_launcher_activity("Failed to launch QEMU process. Error code: %d." % error_code)
        _current_qemu_process_id = 0
        return 0

func terminate_qemu_process():
    """
    Attempts to terminate the currently running QEMU process.
    """
    if _current_qemu_process_id != 0:
        _log_launcher_activity("Attempting to terminate QEMU process (PID: %d)..." % _current_qemu_process_id)
        OS.kill(_current_qemu_process_id) # Send termination signal
        _current_qemu_process_id = 0
        _log_launcher_activity("QEMU process terminated.")
    else:
        _log_launcher_activity("No active QEMU process to terminate.")

func get_current_qemu_process_id() -> int:
    """Returns the PID of the last launched QEMU process, or 0 if none active."""
    return _current_qemu_process_id

# --- Logging ---

func _log_launcher_activity(message: String):
    """
    Helper function to log launcher activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXQEMU: " + message)
    else:
        print("PXQemuLauncher (Console Log): ", message)

