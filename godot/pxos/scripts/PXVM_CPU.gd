# PXVM_CPU.gd
# Simulates CPU boot logic for PXVM. Executes the kernel loaded in PXRAM.

extends Node

@export var pxram := {}                # Simulated RAM (shared dictionary)
@export var kernel_addr := 0x00100000  # Default PXRAM address for vmlinuz
@export var initrd_addr := 0x00800000  # PXRAM address for initrd (not yet "used")

@export var boot_mode := "simulate"    # Modes: simulate, debug, no-op

signal cpu_started()
signal cpu_halted()
signal boot_progress(message: String)

func _ready():
    # Optional: auto-start
    pass

func start_boot():
    emit_signal("cpu_started")
    
    match boot_mode:
        "simulate":
            _simulate_boot_process()
        "debug":
            _step_through_kernel()
        "no-op":
            emit_signal("boot_progress", "[PXCPU] No-op mode. Halting.")
            emit_signal("cpu_halted")
        _:
            emit_signal("boot_progress", "[PXCPU] Unknown mode. Halting.")
            emit_signal("cpu_halted")

func _simulate_boot_process():
    emit_signal("boot_progress", "[PXCPU] Booting TinyCore from PXRAM...")
    await _delay(0.5)
    
    var kernel = pxram.get(kernel_addr, null)
    if kernel == null:
        emit_signal("boot_progress", "[PXCPU] Kernel not found at 0x%08x" % kernel_addr)
        emit_signal("cpu_halted")
        return

    emit_signal("boot_progress", "[PXCPU] Kernel size: %d bytes" % kernel.size())
    await _delay(0.4)
    
    emit_signal("boot_progress", "[PXCPU] Decompressing vmlinuz...")
    await _delay(1.0)

    emit_signal("boot_progress", "[PXCPU] Loading initrd (core.gz)...")
    await _delay(0.6)

    emit_signal("boot_progress", "[PXCPU] Jumping to kernel entrypoint at 0x%08x..." % kernel_addr)
    await _delay(0.8)

    emit_signal("boot_progress", "[PXCPU] Welcome to TinyCore (simulated)!")
    emit_signal("cpu_halted")

func _step_through_kernel():
    emit_signal("boot_progress", "[PXCPU] Debug stepping (not implemented).")
    emit_signal("cpu_halted")

func _delay(seconds: float) -> GDScriptFunctionState:
    return await get_tree().create_timer(seconds).timeout
