import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional, Dict, Any
import threading
import time
import os
import queue # For inter-thread communication

# --- Global Constants and Settings ---
SETTINGS = {
    "canvas_width": 800,
    "canvas_height": 600,
    "char_size": 20,
    "font": ("Courier", 14),
    "cursor_start_x": 10,
    "cursor_start_y": 10,
    "max_undo_redo": 1000,  # Limit memory size for performance
    "blink_rate": 500,  # Cursor blink rate in ms
    "color_cache_size": 256,  # Cache for color calculations
    "cpu_speed_hz": 1000, # CPU cycles per second
    "disk_size_bytes": 1024 * 1024, # 1MB disk
    "disk_block_size": 512, # 512 bytes per block
}

# --- Import integrated modules ---
# Assuming all other files are in the same directory or accessible via PYTHONPATH
from terminal import TerminalCanvas
from command import CommandHistory, HistoryMode
from cpu import PixelCPU, OpCode
from cursor import CursorController, CanvasBounds, Position
from memory import PixelMemory, EncodingMode, PixelMemoryError
from disk import PixelDisk


class CanvasApp:
    """
    Main application class for the PixelCanvas Terminal.
    Integrates all components: TerminalCanvas, Cursor, CommandHistory, Memory, CPU, Disk.
    """
    def __init__(self, master: tk.Tk, settings: Dict[str, Any]) -> None:
        self.master = master
        self.settings = settings
        master.title("PixelCanvas Terminal")
        master.geometry(f"{settings['canvas_width']}x{settings['canvas_height'] + 50}") # +50 for status bar/input

        # 1. Initialize TerminalCanvas (the display)
        self.terminal_canvas = TerminalCanvas(
            master=master,
            canvas_width=settings["canvas_width"],
            canvas_height=settings["canvas_height"],
            char_size=settings["char_size"],
            font=settings["font"]
        )

        # 2. Initialize CursorController
        canvas_bounds = CanvasBounds(
            left=0, top=0,
            right=settings["canvas_width"],
            bottom=settings["canvas_height"],
            char_width=settings["char_size"],
            char_height=settings["char_size"]
        )
        self.cursor_controller = CursorController(
            start_position=Position(settings["cursor_start_x"], settings["cursor_start_y"]),
            char_width=settings["char_size"],
            char_height=settings["char_size"],
            canvas_bounds=canvas_bounds,
            initial_column=0, initial_line=0
        )
        # Link cursor to terminal_canvas for drawing
        self.terminal_canvas.set_cursor_controller(self.cursor_controller)

        # 3. Initialize CommandHistory
        self.command_history = CommandHistory(max_size=settings["max_undo_redo"])

        # 4. Initialize PixelMemory
        self.pixel_memory = PixelMemory(
            size=settings["disk_size_bytes"] * 2, # Example: Memory is twice the disk size
            encoding_mode=EncodingMode.PACKED_24BIT
        )
        # Create some initial memory regions (optional, for testing)
        try:
            self.pixel_memory.create_region(0, 1024, "BIOS_ROM", read_only=True)
            self.pixel_memory.create_region(1024, 4096, "MAIN_RAM")
        except PixelMemoryError as e:
            self.terminal_canvas.show_status(f"Memory setup error: {e}", "red")

        # 5. Initialize PixelDisk (uses PixelMemory internally)
        self.pixel_disk = PixelDisk(
            blocks=settings["disk_size_bytes"] // settings["disk_block_size"],
            block_size=settings["disk_block_size"],
            memory=self.pixel_memory # Pass the main memory instance to Disk
        )

        # 6. Initialize PixelCPU
        self.pixel_cpu = PixelCPU(memory=self.pixel_memory)

        # Input entry widget for commands
        self.input_entry = tk.Entry(master, bg="lightgray", fg="black", font=settings["font"])
        self.input_entry.pack(fill=tk.X, padx=5, pady=5)
        self.input_entry.bind("<Return>", self.process_input)
        self.input_entry.bind("<Up>", self.history_up)
        self.input_entry.bind("<Down>", self.history_down)

        # Status bar update (TerminalCanvas already has one, but this can be for app-level messages)
        # self.status_label = tk.Label(master, text="System Ready.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        # self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

        # CPU Threading setup
        self.cpu_thread: Optional[threading.Thread] = None
        self.cpu_run_event = threading.Event()
        self.cpu_pause_event = threading.Event()
        self.cpu_pause_event.set() # Start paused
        self.cpu_output_queue = queue.Queue() # For CPU to send output to main thread

        # Start CPU simulation in a separate thread
        self._start_cpu_thread()

        # Periodically check CPU output queue and update terminal
        self.master.after(100, self._check_cpu_output)

        # Initial display setup
        self.terminal_canvas.clear_all()
        self.terminal_canvas.show_status("Welcome to PixelCanvas OS!", "green")
        self.terminal_canvas.draw_char_at_cursor(">", "white") # Prompt
        self.terminal_canvas.update_cursor_position(visible=True)
        self.input_entry.focus_set()

    def _start_cpu_thread(self) -> None:
        """Starts the CPU simulation in a separate thread."""
        self.cpu_run_event.set() # Allow CPU to run
        self.cpu_thread = threading.Thread(target=self._cpu_loop, daemon=True)
        self.cpu_thread.start()
        self.terminal_canvas.show_status("CPU thread started.", "blue")

    def _cpu_loop(self) -> None:
        """The main loop for the CPU thread."""
        while self.cpu_run_event.is_set():
            self.cpu_pause_event.wait() # Wait if paused
            if not self.pixel_cpu.running:
                self.cpu_output_queue.put("CPU_HALTED")
                self.cpu_run_event.clear() # Stop the thread
                break

            try:
                self.pixel_cpu.step()
                # Simulate CPU speed
                time.sleep(1 / self.settings["cpu_speed_hz"])

                # Intercept CPU output (e.g., PRINT_R0) and put into queue
                # This requires modifications in cpu.py to direct output to queue
                # For now, we'll just check R0
                current_r0 = self.pixel_cpu.registers[self.pixel_cpu.R0]
                # In a real system, CPU would trigger an interrupt/event for output
                # Here, we can simulate by checking for specific opcodes or memory writes
                # For simplicity, let's assume CPU output is handled by a special
                # memory address or a CPU instruction that directly sends to the queue.
                # Since the current CPU prints, we'd need to redirect stdout or
                # modify CPU's PRINT_R0 to push to queue.
                # For this example, let's just show CPU is running
                # self.cpu_output_queue.put(f"CPU_STATUS: R0={current_r0}")

            except Exception as e:
                self.cpu_output_queue.put(f"CPU_ERROR: {e}")
                self.cpu_run_event.clear()
                self.pixel_cpu.running = False # Force halt CPU

    def _check_cpu_output(self) -> None:
        """Periodically checks the CPU output queue and updates the terminal."""
        try:
            while True:
                message = self.cpu_output_queue.get_nowait()
                if message == "CPU_HALTED":
                    self.terminal_canvas.show_status("CPU Halted.", "orange")
                elif message.startswith("CPU_ERROR"):
                    self.terminal_canvas.show_status(message, "red")
                else:
                    # Generic CPU output or status
                    # This would require a more sophisticated CPU instruction
                    # that writes to a 'display memory' region
                    pass # Not directly displaying general CPU status on canvas for now
        except queue.Empty:
            pass # No new messages
        finally:
            self.master.after(100, self._check_cpu_output)


    def process_input(self, event=None) -> None:
        """Processes user input from the entry widget."""
        command_text = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END) # Clear input field

        self.terminal_canvas.delete_prompt() # Delete the old prompt

        if not command_text:
            self.terminal_canvas.draw_char_at_cursor(">", "white") # Redraw prompt
            return

        self.terminal_canvas.write_line(command_text, self.cursor_controller.current_line) # Write command to terminal
        self.command_history.add_command(command_text) # Add to history
        self.terminal_canvas.update_cursor_position(visible=False) # Hide cursor during processing

        # --- Command Processing Logic ---
        output = self.execute_command(command_text)
        if output:
            for line in output.split('\n'):
                self.terminal_canvas.write_line(line) # Write output line by line

        # Always move cursor to a new line and draw prompt for next input
        self.terminal_canvas.new_line()
        self.terminal_canvas.draw_char_at_cursor(">", "white")
        self.terminal_canvas.update_cursor_position(visible=True)

    def execute_command(self, command: str) -> str:
        """Executes a parsed command and returns its output."""
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:]

        output = ""
        self.terminal_canvas.show_status(f"Executing: {command}", "blue")

        try:
            if cmd == "help":
                output = "Available commands:\n" \
                         "  help - Show this help message\n" \
                         "  clear - Clear the terminal\n" \
                         "  mem_stats - Show memory statistics\n" \
                         "  mem_read <address> <length> - Read from memory\n" \
                         "  mem_write <address> <data> - Write to memory\n" \
                         "  cpu_run <cycles> - Run CPU for N cycles\n" \
                         "  cpu_pause - Pause CPU\n" \
                         "  cpu_resume - Resume CPU\n" \
                         "  cpu_reset - Reset CPU\n" \
                         "  disk_save <filename> - Save disk to image\n" \
                         "  disk_load <filename> - Load disk from image\n" \
                         "  disk_format - Format disk\n" \
                         "  echo <text> - Echo text\n" \
                         "  exit - Exit the application"
            elif cmd == "clear":
                self.terminal_canvas.clear_all()
                self.cursor_controller.reset_position()
                self.terminal_canvas.draw_char_at_cursor(">", "white")
                return "" # No output needed, terminal is cleared
            elif cmd == "mem_stats":
                stats = self.pixel_memory.get_stats()
                output = "Memory Statistics:\n"
                for key, value in stats.items():
                    output += f"  {key.replace('_', ' ').title()}: {value}\n"
            elif cmd == "mem_read":
                if len(args) == 2:
                    address = int(args[0])
                    length = int(args[1])
                    read_data = self.pixel_memory.read(address, address + length)
                    output = f"Read {len(read_data)} bytes from {address}: {read_data.hex()}"
                else:
                    output = "Usage: mem_read <address> <length>"
            elif cmd == "mem_write":
                if len(args) == 2:
                    address = int(args[0])
                    data_hex = args[1]
                    try:
                        data_bytes = bytes.fromhex(data_hex)
                        self.pixel_memory.write(address, data_bytes)
                        output = f"Wrote {len(data_bytes)} bytes to {address}"
                    except ValueError:
                        output = "Invalid hex data."
                else:
                    output = "Usage: mem_write <address> <hex_data>"
            elif cmd == "cpu_run":
                cycles = int(args[0]) if args else 100
                self.cpu_pause_event.clear() # Allow CPU to run
                self.pixel_cpu.run(max_cycles=cycles)
                self.cpu_pause_event.set() # Pause after execution
                output = "CPU finished its run."
            elif cmd == "cpu_pause":
                self.cpu_pause_event.clear()
                output = "CPU paused."
            elif cmd == "cpu_resume":
                self.cpu_pause_event.set()
                output = "CPU resumed."
            elif cmd == "cpu_reset":
                self.pixel_cpu = PixelCPU(memory=self.pixel_memory) # Re-initialize CPU
                self.cpu_run_event.set() # Ensure thread can restart
                self._start_cpu_thread() # Restart thread
                output = "CPU reset and restarted."
            elif cmd == "disk_save":
                filename = args[0] if args else "pixel_disk_dump.png"
                self.pixel_disk.save_to_image(filename)
                output = f"Disk saved to {filename}"
            elif cmd == "disk_load":
                filename = args[0] if args else "pixel_disk_dump.png"
                self.pixel_disk.load_from_image(filename)
                output = f"Disk loaded from {filename}"
            elif cmd == "disk_format":
                self.pixel_disk.format_disk()
                output = "Disk formatted."
            elif cmd == "echo":
                output = " ".join(args)
            elif cmd == "exit":
                self.master.quit()
                output = "Exiting application."
            else:
                output = f"Unknown command: {command}"

        except (ValueError, IndexError) as e:
            output = f"Command error: {e}. Check arguments."
        except PixelMemoryError as e:
            output = f"Memory error: {e}"
        except FileNotFoundError as e:
            output = f"File error: {e}"
        except Exception as e:
            output = f"An unexpected error occurred: {e}"

        self.terminal_canvas.show_status("Command execution complete.", "green")
        return output

    def history_up(self, event=None) -> None:
        """Navigate command history upwards."""
        command = self.command_history.get_previous()
        if command is not None:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, command)
            self.terminal_canvas.show_status("History Up", "blue")
        else:
            self.terminal_canvas.show_status("No more history (Up)", "red")

    def history_down(self, event=None) -> None:
        """Navigate command history downwards."""
        command = self.command_history.get_next()
        if command is not None:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, command)
            self.terminal_canvas.show_status("History Down", "blue")
        else:
            self.terminal_canvas.show_status("No more history (Down)", "red")
            self.input_entry.delete(0, tk.END) # Clear input if no more history
            self.command_history._reset_navigation() # Reset so next Up starts fresh


if __name__ == "__main__":
    root = tk.Tk()
    app = CanvasApp(root, SETTINGS)
    root.mainloop()