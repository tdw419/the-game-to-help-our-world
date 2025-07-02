import os
import time
import json
import base64
from collections import defaultdict
import re # For GDScript to Python translation regex

# Define the file where PXOS File System data will be stored
PXOS_FS_FILE = 'pxos_fs.json'
# Define the default path for Godot FS exports
PXOS_GODOT_EXPORT_FILE = 'pxos_godot_export.json'
# Define the default filename for extracted Godot logic
PXOS_CORE_EXTRACTED_FILE = 'PXOSCore_extracted.gd'
# Define the default filename for translated Python logic
PXOS_CORE_TRANSLATED_PY_FILE = 'PXOSCore_translated.py'

# PXOS File System (PXFS) Management
class PXOSFileSystem:
    def __init__(self, fs_file=PXOS_FS_FILE):
        self.fs_file = fs_file
        self.fs_data = {}  # Stores the entire file system structure
        self.current_path = ['root'] # Represents the current working directory as a list
        self._load_fs()

    def _load_fs(self):
        """Loads the file system data from a JSON file."""
        if os.path.exists(self.fs_file):
            try:
                with open(self.fs_file, 'r', encoding='utf-8') as f:
                    self.fs_data = json.load(f)
                print(f"PXOS FS> Loaded file system from {self.fs_file}")
            except json.JSONDecodeError:
                print(f"PXOS FS> Error loading {self.fs_file}. Creating new file system.")
                self._initialize_default_fs()
            except Exception as e:
                print(f"PXOS FS> Unexpected error loading {self.fs_file}: {e}. Creating new file system.")
                self._initialize_default_fs()
        else:
            self._initialize_default_fs()
            print(f"PXOS FS> Created new file system: {self.fs_file}")
        
        # Ensure 'files' key exists in all directories for consistency
        self._ensure_files_key(self.fs_data)

    def _ensure_files_key(self, node):
        """Recursively ensures that every directory node has a 'files' key."""
        if isinstance(node, dict):
            if 'files' not in node:
                node['files'] = {}
            for key, value in node.items():
                if key != 'files' and isinstance(value, dict): # Avoid recursing into 'files' which holds file content
                    self._ensure_files_key(value)

    def _initialize_default_fs(self):
        """Initializes a default file system structure."""
        self.fs_data = {
            'root': {
                'dirs': {
                    'apps': {'dirs': {}, 'files': {}},
                    'users': {
                        'dirs': {
                            'admin': {'dirs': {}, 'files': {}}
                        },
                        'files': {}
                    },
                    'system': {
                        'dirs': {
                            'config': {'dirs': {}, 'files': {}}
                        },
                        'files': {
                            'pxos_settings.txt': 'PXOS_VERSION=1.0\nAI_MODE=TRAINING\n'
                        }
                    }
                },
                'files': {
                    'README.txt': 'Welcome to PXOS! Use \'help\' for commands.'
                }
            }
        }
        self.current_path = ['root']
        self.save_fs() # Save the default structure immediately

    def save_fs(self):
        """Saves the current file system data to a JSON file."""
        try:
            with open(self.fs_file, 'w', encoding='utf-8') as f:
                json.dump(self.fs_data, f, indent=4)
            # print(f"PXOS FS> Saved file system to {self.fs_file}") # Mute for less clutter
        except Exception as e:
            print(f"PXOS FS Error: Failed to save file system to {self.fs_file}: {e}")

    def _get_current_dir_node(self):
        """Returns the dictionary node for the current working directory."""
        node = self.fs_data
        for part in self.current_path:
            if part not in node:
                return None # Should not happen if current_path is always valid
            node = node[part]
        return node

    def _get_node_by_path(self, path_list, create_if_missing=False, is_dir=False):
        """Navigates the file system tree and returns the target node."""
        node = self.fs_data
        for i, part in enumerate(path_list):
            if part not in node:
                if create_if_missing and i == len(path_list) - 1 and is_dir:
                    node[part] = {'dirs': {}, 'files': {}}
                elif create_if_missing and i == len(path_list) - 1 and not is_dir:
                    # For files, the parent directory must exist
                    return None # Indicate parent doesn't exist for file creation
                else:
                    return None # Path does not exist
            node = node[part]
        return node

    def _resolve_path(self, path):
        """Resolves a relative or absolute path to an absolute list of components."""
        if path.startswith('/'):
            parts = ['root'] + [p for p in path.strip('/').split('/') if p]
        else:
            parts = list(self.current_path) # Start from current path
            for p in [p for p in path.split('/') if p]:
                if p == '..':
                    if len(parts) > 1: # Cannot go above 'root'
                        parts.pop()
                elif p == '.':
                    pass
                else:
                    parts.append(p)
        return parts

    def mkdir(self, path):
        """Creates a new directory."""
        abs_path_parts = self._resolve_path(path)
        parent_path_parts = abs_path_parts[:-1]
        dir_name = abs_path_parts[-1]

        parent_node = self._get_node_by_path(parent_path_parts)
        if parent_node is None:
            print(f"PXOS FS Error: Parent directory '{'/'.join(parent_path_parts)}' does not exist.")
            return False
        if dir_name in parent_node.get("dirs", {}):
            print(f"PXOS FS Error: Directory '{path}' already exists.")
            return False
        
        parent_node.get("dirs", {})[dir_name] = {'dirs': {}, 'files': {}}
        self.save_fs()
        print(f"PXOS FS> Directory '{path}' created.")
        return True

    def cd(self, path):
        """Changes the current working directory."""
        if path == '':
            self.current_path = ['root']
            print(f"PXOS FS> Changed directory to {self.pwd()}")
            return True

        target_path_parts = self._resolve_path(path)
        target_node = self._get_node_by_path(target_path_parts)

        if target_node is None or 'dirs' not in target_node: # Must be a directory
            print(f"PXOS FS Error: Directory '{path}' not found.")
            return False
        
        self.current_path = target_path_parts
        print(f"PXOS FS> Changed directory to {self.pwd()}")
        return True

    def pwd(self):
        """Returns the current working directory as a string."""
        return '/' + '/'.join(self.current_path[1:]) # Skip 'root' for display

    def ls(self, path=''):
        """Lists contents of a directory."""
        target_path_parts = self._resolve_path(path) if path else self.current_path
        target_node = self._get_node_by_path(target_path_parts)

        if target_node is None or 'dirs' not in target_node:
            print(f"PXOS FS Error: Directory '{path if path else self.pwd()}' not found.")
            return "" # Return empty string for error in ls

        output = f"\n--- Contents of {self.pwd() if not path else path} ---\n"
        
        # List directories first
        dirs_list = sorted(target_node.get("dirs", {}).keys())
        for dir_name in dirs_list:
            output += f"  [DIR] {dir_name}/\n"
        
        # Then list files
        files_list = sorted(target_node.get("files", {}).keys())
        for file_name in files_list:
            output += f"  [FILE] {file_name}\n"
        
        output += "----------------------------------"
        return output

    def touch(self, path):
        """Creates an empty file at the given path."""
        abs_path_parts = self._resolve_path(path)
        if not abs_path_parts or len(abs_path_parts) == 1 and abs_path_parts[0] == 'root': # Cannot touch root
            print("PXOS FS Error: Invalid file path.")
            return False

        file_name = abs_path_parts[-1]
        parent_path_parts = abs_path_parts[:-1]
        parent_node = self._get_node_by_path(parent_path_parts)

        if parent_node is None or 'files' not in parent_node:
            print(f"PXOS FS Error: Parent directory '{'/'.join(parent_path_parts)}' does not exist.")
            return False
        
        if file_name in parent_node.get("files", {}):
            print(f"PXOS FS Warning: File '{path}' already exists. Touching updates timestamp (simulated).")
        
        parent_node.get("files", {})[file_name] = "" # Empty content
        self.save_fs()
        print(f"PXOS FS> File '{path}' created/updated.")
        return True

    def cat(self, path):
        """Displays content of a file."""
        abs_path_parts = self._resolve_path(path)
        if not abs_path_parts or len(abs_path_parts) == 1 and abs_path_parts[0] == 'root':
            return "PXOS FS Error: Invalid file path."

        file_name = abs_path_parts[-1]
        parent_path_parts = abs_path_parts[:-1]
        parent_node = self._get_node_by_path(parent_path_parts)

        if parent_node is None or file_name not in parent_node.get("files", {}):
            return f"PXOS FS Error: File '{path}' not found."
        
        content = parent_node.get("files", {})[file_name]
        return f"--- Content of {path} ---\n{content}\n--------------------------"

    def write(self, path, content, append=False):
        """Writes content to a file. Creates file if it doesn't exist."""
        abs_path_parts = self._resolve_path(path)
        if not abs_path_parts or len(abs_path_parts) == 1 and abs_path_parts[0] == 'root':
            print("PXOS FS Error: Invalid file path.")
            return False

        file_name = abs_path_parts[-1]
        parent_path_parts = abs_path_parts[:-1]
        parent_node = self._get_node_by_path(parent_path_parts)

        if parent_node is None or 'files' not in parent_node:
            print(f"PXOS FS Error: Parent directory '{'/'.join(parent_path_parts)}' does not exist.")
            return False
        
        if file_name not in parent_node.get("files", {}):
            print(f"PXOS FS> Creating new file '{path}' for writing.")
            parent_node.get("files", {})[file_name] = ""
        
        if append:
            parent_node.get("files", {})[file_name] += content
            print(f"PXOS FS> Appended content to '{path}'.")
        else:
            parent_node.get("files", {})[file_name] = content
            print(f"PXOS FS> Wrote content to '{path}'.")
        
        self.save_fs()
        return True

    def rm(self, path):
        """Removes a file or an empty directory."""
        abs_path_parts = self._resolve_path(path)
        if not abs_path_parts or len(abs_path_parts) == 1 and abs_path_parts[0] == 'root': # Cannot remove root
            print("PXOS FS Error: Cannot remove root directory.")
            return False

        item_name = abs_path_parts[-1]
        parent_path_parts = abs_path_parts[:-1]
        parent_node = self._get_node_by_path(parent_path_parts)

        if parent_node is None:
            print(f"PXOS FS Error: Path '{path}' not found.")
            return False

        # Check if it's a directory
        if item_name in parent_node.get("dirs", {}):
            target_dir_node = parent_node["dirs"][item_name]
            if not target_dir_node.get("dirs", {}).empty() or not target_dir_node.get("files", {}).empty():
                print(f"PXOS FS Error: Directory '{path}' is not empty.")
                return False
            else:
                del parent_node["dirs"][item_name]
                self.save_fs()
                print(f"PXOS FS> Directory '{path}' removed.")
                return True
        
        # Check if it's a file
        if item_name in parent_node.get("files", {}):
            del parent_node["files"][item_name]
            self.save_fs()
            print(f"PXOS FS> File '{path}' removed.")
            return True
        
        print(f"PXOS FS Error: Item '{path}' not found or is a non-empty directory.")
        return False

    def get_file_content(self, path_parts):
        """Retrieves file content from PXFS based on path parts."""
        node = self.fs_data
        for i, part in enumerate(path_parts):
            if i == len(path_parts) - 1: # Last part is the file name
                # Ensure we are looking in the 'files' dictionary of the parent
                if "files" in node:
                    return node["files"].get(part)
                else:
                    return None # Parent is not a directory with files
            else: # Navigate through directories
                node = node.get("dirs", {}).get(part, {})
                if not node:
                    return None # Path not found
        return None


# PXOS AI with Training Capabilities (Python Port)
class PXOSTrainingBot:
    def __init__(self, fs_file=PXOS_FS_FILE):
        self.intelligence = 75
        self.knowledge_points = 0
        self.training_files = [] # This will still hold detailed info about trained files
        self.conversation_history = []
        self.is_thinking = False
        self.current_phase = 'READY'
        self.pxram_viewer_visible = False # State for PXRAM viewer toggle
        self.pxfs = PXOSFileSystem(fs_file) # Initialize PXFS
        
        # Initialize the training system and display initial message
        self._initialize_training()

    def _initialize_training(self):
        """Initializes the training system and prints the welcome message."""
        print("🎓 PXOS Training System initialized (Python version)")
        self._print_initial_welcome_message()

    def _print_initial_welcome_message(self):
        """Prints the initial welcome message for the PXOS AI."""
        print(f"""
🚀 PXOS AI with Training Hub initialized! I can now learn from any file type you simulate uploading:

📄 Documents: PDF, DOC, TXT, MD for knowledge extraction
💻 Code Files: JS, PY, HTML, CSS, JSON for pattern learning
🖼️ Images: PNG, JPG for visual analysis and memory storage
📊 Data: CSV, XLS, JSON for data pattern recognition
🎵 Media: Audio/video files for content analysis

Type 'help' for commands.
""")

    def handle_files(self, real_file_paths):
        """Processes a list of real file paths for training and copies to PXFS."""
        for real_file_path in real_file_paths:
            self._process_real_file_for_training(real_file_path)
        self._update_training_stats()

    def _process_real_file_for_training(self, real_file_path):
        """Processes a single real file for training, extracts knowledge, and copies to PXFS."""
        if not os.path.exists(real_file_path):
            print(f"PXOS Error: Real file '{real_file_path}' not found on host system.")
            return

        file_name = os.path.basename(real_file_path)
        file_ext = os.path.splitext(file_name)[1].lstrip('.').lower()
        file_size = os.path.getsize(real_file_path)

        file_content = None
        content_preview = None
        knowledge_extracted = 0

        try:
            if file_ext in ['txt', 'md', 'js', 'py', 'html', 'css', 'json', 'gd']: # Added 'gd' for Godot scripts
                with open(real_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read() # Read full content for PXFS
                    content_preview = file_content[:1024] # Preview for training data
                if file_ext in ['txt', 'md']:
                    knowledge_extracted = self._extract_text_knowledge(file_content)
                else: # Includes 'gd' scripts now
                    knowledge_extracted = self._extract_code_knowledge(file_content, file_ext)
            elif file_ext in ['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx']:
                with open(real_file_path, 'rb') as f:
                    file_content_bytes = f.read()
                    if file_size < 1024 * 1024: # Less than 1MB
                        file_content = base64.b64encode(file_content_bytes).decode('utf-8')
                        content_preview = f"Base64 encoded binary data ({file_size} bytes)"
                    else:
                        file_content = f"BINARY_DATA_TOO_LARGE_FOR_INLINE_STORAGE_({file_size}_bytes)"
                        content_preview = f"Binary data ({file_size} bytes)"

                if file_ext in ['png', 'jpg', 'jpeg']:
                    knowledge_extracted = self._extract_image_knowledge(file_size)
                else: # pdf, doc, docx
                    knowledge_extracted = self._extract_document_knowledge(file_size)
            else:
                with open(real_file_path, 'rb') as f:
                    file_content_bytes = f.read()
                    if file_size < 1024 * 1024: # Less than 1MB
                        file_content = base64.b64encode(file_content_bytes).decode('utf-8')
                        content_preview = f"Base64 encoded generic data ({file_size} bytes)"
                    else:
                        file_content = f"BINARY_DATA_TOO_LARGE_FOR_INLINE_STORAGE_({file_size}_bytes)"
                        content_preview = f"Generic binary data ({file_size} bytes)"
                knowledge_extracted = 5 # Base knowledge for any file

            # Add to training_files list
            file_info = {
                'name': file_name,
                'path': real_file_path, # Original host path
                'size': file_size,
                'type': file_ext,
                'extension': file_ext,
                'content_preview': content_preview,
                'processed': True,
                'knowledge_extracted': knowledge_extracted,
                'timestamp': os.path.getmtime(real_file_path)
            }
            self.training_files.append(file_info)
            self.knowledge_points += knowledge_extracted
            self.intelligence = min(100, self.intelligence + knowledge_extracted // 10)
            print(f"PXOS> 📚 Learned from {file_name}: +{knowledge_extracted} knowledge points")

            # Also copy the file content into PXFS
            pxfs_path = self.pxfs.pwd() + '/' + file_name # Save to current PXFS directory
            self.pxfs.write(pxfs_path, file_content, append=False)
            print(f"PXOS FS> Copied '{file_name}' to PXFS at '{pxfs_path}'.")

        except Exception as e:
            print(f"PXOS Error: Failed to process real file {real_file_path}: {e}")
            
    def _extract_text_knowledge(self, content):
        """Simulates knowledge extraction from text content."""
        words = len(content.split())
        lines = content.count('\n') + 1
        return min(50, words // 10 + lines)

    def _extract_code_knowledge(self, content, language):
        """Simulates knowledge extraction from code content."""
        lines = content.count('\n') + 1
        functions = content.count('func ') + content.count('def ') + content.count('class ') # Simple count
        return min(100, lines + (functions * 5))

    def _extract_image_knowledge(self, size):
        """Simulates knowledge extraction from image size."""
        return min(30, size // 10000)

    def _extract_document_knowledge(self, size):
        """Simulates knowledge extraction from document size."""
        return min(75, size // 1000)

    def _update_training_stats(self):
        """Prints current training statistics."""
        print(f"\n--- PXOS Training Status ---")
        print(f"Files Processed: {len(self.training_files)}")
        print(f"Knowledge Extracted: {self.knowledge_points} points")
        print(f"Intelligence Level: {self.intelligence}%")
        print(f"--------------------------\n")

    def process_command(self, user_input):
        """Processes user commands in the terminal."""
        self.conversation_history.append({'role': 'user', 'content': user_input, 'timestamp': time.time()})
        lower_input = user_input.lower().strip()
        command_parts = lower_input.split(maxsplit=1)
        command = command_parts[0]
        args = command_parts[1] if len(command_parts) > 1 else ''

        if command == 'clear':
            print("\n" * 50) # Simulate clearing by printing many newlines
            print("PXOS> Terminal cleared.")
        elif command == 'import':
            file_paths = [p.strip() for p in args.split(',') if p.strip()]
            if file_paths:
                self.handle_files(file_paths)
            else:
                print("PXOS> Usage: import <filepath1>[, <filepath2>, ...]")
        elif command == 'status' or lower_input == 'train status':
            print(self._handle_training_query())
        elif command == 'pxram' or lower_input == 'toggle pxram':
            self._toggle_pxram_viewer()
        elif command == 'analyze':
            self._analyze_file_command(args)
        elif command == 'remove':
            self._remove_file_command(args)
        elif command == 'ls':
            print(self.pxfs.ls(args)) # Print output from PXFS
        elif command == 'pwd':
            print(f"PXOS> Current directory: {self.pxfs.pwd()}")
        elif command == 'cd':
            self.pxfs.cd(args)
        elif command == 'mkdir':
            self.pxfs.mkdir(args)
        elif command == 'touch':
            self.pxfs.touch(args)
        elif command == 'cat':
            print(self.pxfs.cat(args)) # Print output from PXFS
        elif command == 'write':
            # For 'write' command, we need multi-line input
            print("PXOS> Enter content (end with 'EOF' on a new line):")
            content_lines = []
            while True:
                line = input("... ")
                if line.strip().upper() == 'EOF':
                    break
                content_lines.append(line)
            content_to_write = "\n".join(content_lines)
            self.pxfs.write(args, content_to_write)
        elif command == 'rm':
            self.pxfs.rm(args)
        elif command == 'export_pxseed':
            # This command is for Godot side to export, but we can simulate here
            print("PXOS> 'export_pxseed' command is primarily for Godot environment to create PNG.")
            print("PXOS> You can export the current PXFS to JSON using 'export fs json'.")
        elif command == 'export': # New command to export current PXFS to JSON
            if args == 'fs json':
                self.export_fs_to_json(PXOS_GODOT_EXPORT_FILE)
            else:
                print("PXOS> Usage: export fs json")
        elif command == 'import':
            if args.startswith('godot fs'):
                self.import_godot_fs_from_json(PXOS_GODOT_EXPORT_FILE)
            else: # Original import for host files
                file_paths = [p.strip() for p in args.split(',') if p.strip()]
                if file_paths:
                    self.handle_files(file_paths)
                else:
                    print("PXOS> Usage: import <filepath1>[, <filepath2>, ...]")
        elif command == 'extract':
            if args == 'pxlogic':
                self.extract_pxos_logic_from_fs(PXOS_CORE_EXTRACTED_FILE)
            else:
                print("PXOS> Usage: extract pxlogic")
        elif command == 'translate': # New command to translate extracted GDScript to Python
            if args == 'gd to py':
                self.translate_gd_to_py(PXOS_CORE_EXTRACTED_FILE, PXOS_CORE_TRANSLATED_PY_FILE)
            else:
                print("PXOS> Usage: translate gd to py")
        # --- AI-specific commands ---
        elif command == 'generate_code':
            print(self._generate_code_response(args))
        # --- Doctrine/Ethical commands (future expansion) ---
        elif command == 'doctrine':
            print(self._get_doctrine_text())
        # --- Default/Unknown Command ---
        elif command == 'help':
            self._display_help()
        else:
            # Default AI response based on training
            relevant_files = self._find_relevant_files(user_input)
            response = self._generate_intelligent_response(user_input, relevant_files)
            print(f"PXOS> {response}")

    # Always emit status after a command, as internal state might change
    # (In Python, we just print, no signals)
    # pxos_status_changed.emit(intelligence, knowledge_points, training_files_count)


# --- AI Response Generation (Conceptual) ---

    def _handle_training_query(self):
        """Generates a detailed training status report."""
        recent_files_summary = "\n".join([
            f"• {f['name']} (+{f['knowledge_extracted']} pts)" for f in self.training_files[-3:]
        ])
        return f"""
🎓 **Training System Status**

**Files Processed**: {len(self.training_files)} files
**Knowledge Extracted**: {self.knowledge_points} points
**Intelligence Level**: {self.intelligence}% (+{self.intelligence - 75}% from base)

**Recent Training Data**:
{recent_files_summary if recent_files_summary else "No recent files."}

**Training Capabilities**:
• Code Analysis: Learn programming patterns from JS, Python, HTML, CSS, GDScript
• Document Processing: Extract knowledge from PDFs, text files, markdown
• Image Understanding: Process PNG/JPG for visual pattern recognition
• Data Learning: Analyze CSV, JSON for data structure patterns

Upload more files using 'import <filepath>' to increase my intelligence and capabilities!
"""

    def _find_relevant_files(self, input_text):
        """Finds files in the training data relevant to the input text."""
        input_words = input_text.lower().split()
        relevant = []
        for file in self.training_files:
            file_name_lower = file['name'].lower()
            file_ext_lower = file['extension'].lower()
            
            # Check if any input word is in file name or extension
            if any(word in file_name_lower or word in file_ext_lower for word in input_words):
                relevant.append(file)
            # Check if any input word is in content preview (if available and text-based)
            elif file['content_preview'] and isinstance(file['content_preview'], str) and \
                 any(word in file['content_preview'].lower() for word in input_words):
                relevant.append(file)
        return relevant

    def _generate_intelligent_response(self, user_input, relevant_files):
        """Generates an AI response based on current intelligence and relevant files."""
        training_context = (
            f"Using knowledge from {len(relevant_files)} relevant files in my training data"
            if relevant_files
            else f"Drawing from {len(self.training_files)} files in my knowledge base"
        )
        return f"""
🧠 **Training-Enhanced Response**

**{training_context}**
**Intelligence Level**: {self.intelligence}% (enhanced by uploaded files)
**Knowledge Points**: {self.knowledge_points} accumulated

I can help you with questions related to the files you've uploaded.
What specific information do you need from my training data?
"""

    def _toggle_pxram_viewer(self):
        """Toggles the visibility of the simulated PXRAM viewer."""
        self.pxram_viewer_visible = not self.pxram_viewer_visible
        status = "VISIBLE" if self.pxram_viewer_visible else "HIDDEN"
        print(f"PXOS> PXRAM Viewer is now: {status}")
        if self.pxram_viewer_visible:
            self._display_pxram_content()

    def _display_pxram_content(self):
        """Simulates displaying PXRAM content."""
        print("\n--- PXRAM Viewer ---")
        if not self.training_files:
            print("No data in PXRAM. Upload files to see content.")
            print("--------------------")
            return

        print("Simulated Memory Blocks (based on recent training data):")
        for i, file in enumerate(self.training_files[-5:]): # Show last 5 files
            print(f"  Block {i+1}: {file['name']} (Size: {self._format_file_size(file['size'])}, Knowledge: {file['knowledge_extracted']} pts)")
            if file['content_preview']:
                preview_line = file['content_preview'].replace('\n', ' ').replace('\r', '')
                print(f"    Preview: {preview_line[:70]}...")
        print("--------------------")

    def _analyze_file_command(self, file_name_to_analyze):
        """Analyzes a specific file from the training data."""
        found_file = None
        for file in self.training_files:
            if file['name'].lower() == file_name_to_analyze.lower():
                found_file = file
                break
        
        if found_file:
            print(f"PXOS> 📊 **File Analysis: {found_file['name']}**\n")
            print(f"**Type**: {found_file['extension'].upper()}")
            print(f"**Size**: {self._format_file_size(found_file['size'])}")
            print(f"**Knowledge Extracted**: {found_file['knowledge_extracted']} points")
            print(f"**Processing Status**: {'Successfully processed' if found_file['processed'] else 'Processing failed'}")
            print(f"**Content Preview**: {found_file['content_preview'][:200] + '...' if found_file['content_preview'] else 'N/A'}\n")
            print("This file contributed to my learning and improved my capabilities!")
        else:
            print(f"PXOS> File '{file_name_to_analyze}' not found in training data.")

    def _remove_file_command(self, file_name_to_remove):
        """Removes a file from the training data."""
        initial_count = len(self.training_files)
        self.training_files = [f for f in self.training_files if f['name'].lower() != file_name_to_remove.lower()]
        
        if len(self.training_files) < initial_count:
            # Recalculate knowledge points after removal
            self.knowledge_points = sum(f['knowledge_extracted'] for f in self.training_files)
            self.intelligence = min(100, 75 + self.knowledge_points // 10) # Base + derived
            print(f"PXOS> 🗑️ Removed {file_name_to_remove} from training data.")
            self._update_training_stats()
        else:
            print(f"PXOS> File '{file_name_to_remove}' not found in training data.")

    def _list_training_files(self):
        """Lists all files in the training data."""
        if not self.training_files:
            print("PXOS> No files in training data. Use 'import <filepath>' to add some.")
            return
        
        print("\n--- PXOS Trained Files ---")
        for i, file in enumerate(self.training_files):
            print(f"{i+1}. {file['name']} ({self._format_file_size(file['size'])}) - {file['knowledge_extracted']} pts")
        print("--------------------------")

    def _format_file_size(self, bytes_val):
        """Formats file size for human readability."""
        if bytes_val == 0: return '0 B'
        k = 1024
        sizes = ['B', 'KB', 'MB', 'GB']
        i = (bytes_val.bit_length() // 10) # More robust log base 2
        return f"{bytes_val / (k ** i):.1f} {sizes[i]}"

    def _display_help(self):
        """Displays available commands."""
        print("""
--- PXOS Commands ---
clear          : Clears the terminal screen.
import <path>  : Imports a real file from your host system for AI training and copies to PXFS.
status         : Shows PXOS AI training and intelligence status.
pxram          : Toggles the PXRAM viewer to see simulated memory content.
ls [path]      : Lists contents of current directory or specified path in PXFS.
pwd            : Prints the current working directory in PXFS.
cd <path>      : Changes the current working directory in PXFS.
mkdir <name>   : Creates a new directory in PXFS.
touch <name>   : Creates an empty file in PXFS.
cat <path>     : Displays content of a file in PXFS.
write <path>   : Writes content to a file in PXFS. Prompts for multi-line input.
rm <path>      : Removes a file or empty directory from PXFS.
analyze <name> : Shows detailed analysis of a trained file by name.
remove <name>  : Removes a file from AI training data.
export fs json : Exports the current PXFS state to a JSON file (pxos_godot_export.json).
import godot fs: Imports PXFS state from a Godot-exported JSON file (pxos_godot_export.json).
extract pxlogic: Extracts PXOSCore.gd from PXFS and saves it locally.
translate gd to py: Translates PXOSCore_extracted.gd to Python.
generate_code <prompt>: AI generates code based on prompt (conceptual).
doctrine       : Displays core ethical directives.
help           : Displays this help message.
exit           : Shuts down the PXOS terminal.
---------------------
""")

    # New functions for Godot sync
    def export_fs_to_json(self, json_path=PXOS_GODOT_EXPORT_FILE):
        """Exports the current PXFS data to a JSON file."""
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.pxfs.fs_data, f, indent=4)
            print(f"PXOS> Current PXFS exported to '{json_path}'.")
            print("PXOS> Copy this file to your Godot project's 'user://' folder to import it there.")
        except Exception as e:
            print(f"PXOS FS Error: Failed to export PXFS to '{json_path}': {e}")

    def import_godot_fs_from_json(self, json_path=PXOS_GODOT_EXPORT_FILE):
        """Imports PXFS data from a Godot-exported JSON file."""
        if not os.path.exists(json_path):
            print(f"PXOS FS Error: File '{json_path}' not found. Please ensure it's in the same directory.")
            return False
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                godot_fs = json.load(f)
            self.pxfs.fs_data = godot_fs # Replace internal PXFS with this
            self.pxfs.current_path = ['root'] # Reset CWD to root after import
            self.pxfs._ensure_files_key(self.pxfs.fs_data) # Ensure new FS is structured correctly
            print("PXOS> Successfully imported FS from Godot JSON.")
            self.pxfs.save_fs() # Save the newly imported FS
            return True
        except json.JSONDecodeError:
            print(f"PXOS FS Error: Invalid JSON format in '{json_path}'.")
            return False
        except Exception as e:
            print(f"PXOS FS Error: Could not import Godot FS - {e}")
            return False

    def extract_pxos_logic_from_fs(self, target_filename=PXOS_CORE_EXTRACTED_FILE):
        """
        Extracts the content of PXOSCore.gd from the PXFS and saves it to a local file.
        This allows you to get the latest Godot-developed logic from your PXOS FS.
        """
        # Define common paths where PXOSCore.gd might be stored in PXFS
        known_paths = [
            ["root", "apps", "PXOSCore.gd"], # Example: if stored in /apps
            ["root", "users", "admin", "PXOSCore.gd"], # Example: if stored in /users/admin
            ["root", "system", "PXOSCore.gd"], # Example: if stored in /system
            ["root", "PXOSCore.gd"] # Example: if stored at root
        ]
        
        found_content = None
        for path_parts in known_paths:
            # Need to resolve path parts to get content from PXFS
            content = self.pxfs.get_file_content(path_parts)
            if content is not None:
                found_content = content
                break
        
        if found_content is not None:
            try:
                with open(target_filename, "w", encoding="utf-8") as f:
                    f.write(found_content)
                print(f"PXOS> PXOSCore logic extracted and saved to '{target_filename}'.")
                print("PXOS> You can now inspect or use this GDScript file.")
                return True
            except Exception as e:
                print(f"PXOS Error: Failed to save extracted logic to '{target_filename}': {e}")
                return False
        else:
            print("PXOS> PXOSCore.gd not found in PXFS at common locations.")
            print("PXOS> Ensure you have imported/written PXOSCore.gd into your PXFS.")
            return False

    def translate_gd_to_py(self, gd_file_path=PXOS_CORE_EXTRACTED_FILE, py_file_path=PXOS_CORE_TRANSLATED_PY_FILE):
        """
        Translates a GDScript file (like PXOSCore_extracted.gd) into a Python file.
        This is a simplified translation and may not cover all GDScript nuances.
        """
        if not os.path.exists(gd_file_path):
            print(f"PXOS Error: GDScript file '{gd_file_path}' not found for translation.")
            return False
        
        try:
            with open(gd_file_path, 'r', encoding='utf-8') as f:
                gdscript_content = f.read()

            python_content = []
            # Basic GDScript to Python translation rules
            # This is a simplified translator and will need expansion for complex GDScript features.
            
            # Replace 'extends Node' with a base class or just remove if not needed for direct execution
            # Assuming 'extends Node' means it's a class.
            gdscript_content = re.sub(r'extends\s+(\w+)', r'# extends \1 (GDScript specific)', gdscript_content)
            
            # class_name PXOSCore -> class PXOSCore:
            gdscript_content = re.sub(r'class_name\s+(\w+)', r'class \1:', gdscript_content)

            # var variable_name: Type = value -> variable_name = value
            gdscript_content = re.sub(r'var\s+([\w_]+)(?::\s*\w+)?\s*=\s*(.+)', r'\1 = \2', gdscript_content)
            gdscript_content = re.sub(r'var\s+([\w_]+)(?::\s*\w+)?', r'\1 = None # GDScript var without initial value', gdscript_content)


            # func _ready(): -> def _ready(self):
            gdscript_content = re.sub(r'func\s+([\w_]+)\((.*?)\):', r'def \1(self, \2):', gdscript_content)
            
            # print() -> print() (already similar)
            # gdscript_content = gdscript_content.replace('print(', 'print(')

            # @onready var -> # @onready var (Godot specific)
            gdscript_content = re.sub(r'@onready\s+var\s+', r'# @onready var (Godot specific) ', gdscript_content)

            # Signals: These are Godot-specific and need careful handling or removal
            gdscript_content = re.sub(r'signal\s+([\w_]+.*)', r'# signal \1 (GDScript specific)', gdscript_content)
            gdscript_content = re.sub(r'\.emit\(', '.emit(', gdscript_content) # Keep emit for now, might be custom

            # Match statements: Convert to if/elif/else
            # This is complex and a full parser would be needed for perfect conversion.
            # For now, a simple placeholder or comment.
            if "match " in gdscript_content:
                print("PXOS Warning: 'match' statements in GDScript are complex to translate to Python 'if/elif/else' automatically. Manual review needed.")
                gdscript_content = re.sub(r'match\s+(.+):', r'# GDScript match \1: (Manual Python conversion needed)', gdscript_content)

            # GDScript-specific global functions/constants (e.g., OK, ProjectSettings, FileAccess)
            gdscript_content = gdscript_content.replace('OK', '0') # OK is 0 in Godot
            gdscript_content = gdscript_content.replace('ProjectSettings.globalize_path(', 'os.path.abspath(') # Basic path conversion
            gdscript_content = gdscript_content.replace('FileAccess.open(', 'open(') # Basic file open
            gdscript_content = gdscript_content.replace('FileAccess.READ', "'r'")
            gdscript_content = gdscript_content.replace('FileAccess.WRITE', "'w'")
            gdscript_content = gdscript_content.replace('file.get_as_text()', 'file.read()')
            gdscript_content = gdscript_content.replace('file.store_string(', 'file.write(')
            gdscript_content = gdscript_content.replace('file.close()', 'file.close()')
            gdscript_content = gdscript_content.replace('JSON.stringify(', 'json.dumps(')
            gdscript_content = gdscript_content.replace('to_json(', 'json.dumps(') # For to_json GDScript function
            gdscript_content = gdscript_content.replace('str(', 'str(') # Already similar

            # PoolColorArray, Image, ImageTexture are Godot specific - comment out or replace with placeholders
            gdscript_content = re.sub(r'(var\s+\w+\s*=\s*)?PoolColorArray\(\)', r'# \1PoolColorArray() (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'(var\s+\w+\s*=\s*)?Image\.new\(\)', r'# \1Image.new() (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'(var\s+\w+\s*=\s*)?ImageTexture\.new\(\)', r'# \1ImageTexture.new() (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'image\.create\(.*\)', r'# image.create(...) (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'image\.set_pixel\(.*\)', r'# image.set_pixel(...) (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'image_texture\.create_from_image\(.*\)', r'# image_texture.create_from_image(...) (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'image\.save_png\(.*\)', r'# image.save_png(...) (Godot specific)', gdscript_content)
            gdscript_content = re.sub(r'Color\(.*\)', r'# Color(...) (Godot specific)', gdscript_content)
            
            # Dictionary access: .get("key", {}) -> .get("key", {}) (similar)
            # Array methods: .size() -> len()
            gdscript_content = re.sub(r'\.size\(\)', '.size', gdscript_content) # Will replace later with len()

            # Python-specific adjustments (e.g., self.pxfs.get_file_content(path_parts) needs to be direct access)
            # This is a deep integration point, so we'll assume the PXOSCore.gd is designed to call
            # methods on a 'px_file_system' object, which needs to be passed or accessed.
            # For basic translation, we'll just keep the call as is, assuming the Python context
            # will provide a similar 'px_file_system' object.

            # Indentation: GDScript uses tabs, Python uses spaces (usually 4).
            # This is a simple tab-to-space conversion.
            python_content_lines = []
            for line in gdscript_content.splitlines():
                leading_tabs = 0
                for char in line:
                    if char == '\t':
                        leading_tabs += 1
                    else:
                        break
                python_content_lines.append("    " * leading_tabs + line.lstrip('\t'))
            
            # Final Python-specific fixes
            final_python_content = "\n".join(python_content_lines)
            final_python_content = final_python_content.replace(".size", "") # Fix .size() to len()
            final_python_content = re.sub(r'(\w+)\.empty\(\)', r'not \1', final_python_content) # .empty() -> not
            final_python_content = re.sub(r'(\w+)\.back\(\)', r'\1[-1]', final_python_content) # .back() -> [-1]
            final_python_content = re.sub(r'(\w+)\.strip_prefix\("(.+?)"\)', r'\1.lstrip("\2")', final_python_content) # .strip_prefix()
            final_python_content = re.sub(r'(\w+)\.to_lower\(\)', r'\1.lower()', final_python_content) # .to_lower()
            final_python_content = re.sub(r'(\w+)\.strip_edges\(\)', r'\1.strip()', final_python_content) # .strip_edges()
            final_python_content = re.sub(r'\.split\("(.+?)",\s*false,\s*(\d+)\)', r'.split("\1", \2)', final_python_content) # split with limit
            final_python_content = re.sub(r'\.split\("(.+?)"\)', r'.split("\1")', final_python_content) # split
            final_python_content = re.sub(r'\.split\(\)', r'.split()', final_python_content) # split no args
            final_python_content = re.sub(r'range\((\w+)\.size\(\)\)', r'range(len(\1))', final_python_content) # range(array.size())
            final_python_content = re.sub(r'range\((\w+)\)', r'range(\1)', final_python_content) # range(int)
            final_python_content = re.sub(r'str\((\w+)\)', r'str(\1)', final_python_content) # str()
            final_python_content = re.sub(r'int\((\w+)\)', r'int(\1)', final_python_content) # int()
            final_python_content = re.sub(r'float\((\w+)\)', r'float(\1)', final_python_content) # float()
            final_python_content = re.sub(r'min\((\w+),\s*(\w+)\)', r'min(\1, \2)', final_python_content) # min()
            final_python_content = re.sub(r'max\((\w+),\s*(\w+)\)', r'max(\1, \2)', final_python_content) # max()
            final_python_content = re.sub(r'has_signal\("(\w+)"\)', r'# has_signal("\1") (Godot specific)', final_python_content)
            final_python_content = re.sub(r'connect\((\w+)\)', r'# connect(\1) (Godot specific)', final_python_content)
            final_python_content = re.sub(r'emit_signal\("(\w+)"\)', r'# emit_signal("\1") (Godot specific)', final_python_content)
            final_python_content = re.sub(r'\.get_node_or_null\(', '.get_node_or_null(', final_python_content) # Keep for now, needs context
            final_python_content = re.sub(r'typeof\((\w+)\)\s*==\s*TYPE_DICTIONARY', r'isinstance(\1, dict)', final_python_content) # typeof to isinstance
            final_python_content = re.sub(r'\.duplicate\(\)', '.copy()', final_python_content) # Array.duplicate() to list.copy()
            final_python_content = re.sub(r'\.slice\((\d+),\s*(\w+)\)', r'[\1:\2]', final_python_content) # Array.slice()
            final_python_content = re.sub(r'\.slice\((\d+)\)', r'[\1:]', final_python_content) # Array.slice() with one arg
            final_python_content = re.sub(r'\.pop_back\(\)', '.pop()', final_python_content) # Array.pop_back()
            final_python_content = re.sub(r'\.append\(', '.append(', final_python_content) # Array.append()
            final_python_content = re.sub(r'\.erase\(', '.pop(', final_python_content) # Array.erase() to list.pop()

            # Add necessary Python imports
            final_python_content = "import os\nimport json\nimport re\n\n" + final_python_content
            
            # Add a placeholder for a base class if 'extends Node' was removed
            final_python_content = re.sub(r'# extends Node \(GDScript specific\)', r'class BasePXOSComponent:', final_python_content, 1) # Add a base class
            final_python_content = final_python_content.replace("class PXOSCore:", "class PXOSCore(BasePXOSComponent):") # Make it inherit

            # Handle GDScript comments (semicolon)
            final_python_content = re.sub(r';\s*(.*)', r'# \1', final_python_content)

            with open(py_file_path, 'w', encoding='utf-8') as f:
                f.write(final_python_content)
            
            print(f"PXOS> GDScript from '{gd_file_path}' translated to Python and saved to '{py_file_path}'.")
            print("PXOS> Please review the translated file for accuracy, as automatic translation has limitations.")
            return True

        except Exception as e:
            print(f"PXOS Error: Failed to translate GDScript to Python: {e}")
            return False


# --- Main Terminal Loop ---
def run_pxos_terminal():
    """Main function to run the PXOS terminal."""
    pxos_bot = PXOSTrainingBot()
    
    # Simulate boot sequence
    print("PXOS Booting...")
    time.sleep(1.5) # Simulate boot delay
    print("PXOS Ready.")

    while True:
        try:
            user_input = input(f"PXOS:{pxos_bot.pxfs.pwd()}> ").strip() # Show current PXFS path in prompt
            if user_input.lower() == 'exit':
                print("PXOS> Shutting down. Goodbye.")
                pxos_bot.pxfs.save_fs() # Ensure FS is saved on exit
                break
            
            pxos_bot.process_command(user_input)
            pxos_bot.pxfs.save_fs() # Save FS after each command
        except KeyboardInterrupt:
            print("\nPXOS> Interrupted. Shutting down.")
            pxos_bot.pxfs.save_fs() # Ensure FS is saved on interrupt
            break
        except Exception as e:
            print(f"PXOS Error: An unexpected error occurred: {e}")
            pxos_bot.pxfs.save_fs() # Attempt to save FS even on error

if __name__ == "__main__":
    run_pxos_terminal()
