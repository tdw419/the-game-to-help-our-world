# disk.py

from typing import List, Dict, Any
from memory import PixelMemory # Import PixelMemory for type hinting

class DiskError(Exception):
    """Custom exception for disk-related operations."""
    pass

class PixelDisk:
    """
    Simulates a simple disk where storage is measured in 'pixels' (bytes in a real disk).
    It manages blocks of a fixed size. This disk will conceptually operate
    on a given PixelMemory instance.
    """
    def __init__(self, memory_interface: PixelMemory, total_size_pixels: int, block_size_pixels: int) -> None:
        if total_size_pixels <= 0 or block_size_pixels <= 0:
            raise ValueError("Disk size and block size must be positive.")
        if total_size_pixels % block_size_pixels != 0:
            raise ValueError("Total disk size must be a multiple of block size.")

        # Store the PixelMemory instance this disk operates on
        self.memory_interface = memory_interface

        self.total_size_pixels = total_size_pixels
        self.block_size_pixels = block_size_pixels
        self.num_blocks = self.total_size_pixels // self.block_size_pixels

        # IMPORTANT: For a true "disk on memory", these blocks would reference
        # regions within self.memory_interface. For now, they are internal.
        # This will need refactoring if the disk is meant to directly use PixelMemory as its storage medium.
        self.blocks: List[bytearray] = [bytearray(self.block_size_pixels) for _ in range(self.num_blocks)]
        self.free_blocks: List[int] = list(range(self.num_blocks)) # List of available block indices

        self.clear() # Initialize all blocks to zeros

    def clear(self) -> None:
        """Clears all data on the disk and marks all blocks as free."""
        for i in range(self.num_blocks):
            self.blocks[i] = bytearray(self.block_size_pixels) # Re-initialize to zeros
        self.free_blocks = list(range(self.num_blocks))

    def allocate_blocks(self, num_blocks_to_allocate: int) -> List[int]:
        """
        Allocates a specified number of free blocks.
        Returns a list of allocated block indices.
        """
        if num_blocks_to_allocate <= 0:
            return []
        if num_blocks_to_allocate > len(self.free_blocks):
            raise DiskError(f"Not enough free blocks. Requested {num_blocks_to_allocate}, available {len(self.free_blocks)}")

        allocated = []
        for _ in range(num_blocks_to_allocate):
            block_idx = self.free_blocks.pop(0) # Take from the front of the free list
            allocated.append(block_idx)
        return allocated

    def free_blocks_by_index(self, block_indices: List[int]) -> None:
        """Frees blocks by their indices."""
        for idx in block_indices:
            if not (0 <= idx < self.num_blocks):
                raise DiskError(f"Invalid block index: {idx}")
            if idx in self.free_blocks:
                # Optionally warn if trying to free an already free block
                print(f"Warning: Block {idx} is already free.")
                continue
            self.blocks[idx] = bytearray(self.block_size_pixels) # Clear data on free
            self.free_blocks.append(idx)
        self.free_blocks.sort() # Keep free blocks sorted for consistency

    def write_block(self, block_index: int, data: bytes) -> None:
        """Writes data to a specific block."""
        if not (0 <= block_index < self.num_blocks):
            raise DiskError(f"Block index {block_index} out of bounds.")
        if len(data) > self.block_size_pixels:
            raise ValueError(f"Data size ({len(data)}) exceeds block size ({self.block_size_pixels}).")

        # Pad data with zeros if it's smaller than the block size
        padded_data = data + b'\x00' * (self.block_size_pixels - len(data))
        self.blocks[block_index] = bytearray(padded_data)

        # TODO: If this disk is meant to operate directly on PixelMemory,
        # you would call self.memory_interface.write() here with the correct byte offset.

    def read_block(self, block_index: int) -> bytes:
        """Reads data from a specific block."""
        if not (0 <= block_index < self.num_blocks):
            raise DiskError(f"Block index {block_index} out of bounds.")

        # TODO: If this disk is meant to operate directly on PixelMemory,
        # you would call self.memory_interface.read() here with the correct byte offset.

        return bytes(self.blocks[block_index])

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the disk."""
        used_blocks = self.num_blocks - len(self.free_blocks)
        return {
            "total_size_pixels": self.total_size_pixels,
            "block_size_pixels": self.block_size_pixels,
            "num_blocks": self.num_blocks,
            "free_blocks_count": len(self.free_blocks),
            "used_blocks_count": used_blocks,
            "free_space_pixels": len(self.free_blocks) * self.block_size_pixels,
            "used_space_pixels": used_blocks * self.block_size_pixels,
            "usage_percent": (used_blocks / self.num_blocks) * 100 if self.num_blocks > 0 else 0
        }