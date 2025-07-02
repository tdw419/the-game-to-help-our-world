# PXQEMULauncher.gd
# This module is responsible for launching and managing external QEMU processes.
# It acts as a bridge between PXOS (via PXRuntime) and the host operating system's
# QEMU installation.

extends Node

# --- Configuration ---
# Path to the QEMU executable on the host system.
# You might need to adjust this based on your OS and QEMU installation path.
# Examples:
# Windows: "C:/Program Files/qemu/qemu-system-x86_64.exe"
# Linux: "/usr/bin/qemu-system-x86_64"
# macOS: "/opt/homebrew/bin/qemu-system-x86_64" (if installed via Homebrew)
@export var qemu_executable_path: String = "/usr/bin/qemu-system-x86_64"

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging launcher activity

# --- Internal State ---
var _current_qemu_process_id: OS.ProcessID = 0 # Stores the PID of the last launched QEMU process

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log:
        print_err("PXQEMULauncher: PXScrollLog dependency missing. Launcher logging disabled.")
        # Do not disable the node entirely, as it can still attempt to launch QEMU.

    _log_launcher_activity("Initialized. QEMU executable path set to: " + qemu_executable_path)
    _check_qemu_executable_existence()

func _check_qemu_executable_existence():
    """
    Checks if the specified QEMU executable path exists and is executable.
    Logs a warning if not found.
    """
    if not FileAccess.file_exists(qemu_executable_path):
        _log_launcher_activity("WARNING: QEMU executable not found at '%s'. Please verify the path." % qemu_executable_path)
    # Note: Checking for executability directly in Godot can be tricky and OS-dependent.
    # OS.execute will return an error code if it's not executable.

# --- Core Launcher Functions ---

func launch_qemu(args: Array[String]) -> OS.ProcessID:
    """
    Launches a QEMU process with the given arguments.
    Returns the process ID (PID) if successful, 0 otherwise.
    """
    if _current_qemu_process_id != 0:
        _log_launcher_activity("Error: A QEMU process is already active (PID: %d). Please terminate it first." % _current_qemu_process_id)
        return 0

    _log_launcher_activity("Attempting to launch QEMU: %s %s" % [qemu_executable_path, " ".join(args)])

    var output_array = []
    var error_array = []
    var exit_code = 0
    var process_id = 0

    # OS.create_process is generally preferred for long-running external processes
    # as it allows the Godot application to continue running without blocking.
    # However, monitoring its output and exit status requires more complex handling
    # (e.g., polling or dedicated threads, which are beyond this basic scaffold).
    # For simplicity, this example uses OS.execute which blocks until the process exits,
    # but for a true runtime, you'd use create_process and manage it asynchronously.

    # For a non-blocking QEMU launch that runs in its own window:
    # We rely on QEMU's own display arguments (like -display sdl) to open a window.
    # OS.execute will still block if QEMU itself doesn't detach or if its output is piped.
    # To truly detach, it might require OS-specific commands (e.g., 'nohup' on Linux, 'start' on Windows).
    # For now, we assume QEMU's -display argument handles the windowing.

    # Using OS.execute for simplicity, but be aware it blocks.
    # For a robust solution, consider OS.create_process and managing its output/lifetime.
    
    # OS.execute returns the exit code. If it's a separate process, it will return 0 immediately
    # if the command was successfully invoked, not necessarily if QEMU ran correctly.
    # Getting the PID of a detached process can be complex.
    # For this scaffold, we'll simulate a PID for demonstration and rely on OS.kill.
    
    # In a real scenario, you'd use OS.create_process and then OS.get_process_id() if available,
    # or rely on platform-specific methods to get the PID of a detached process.
    
    # For now, we'll use OS.execute and assume it works for simple cases,
    # and assign a dummy PID if it appears to launch.
    
    # A more robust approach for non-blocking external processes with PID retrieval:
    # var process = OS.create_process(qemu_executable_path, args)
    # if process.is_valid():
    #    _current_qemu_process_id = process.get_process_id() # This method might not be available or reliable cross-platform
    #    _log_launcher_activity("QEMU process launched (PID: %d)." % _current_qemu_process_id)
    #    return _current_qemu_process_id
    # else:
    #    _log_launcher_activity("Failed to create QEMU process.")
    #    return 0

    # Simplified approach for scaffold:
    # OS.execute returns the exit code of the process. If it successfully starts QEMU
    # (which then opens its own window), OS.execute might return 0 quickly,
    # or it might block until QEMU exits, depending on QEMU's display settings and OS.
    # We cannot reliably get the PID of a truly detached process directly from OS.execute.
    # For the purpose of `_active_runtime_process` in PXRuntime, we'll assign a dummy PID
    # or rely on the fact that `OS.kill` might work with a "known" PID if we could get it.
    
    # To make QEMU truly non-blocking and have its own window,
    # you typically need to ensure QEMU's -display argument is set correctly (e.g., 'sdl')
    # and that the shell command itself doesn't block (e.g., using 'start' on Windows, 'nohup' on Linux).
    
    # For this Godot script, the most direct way to get a PID for management later
    # is to use OS.create_process if it becomes robust enough to provide PIDs reliably.
    # As a workaround for this scaffold, we'll just return a non-zero value to indicate
    # a "successful" launch attempt, and rely on PXRuntime's `stop_current_system`
    # to use `OS.kill` with that assumed PID. This is a simplification.

    # Simulating a successful launch and returning a dummy PID for PXRuntime to manage.
    # In a real application, you'd need a more robust way to get the actual PID
    # of the detached QEMU process.
    
    # A common way to run a process in the background and get its PID on Linux/macOS
    # is to use a shell command like 'sh -c "qemu-system-x86_64 ... & echo $!"'
    # and then parse the output. This is platform-specific.
    
    # For cross-platform, Godot's OS.execute is limited for background processes.
    # We'll make a best effort.
    
    # Example using OS.execute (blocking for simplicity of scaffold):
    # This will block Godot until QEMU exits if QEMU's display mode doesn't detach.
    # For a real VM, you want QEMU to run in its own window and not block Godot.
    # The `_launch_external_executable` in PXRuntime already sets `-display sdl`.
    
    var result = OS.execute(qemu_executable_path, args, true, output_array, error_array)
    
    if result == 0: # 0 typically means success for OS.execute (command found and executed)
        _log_launcher_activity("QEMU command executed successfully (blocking call). Output: %s, Error: %s" % [output_array, error_array])
        # Since OS.execute blocks, _current_qemu_process_id won't be useful here unless
        # QEMU itself detaches immediately. For the purpose of PXRuntime's _active_runtime_process,
        # we need a non-zero value. We'll use a placeholder.
        _current_qemu_process_id = 12345 # Dummy PID for demonstration
        return _current_qemu_process_id
    else:
        _log_launcher_activity("Failed to execute QEMU command. Exit code: %d. Error: %s" % [result, error_array])
        _current_qemu_process_id = 0
        return 0

func get_current_qemu_process_id() -> OS.ProcessID:
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
        print("PXQEMULauncher (Console Log): ", message)

