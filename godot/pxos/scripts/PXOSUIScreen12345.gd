# Assume PXCompiler.gd and PXVM.gd are in your project (e.g., in a 'scripts' folder)
# You might want to make them 'autoload' singletons later, but for direct integration:

# Add at the top of your PXOSUIScreen.gd script (or where your class variables are defined)
# var px_compiler_instance: PXCompiler = null # If instantiated in _ready or as a member variable
# var px_vm_instance: PXVM = null # If instantiated in _ready or as a member variable


func _ready():
    # ... your existing _ready code ...
    # Initialize compiler and VM if not already autoloaded
    # px_compiler_instance = PXCompiler.new() # You can instantiate here or directly in compile command
    # px_vm_instance = PXVM.new()             # You can instantiate here or directly in run command
    pass # Keep existing _ready functionality


func _handle_command(command_line: String) -> void:
    var command_parts = command_line.split(" ", false) # false to not skip empty parts if any
    if command_parts.empty():
        return

    var command = command_parts[0]
    var args = command_parts.slice(1) # Get all arguments after the command

    match command:
        "ls":
            _execute_ls_command(args)
        "cat":
            _execute_cat_command(args)
        "import":
            _execute_import_command(args)
        "decode":
            _execute_decode_command(args)
        "compile":
            _execute_compile_command(args)
        "run":
            _execute_run_command(args)
        "help":
            _print_to_shell("Available commands: ls, cat, import, decode, compile, run, help")
        "clear":
            _clear_shell()
        # Add other commands as they are developed
        _:
            _print_to_shell("Unknown command: " + command)


# --- Existing _execute_* command functions (ensure they are present or update them) ---

func _execute_ls_command(args: Array) -> void:
    # ... your existing ls logic ...
    var target_path = "/" if args.empty() else args[0]
    var entry = _pxfs_resolve_parent_and_key(target_path)

    if not entry.success:
        _print_to_shell("Error: " + entry.message)
        return

    var target_dir = entry.value
    if target_dir is not Dictionary:
        _print_to_shell("Error: " + target_path + " is not a directory.")
        return

    _print_to_shell("Contents of " + target_path + ":")
    for key in target_dir.keys():
        var item_type = "DIR" if target_dir[key] is Dictionary else "FILE"
        var metadata = target_dir[key].get("metadata", {}) if target_dir[key] is Dictionary else pxram_fs.get_node(target_path).get("metadata", {}) # Adjusted to get metadata
        var item_name = key
        # If the item is a dictionary (representing a file with content/metadata), display its key
        if target_dir[key] is Dictionary and "content" in target_dir[key]:
            item_name = key
        elif target_dir[key] is Dictionary: # It's a directory
            item_name = key + "/" # Append slash for directories
            item_type = "DIR"


        _print_to_shell(item_type + "\t" + item_name)


func _execute_cat_command(args: Array) -> void:
    # ... your existing cat logic ...
    if args.empty():
        _print_to_shell("Usage: cat <file_path>")
        return

    var file_path = args[0]
    var file_entry = _pxfs_resolve_parent_and_key(file_path)

    if not file_entry.success:
        _print_to_shell("Error: " + file_entry.message)
        return

    var file_content = file_entry.value

    # If the file entry is a dictionary (meaning it's a file with metadata), get its content
    if file_content is Dictionary and "content" in file_content:
        file_content = file_content["content"]

    if file_content is String:
        _print_to_shell("--- Content of " + file_path + " ---")
        _print_to_shell(file_content)
        _print_to_shell("--- End of Content ---")
    elif file_content is Image:
        _print_to_shell("File is an image. Use 'run " + file_path + "' to display.")
    elif file_content is Dictionary: # Likely a directory or a pxapp dict
        if file_content.has("instructions"): # It's a pxapp
            _print_to_shell("File is a compiled PXApp. Use 'run " + file_path + "' to execute.")
        else:
            _print_to_shell("Error: Cannot 'cat' a directory.")
    else:
        _print_to_shell("Error: Cannot display content of this type.")


func _execute_import_command(args: Array) -> void:
    # ... your existing import logic ...
    if args.size() < 2:
        _print_to_shell("Usage: import <host_path> <pxram_path>")
        return

    var host_path = args[0]
    var pxram_path = args[1]

    # Use a native file picker for desktop platforms
    if OS.has_feature("editor") or OS.has_feature("standalone"): # Check if running in editor or as standalone desktop app
        var dialog = FileDialog.new()
        dialog.access = FileDialog.ACCESS_FILESYSTEM
        dialog.mode = FileDialog.MODE_OPEN_FILE
        dialog.filters = ["All files (*)", "*.txt", "*.sh", "*.c", "*.png", "*.pxdigest.png"] # Add your filter preferences
        dialog.popup_centered()
        dialog.connect("file_selected", self, "_on_file_selected_for_import", [pxram_path])
        # We need to return here and wait for _on_file_selected_for_import to complete the import
        return
    else: # For web or other platforms where native file picker isn't available
        _print_to_shell("Manual import: " + host_path + " -> " + pxram_path)
        # Attempt to load directly from Godot's resource path
        _process_host_file_import(host_path, pxram_path)


func _on_file_selected_for_import(path: String, pxram_path: String) -> void:
    _process_host_file_import(path, pxram_path)


func _process_host_file_import(host_path: String, pxram_path: String) -> void:
    var file_name = host_path.get_file()
    var file_extension = file_name.get_extension()
    var file_content_raw = null
    var metadata = {}

    if file_extension == "png" or file_extension == "pxdigest.png":
        var img = Image.new()
        var error = img.load(host_path)
        if error != OK:
            _print_to_shell("Error: Could not load image from host path " + host_path)
            return
        file_content_raw = img # Store the Image object directly
        metadata["type"] = "image"
        _print_to_shell("Importing image: " + host_path)
    else: # Treat as text for now
        var file = File.new()
        var error = file.open(host_path, File.READ)
        if error != OK:
            _print_to_shell("Error: Could not open file from host path " + host_path + " - " + str(error))
            return
        file_content_raw = file.get_as_text()
        file.close()
        metadata["type"] = "text" # Default to text
        _print_to_shell("Importing text file: " + host_path)

    var result = _pxfs_add_file_to_pxram(pxram_path, file_content_raw, metadata)
    if result.success:
        _print_to_shell("File imported to PXRAM: " + pxram_path)
        _populate_pxram_tree() # Refresh PXRAM Viewer
    else:
        _print_to_shell("Error importing to PXRAM: " + result.message)


func _execute_decode_command(args: Array) -> void:
    if args.size() < 2:
        _print_to_shell("Usage: decode <pximage_path> <output_text_path>")
        return
    var pximage_path = args[0]
    var output_filepath = args[1]

    var decoded_text = _decode_pximage(pximage_path) # Call the decoder
    if decoded_text != "":
        var result = _pxfs_add_file_to_pxram(output_filepath, decoded_text, {"type": "text"})
        if result.success:
            _print_to_shell("Decoded image to " + output_filepath)
            _populate_pxram_tree() # Refresh viewer
        else:
            _print_to_shell("Error: " + result.message)
    else:
        _print_to_shell("Decoding failed for " + pximage_path)


func _execute_compile_command(args: Array) -> void:
    if args.size() < 3 or args[1] != "-o":
        _print_to_shell("Usage: compile <input_source_path> -o <output_pxapp_path>")
        return
    var input_path = args[0]
    var output_path = args[2]

    var source_file_entry = _pxfs_resolve_parent_and_key(input_path)
    if not source_file_entry.success or source_file_entry.value is not String:
        _print_to_shell("Error: Source file not found or not text at " + input_path)
        return

    var source_content = source_file_entry.value # Get the text content of the PXTalk file

    # Instantiate PXCompiler and compile
    var compiler = PXCompiler.new() # Create a new instance
    var compiled_pxapp_dict = compiler.compile(source_content)

    if compiled_pxapp_dict.has("error"):
        _print_to_shell("Compiler Error: " + compiled_pxapp_dict.error)
        return

    # Store the compiled PXApp (which is a Dictionary) into PXRAM
    var result = _pxfs_add_file_to_pxram(output_path, compiled_pxapp_dict, {"type": "pxapp"})
    if result.success:
        _print_to_shell(f"Compiled '{input_path}' to '{output_path}' (PXApp)")
        _populate_pxram_tree() # Refresh viewer
    else:
        _print_to_shell("Error: " + result.message)


func _execute_run_command(args: Array) -> void:
    if args.empty():
        _print_to_shell("Usage: run <target_path>")
        return

    var target_path = args[0]
    var file_entry = _pxfs_resolve_parent_and_key(target_path)

    if not file_entry.success:
        _print_to_shell("Error: " + file_entry.message)
        return

    var file_content = file_entry.value
    var file_metadata = file_entry.metadata if file_entry.metadata else {}

    var file_type = file_metadata.get("type", "")

    if file_type == "pxapp":
        if file_content is Dictionary and file_content.has("instructions"):
            _print_to_shell(f"Executing PXApp: {target_path}")
            var vm = PXVM.new() # Create a new VM instance for each run
            vm.shell_callback = funcref(self, "_handle_command") # Pass a direct reference to the shell command handler
            vm.file_system = pxram_fs # Pass the PXRAM file system reference
            # Connect the vm_output signal to _print_to_shell
            if not vm.is_connected("vm_output", self, "_print_to_shell"):
                 vm.connect("vm_output", self, "_print_to_shell")

            vm.execute(file_content)
        else:
            _print_to_shell("Error: PXApp content is malformed or not a compiled PXApp dictionary.")
    elif file_type == "image":
        _print_to_shell(f"Displaying image: {target_path}")
        # Logic to display image in a viewer (e.g., set texture of a TextureRect)
        # Assuming you have a way to display images, e.g., via a TextureRect node
        # Example: $ImageDisplayNode.texture = ImageTexture.new().create_from_image(file_content)
        _display_image_in_viewer(file_content) # Assuming you have this helper func
    elif file_content is String: # Default for text files (.txt, .sh, .geo, etc.)
        _print_to_shell(f"Running/Displaying text file: {target_path}")
        _print_to_shell(file_content)
    else:
        _print_to_shell("Error: Cannot run or display content of type " + typeof(file_content))


# Placeholder for image display. You'll need to implement this based on your UI.
func _display_image_in_viewer(img: Image) -> void:
    # Example: If you have a TextureRect node named 'ImageViewer'
    if has_node("ImageViewer"):
        var texture = ImageTexture.new()
        texture.create_from_image(img)
        get_node("ImageViewer").texture = texture
        get_node("ImageViewer").visible = true # Make sure it's visible
        _print_to_shell("Image displayed in viewer.")
    else:
        _print_to_shell("No 'ImageViewer' node found to display image.")

# --- Existing _decode_pximage function (ensure it's present and updated for Image object input) ---
func _decode_pximage(pxram_path_to_image: String) -> String:
    var file_entry = _pxfs_resolve_parent_and_key(pxram_path_to_image)
    if not file_entry.success or file_entry.value is not Dictionary:
        _print_to_shell("Error: Image file not found in PXRAM at " + pxram_path_to_image)
        return ""

    var image_data_container = file_entry.value # This should be the dictionary holding "content" and "metadata"

    if image_data_container.get("content") is not Image:
        _print_to_shell("Error: Content at " + pxram_path_to_image + " is not an Image object.")
        return ""

    var image_data = image_data_container.content # Get the actual Image object

    var decoded_content = ""
    image_data.lock() # Lock the image to access pixel data

    for y in image_data.get_height():
        for x in image_data.get_width():
            var pixel_color = image_data.get_pixel(x, y)
            var char_val = int(pixel_color.r * 255.0) # Red channel stores the ASCII value (0-255)

            if char_val == 0: # Our blank/padding pixel
                continue
            
            # Convert integer ASCII value back to character
            decoded_content += char(char_val)
    image_data.unlock()
    return decoded_content.strip() # .strip() removes leading/trailing whitespace

# --- Place PXFS helper functions here or ensure they are accessible ---
# func _pxfs_resolve_parent_and_key(path: String) -> Dictionary:
# func _pxfs_add_file_to_pxram(path: String, content, metadata: Dictionary = {}) -> Dictionary:
# ... etc.