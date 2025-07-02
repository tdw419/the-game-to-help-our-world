# PXOSUIScreen.gd (patch: PXCompiler & PXVM integration)

func _execute_compile_command(args: Array) -> void:
    if args.size() < 3 or args[1] != "-o":
        _print_to_shell("Usage: compile <input_source_path> -o <output_pxapp_path>")
        return
    var input_path = args[0]
    var output_path = args[2]

    var source_entry = _pxfs_resolve_parent_and_key(input_path)
    if not source_entry.success or source_entry.value is not String:
        _print_to_shell("Error: Source not found or invalid at " + input_path)
        return

    var compiler = PXCompiler.new()
    var pxapp = compiler.compile(source_entry.value)

    if pxapp.has("error"):
        _print_to_shell("Compiler Error: " + pxapp.error)
        return

    var result = _pxfs_add_file_to_pxram(output_path, pxapp, {"type": "pxapp"})
    if result.success:
        _print_to_shell("Compiled " + input_path + " to " + output_path)
    else:
        _print_to_shell("Error compiling: " + result.message)


func _execute_run_command(args: Array) -> void:
    if args.empty():
        _print_to_shell("Usage: run <file_path>")
        return

    var file_path = args[0]
    var entry = _pxfs_resolve_parent_and_key(file_path)

    if not entry.success:
        _print_to_shell("Error: " + entry.message)
        return

    var file_data = entry.value
    var metadata = entry.metadata
    var ftype = metadata.get("type", "")

    if ftype == "pxapp":
        if file_data is Dictionary and file_data.has("instructions"):
            var vm = PXVM.new()
            vm.shell_callback = funcref(self, "_handle_command")
            vm.file_system = pxram_fs
            if not vm.is_connected("vm_output", self, "_print_to_shell"):
                vm.connect("vm_output", self, "_print_to_shell")
            vm.execute(file_data)
        else:
            _print_to_shell("Error: Malformed PXApp at " + file_path)
    elif file_data is String:
        _print_to_shell(file_data)
    else:
        _print_to_shell("Unsupported run target: " + file_path)