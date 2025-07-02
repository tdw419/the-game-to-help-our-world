# In PXRuntime.gd

# Add new dependency for PXTalkVM (conceptual)
@onready var px_talk_vm: PXTalkVM = get_node_or_null("../PXTalkVM") # You'll need to create this node/script

# Modify _on_file_dropped_into_dropzone to handle .pxboot
func _on_file_dropped_into_dropzone(file_path: String, file_type: String):
    _log_runtime_activity("Received file via DropZone: %s (Type: %s)" % [file_path, file_type])
    
    _loaded_file_path = file_path
    _loaded_file_type = file_type
    
    emit_signal("file_loaded_into_runtime", file_path, file_type)
    
    match file_type.to_lower():
        "iso":
            _log_runtime_activity("ISO file type detected. Routing to dedicated ISO handler.")
            _on_iso_file_dropped(file_path)
        "pxdigest":
            _log_runtime_activity("PXDigest file detected. Routing to PXDigestLoader.")
            if px_digest_loader:
                px_digest_loader.load_digest(file_path)
            else:
                _log_runtime_activity("Error: PXDigestLoader not available.")
        "pxboot": # <--- NEW: Handle .pxboot files for native boot
            _log_runtime_activity("PXBoot file detected. Initiating native PXTalk BIOS boot.")
            if px_talk_vm:
                _current_session_id = generate_session_id()
                _log_runtime_activity("Starting new PXTalk boot session: " + _current_session_id + " for " + file_path)
                emit_signal("runtime_session_started", _current_session_id, file_path)
                px_talk_vm.boot_pxboot_file(file_path) # Call the PXTalk VM to boot
            else:
                _log_runtime_activity("Error: PXTalkVM not available for native boot.")
        "img", "elf":
            _log_runtime_activity("File type '%s' loaded. Direct launch not yet implemented for this type." % file_type)
        _:
            _log_runtime_activity("Unknown file type '%s' loaded. No automatic launch configured." % file_type)

# You will need a conceptual PXTalkVM.gd script that has a method like:
# func boot_pxboot_file(boot_file_path: String):
#     # This method would:
#     # 1. Read boot_file_path (boot.pxboot)
#     # 2. Parse its zTXT header to get JMP_ADDRESS and VM_ENTRY_POINT
#     # 3. Load pxbios_interpreter.pxtalk (using px_fs_reader)
#     # 4. Execute the 'INIT' function of pxbios_interpreter.pxtalk within the VM.
#     # 5. Handle PX_LOG and PX_PRINT_STR commands by forwarding to PXLogTerminal/PXFramebuffer.

# Add a placeholder for PXTalkVM.gd (conceptual, detailed implementation is complex)
# Create a new file named PXTalkVM.gd:
# extends Node
# @onready var px_fs_reader: PXFsReader = get_node_or_null("../PXFsReader")
# @onready var px_log_terminal: PXLogTerminal = get_node_or_null("../PXLogTerminal") # Assuming you use PXLogTerminal
# @onready var px_framebuffer: PXFramebuffer = get_node_or_null("../PXFramebuffer") # If you want visual output
# var _simulated_memory: Dictionary = {} # Simple key-value memory for PXTalk state

# func boot_pxboot_file(boot_file_path: String):
#     _log("PXTalkVM: Starting boot from " + boot_file_path)
#     var boot_content = px_fs_reader.read_file_by_name(boot_file_path)
#     # Parse boot_content to get entry point and interpreter path
#     # For this conceptual VM, we'll hardcode the interpreter for now
#     _log("PXTalkVM: Loading pxbios_interpreter.pxtalk...")
#     var interpreter_content = px_fs_reader.read_file_by_name("pxdisk/pxbios_interpreter.pxtalk")
#     # Simulate execution of interpreter's INIT function
#     _execute_pxtalk_function(interpreter_content, "INIT")
#     _log("PXTalkVM: Boot sequence complete.")

# func _execute_pxtalk_function(pxtalk_content: String, function_name: String):
#     # This is a very simplified PXTalk interpreter.
#     # A real one would parse complex instructions, manage stack, registers, etc.
#     # For now, it just simulates the log/print commands.
#     var lines = pxtalk_content.split("\n")
#     var in_function = false
#     for line in lines:
#         var trimmed_line = line.strip_edges()
#         if trimmed_line.begins_with("PX_FUNCTION " + function_name + ":"):
#             in_function = true
#             continue
#         if in_function and trimmed_line.begins_with("PX_FUNCTION"): # End of current function
#             in_function = false
#             break
#         if in_function:
#             if trimmed_line.begins_with("PX_LOG "):
#                 var log_msg = trimmed_line.replace("PX_LOG ", "")
#                 _log(log_msg)
#             elif trimmed_line.begins_with("PX_PRINT_STR "):
#                 var print_msg = trimmed_line.replace("PX_PRINT_STR ", "").replace("\"", "")
#                 if px_log_terminal:
#                     px_log_terminal.add_line(print_msg, "PXTERM", Color.LIME_GREEN, true)
#                 else:
#                     _log("PXTERM: " + print_msg)
#             elif trimmed_line.begins_with("PX_CALL_FUNCTION MOUNT_FS"): # Simulate internal calls
#                 _log("PXTalkVM: Simulating MOUNT_FS...")
#                 _simulated_memory["PXLDISK_STATUS"] = "MOUNTED"
#             elif trimmed_line.begins_with("PX_CALL_MODULE "): # Simulate module calls
#                 if trimmed_line.find("PX_KERNEL_MODULE") != -1:
#                     _log("PXTalkVM: Simulating call to PX_KERNEL_MODULE BOOT...")
#                     var kernel_content = px_fs_reader.read_file_by_name("pxdisk/pxkernel.pxtalk")
#                     _execute_pxtalk_function(kernel_content, "BOOT")
#                 elif trimmed_line.find("PX_SHELL_MODULE") != -1:
#                     _log("PXTalkVM: Simulating call to PX_SHELL_MODULE MAIN...")
#                     var shell_content = px_fs_reader.read_file_by_name("pxdisk/pxshell.pxtalk")
#                     _execute_pxtalk_function(shell_content, "MAIN")
#             elif trimmed_line.begins_with("PX_HALT "):
#                 var halt_reason = trimmed_line.replace("PX_HALT ", "")
#                 _log("PXTalkVM: HALT command received: " + halt_reason)
#                 # You might emit a signal here to PXRuntime to stop the session
#                 break # Exit function
#             elif trimmed_line.begins_with("PX_READ_INPUT"):
#                 # For shell, you'd need a way to get user input from UI
#                 _log("PXTalkVM: Simulating READ_INPUT (requires UI integration).")
#                 if px_log_terminal:
#                     px_log_terminal.add_line("Input required (not yet implemented).", "PXTERM", Color.YELLOW)
#                 # For now, just set a dummy input or break loop
#                 _simulated_memory["USER_INPUT"] = "help" # Dummy input for non-interactive
#                 
#             # Add more PXTalk instruction simulations here
#     _log("PXTalkVM: Function '%s' execution simulated." % function_name)

# func _log(msg: String):
#     if px_scroll_log:
#         px_scroll_log.add_line("PXTalkVM: " + msg)
#     else:
#         print("PXTalkVM (Log): ", msg)