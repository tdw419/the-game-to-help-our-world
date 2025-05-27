class PixelCPU:
    def __init__(self, memory):
        self.memory = memory              # Link to PixelMemory object
        self.pc = 0                       # Program Counter
        self.registers = [0] * 8          # 8 general-purpose registers (R0-R7)
        self.running = True

    def fetch(self):
        return self.memory.read(self.pc)

    def decode_execute(self, opcode):
        if opcode == (255, 0, 0):         # RED pixel = HALT
            print("HALT")
            self.running = False

        elif opcode == (0, 255, 0):       # GREEN pixel = INC R0
            self.registers[0] += 1
            print(f"R0 incremented to {self.registers[0]}")

        elif opcode == (0, 0, 255):       # BLUE pixel = PRINT R0
            print(f"R0: {self.registers[0]}")

        else:
            print(f"Unknown opcode: {opcode}")

    def step(self):
        opcode = self.fetch()
        self.decode_execute(opcode)
        self.pc += 1

    def run(self, max_cycles=100):
        cycle = 0
        while self.running and cycle < max_cycles:
            self.step()
            cycle += 1
