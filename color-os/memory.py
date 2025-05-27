# memory.py

import enum
from typing import List, Tuple, Dict, Any # <-- ADDED Dict HERE

class PixelMemoryError(Exception):
    """Custom exception for PixelMemory operations."""
    pass

class EncodingMode(enum.Enum):
    """Defines how pixel data is interpreted (e.g., RGB, Grayscale)."""
    BYTE = 1        # Represents single byte values (0-255)
    RGB_888 = 2     # Represents 24-bit RGB, 8 bits per channel (R, G, B)
    # Add other encoding modes here as needed, e.g.,
    # ARGB_8888 = 3
    # GRAYSCALE_8BIT = 4

class PixelMemory:
    """
    Simulates pixel-based memory, where each 'address' stores a pixel's color data.
    The memory is essentially a flat array of bytes that can be interpreted
    based on the EncodingMode.
    """
    def __init__(self, width: int, height: int, encoding_mode: EncodingMode = EncodingMode.RGB_888) -> None:
        self.width = width
        self.height = height
        self.encoding_mode = encoding_mode
        self.total_pixels = width * height

        # Each pixel typically stores 3 bytes (R, G, B) for RGB_888
        # The underlying memory is a bytearray
        self.bytes_per_pixel = self._get_bytes_per_pixel(encoding_mode)
        self.total_size_bytes = self.total_pixels * self.bytes_per_pixel
        self.memory = bytearray(self.total_size_bytes)
        self.clear() # Initialize memory to zeros

    def _get_bytes_per_pixel(self, mode: EncodingMode) -> int:
        if mode == EncodingMode.RGB_888:
            return 3 # R, G, B
        elif mode == EncodingMode.BYTE:
            return 1 # Single byte
        else:
            raise ValueError(f"Unsupported encoding mode: {mode}")

    def clear(self) -> None:
        """Resets all memory to black (0,0,0) or zero bytes."""
        for i in range(self.total_size_bytes):
            self.memory[i] = 0

    def _address_to_byte_index(self, pixel_address: int) -> int:
        """Converts a pixel address to its starting byte index in the memory array."""
        if not (0 <= pixel_address < self.total_pixels):
            raise PixelMemoryError(f"Pixel address {pixel_address} out of bounds (0-{self.total_pixels-1})")
        return pixel_address * self.bytes_per_pixel

    def read(self, start_address_bytes: int, end_address_bytes: int) -> bytes:
        """
        Reads a sequence of bytes from memory.
        Addresses are byte addresses, not pixel addresses.
        """
        if not (0 <= start_address_bytes < self.total_size_bytes and
                0 <= end_address_bytes <= self.total_size_bytes and
                start_address_bytes <= end_address_bytes):
            raise PixelMemoryError(f"Invalid byte address range: {start_address_bytes}-{end_address_bytes} (Memory size: {self.total_size_bytes})")
        return bytes(self.memory[start_address_bytes:end_address_bytes])

    def write(self, start_address_bytes: int, data_bytes: bytes) -> None:
        """
        Writes a sequence of bytes to memory.
        Addresses are byte addresses, not pixel addresses.
        """
        end_address_bytes = start_address_bytes + len(data_bytes)
        if not (0 <= start_address_bytes < self.total_size_bytes and
                0 <= end_address_bytes <= self.total_size_bytes):
            raise PixelMemoryError(f"Write out of bounds: trying to write {len(data_bytes)} bytes starting at {start_address_bytes}. Max address: {self.total_size_bytes-1}")
        self.memory[start_address_bytes:end_address_bytes] = data_bytes

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Gets the RGB color of a pixel at (x, y) coordinates."""
        if self.encoding_mode != EncodingMode.RGB_888:
            raise PixelMemoryError("get_pixel only supported for RGB_888 encoding mode.")
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise PixelMemoryError(f"Coordinates ({x}, {y}) out of bounds for canvas ({self.width}, {self.height})")

        pixel_address = (y * self.width) + x
        byte_index = self._address_to_byte_index(pixel_address)
        
        # Read 3 bytes for R, G, B
        r = self.memory[byte_index]
        g = self.memory[byte_index + 1]
        b = self.memory[byte_index + 2]
        return (r, g, b)

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Sets the RGB color of a pixel at (x, y) coordinates."""
        if self.encoding_mode != EncodingMode.RGB_888:
            raise PixelMemoryError("set_pixel only supported for RGB_888 encoding mode.")
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise PixelMemoryError(f"Coordinates ({x}, {y}) out of bounds for canvas ({self.width}, {self.height})")
        if not (isinstance(color, tuple) and len(color) == 3 and
                all(0 <= c <= 255 for c in color)):
            raise ValueError("Color must be an RGB tuple (r, g, b) with values 0-255.")

        pixel_address = (y * self.width) + x
        byte_index = self._address_to_byte_index(pixel_address)
        
        # Write 3 bytes for R, G, B
        self.memory[byte_index] = color[0]
        self.memory[byte_index + 1] = color[1]
        self.memory[byte_index + 2] = color[2]

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics about the memory."""
        return {
            "width": self.width,
            "height": self.height,
            "total_pixels": self.total_pixels,
            "encoding_mode": self.encoding_mode.name,
            "bytes_per_pixel": self.bytes_per_pixel,
            "total_size_bytes": self.total_size_bytes,
            "memory_usage_percent": (len(self.memory) / self.total_size_bytes) * 100 if self.total_size_bytes > 0 else 0
        }

    # You might want to add methods like:
    # get_byte(byte_address: int) -> int
    # set_byte(byte_address: int, value: int) -> None
    # get_word(byte_address: int) -> int (for 16-bit or 32-bit words)
    # set_word(byte_address: int, value: int) -> None