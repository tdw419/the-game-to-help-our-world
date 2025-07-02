# PXVM.gd - UPDATED (add these cases to your existing 'match opcode' block)

# ... (existing opcodes) ...

			# --- NEW DRAWING PRIMITIVES ---
			"draw_line":
				var x1 = _resolve_arg_value(args[0])
				var y1 = _resolve_arg_value(args[1])
				var x2 = _resolve_arg_value(args[2])
				var y2 = _resolve_arg_value(args[3])
				var r = _resolve_arg_value(args[4])
				var g = _resolve_arg_value(args[5])
				var b = _resolve_arg_value(args[6])
				if display_manager:
					display_manager.draw_line(x1, y1, x2, y2, r, g, b)
			"draw_circle":
				var cx = _resolve_arg_value(args[0])
				var cy = _resolve_arg_value(args[1])
				var radius = _resolve_arg_value(args[2])
				var r = _resolve_arg_value(args[3])
				var g = _resolve_arg_value(args[4])
				var b = _resolve_arg_value(args[5])
				if display_manager:
					display_manager.draw_circle(cx, cy, radius, r, g, b)
			"draw_image":
				var image_path = _resolve_arg_value(args[0])
				var x = _resolve_arg_value(args[1])
				var y = _resolve_arg_value(args[2])
				if display_manager:
					var img_obj = _pxfs_get_file_content(image_path) # Get the Image object from PXRAM
					if img_obj is Image:
						display_manager.draw_image_from_file(img_obj, x, y)
					else:
						emit_signal("vm_output", "Error: draw_image: '" + image_path + "' is not a valid image in PXRAM.")

# ... (rest of PXVM.gd) ...