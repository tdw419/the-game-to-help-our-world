import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab
from typing import List, Tuple, Optional, Dict, Any
import threading
import time
import os
import queue

# --- Import SETTINGS from the new settings.py file ---
from settings import SETTINGS

# --- Import integrated modules ---
from terminal import TerminalCanvas
from command import CommandHistory, HistoryMode
from cpu import PixelCPU, OpCode
from cursor import CursorController, CanvasBounds, Position
from memory import PixelMemory, EncodingMode, PixelMemoryError
from disk import PixelDisk


class CanvasApp:
    def __init__(self, master: tk.Tk, settings: Dict[str, Any]) -> None:
        self.master = master
        self.settings = settings
        self.master.title("PixelOS Terminal")
        self.master.geometry(f"{self.settings['window_width']}x{self.settings['window_height']}")
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Threading events for CPU control
        self.cpu_run_event = threading.Event()  # Set to allow CPU to run, Clear to stop
        self.cpu_pause_event = threading.Event() # Set to pause CPU, Clear to unpause
        self.cpu_pause_event.set() # Start paused by default
        self.cpu_output_queue = queue.Queue() # For CPU to send output to GUI thread
        self.cpu_thread: Optional[threading.Thread] = None

        # Initialize components
        self._init_terminal_canvas()
        self._init_cursor_controller()
        self._init_command_history()
        self._init_pixel_memory()
        self._init_pixel_disk()
        self._init_pixel_cpu()
        self._init_input_entry()

        # Start CPU simulation in a separate thread
        self._start_cpu_thread()

        # Periodically check CPU output queue and update terminal
        self.master.after(100, self._check_cpu_output)

    def _init_terminal_canvas(self) -> None:
        """Initialize TerminalCanvas."""
        self.terminal_canvas = TerminalCanvas(
            master=self.master,
            canvas_width=self.settings["canvas_width"],
            canvas_height=self.settings["canvas_height"],
            char_size=self.settings["char_size"],
            font=self.settings["font"]
        )

    def _init_cursor_controller(self) -> None:
        """Initialize CursorController."""
        canvas_bounds = CanvasBounds(
            left=0, top=0,
            right=self.settings["canvas_width"],
            bottom=self.settings["canvas_height"]
        )
        self.cursor_controller = CursorController(
            start_position=Position(self.settings["cursor_start_x"], self.settings["cursor_start_y"]),
            char_width=self.settings["char_size"],
            char_height=self.settings["char_size"],
            canvas_bounds=canvas_bounds,
            initial_column=0, initial_line=0
        )
        self.terminal_canvas.set_cursor_controller(self.cursor_controller)

    def _init_command_history(self) -> None:
        """Initialize CommandHistory."""
        self.command_history = CommandHistory(capacity=self.settings["history_capacity"])

    def _init_pixel_memory(self) -> None:
        """Initialize PixelMemory."""
        self.pixel_memory = PixelMemory(
            width=self.settings["canvas_width"],
            height=self.settings["canvas_height"],
            encoding_mode=EncodingMode.RGB_888 # Or as specified in settings
        )
        # Link memory to terminal canvas for direct drawing
        self.terminal_canvas.set_pixel_memory(self.pixel_memory)

    def _init_pixel_disk(self) -> None:
        """Initialize PixelDisk."""
        self.pixel_disk = PixelDisk(
            total_size_pixels=self.settings["disk_total_size_pixels"],
            block_size_pixels=self.settings["disk_block_size_pixels"],
            memory_interface=self.pixel_memory # Disk uses PixelMemory as its interface
        )

    def _init_pixel_cpu(self) -> None:
        """Initialize PixelCPU."""
        self.pixel_cpu = PixelCPU(
            memory=self.pixel_memory,
            output_queue=self.cpu_output_queue # CPU writes output to this queue
        )

    def _init_input_entry(self) -> None:
        """Initialize the input entry widget and bind events."""
        self.input_frame = tk.Frame(self.master, bg="black")
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_label = tk.Label(self.input_frame, text="Input:", fg="white", bg="black")
        self.input_label.pack(side=tk.LEFT, padx=(5, 0))

        self.input_entry = tk.Entry(self.input_frame, bg="black", fg="white",
                                    insertbackground="white", bd=0, relief=tk.FLAT)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=5)
        self.input_entry.bind("<Return>", self.process_input)
        self.input_entry.bind("<Up>", self.history_up)
        self.input_entry.bind("<Down>", self.history_down)
        self.input_entry.focus_set() # Set focus to input field

        # Initial prompt drawing
        self.terminal_canvas.draw_char_at_cursor(">", "white")
        self.terminal_canvas.update_cursor_position(visible=True)

    def _on_closing(self) -> None:
        """Handles the window closing event, stopping CPU thread and destroying the window."""
        print("Closing application...")
        # Signal the CPU thread to stop
        self.cpu_run_event.clear()
        self.cpu_pause_event.set() # Ensure the CPU thread is unpaused so it can check run_event

        if self.cpu_thread and self.cpu_thread.is_alive():
            self.cpu_thread.join(timeout=1.0) # Wait for the thread to finish, with a timeout
            if self.cpu_thread.is_alive():
                print("Warning: CPU thread did not terminate gracefully.")
        
        self.master.destroy() # Destroy the Tkinter window

    def _start_cpu_thread(self) -> None:
        """Starts the CPU simulation in a separate thread."""
        if self.cpu_thread is None or not self.cpu_thread.is_alive():
            self.cpu_run_event.set()  # Allow CPU to run
            self.cpu_thread = threading.Thread(target=self._cpu_loop, daemon=True)
            self.cpu_thread.start()
            self.terminal_canvas.show_status("CPU thread started.", "blue")
        else:
            self.terminal_canvas.show_status("CPU thread is already running.", "orange")

    def _cpu_loop(self) -> None:
        """The main loop for the CPU simulation thread."""
        while self.cpu_run_event.is_set():
            self.cpu_pause_event.wait()  # Wait if paused

            if not self.pixel_cpu.running:
                self.cpu_output_queue.put("CPU_HALTED")
                self.cpu_run_event.clear() # Stop the thread
                break

            try:
                self.pixel_cpu.step()
                time.sleep(1 / self.settings["cpu_speed_hz"])

            except Exception as e:
                self.cpu_output_queue.put(f"CPU_ERROR: {e}")
                self.cpu_run_event.clear()
                self.pixel_cpu.running = False

    def _check_cpu_output(self) -> None:
        """
        Periodically checks the CPU output queue and updates the terminal.
        This runs in the main Tkinter thread.
        """
        try:
            while not self.cpu_output_queue.empty():
                message = self.cpu_output_queue.get_nowait()
                if message == "CPU_HALTED":
                    self.terminal_canvas.show_status("CPU Halted.", "orange")
                elif message.startswith("CPU_ERROR"):
                    self.terminal_canvas.show_status(message, "red")
                else:
                    # Write CPU output directly to terminal, managing cursor
                    self.terminal_canvas.write_line(str(message))
                    self.terminal_canvas.new_line() # Ensure new line after CPU output
                    self.terminal_canvas.draw_char_at_cursor(">", "white") # Redraw prompt
                    self.terminal_canvas.update_cursor_position(visible=True)
                self.cpu_output_queue.task_done()
        except queue.Empty:
            pass
        except Exception as e:
            self.terminal_canvas.show_status(f"Error checking CPU output: {e}", "red")
        finally:
            self.master.after(100, self._check_cpu_output)

    def process_input(self, event=None) -> None:
        """Processes user input from the entry widget."""
        command_text = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END) # Clear input field

        self.terminal_canvas.delete_prompt() # Delete the old prompt

        # If command is empty, just redraw prompt and return
        if not command_text:
            self.terminal_canvas.draw_char_at_cursor(">", "white") # Redraw prompt
            return

        # Write the command itself to the terminal
        self.terminal_canvas.write_line(command_text, self.cursor_controller.current_line)
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
                         "  load_program <filename> - Load raw byte program into memory\n" \
                         "  hexdump <address> [length] - Display memory hexdump\n" \
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
                    # PixelMemory.read now returns bytes
                    read_data_bytes = self.pixel_memory.read(address, address + length)
                    output = f"Read {len(read_data_bytes)} bytes from {address}: {read_data_bytes.hex()}"
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
                cycles = int(args[0]) if args else -1  # -1 means run indefinitely until halted
                self.pixel_cpu.set_cycles_to_run(cycles)
                self.pixel_cpu.running = True # Set CPU to running state
                self.cpu_pause_event.clear() # Allow CPU thread to proceed
                # The _cpu_loop will handle the actual running based on pixel_cpu.running state
                output = f"CPU set to run for max {cycles} cycles. Check status for completion."
            elif cmd == "cpu_pause":
                self.cpu_pause_event.set() # Pause the CPU thread
                output = "CPU paused."
            elif cmd == "cpu_resume":
                self.cpu_pause_event.clear() # Resume the CPU thread
                self.pixel_cpu.running = True # Ensure CPU is marked as running
                output = "CPU resumed."
            elif cmd == "cpu_reset":
                self.cpu_pause_event.set() # Ensure CPU thread is paused
                self.cpu_run_event.clear() # Signal CPU thread to stop
                if self.cpu_thread and self.cpu_thread.is_alive():
                    self.cpu_thread.join(timeout=1.0) # Wait for thread to finish
                
                # Re-initialize CPU and restart its thread
                self.pixel_cpu = PixelCPU(memory=self.pixel_memory, output_queue=self.cpu_output_queue)
                self._start_cpu_thread()  # Restart the CPU thread
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
                self._on_closing() # Call the closing handler
                output = "Exiting application."
            elif cmd == "load_program":
                self._load_program_to_memory(args[0] if args else "")
                output = "" # Output handled by _load_program_to_memory
            elif cmd == "hexdump":
                self._hexdump_memory(args)
                output = "" # Output handled by _hexdump_memory
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

    def _load_program_to_memory(self, filename: str) -> None:
        """Loads a program (raw bytes) from a file into pixel memory."""
        if not filename:
            self.terminal_canvas.show_status("Usage: load_program <filename>", "red")
            return
        try:
            with open(filename, 'rb') as f: # Read as binary
                program_bytes = f.read()
            
            # Clear memory before loading new program
            self.pixel_memory.clear()

            # Write bytes to memory. Assuming the file contains raw bytes
            # that represent the sequence of R,G,B values for opcodes/data.
            # Each 3 bytes in the file corresponds to one pixel/opcode.
            current_address = 0
            for i in range(0, len(program_bytes), 3):
                if i + 2 < len(program_bytes): # Ensure we have full RGB
                    r = program_bytes[i]
                    g = program_bytes[i+1]
                    b = program_bytes[i+2]
                    self.pixel_memory.write(current_address, bytes([r, g, b]))
                    current_address += 3 # Advance by 3 bytes for the next pixel/opcode
                else:
                    self.terminal_canvas.show_status(f"Warning: Program file '{filename}' has incomplete opcode at end. Truncating.", "orange")
                    break # Stop if incomplete opcode

            self.terminal_canvas.show_status(f"Program '{filename}' loaded into memory. Size: {len(program_bytes)} bytes.", "green")
            # Reset CPU to start of loaded program
            self.pixel_cpu.reset(start_address=0)
            self.pixel_cpu.running = False # Do not auto-run after loading, user will run with cpu_run
        except FileNotFoundError:
            self.terminal_canvas.show_status(f"Error: Program file '{filename}' not found.", "red")
        except Exception as e:
            self.terminal_canvas.show_status(f"Error loading program: {e}", "red")

    def _hexdump_memory(self, args: List[str]) -> None:
        """Displays a hexadecimal dump of memory."""
        try:
            if not args:
                self.terminal_canvas.show_status("Usage: hexdump <address> [length]", "red")
                return

            address = int(args[0])
            length = int(args[1]) if len(args) > 1 else 16 # Default length

            # Read data from memory using the updated API
            data_bytes = self.pixel_memory.read(address, address + length)
            
            if data_bytes:
                self.terminal_canvas.write_line(f"Hexdump of memory from address {address} (length {len(data_bytes)}):")
                # Format into lines of 16 bytes for readability
                for i in range(0, len(data_bytes), 16):
                    chunk = data_bytes[i:i+16]
                    hex_line = ' '.join(f'{b:02x}' for b in chunk)
                    ascii_line = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
                    self.terminal_canvas.write_line(f"{address + i:08x}: {hex_line.ljust(48)} | {ascii_line}")
                self.terminal_canvas.show_status(f"Hexdump displayed for {len(data_bytes)} bytes.", "blue")
            else:
                self.terminal_canvas.show_status("No data to display or invalid address/length.", "red")
        except ValueError:
            self.terminal_canvas.show_status("Usage: hexdump <address> [length]", "red")
        except PixelMemoryError as e:
            self.terminal_canvas.show_status(f"Memory error: {e}", "red")
        except Exception as e:
            self.terminal_canvas.show_status(f"Error hexdumping memory: {e}", "red")

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