# File: /ColorOS/ProgramLoader.py
# Part of Color OS – Loads .pxl programs from a pixel-based disk image

from PIL import Image

class ProgramLoader:
    def __init__(self, disk_image_path):
        self.disk_image_path = disk_image_path
        self.image = Image.open(disk_image_path)
        self.pixels = self.image.load()
        self.width, self.height = self.image.size

    def find_program_headers(self, header_color=(255, 0, 0)):
        """
        Scan the image for program start markers.
        Default marker: bright red pixel (255, 0, 0).
        Returns: list of (x, y) tuples marking program locations.
        """
        headers = []
        for y in range(self.height):
            for x in range(self.width):
                if self.pixels[x, y][:3] == header_color:
                    headers.append((x, y))
        return headers

    def extract_program(self, header_pos, program_size=(64, 64)):
        """
        Extract a square program region from disk image.
        Assumes program is stored directly below and right of header.
        Returns: PIL Image of extracted .pxl program
        """
        x0, y0 = header_pos
        w, h = program_size
        box = (x0 + 1, y0 + 1, x0 + 1 + w, y0 + 1 + h)
        program_img = self.image.crop(box)
        return program_img

    def load_all_programs(self, header_color=(255, 0, 0), program_size=(64, 64)):
        """
        Finds and extracts all programs from the disk.
        Returns: list of (position, Image) tuples
        """
        programs = []
        headers = self.find_program_headers(header_color)
        for header in headers:
            img = self.extract_program(header, program_size)
            programs.append((header, img))
        return programs

# Example usage:
if __name__ == "__main__":
    loader = ProgramLoader("disks/bootdisk.img.png")
    programs = loader.load_all_programs()
    for i, (pos, img) in enumerate(programs):
        out_path = f"loaded_program_{i}.pxl.png"
        img.save(out_path)
        print(f"Saved program from {pos} to {out_path}")
