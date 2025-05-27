from enum import Enum
from typing import Tuple, List, Optional
import queue # For inter-thread communication
# Import the main PixelMemory from memory.py
from memory import PixelMemory, PixelMemoryError, EncodingMode


# --- Define Opcodes using an Enum for clarity ---
class OpCode(Enum):
    HALT = (255, 0, 0)      # Red pixel
    INC_R0 = (0, 255, 0)    # Green pixel
    PRINT_R0 = (0, 0, 255)  # Blue pixel
    # --- New Instructions ---
    DEC_R0 = (255, 255, 0)  # Yellow pixel = Decrement R0
    LOAD_R0 = (0, 255, 255) # Cyan pixel = Load immediate value into R0 (next memory address)


# --- PixelCPU Class ---
class PixelCPU:
    """
    A simple CPU that operates on a PixelMemory.
    It fetches opcodes (pixels), decodes them, and executes corresponding operations.
    """
    
    def __init__(self, memory: PixelMemory, start_address: int = 0, output_queue: Optional[queue.Queue] = None) -> None:
        """
        Initializes the CPU with a reference to PixelMemory and a starting address.
        """
        if not isinstance(memory, PixelMemory):
            raise TypeError("Memory must be an instance of PixelMemory.")

        self.memory = memory
        self.pc = start_address  # Program Counter
        self.registers = [0] * 16  # Example: 16 general-purpose registers, R0-R15
        self.running = False # CPU power state, controlled externally (e.g., by CanvasApp)
        self.output_queue = output_queue if output_queue is not None else queue.Queue()

        self._log(f"CPU initialized. PC: {self.pc}, Registers: {self.registers}")

    def _log(self, message: str) -> None:
        """Simple logging for CPU events, sends to output queue."""
        self.output_queue.put(f"[CPU] {message}")

    def get_output_queue(self) -> queue.Queue:
        """Returns the queue used for CPU output."""
        return self.output_queue

    def reset(self, start_address: int = 0) -> None:
        """Resets the CPU state (PC, registers) and sets starting address."""
        self.pc = start_address
        self.registers = [0] * 16
        self.running = False # Reset to not running, external control will start it
        self._log(f"CPU reset. PC: {self.pc}, Registers cleared.")

    def fetch(self) -> Tuple[int, int, int]:
        """
        Fetches the next opcode (pixel) from memory.
        Assumes opcodes are stored as individual RGB pixels (3 bytes).
        """
        try:
            # Read 3 bytes from memory, which represent one opcode pixel
            opcode_bytes = self.memory.read(self.pc, self.pc + 3)
            
            if len(opcode_bytes) < 3:
                raise IndexError(f"Incomplete opcode at PC {self.pc}: expected 3 bytes, got {len(opcode_bytes)}")
            
            opcode_pixel = (opcode_bytes[0], opcode_bytes[1], opcode_bytes[2])
            self._log(f"Fetched: {opcode_pixel} from PC={self.pc}")
            return opcode_pixel
        except (IndexError, PixelMemoryError) as e:
            self._log(f"CPU Error: Failed to fetch instruction at PC {self.pc}: {e}. Halting CPU.")
            self.running = False
            return OpCode.HALT.value # Return HALT instruction if error occurs

    def decode_execute(self, opcode_pixel: Tuple[int, int, int]) -> None:
        """Decodes the opcode and executes the corresponding instruction."""
        if not self.running:
            return

        # Find the OpCode enum member that matches the pixel value
        opcode_found: Optional[OpCode] = None
        for op in OpCode:
            if op.value == opcode_pixel:
                opcode_found = op
                break

        if opcode_found is None:
            self._log(f"Unknown opcode: {opcode_pixel}. Halting CPU.")
            self.running = False
            return

        self._log(f"Executing: {opcode_found.name}")

        # R0 is registers[0]
        R0_index = 0

        if opcode_found == OpCode.HALT:
            self.running = False
        elif opcode_found == OpCode.INC_R0:
            self.registers[R0_index] = (self.registers[R0_index] + 1) % 256 # Wrap around at 255
            self._log(f"R0 incremented to {self.registers[R0_index]}")
        elif opcode_found == OpCode.DEC_R0:
            self.registers[R0_index] = (self.registers[R0_index] - 1) % 256 # Wrap around
            self._log(f"R0 decremented to {self.registers[R0_index]}")
        elif opcode_found == OpCode.PRINT_R0:
            self.output_queue.put(f"CPU Output: R0 = {self.registers[R0_index]}")
            self._log(f"PRINT_R0: R0 = {self.registers[R0_index]}")
        elif opcode_found == OpCode.LOAD_R0:
            # LOAD_R0 instruction: takes the value from the next memory address
            # and loads it into R0. PC must be advanced past this immediate value.
            try:
                # Read 3 bytes for the immediate value (assuming it's also a pixel)
                immediate_value_bytes = self.memory.read(self.pc + 3, self.pc + 3 + 3) 
                
                if len(immediate_value_bytes) < 3:
                    raise IndexError(f"Incomplete immediate value for LOAD_R0 at {self.pc + 3}")

                # For simplicity, let's just use the first byte of the pixel as the value
                value = immediate_value_bytes[0] 
                self.registers[R0_index] = value
                self.pc += 3 # Advance PC past the immediate value (which is 3 bytes)
                self._log(f"LOAD_R0: Loaded {self.registers[R0_index]} into R{R0_index} from address {self.pc}")
            except (IndexError, PixelMemoryError) as e:
                self._log(f"LOAD_R0: Failed to read immediate value at {self.pc + 3}: {e}. Halting CPU.")
                self.running = False
        else:
            self._log(f"Unimplemented instruction: {opcode_found.name}. Halting CPU.")
            self.running = False

        self._log(f"PC after instruction: {self.pc}")

    def step(self) -> None:
        """Execute the next opcode."""
        if not self.running:
            return

        opcode = self.fetch()
        if not self.running: # Check if fetch caused a halt
            return

        original_pc = self.pc
        self.decode_execute(opcode)

        # Advance PC by 3 (size of one opcode pixel) if the instruction didn't change PC itself
        if self.pc == original_pc: 
            self.pc += 3 

    def run(self, max_cycles: int = 100) -> None:
        """
        Runs the CPU for a maximum number of cycles.
        This method is primarily for direct testing/debugging of CPU.
        In CanvasApp, the CPU runs in a separate thread controlled by _cpu_loop.
        """
        self._log(f"--- Starting CPU run (max {max_cycles} cycles) ---")
        cycle = 0
        self.running = True # Set running state for this local run
        try:
            while self.running and cycle < max_cycles:
                self._log(f"Cycle {cycle}: PC={self.pc}")
                self.step()
                cycle += 1
            if cycle >= max_cycles and self.running:
                self._log(f"--- CPU halted: Maximum cycles ({max_cycles}) reached. ---")
            else:
                self._log(f"--- CPU halted successfully after {cycle} cycles. ---")
        except Exception as e:
            self._log(f"--- CPU encountered an unhandled error during run: {e}. Halting. ---")
            self.running = False

# Example usage for testing (if this file were run directly)
if __name__ == "__main__":
    # Create a simple program: INC_R0, INC_R0, PRINT_R0, HALT
    # The actual PixelMemory needs to be initialized for byte storage.
    
    # Program in terms of pixel values
    program_instructions_pixels = [
        OpCode.INC_R0.value,
        OpCode.INC_R0.value,
        OpCode.PRINT_R0.value,
        OpCode.LOAD_R0.value, # Load an immediate value
        (10, 20, 30),        # The value to load (as a pixel, but we'll use R component)
        OpCode.PRINT_R0.value,
        OpCode.HALT.value
    ]

    # Convert pixel instructions to a bytearray suitable for PixelMemory (PACKED_24BIT)
    program_bytes = bytearray()
    for r, g, b in program_instructions_pixels:
        program_bytes.extend([r, g, b])

    # Create a PixelMemory instance (from memory.py)
    mem_size = len(program_bytes) + 100 # Add some extra space
    mem = PixelMemory(size=mem_size, encoding_mode=EncodingMode.PACKED_24BIT)

    # Create a queue for CPU output
    cpu_test_output_queue = queue.Queue()

    # Initialize CPU with the memory and output queue
    cpu = PixelCPU(memory=mem, output_queue=cpu_test_output_queue)
    
    # Load program into memory
    current_address = 0
    for i in range(0, len(program_bytes), 3):
        r = program_bytes[i]
        g = program_bytes[i+1]
        b = program_bytes[i+2]
        mem.write(current_address, bytes([r, g, b]))
        current_address += 3

    cpu.reset(start_address=0)
    cpu.running = True
    cpu.run(max_cycles=20) # Run for a few cycles

    print("\n--- CPU Output Queue Content ---")
    while not cpu_test_output_queue.empty():
        print(cpu_test_output_queue.get())