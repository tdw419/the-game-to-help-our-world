import struct
import json
import os

class ISO9660Parser:
    """
    A simplified ISO9660 parser to extract basic information
    needed to generate PXTalk boot script.
    This parser focuses on finding the Primary Volume Descriptor (PVD)
    and then the root directory record to locate files like vmlinuz and core.gz.
    It does NOT implement a full recursive directory parser.
    """
    
    SECTOR_SIZE = 2048 # Standard ISO9660 sector size

    def __init__(self, iso_path):
        self.iso_path = iso_path
        self.file_handle = None
        self.pvd_info = {}
        self.root_dir_entries = [] # Stores parsed entries from the root directory

    def _read_bytes(self, offset, length):
        """Reads a specified number of bytes from the ISO at a given offset."""
        if not self.file_handle:
            raise IOError("ISO file not opened.")
        self.file_handle.seek(offset)
        return self.file_handle.read(length)

    def _read_le_uint32(self, data, offset):
        """Reads a 32-bit little-endian unsigned integer from bytes."""
        return struct.unpack('<I', data[offset:offset+4])[0]

    def _read_be_uint32(self, data, offset):
        """Reads a 32-bit big-endian unsigned integer from bytes."""
        return struct.unpack('>I', data[offset:offset+4])[0]

    def parse_pvd(self):
        """Parses the Primary Volume Descriptor (PVD) at 0x8000."""
        pvd_offset = 0x8000 # Sector 16 * 2048 bytes/sector
        pvd_data = self._read_bytes(pvd_offset, self.SECTOR_SIZE)

        if not pvd_data or len(pvd_data) < 156:
            raise ValueError("Failed to read PVD or PVD too small.")

        # Check Volume Descriptor Type (1 byte, should be 1 for PVD)
        vd_type = pvd_data[0]
        if vd_type != 1:
            raise ValueError(f"Invalid Volume Descriptor Type: {vd_type} (expected 1 for PVD).")

        # Check Standard Identifier (5 bytes, should be "CD001")
        std_identifier = pvd_data[1:6].decode('ascii')
        if std_identifier != "CD001":
            raise ValueError(f"Invalid Standard Identifier: '{std_identifier}' (expected 'CD001').")

        # Extract Root Directory Record information
        # Root Directory Record starts at byte 156 (offset 156) in PVD
        # LBA of extent (4 bytes LE and 4 bytes BE)
        root_dir_lba_le = self._read_le_uint32(pvd_data, 158) # LBA is at offset 158 (4 bytes LE)
        root_dir_lba_be = self._read_be_uint32(pvd_data, 162) # LBA is at offset 162 (4 bytes BE)
        
        # Data Length of extent (8 bytes LE and 8 bytes BE)
        # For simplicity, we'll use the LE 32-bit value for size here, as TinyCore often fits.
        # A full parser would handle 64-bit size.
        root_dir_size_le = self._read_le_uint32(pvd_data, 166) # Size is at offset 166 (4 bytes LE)
        root_dir_size_be = self._read_be_uint32(pvd_data, 170) # Size is at offset 170 (4 bytes BE)

        self.pvd_info = {
            "root_dir_lba": root_dir_lba_le,
            "root_dir_size": root_dir_size_le,
            "volume_identifier": pvd_data[40:72].decode('ascii').strip() # Volume Identifier (32 bytes)
        }
        print(f"[Compiler] PVD parsed. Root Dir LBA: {self.pvd_info['root_dir_lba']}, Size: {self.pvd_info['root_dir_size']}")
        print(f"[Compiler] Volume Identifier: '{self.pvd_info['volume_identifier']}'")

    def parse_directory_block(self, lba, size, current_path="/"):
        """
        Parses a single directory block and extracts its entries.
        This is a simplified version and does not handle multi-extent directories
        or deep recursion beyond the first level needed for /boot.
        """
        dir_offset = lba * self.SECTOR_SIZE
        dir_data = self._read_bytes(dir_offset, size)

        if not dir_data:
            print(f"[Compiler] WARNING: No data for directory block at LBA {lba}.")
            return []

        entries = []
        index = 0
        while index < len(dir_data):
            record_length = dir_data[index]
            if record_length == 0: # End of records in this block
                break

            # Extract fields from Directory Record
            lba_le = self._read_le_uint32(dir_data, index + 2)
            file_size_le = self._read_le_uint32(dir_data, index + 10)
            flags = dir_data[index + 25]
            file_id_len = dir_data[index + 32]
            
            # File Identifier (name)
            name_bytes_start = index + 33
            name_bytes_end = name_bytes_start + file_id_len
            if name_bytes_end > len(dir_data):
                print(f"[Compiler] WARNING: Directory entry name extends beyond block bounds. Skipping.")
                break # Avoid IndexError
            
            name = dir_data[name_bytes_start:name_bytes_end].decode('ascii')
            
            # Clean up ISO9660 specific naming conventions
            if ';' in name:
                name = name.split(';')[0]
            if name.endswith('.'):
                name = name[:-1]
            name = name.lower() # Normalize to lowercase

            is_dir = (flags & 0x02) != 0 # Check if directory flag is set

            # Skip special entries '.' (0x00) and '..' (0x01)
            if file_id_len == 1 and (name_bytes_start < len(dir_data) and (dir_data[name_bytes_start] == 0x00 or dir_data[name_bytes_start] == 0x01)):
                pass
            else:
                entry_path = os.path.join(current_path, name).replace("\\", "/") # Use os.path.join for robustness
                if is_dir and not entry_path.endswith('/'):
                    entry_path += '/' # Ensure directories have trailing slash for consistency

                entries.append({
                    "name": name,
                    "full_path": entry_path,
                    "lba": lba_le,
                    "size": file_size_le,
                    "is_dir": is_dir
                })
            
            index += record_length
        return entries

    def find_file_in_dir(self, directory_entries, filename):
        """Searches for a file within a list of directory entries."""
        normalized_filename = filename.lower()
        if normalized_filename.endswith('/'): # If searching for a directory, remove trailing slash for comparison
            normalized_filename = normalized_filename[:-1]

        for entry in directory_entries:
            # Check for exact match first
            if entry["name"] == normalized_filename:
                return entry
            
            # Fuzzy match: check if entry name starts with normalized filename
            # This helps find "vmlinuz-5.10.0-rc1" when looking for "vmlinuz"
            if entry["name"].startswith(normalized_filename):
                print(f"[Compiler] Fuzzy match: Found '{entry['name']}' for '{filename}'.")
                return entry
        return None

    def compile_to_pxtalk(self, output_file="boot.pxtalk"):
        """
        Opens the ISO, parses necessary info, and generates a PXTalk script.
        This script will be embedded in the ISO later.
        """
        try:
            self.file_handle = open(self.iso_path, "rb")
            print(f"[Compiler] Opened ISO: {self.iso_path}")

            # 1. Parse PVD to get root directory info
            self.parse_pvd()
            root_dir_lba = self.pvd_info["root_dir_lba"]
            root_dir_size = self.pvd_info["root_dir_size"]

            # 2. Parse the root directory to find /boot
            root_entries = self.parse_directory_block(root_dir_lba, root_dir_size, current_path="/")
            
            boot_dir_entry = self.find_file_in_dir(root_entries, "boot")
            if not boot_dir_entry or not boot_dir_entry["is_dir"]:
                raise FileNotFoundError("/boot directory not found in ISO root.")
            
            # 3. Parse the /boot directory to find vmlinuz and core.gz
            boot_entries = self.parse_directory_block(boot_dir_entry["lba"], boot_dir_entry["size"], current_path="/boot/")

            vmlinuz_entry = self.find_file_in_dir(boot_entries, "vmlinuz")
            core_gz_entry = self.find_file_in_dir(boot_entries, "core.gz")

            if not vmlinuz_entry:
                raise FileNotFoundError("vmlinuz not found in /boot.")
            if not core_gz_entry:
                raise FileNotFoundError("core.gz (initrd) not found in /boot.")

            # Generate PXTalk script
            pxtalk_script = []
            pxtalk_script.append(f"PX_LOG \"[PXBIOS] Compiling ISO '{self.iso_path}' to PXTalk...\"")
            pxtalk_script.append("")

            # MBR and PVD checks (conceptual, as PXVM already does this)
            pxtalk_script.append("# MBR and PVD checks (simulated for compiler output)")
            pxtalk_script.append("PX_READ_BYTES \"tinycore.iso\" 0 512 -> mbr_data")
            pxtalk_script.append("PX_COMPARE mbr_data 0x1FE 0xAA55 THEN \"LABEL MBR_OK\" ELSE \"PX_HALT\"")
            pxtalk_script.append("LABEL MBR_OK")
            pxtalk_script.append("PX_READ_ISO_PVD # This would internally verify CD001 and get root_dir_lba/size")
            pxtalk_script.append("PX_LOG \"[PXBIOS] ISO structure validated.\"")
            pxtalk_script.append("")

            # Dynamic file locations based on parsing
            pxtalk_script.append("# Dynamically discovered kernel and initrd locations")
            pxtalk_script.append(f"PX_SET kernel_offset {vmlinuz_entry['lba'] * self.SECTOR_SIZE}")
            pxtalk_script.append(f"PX_SET kernel_size {vmlinuz_entry['size']}")
            pxtalk_script.append(f"PX_SET initrd_offset {core_gz_entry['lba'] * self.SECTOR_SIZE}")
            pxtalk_script.append(f"PX_SET initrd_size {core_gz_entry['size']}")
            pxtalk_script.append("")

            pxtalk_script.append("PX_LOG \"[PXBIOS] Found kernel at offset $kernel_offset (size $kernel_size)\"")
            pxtalk_script.append("PX_LOG \"[PXBIOS] Found initrd at offset $initrd_offset (size $initrd_size)\"")
            pxtalk_script.append("")

            pxtalk_script.append("# Read kernel and initrd data into PXRAM")
            pxtalk_script.append("PX_READ_BYTES \"tinycore.iso\" $kernel_offset $kernel_size -> kernel_data")
            pxtalk_script.append("PX_READ_BYTES \"tinycore.iso\" $initrd_offset $initrd_size -> initrd_data")
            pxtalk_script.append("")

            pxtalk_script.append("PX_LOG \"[PXBIOS] Kernel and Initrd loaded. Handoff to kernel simulation...\"")
            pxtalk_script.append("PX_EXEC_KERNEL")

            with open(output_file, "w") as f:
                f.write("\n".join(pxtalk_script))
            print(f"[Compiler] Successfully compiled '{self.iso_path}' to '{output_file}'")

        except FileNotFoundError as e:
            print(f"[Compiler] ERROR: {e}")
        except ValueError as e:
            print(f"[Compiler] ERROR: ISO parsing failed - {e}")
        except IOError as e:
            print(f"[Compiler] ERROR: File operation failed - {e}")
        finally:
            if self.file_handle:
                self.file_handle.close()

# Example Usage:
if __name__ == "__main__":
    # IMPORTANT: Replace 'path/to/your/tinycore.iso' with the actual path to your TinyCore ISO file.
    # This script should be run from your Python environment.
    # Make sure you have a tinycore.iso available.
    
    # For testing, you might put a tinycore.iso in the same directory as this script.
    
    # Example: If tinycore.iso is in the same directory as the script:
    iso_file = "tinycore.iso" 
    
    # If it's in a subdirectory:
    # iso_file = "iso_files/tinycore.iso" 

    # Check if the ISO file exists before proceeding
    if not os.path.exists(iso_file):
        print(f"Error: ISO file '{iso_file}' not found.")
        print("Please ensure your tinycore.iso is in the correct path relative to this script.")
        print("You can download TinyCore Linux from: http://www.tinycorelinux.net/downloads.html")
    else:
        parser = ISO9660Parser(iso_file)
        parser.compile_to_pxtalk("tinycore_boot.pxtalk")

