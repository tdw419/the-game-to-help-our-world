#!/usr/bin/env python3
"""
PXOS Launcher with AI-Friendly Visual Filesystem
==============================================

A simulated operating system launcher with a hierarchical, optimized visual filesystem
designed for AI interaction and manipulation. Combines low-level ASM execution with
a treemap-based filesystem visualization.

Key Features:
- Hierarchical filesystem with directories, file types, symbolic links, and permissions
- Treemap visualization using Pygame
- Low-level ASM stub execution (Windows-specific)
- AI-friendly API for querying and updating the filesystem
- JSON serialization for state persistence
- Spatial indexing for fast lookups
- Boot simulation and interactive Pygame window
"""

import pygame
import ctypes
import sys
import time
from PIL import Image, ImageDraw
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import random
import squarify
import logging
import asyncio
import platform

# ---------------- Constants ----------------

CANVAS_SIZE = 128
BLOB_SIZE = 32
MAX_LOADED_BLOBS = 16
OUTPUT_FILE = "os_ecosystem.png"
REGISTRY_FILE = "blobs.json"
BOOT_PREFIX = "boot_step_"
COLORS = {
    "HOT": (255, 100, 100),
    "WARM": (255, 200, 100),
    "COLD": (100, 150, 255)
}
SCREEN_SIZE = (640, 480)

# ---------------- Logging Setup ----------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ---------------- Data Structures ----------------

class Priority(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"

class FileType(Enum):
    EXECUTABLE = "●"
    CONFIG = "⚙"
    LIBRARY = "📚"
    DATA = "📄"
    LOG = "📝"
    DIRECTORY = "📁"

@dataclass
class Directory:
    dir_id: int
    path: str
    file_count: int
    size_mb: float
    priority: Priority
    last_modified: float
    version: str
    parent_id: Optional[int]

@dataclass
class DirectoryFileType:
    dir_type_id: int
    dir_id: int
    type_id: int
    count: int

@dataclass
class SymbolicLink:
    link_id: int
    source_dir_id: int
    target_dir_id: int

@dataclass
class Permission:
    perm_id: int
    dir_id: int
    user: str
    read: bool
    write: bool
    execute: bool

class LazyBlob:
    def __init__(self, dir_id: int, vfs: 'VisualFilesystem'):
        self.dir_id = dir_id
        self.vfs = vfs
        self.loaded = False
        self.dirty = True
        self.bounds: Tuple[int, int, int, int] = (0, 0, 0, 0)
        self.content_hash = ""
        self.load_if_needed()
    
    def mark_dirty(self):
        self.dirty = True
    
    def load_if_needed(self):
        if not self.loaded:
            self.loaded = True
            self._update_hash()
    
    def _update_hash(self):
        dir_data = self.vfs.directories[self.dir_id]
        content = f"{dir_data.path}:{dir_data.file_count}:{dir_data.last_modified}"
        self.content_hash = hashlib.md5(content.encode()).hexdigest()[:8]

# ---------------- Visual Filesystem ----------------

class VisualFilesystem:
    def __init__(self, canvas_size: int = CANVAS_SIZE, max_loaded_blobs: int = MAX_LOADED_BLOBS):
        self.canvas_size = canvas_size
        self.max_loaded_blobs = max_loaded_blobs
        self.directories: Dict[int, Directory] = {}
        self.file_types: Dict[int, FileType] = {i: ft for i, ft in enumerate(FileType, 1)}
        self.directory_file_types: Dict[int, DirectoryFileType] = {}
        self.symbolic_links: Dict[int, SymbolicLink] = {}
        self.permissions: Dict[int, Permission] = {}
        self.blobs: Dict[int, LazyBlob] = {}
        self.blob_hierarchy: Dict[int, List[int]] = {}
        self.spatial_index: Dict[Tuple[int, int, int, int], int] = {}
        self.canvas = None
        self.zoom_level = 1.0
        self.focus_path = "/"
        self.last_render_time = 0
        self.render_count = 0
        self.next_dir_id = 1
        self.next_type_id = len(self.file_types) + 1
        self.next_link_id = 1
        self.next_perm_id = 1
        self._initialize_unix_structure()
    
    def _initialize_unix_structure(self):
        unix_dirs = [
            ("/kernel", 10, 50.0, Priority.COLD, {FileType.EXECUTABLE: 8, FileType.DATA: 2}),
            ("/bin", 150, 50.0, Priority.COLD, {FileType.EXECUTABLE: 140, FileType.DATA: 10}),
            ("/sbin", 30, 20.0, Priority.COLD, {FileType.EXECUTABLE: 28, FileType.DATA: 2}),
            ("/usr", 1250, 800.0, Priority.WARM, {FileType.EXECUTABLE: 400, FileType.LIBRARY: 600, FileType.DATA: 250}),
            ("/etc", 200, 15.0, Priority.WARM, {FileType.CONFIG: 180, FileType.DATA: 20}),
            ("/lib", 300, 150.0, Priority.COLD, {FileType.LIBRARY: 280, FileType.DATA: 20}),
            ("/var", 500, 200.0, Priority.HOT, {FileType.LOG: 300, FileType.DATA: 200}),
            ("/tmp", 50, 5.0, Priority.HOT, {FileType.DATA: 45, FileType.LOG: 5}),
            ("/home", 800, 500.0, Priority.WARM, {FileType.DATA: 600, FileType.CONFIG: 200}),
            ("/root", 10, 2.0, Priority.WARM, {FileType.CONFIG: 8, FileType.DATA: 2}),
            ("/dev", 50, 0.5, Priority.HOT, {FileType.DATA: 50}),
            ("/proc", 1000, 0.1, Priority.HOT, {FileType.DATA: 1000}),
            ("/mnt", 20, 10.0, Priority.WARM, {FileType.DATA: 20}),
            ("/opt", 100, 50.0, Priority.WARM, {FileType.EXECUTABLE: 80, FileType.DATA: 20}),
            ("/srv", 50, 25.0, Priority.WARM, {FileType.DATA: 50}),
            ("/sys", 200, 1.0, Priority.HOT, {FileType.DATA: 200}),
        ]
        for path, count, size, priority, types in unix_dirs:
            dir_id = self.add_directory(path, count, size, priority, {k.value: v for k, v in types.items()})
            self.add_permission(dir_id, "root", True, True, True)
        self.add_symbolic_link("/usr/local", "/usr")
    
    def add_directory(self, path: str, file_count: int = 0, size_mb: float = 0, 
                     priority: Priority = Priority.WARM, file_types: Dict[str, int] = None) -> int:
        try:
            if any(d.path == path for d in self.directories.values()):
                raise ValueError(f"Directory {path} already exists")
            parent_id = next((d for d in self.directories if self.directories[d].path == self._get_parent_path(path)), None)
            dir_id = self.next_dir_id
            self.next_dir_id += 1
            self.directories[dir_id] = Directory(
                dir_id=dir_id,
                path=path,
                file_count=file_count,
                size_mb=size_mb,
                priority=priority,
                last_modified=time.time(),
                version="1.0",
                parent_id=parent_id
            )
            self.blobs[dir_id] = LazyBlob(dir_id, self)
            if parent_id is not None:
                if parent_id not in self.blob_hierarchy:
                    self.blob_hierarchy[parent_id] = []
                self.blob_hierarchy[parent_id].append(dir_id)
            if file_types:
                for type_name, count in file_types.items():
                    type_id = next(t for t, ft in self.file_types.items() if ft.value == type_name)
                    self.directory_file_types[len(self.directory_file_types) + 1] = DirectoryFileType(
                        dir_type_id=len(self.directory_file_types) + 1,
                        dir_id=dir_id,
                        type_id=type_id,
                        count=count
                    )
            logging.info(f"Added directory {path} with ID {dir_id}")
            return dir_id
        except Exception as e:
            logging.error(f"Failed to add directory {path}: {e}")
            raise
    
    def add_symbolic_link(self, source_path: str, target_path: str) -> int:
        try:
            source_id = next(d for d in self.directories if self.directories[d].path == source_path)
            target_id = next(d for d in self.directories if self.directories[d].path == target_path)
            link_id = self.next_link_id
            self.next_link_id += 1
            self.symbolic_links[link_id] = SymbolicLink(link_id, source_id, target_id)
            logging.info(f"Added symbolic link {source_path} -> {target_path}")
            return link_id
        except Exception as e:
            logging.error(f"Failed to add symbolic link {source_path} -> {target_path}: {e}")
            raise
    
    def add_permission(self, dir_id: int, user: str, read: bool, write: bool, execute: bool) -> int:
        try:
            perm_id = self.next_perm_id
            self.next_perm_id += 1
            self.permissions[perm_id] = Permission(perm_id, dir_id, user, read, write, execute)
            logging.info(f"Added permissions for dir_id {dir_id}")
            return perm_id
        except Exception as e:
            logging.error(f"Failed to add permissions for dir_id {dir_id}: {e}")
            raise
    
    def _get_parent_path(self, path: str) -> str:
        if path == "/":
            return ""
        parts = path.rstrip("/").split("/")
        if len(parts) <= 2:
            return "/"
        return "/".join(parts[:-1])
    
    def query_directory(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            dir_id = next((d for d in self.directories if self.directories[d].path == path), None)
            if dir_id is None:
                return None
            blob = self.blobs[dir_id]
            blob.load_if_needed()
            dir_data = self.directories[dir_id]
            file_types = {self.file_types[dt.type_id].value: dt.count for dt in self.directory_file_types.values() if dt.dir_id == dir_id}
            perms = [p for p in self.permissions.values() if p.dir_id == dir_id]
            return {
                "path": dir_data.path,
                "file_count": dir_data.file_count,
                "size_mb": dir_data.size_mb,
                "file_types": file_types,
                "priority": dir_data.priority.value,
                "last_modified": dir_data.last_modified,
                "children": [self.directories[c].path for c in self.blob_hierarchy.get(dir_id, [])],
                "permissions": [{"user": p.user, "read": p.read, "write": p.write, "execute": p.execute} for p in perms],
                "loaded": blob.loaded,
                "dirty": blob.dirty,
                "content_hash": blob.content_hash
            }
        except Exception as e:
            logging.error(f"Failed to query directory {path}: {e}")
            return None
    
    def query_blobs(self, query: Dict[str, Any]) -> List[str]:
        try:
            results = []
            for dir_id, dir_data in self.directories.items():
                matches = True
                if "file_count_gt" in query and dir_data.file_count <= query["file_count_gt"]:
                    matches = False
                if "file_type" in query:
                    type_id = next(t for t, ft in self.file_types.items() if ft.value == query["file_type"])
                    if not any(dt.dir_id == dir_id and dt.type_id == type_id for dt in self.directory_file_types.values()):
                        matches = False
                if "has_children" in query and query["has_children"] != (dir_id in self.blob_hierarchy):
                    matches = False
                if matches:
                    results.append(dir_data.path)
            logging.info(f"Query executed: {query}, found {len(results)} results")
            return results
        except Exception as e:
            logging.error(f"Query failed: {e}")
            return []
    
    def update_directory(self, dir_id: int, **kwargs) -> bool:
        try:
            if dir_id not in self.directories:
                return False
            dir_data = self.directories[dir_id]
            blob = self.blobs[dir_id]
            for key, value in kwargs.items():
                if hasattr(dir_data, key):
                    setattr(dir_data, key, value)
                    blob.mark_dirty()
            dir_data.last_modified = time.time()
            blob._update_hash()
            logging.info(f"Updated directory {dir_data.path}")
            return True
        except Exception as e:
            logging.error(f"Failed to update directory {dir_id}: {e}")
            return False
    
    def get_blob_at_position(self, x: int, y: int) -> Optional[int]:
        for bounds, dir_id in self.spatial_index.items():
            x0, y0, x1, y1 = bounds
            if x0 <= x <= x1 and y0 <= y <= y1:
                return dir_id
        return None
    
    def clear_all_dirty(self):
        for blob in self.blobs.values():
            blob.dirty = False
    
    def calculate_treemap_bounds(self) -> None:
        try:
            sizes = [self.directories[d].size_mb for d in self.directories]
            norm_sizes = squarify.normalize_sizes(sizes, self.canvas_size, self.canvas_size)
            rects = squarify.squarify(norm_sizes, 0, 0, self.canvas_size, self.canvas_size)
            for i, dir_id in enumerate(self.directories):
                rect = rects[i]
                self.blobs[dir_id].bounds = (int(rect["x"]), int(rect["y"]), int(rect["x"] + rect["dx"]), int(rect["y"] + rect["dy"]))
                self.spatial_index[self.blobs[dir_id].bounds] = dir_id
            logging.info("Calculated treemap bounds")
        except Exception as e:
            logging.error(f"Failed to calculate treemap bounds: {e}")
            raise
    
    def get_priority_color(self, priority: Priority) -> Tuple[int, int, int]:
        return COLORS.get(priority.value, (128, 128, 128))
    
    def render_blob(self, draw: ImageDraw, blob: LazyBlob, detail_level: int = 2, zoom_level: float = 1.0) -> None:
        if not blob.dirty and blob.loaded:
            return
        x0, y0, x1, y1 = blob.bounds
        dir_data = self.directories[blob.dir_id]
        base_color = self.get_priority_color(dir_data.priority)
        draw.rectangle(blob.bounds, fill=base_color, outline=(255, 255, 255))
        if detail_level >= 1 and zoom_level >= 0.5:
            name = dir_data.path.split("/")[-1] or "root"
            draw.text((x0 + 1, y0 + 1), name[:8], fill=(0, 0, 0))
            draw.text((x0 + 1, y0 + 10), f"{dir_data.file_count}f", fill=(0, 0, 0))
        if detail_level == 2 and zoom_level >= 1.0:
            draw.text((x0 + 1, y0 + 18), f"{dir_data.size_mb:.0f}M", fill=(0, 0, 0))
            file_types = {self.file_types[dt.type_id].value: dt.count for dt in self.directory_file_types.values() if dt.dir_id == blob.dir_id}
            if file_types:
                dominant_type = max(file_types, key=file_types.get)
                draw.text((x0 + 1, y0 + 26), dominant_type, fill=(0, 0, 0))
        blob.dirty = False
    
    def render(self, detail_level: int = 2, focus_path: str = None, zoom_level: float = 1.0) -> Image:
        try:
            start_time = time.time()
            self.canvas = Image.new("RGB", (self.canvas_size, self.canvas_size), (20, 20, 50))
            draw = ImageDraw.Draw(self.canvas)
            self.calculate_treemap_bounds()
            for dir_id, blob in self.blobs.items():
                if focus_path and not self.directories[dir_id].path.startswith(focus_path):
                    continue
                blob.load_if_needed()
                self.render_blob(draw, blob, detail_level, zoom_level)
            self.last_render_time = time.time() - start_time
            self.render_count += 1
            self.clear_all_dirty()
            logging.info(f"Rendered canvas in {self.last_render_time:.3f}s")
            return self.canvas
        except Exception as e:
            logging.error(f"Render failed: {e}")
            raise
    
    def save(self, filename: str = OUTPUT_FILE) -> None:
        try:
            if self.canvas is None:
                self.render()
            self.canvas.save(filename)
            logging.info(f"Saved {filename}")
        except Exception as e:
            logging.error(f"Failed to save {filename}: {e}")
            raise
    
    def save_blob(self, blob: LazyBlob, filename: str) -> None:
        try:
            x0, y0, x1, y1 = blob.bounds
            blob_img = self.canvas.crop((x0, y0, x1 + 1, y1 + 1)).convert("P", palette=Image.ADAPTIVE, colors=256)
            blob_img.save(filename, optimize=True)
            dir_data = self.directories[blob.dir_id]
            file_types = {self.file_types[dt.type_id].value: dt.count for dt in self.directory_file_types.values() if dt.dir_id == blob.dir_id}
            perms = [p for p in self.permissions.values() if p.dir_id == blob.dir_id]
            metadata = {
                "path": dir_data.path,
                "file_count": dir_data.file_count,
                "size_mb": dir_data.size_mb,
                "file_types": file_types,
                "priority": dir_data.priority.value,
                "last_modified": dir_data.last_modified,
                "version": dir_data.version,
                "children": [self.directories[c].path for c in self.blob_hierarchy.get(blob.dir_id, [])],
                "permissions": [{"user": p.user, "read": p.read, "write": p.write, "execute": p.execute} for p in perms]
            }
            with open(f"{filename[:-4]}.json", "w") as f:
                json.dump(metadata, f)
            logging.info(f"Saved {filename} and {filename[:-4]}.json")
        except Exception as e:
            logging.error(f"Failed to save blob {filename}: {e}")
            raise
    
    def export_state(self) -> Dict[str, Any]:
        try:
            return {
                "canvas_size": self.canvas_size,
                "zoom_level": self.zoom_level,
                "focus_path": self.focus_path,
                "render_stats": {
                    "last_render_time": self.last_render_time,
                    "render_count": self.render_count
                },
                "directories": {d: vars(self.directories[d]) for d in self.directories},
                "file_types": {t: self.file_types[t].value for t in self.file_types},
                "directory_file_types": {dt: vars(self.directory_file_types[dt]) for dt in self.directory_file_types},
                "symbolic_links": {l: vars(self.symbolic_links[l]) for l in self.symbolic_links},
                "permissions": {p: vars(self.permissions[p]) for p in self.permissions},
                "blobs": {
                    d: {
                        "loaded": self.blobs[d].loaded,
                        "dirty": self.blobs[d].dirty,
                        "bounds": self.blobs[d].bounds,
                        "content_hash": self.blobs[d].content_hash
                    }
                    for d in self.blobs
                },
                "hierarchy": self.blob_hierarchy
            }
        except Exception as e:
            logging.error(f"Failed to export state: {e}")
            raise
    
    def save_registry(self) -> None:
        try:
            with open(REGISTRY_FILE, "w") as f:
                json.dump(self.export_state(), f)
            logging.info(f"Saved {REGISTRY_FILE}")
        except Exception as e:
            logging.error(f"Failed to save registry: {e}")
            raise

# ---------------- PXOS Launcher ----------------

class PXOSLauncher:
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption("PXOS Launcher - AI & Human Interface")
        
        # Initialize Visual Filesystem
        self.vfs = VisualFilesystem()
        
        # Define pxboot_init blob (simplified ASM stub)
        self.pxboot_init = bytes.fromhex("B8 01 00 00 00 50 48 31 C0 48 FF C0 C3")  # mov eax, 1; push rax; xor rax, rax; inc rax; ret
        
        # Render initial filesystem
        self.vfs.render()
        self.vfs.save()
        self.update_screen()
        
        # Initialize memory execution
        self.memory = None
        self.thread = None
        if platform.system() == "Windows":
            self.setup_memory_execution()
    
    def update_screen(self):
        """Update Pygame screen with current filesystem rendering."""
        img = pygame.image.load(OUTPUT_FILE)
        # Scale 128x128 canvas to 640x480 screen
        img = pygame.transform.scale(img, SCREEN_SIZE)
        self.screen.blit(img, (0, 0))
        pygame.display.flip()
    
    def setup_memory_execution(self):
        """Allocate memory and execute ASM stub (Windows-specific)."""
        try:
            kernel32 = ctypes.windll.kernel32
            process = kernel32.GetCurrentProcess()
            # Allocate memory for pxboot_init
            size = len(self.pxboot_init)
            self.memory = kernel32.VirtualAllocEx(process, 0, size, 0x3000, 0x40)  # MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
            if not self.memory:
                logging.error("VirtualAlloc failed!")
                return
            
            # Write ASM stub to memory
            kernel32.WriteProcessMemory(process, self.memory, self.pxboot_init, size, None)
            
            # Create thread to execute ASM
            self.thread = kernel32.CreateThread(None, 0, self.memory, None, 0, None)
            if not self.thread:
                logging.error("CreateThread failed!")
                return
        except Exception as e:
            logging.error(f"Memory execution setup failed: {e}")
    
    async def simulate_boot(self):
        """Simulate PXOS boot sequence."""
        boot_order = ["/kernel", "/bin", "/etc", "/usr"]
        for i, path in enumerate(boot_order):
            self.vfs.render(focus_path=path)
            self.vfs.save(f"{BOOT_PREFIX}{i}.png")
            self.update_screen()
            logging.info(f"Boot step {i}: {path}")
            await asyncio.sleep(0.5)  # Simulate boot delay
    
    async def run(self):
        """Run the PXOS launcher with interactive Pygame window."""
        try:
            print("Launching PXOS runtime with Visual Filesystem...")
            await self.simulate_boot()
            
            running = True
            zoom_level = 1.0
            offset = (0, 0)
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        adjusted_x = int((x - offset[0]) * self.vfs.canvas_size / SCREEN_SIZE[0] / zoom_level)
                        adjusted_y = int((y - offset[1]) * self.vfs.canvas_size / SCREEN_SIZE[1] / zoom_level)
                        blob_id = self.vfs.get_blob_at_position(adjusted_x, adjusted_y)
                        if blob_id:
                            logging.info(f"Clicked on {self.vfs.directories[blob_id].path}")
                            self.vfs.render(focus_path=self.vfs.directories[blob_id].path, zoom_level=zoom_level)
                            self.vfs.save()
                            self.update_screen()
                    elif event.type == pygame.MOUSEWHEEL:
                        zoom_level = max(0.5, min(2.0, zoom_level + event.y * 0.1))
                        self.vfs.render(zoom_level=zoom_level)
                        self.vfs.save()
                        self.update_screen()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LEFT:
                            offset = (offset[0] + 10, offset[1])
                        elif event.key == pygame.K_RIGHT:
                            offset = (offset[0] - 10, offset[1])
                        elif event.key == pygame.K_UP:
                            offset = (offset[0], offset[1] + 10)
                        elif event.key == pygame.K_DOWN:
                            offset = (offset[0], offset[1] - 10)
                        self.update_screen()
                
                await asyncio.sleep(1.0 / 60)  # 60 FPS
            
            pygame.quit()
        except Exception as e:
            logging.error(f"Launcher run failed: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources."""
        if platform.system() == "Windows" and self.memory:
            ctypes.windll.kernel32.VirtualFreeEx(ctypes.windll.kernel32.GetCurrentProcess(), self.memory, 0, 0x8000)  # MEM_RELEASE
        pygame.quit()

# ---------------- AI-Friendly API ----------------

class PXOSInterface:
    def __init__(self, vfs: VisualFilesystem):
        self.vfs = vfs
    
    def query_blob(self, path: str) -> dict:
        """Query directory metadata."""
        result = self.vfs.query_directory(path)
        return result if result else {}
    
    def update_blob(self, path: str, size_mb: int) -> bool:
        """Update directory size."""
        dir_id = next((d for d in self.vfs.directories if self.vfs.directories[d].path == path), None)
        if dir_id and 0 <= size_mb <= 8000:
            return self.vfs.update_directory(dir_id, size_mb=size_mb)
        return False
    
    def execute_command(self, command: str) -> str:
        """Simulate PXOS command execution."""
        if command == "detect_pci":
            return "Detected devices: 8086:1916, 10DE:1347"
        elif command == "list_dirs":
            return ", ".join(self.vfs.query_blobs({}))
        return "Command not recognized"

# ---------------- Main ----------------

async def main():
    launcher = PXOSLauncher()
    pxos = PXOSInterface(launcher.vfs)
    try:
        await launcher.run()
        
        # Demo API usage
        print(pxos.query_blob("/usr"))
        print(pxos.update_blob("/usr", 2000))
        print(pxos.query_blob("/usr"))
        print(pxos.execute_command("detect_pci"))
        print(pxos.execute_command("list_dirs"))
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    if platform.system() == "Emscripten":
        asyncio.ensure_future(main())
    else:
        asyncio.run(main())