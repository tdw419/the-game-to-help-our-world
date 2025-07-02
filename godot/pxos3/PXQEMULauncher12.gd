# PXQEMULauncher.gd
extends Node

var qemu_path := "qemu-system-x86_64"  # Can override via config
var ram_size := "2048"
var cpu_cores := "2"

func launch_iso(iso_path: String):
    if not FileAccess.file_exists(iso_path):
        push_error("[PXQEMULauncher] ISO file not found: " + iso_path)
        return

    # Resolve platform-specific QEMU path override
    if OS.has_feature("windows"):
        qemu_path = "qemu-system-x86_64.exe"

    var args = [
        "-cdrom", iso_path,
        "-boot", "d",
        "-m", ram_size,
        "-smp", cpu_cores,
        "-enable-kvm",  # Optional: remove on Windows if unsupported
        "-display", "sdl"  # Switch to "gtk" or "curses" if needed
    ]

    var pid = OS.execute(qemu_path, args, false)
    if pid == OK:
        print("[PXQEMULauncher] QEMU launched with ISO: " + iso_path)
        get_node_or_null("/root/PXScrollLog")?.add_entry("QEMU launched: " + iso_path)
    else:
        push_error("[PXQEMULauncher] Failed to execute QEMU.")
