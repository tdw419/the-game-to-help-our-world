class PixelMemory:
    def __init__(self):
        # Virtual memory map: address (int) → RGB tuple
        self.memory_map = {}

    def encode_to_rgb(self, byte_val):
        """Encodes a single byte into an RGB tuple."""
        return (byte_val, 0, 0)

    def decode_from_rgb(self, rgb):
        """Decodes an RGB tuple back into a single byte."""
        return rgb[0]

    def write(self, address, value):
        """Write a byte to a virtual memory address."""
        rgb = self.encode_to_rgb(value)
        self.memory_map[address] = rgb

    def read(self, address):
        """Read a byte from a virtual memory address."""
        rgb = self.memory_map.get(address, (0, 0, 0))
        return self.decode_from_rgb(rgb)

    def dump_memory(self):
        """Returns a full copy of the current memory map."""
        return dict(self.memory_map)

    def load_memory(self, mem_map):
        """Load a previously saved memory map (RGB format)."""
        self.memory_map = dict(mem_map)