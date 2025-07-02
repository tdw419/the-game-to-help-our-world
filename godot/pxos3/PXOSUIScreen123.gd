# PXOSUIScreen.gd
# This script serves as the basic handoff display from PXVM.gd
# when PX_EXEC_KERNEL is executed. It displays information passed via PXRAM.

extends Control

@onready var log_label: RichTextLabel = $LogLabel

var pxram: Dictionary = {} # To store PXRAM data passed from PXVM

func _ready():
    log_label.text = "" # Clear any initial text

func set_pxram_data(data: Dictionary):
    """
    Receives the PXRAM data from PXVM.gd after kernel handoff.
    """
    pxram = data
    _update_display()

func _update_display():
    """
    Updates the RichTextLabel with information from PXRAM.
    """
    log_label.append_text("[PXOS] Booting into simulated OS...\n")
    log_label.append_text(f"[PXOS] Kernel size: {pxram.get('kernel_size', 'N/A')} bytes\n")
    log_label.append_text(f"[PXOS] Initrd size: {pxram.get('initrd_size', 'N/A')} bytes\n")
    log_label.append_text("\n[PXOS] Simulated kernel execution complete.\n")
    log_label.append_text("Type 'exit' to quit.") # Placeholder for future interactive shell
