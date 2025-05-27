from pixel_memory import PixelMemory

class PixelDisk:
    def __init__(self, blocks=1024, block_size=512):
        self.blocks = blocks
        self.block_size = block_size
        self.memory = PixelMemory(size=blocks * block_size)

    def read_block(self, index):
        if index < 0 or index >= self.blocks:
            raise IndexError("Invalid block index")
        start = index * self.block_size
        end = start + self.block_size
        return self.memory.read(start, end)

    def write_block(self, index, data):
        if index < 0 or index >= self.blocks:
            raise IndexError("Invalid block index")
        if len(data) != self.block_size:
            raise ValueError(f"Data must be exactly {self.block_size} bytes")
        start = index * self.block_size
        self.memory.write(start, data)

    def format_disk(self):
        self.memory.clear()

    def save_to_image(self, filename="pixel_disk.png"):
        self.memory.save(filename)

    def load_from_image(self, filename="pixel_disk.png"):
        self.memory.load(filename)
