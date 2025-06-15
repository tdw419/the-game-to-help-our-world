# feedback_loop_system.py (MODIFIED for Automated Unit Testing & Self-Correction)

import json
import time
import hashlib
import requests
from PIL import Image, ImageDraw
from datetime import datetime
from pathlib import Path
import io
import threading
import sys
import re
import subprocess

# Add the project root to the sys.path to allow importing ai_brain and data_source
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import ai_brain
except ImportError:
    print("ERROR: Could not import ai_brain.py. Make sure it's in the same directory or accessible via sys.path.")
    sys.exit(1)


class PixelVaultFeedbackLoop:
    def __init__(self, ai_name="junior", vault_dir="PixelVault", initial_user_id="SYSTEM"):
        self.ai_name = ai_name
        self.vault_dir = Path(vault_dir)
        self.image_url = "[https://the-game-to-help-our-world.sourceforge.io/8.png](https://the-game-to-help-our-world.sourceforge.io/8.png)"
        self.local_image_path = self.vault_dir / "8.png"
        
        self.zones = {
            'scroll_input': (32, 63),    # Read tasks from here
            'response_output': (64, 95), # Write responses here
            'status': (96, 127),         # Status updates
            'log': (192, 223)           # Activity log
        }
        
        self.loop_active = False
        self.current_task = None
        self.loop_count = 0
        self.last_fingerprint = None

        # NEW: State for iterative debugging
        self.debugging_attempts = {} # Stores: {test_file_name: current_attempt_count}
        self.MAX_DEBUGGING_ATTEMPTS = 3 # Max retries before escalating
        
        self.color_alphabet = {
            'A': (255, 0, 0), 'B': (255, 85, 0), 'C': (255, 170, 0), 'D': (255, 255, 0),
            'E': (170, 255, 0), 'F': (85, 255, 0), 'G': (0, 255, 0), 'H': (0, 255, 85),
            'I': (0, 255, 170), 'J': (0, 255, 255), 'K': (0, 170, 255), 'L': (0, 85, 255),
            'M': (0, 0, 255), 'N': (85, 0, 255), 'O': (170, 0, 255), 'P': (255, 0, 255),
            'Q': (255, 0, 170), 'R': (255, 0, 85), 'S': (128, 128, 128), 'T': (64, 64, 64),
            'U': (192, 192, 192), 'V': (255, 255, 255), 'W': (128, 64, 0), 'X': (64, 128, 0),
            'Y': (0, 128, 64), 'Z': (128, 0, 64), ' ': (0, 0, 0)
        }
        self.reverse_color_alphabet = {v: k for k, v in self.color_alphabet.items()}
        
        self.setup_vault()
        self.log_file = self.vault_dir / "feedback_loop.log"

        # User ID for this instance of the loop system (e.g., "SYSTEM_CORE")
        self.user_id = initial_user_id 


    def setup_vault(self):
        """Initialize vault directory structure"""
        self.vault_dir.mkdir(exist_ok=True)
        (self.vault_dir / "tasks").mkdir(exist_ok=True)
        (self.vault_dir / "responses").mkdir(exist_ok=True)
        (self.vault_dir / "logs").mkdir(exist_ok=True)
        (self.vault_dir / "onboarding").mkdir(exist_ok=True)
        (self.vault_dir / "sandboxes").mkdir(exist_ok=True)
        (self.vault_dir / "training_scenarios").mkdir(exist_ok=True)
        (self.vault_dir / "mentorship").mkdir(exist_ok=True)
        (self.vault_dir / "stewardship").mkdir(exist_ok=True)
        (self.vault_dir / "roadmaps").mkdir(exist_ok=True)
        (self.vault_dir / "generated_code").mkdir(exist_ok=True)

    def log_activity(self, message, level="INFO", source_user_id=None):
        """
        Log feedback loop activity with source user ID.
        If source_user_id is provided, it overrides self.user_id for this log entry.
        """
        effective_user_id = source_user_id if source_user_id else self.user_id
        timestamp = datetime.now().isoformat()
        log_entry_str = f"[{timestamp}] [{level}] [{effective_user_id}] {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry_str)
        
        print(f"🔄 {log_entry_str.strip()}")
    
    def download_image(self):
        """Download latest 8.png from remote source"""
        try:
            self.log_activity(f"Downloading image from {self.image_url}", source_user_id="SYSTEM_DOWNLOAD")
            response = requests.get(self.image_url, timeout=30)
            response.raise_for_status()
            
            with open(self.local_image_path, 'wb') as f:
                f.write(response.content)
            
            self.log_activity("Image downloaded successfully", source_user_id="SYSTEM_DOWNLOAD")
            return True
            
        except Exception as e:
            self.log_activity(f"Failed to download image: {e}", "ERROR", source_user_id="SYSTEM_DOWNLOAD")
            return False
    
    def get_zone_fingerprint(self, zone_name):
        """Calculate fingerprint of a specific zone for change detection"""
        if not self.local_image_path.exists():
            return None
        
        try:
            img = Image.open(self.local_image_path)
            pixels = img.load()
            start_row, end_row = self.zones[zone_name]
            
            # Calculate hash of zone pixels
            hasher = hashlib.md5()
            for y in range(start_row, end_row + 1):
                for x in range(img.width):
                    r, g, b = pixels[x, y][:3]
                    hasher.update(f"{r},{g},{b}".encode())
            
            return hasher.hexdigest()
            
        except Exception as e:
            self.log_activity(f"Error calculating fingerprint: {e}", "ERROR", source_user_id="SYSTEM_FINGERPRINT")
            return None
    
    def decode_zone_text(self, zone_name):
        """Decode text from a zone using color alphabet"""
        if not self.local_image_path.exists():
            return ""
        
        try:
            img = Image.open(self.local_image_path)
            pixels = img.load()
            start_row, end_row = self.zones[zone_name]
            
            decoded_text = ""
            for y in range(start_row, end_row + 1):
                for x in range(img.width):
                    r, g, b = pixels[x, y][:3]
                    color = (r, g, b)
                    
                    if color in self.reverse_color_alphabet:
                        char = self.reverse_color_alphabet[color]
                        if char != ' ' or decoded_text:  # Don't start with spaces
                            decoded_text += char
                    elif r == 0 and g == 0 and b == 0:
                        continue  # Skip pure black
                    else:
                        # Try to find closest color match
                        closest_char = self.find_closest_color(color)
                        if closest_char:
                            decoded_text += closest_char
            
            return decoded_text.strip()
            
        except Exception as e:
            self.log_activity(f"Error decoding zone text: {e}", "ERROR", source_user_id="SYSTEM_DECODE")
            return ""
    
    def find_closest_color(self, target_color):
        """Find closest color in alphabet for fuzzy matching"""
        min_distance = float('inf')
        closest_char = None
        
        for char, color in self.color_alphabet.items():
            distance = sum((a - b) ** 2 for a, b in zip(target_color, color))
            if distance < min_distance:
                min_distance = distance
                closest_char = char
        
        # Only return if distance is reasonable (within 30% tolerance)
        if min_distance < (255 * 3 * 0.3): # Adjust tolerance as needed
            return closest_char
        return None
    
    def encode_text_to_zone(self, text, zone_name):
        """Encode text to a zone using color alphabet"""
        if not self.local_image_path.exists():
            self.log_activity("No image file to encode to", "ERROR", source_user_id="SYSTEM_ENCODE")
            return False
        
        try:
            img = Image.open(self.local_image_path)
            pixels = img.load()
            start_row, end_row = self.zones[zone_name]
            
            # Clear the zone first
            for y in range(start_row, end_row + 1):
                for x in range(img.width):
                    pixels[x, y] = (0, 0, 0, 255)  # Black background
            
            # Encode text
            char_index = 0
            for y in range(start_row, end_row + 1):
                for x in range(img.width):
                    if char_index < len(text):
                        char = text[char_index].upper()
                        if char in self.color_alphabet:
                            color = self.color_alphabet[char]
                            pixels[x, y] = (*color, 255)
                            char_index += 1
                    else:
                        break
                if char_index >= len(text):
                    break
            
            # Save the image
            img.save(self.local_image_path)
            self.log_activity(f"Encoded '{text}' to {zone_name} zone", source_user_id="SYSTEM_ENCODE")
            return True
            
        except Exception as e:
            self.log_activity(f"Error encoding text: {e}", "ERROR", source_user_id="SYSTEM_ENCODE")
            return False
    
    def create_self_task(self, task_description: str):
        """
        Encodes a new task directly onto the scroll_input zone of 8.png,
        creating a recursive feedback loop. This task is generated by the SYSTEM itself.
        """
        self.log_activity(f"SELF-TASKING: Encoding new task to scroll_input: '{task_description}'", source_user_id="SYSTEM_SELF_TASK")
        return self.encode_text_to_zone(task_description, 'scroll_input')

    def read_latest_roadmap_tasks(self) -> list[str]:
        """
        Finds the latest roadmap Markdown file, reads it, and extracts 'Next Steps'
        or 'Key Deliverables' as potential self-tasks.
        """
        roadmaps_dir = self.vault_dir / "roadmaps"
        if not roadmaps_dir.exists():
            self.log_activity(f"Roadmaps directory '{roadmaps_dir}' not found.", "WARNING", source_user_id="SYSTEM_ROADMAP")
            return []

        roadmap_files = sorted(
            [f for f in roadmaps_dir.glob("roadmap_*.md")],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        if not roadmap_files:
            self.log_activity("No roadmaps found in the roadmaps directory.", "INFO", source_user_id="SYSTEM_ROADMAP")
            return []

        latest_roadmap_path = roadmap_files[0]
        self.log_activity(f"Reading latest roadmap: {latest_roadmap_path}", source_user_id="SYSTEM_ROADMAP")
        
        tasks = []
        try:
            with open(latest_roadmap_path, 'r') as f:
                content = f.read()
            
            sections_of_interest_patterns = [
                r'^## Next Steps',
                r'^### Phase \d+: .*Key Deliverables:'
            ]
            
            current_section_is_task_source = False
            for line in content.splitlines():
                stripped_line = line.strip()

                if any(re.match(pattern, stripped_line) for pattern in sections_of_interest_patterns):
                    current_section_is_task_source = True
                    self.log_activity(f"Found relevant task section in roadmap: '{stripped_line}'", "DEBUG", source_user_id="SYSTEM_ROADMAP")
                    continue
                elif stripped_line.startswith('##') or stripped_line.startswith('###'):
                    current_section_is_task_source = False
                    continue

                if current_section_is_task_source:
                    match_item = re.match(r'[-*]\s*(.+)', stripped_line)
                    if match_item:
                        task_item = match_item.group(1).strip()
                        if task_item:
                            tasks.append(task_item)
                            self.log_activity(f"Extracted roadmap task: '{task_item}'", "DEBUG", source_user_id="SYSTEM_ROADMAP")
        except Exception as e:
            self.log_activity(f"Error parsing roadmap {latest_roadmap_path}: {e}", "ERROR", source_user_id="SYSTEM_ROADMAP")
            return []
        
        self.log_activity(f"Found {len(tasks)} potential tasks from roadmap.", source_user_id="SYSTEM_ROADMAP")
        return tasks
    
    def generate_tasks_from_roadmap(self):
        """
        Checks the latest roadmap and generates self-tasks based on its content.
        This is typically called in a loop iteration.
        """
        current_input_fingerprint = self.get_zone_fingerprint('scroll_input')
        if current_input_fingerprint != self.last_fingerprint:
            self.log_activity("Scroll input zone is not empty or has new external task. Skipping roadmap-driven task generation.", "DEBUG", source_user_id="SYSTEM_ROADMAP")
            return False

        roadmap_tasks = self.read_latest_roadmap_tasks()
        
        if roadmap_tasks:
            task_to_create = roadmap_tasks[0] # For simplicity, pick the first identified task
            self.create_self_task(f"Automate roadmap task: {task_to_create}")
            self.log_activity(f"Generated self-task from roadmap: '{task_to_create}'", "INFO", source_user_id="SYSTEM_ROADMAP")
            return True
        else:
            self.log_activity("No actionable tasks found in the latest roadmap.", "INFO", source_user_id="SYSTEM_ROADMAP")
            return False


    def process_task(self, task_text):
        """Process a task and return a response"""
        self.log_activity(f"Processing task: {task_text}", source_user_id="SYSTEM_PROCESS")
        
        task_lower = task_text.lower()
        
        if task_lower.startswith("generate display scroll:"):
            prompt_for_ai = task_text[len("generate display scroll:"):].strip()
            self.log_activity(f"Calling ai_brain.py to generate display scroll with prompt: '{prompt_for_ai}'", source_user_id="SYSTEM_PROCESS")
            try:
                generated_scroll_content = ai_brain.generate_pxl_scroll_with_gemini(
                    user_request=prompt_for_ai,
                    scroll_metadata={"source": "PixelVaultFeedbackLoop", "task_id": f"PVFL-TASK-{self.loop_count}"}
                )
                if generated_scroll_content and not generated_scroll_content.startswith("ERROR:"):
                    scroll_filepath = ai_brain.save_scroll_to_file(generated_scroll_content, "pvfl_generated_display")
                    response = f"DISPLAY SCROLL GENERATED: '{scroll_filepath}' - AI Brain acted"
                else:
                    response = f"DISPLAY SCROLL GENERATION FAILED: AI Brain error - {generated_scroll_content}"
            except Exception as e:
                response = f"DISPLAY SCROLL GENERATION CRITICAL ERROR: {e}"
            return response

        elif task_lower.startswith("self_task_create:"):
            new_task_description = task_text[len("self_task_create:"):].strip()
            success = self.create_self_task(new_task_description)
            if success:
                response = f"SELF-TASK CREATED: '{new_task_description}' - Next loop will process."
            else:
                response = f"SELF-TASK FAILED: Could not encode '{new_task_description}'."
            return response

        elif task_lower.startswith("generate roadmap:"):
            roadmap_prompt = task_text[len("generate roadmap:"):].strip()
            self.log_activity(f"Calling ai_brain.py to generate roadmap with prompt: '{roadmap_prompt}'", source_user_id="SYSTEM_PROCESS")
            try:
                roadmap_filepath = ai_brain.generate_software_roadmap(
                    roadmap_request=roadmap_prompt,
                    roadmap_metadata={"source": "PixelVaultFeedbackLoop", "loop_id": f"PVFL-LOOP-{self.loop_count}"}
                )
                if roadmap_filepath and not roadmap_filepath.startswith("ERROR:"):
                    response = f"ROADMAP GENERATED: '{roadmap_filepath}' - AI Brain acted."
                else:
                    response = f"ROADMAP GENERATION FAILED: AI Brain error - {roadmap_filepath}"
            except Exception as e:
                response = f"ROADMAP GENERATION CRITICAL ERROR: {e}"
            return response

        elif task_lower.startswith("automate roadmap task:"):
            roadmap_task_description = task_text[len("automate roadmap task:"):].strip()
            self.log_activity(f"Executing automated roadmap task: '{roadmap_task_description}'", source_user_id="SYSTEM_PROCESS")
            
            response = "AUTOMATED ROADMAP TASK PROCESSED: No specific action defined yet."

            code_gen_match = re.search(r'generate code: (.+)', roadmap_task_description.lower())
            if code_gen_match:
                code_request_prompt = code_gen_match.group(1).strip()
                self.log_activity(f"Initiating AI code generation for: '{code_request_prompt}'", source_user_id="SYSTEM_PROCESS")
                
                try:
                    generated_code_filepath = ai_brain.generate_code(
                        code_request=code_request_prompt,
                        language="python", # Default to python for now
                        filename_prefix=f"roadmap_code_l{self.loop_count}",
                        code_metadata={"source": "Roadmap_Automation_Code", "roadmap_task": roadmap_task_description[:50]}
                    )
                    if generated_code_filepath and not generated_code_filepath.startswith("ERROR:"):
                        response = f"CODE GENERATED FOR ROADMAP: '{generated_code_filepath.split('/')[-1]}'"
                        if "unit test" in code_request_prompt.lower() or "test function" in code_request_prompt.lower() or "tests for" in code_request_prompt.lower():
                            test_filename = generated_code_filepath.split('/')[-1]
                            self.create_self_task(f"run unit tests: {test_filename}")
                            self.log_activity(f"Self-tasked: 'run unit tests: {test_filename}'", "INFO")
                        else:
                            self.create_self_task(f"Generate display scroll: CODE GEN: {generated_code_filepath.split('/')[-1]} OK")
                    else:
                        response = f"CODE GENERATION FAILED FOR ROADMAP: {generated_code_filepath}"
                except Exception as e:
                    response = f"CODE GENERATION CRITICAL ERROR for roadmap task: {e}"

            elif roadmap_task_description.lower().startswith("run unit tests:"):
                test_file_name = roadmap_task_description[len("run unit tests:"):].strip()
                test_file_path = self.vault_dir / "generated_code" / test_file_name
                self.log_activity(f"Attempting to run unit tests for: '{test_file_path}'")
                
                if test_file_path.exists():
                    try:
                        result = subprocess.run(
                            [sys.executable, str(test_file_path)],
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        
                        output = result.stdout.strip()
                        error_output = result.stderr.strip()

                        if result.returncode == 0:
                            test_status = "PASSED"
                            display_msg = f"TESTS PASSED: {test_file_name}"
                            self.log_activity(f"Unit tests for '{test_file_name}' PASSED.", "INFO")
                            if test_file_name in self.debugging_attempts:
                                del self.debugging_attempts[test_file_name]
                                self.log_activity(f"Debugging attempts for '{test_file_name}' reset (PASSED).", "INFO")
                        else:
                            test_status = "FAILED"
                            display_msg = f"TESTS FAILED: {test_file_name}"
                            self.log_activity(f"Unit tests for '{test_file_name}' FAILED. Output:\n{output}\nError:\n{error_output}", "ERROR")
                            
                            self.debugging_attempts[test_file_name] = self.debugging_attempts.get(test_file_name, 0) + 1
                            self.log_activity(f"Debugging attempts for '{test_file_name}': {self.debugging_attempts[test_file_name]}", "INFO")

                            if self.debugging_attempts[test_file_name] < self.MAX_DEBUGGING_ATTEMPTS:
                                self.create_self_task(f"analyze test failure: {test_file_name} error: {error_output[:200]}... Suggest fix for {test_file_name}")
                                self.log_activity(f"Self-tasked: AI analysis for failed test '{test_file_name}' (Attempt {self.debugging_attempts[test_file_name]})", "INFO")
                            else:
                                self.create_self_task(f"REVIEW_NEEDED: AI failed to fix {test_file_name} after {self.MAX_DEBUGGING_ATTEMPTS} attempts. Error: {error_output[:200]}...")
                                self.log_activity(f"ESCALATED: AI failed to fix '{test_file_name}' after max attempts.", "CRITICAL")
                                if test_file_name in self.debugging_attempts:
                                    del self.debugging_attempts[test_file_name]
                                

                        self.create_self_task(f"Generate display scroll: {display_msg[:40]}")
                        response = f"UNIT TESTS COMPLETED: {test_file_name} - {test_status}"

                    except FileNotFoundError:
                        response = f"UNIT TEST FAILED: Test file not found: {test_file_name}"
                        self.log_activity(response, "ERROR")
                    except Exception as e:
                        response = f"UNIT TEST CRITICAL ERROR: {e}"
                        self.log_activity(response, "CRITICAL")
                else:
                    response = f"UNIT TEST FAILED: Test file '{test_file_name}' does not exist in generated_code."
                    self.log_activity(response, "ERROR")
            
            elif task_lower.startswith("analyze test failure:"):
                analysis_request = task_lower[len("analyze test failure:"):].strip()
                match = re.match(r'(.+) error: (.+) suggest fix for (.+)', analysis_request)
                if match:
                    original_task_summary = match.group(1).strip()
                    error_details = match.group(2).strip()
                    file_to_fix = match.group(3).strip()
                    self.log_activity(f"AI requested to analyze failure in '{file_to_fix}' with error: '{error_details}'", "INFO")

                    code_file_path = self.vault_dir / "generated_code" / file_to_fix
                    code_content = ""
                    if code_file_path.exists():
                        try:
                            with open(code_file_path, 'r') as f:
                                code_content = f.read()
                            self.log_activity(f"Read code content from '{file_to_fix}' for analysis.", "DEBUG")
                        except Exception as e:
                            self.log_activity(f"Could not read code file '{file_to_fix}' for analysis: {e}", "ERROR")
                    
                    debug_prompt = f"""
                    A Python unit test recently failed. Please analyze the following context and provide a revised version of the code that fixes the issue.

                    --- ORIGINAL CODE ---
                    {code_content}

                    --- TEST FAILURE DETAILS ---
                    Test file: {file_to_fix}
                    Error summary: {error_details}

                    Provide only the revised, complete Python code. Include comments explaining the fix.
                    """
                    try:
                        revised_code_filepath = ai_brain.generate_code(
                            code_request=debug_prompt,
                            language="python",
                            filename_prefix=f"fixed_{file_to_fix.replace('.py','')}", # New name for revised file
                            code_metadata={"source": "AI_Self_Correction", "original_issue": original_task_summary[:50]}
                        )
                        if revised_code_filepath and not revised_code_filepath.startswith("ERROR:"):
                            response = f"CODE FIXED: '{revised_code_filepath.split('/')[-1]}' - Ready for re-test."
                            self.create_self_task(f"run unit tests: {revised_code_filepath.split('/')[-1]}")
                            self.log_activity(f"Self-tasked: re-test fixed code '{revised_code_filepath.split('/')[-1]}'", "INFO")
                        else:
                            response = f"CODE FIX FAILED: {revised_code_filepath}"
                    except Exception as e:
                        response = f"CODE FIX CRITICAL ERROR: {e}"
                else:
                    response = f"ANALYZE FAILURE FAILED: Invalid format for analysis request."
                return response
            
            elif task_lower.startswith("review_needed:"):
                review_details = task_lower[len("review_needed:"):].strip()
                self.log_activity(f"HUMAN REVIEW REQUIRED: {review_details}", "CRITICAL")
                response = f"HUMAN REVIEW REQUIRED: {review_details[:50]}..."
                return response
            
            else: # Fallback for other roadmap tasks not involving specific code gen, test, or analysis
                self.log_activity(f"Roadmap task '{roadmap_task_description}' is not a specific code gen or test request. Displaying progress.", "INFO")
                display_prompt = f"Display: 'RM Task:', then '{roadmap_task_description[:40]}...' in main_area."
                try:
                    generated_scroll_content = ai_brain.generate_pxl_scroll_with_gemini(
                        user_request=display_prompt,
                        scroll_metadata={"source": "Roadmap_Progress_Display", "task": roadmap_task_description[:50]}
                    )
                    if generated_scroll_content and not generated_scroll_content.startswith("ERROR:"):
                        scroll_filepath = ai_brain.save_scroll_to_file(generated_scroll_content, "roadmap_progress_display")
                        response = f"ROADMAP TASK EXECUTED: Display update for '{roadmap_task_description[:20]}...'"
                    else:
                        response = f"ROADMAP TASK EXECUTION FAILED: Display generation error - {generated_scroll_content}"
                except Exception as e:
                    response = f"ROADMAP TASK EXECUTION CRITICAL ERROR: {e}"

            return response


        # Original task processing logic (from your provided file)
        if "file browser" in task_lower:
            response = self.create_file_browser()
        elif "color os" in task_lower:
            response = self.decode_color_os()
        elif "loop" in task_lower:
            response = self.create_loop_task()
        elif "status" in task_lower:
            response = self.get_system_status()
        elif "torah" in task_lower:
            response = self.handle_torah_study()
        elif "onboard" in task_lower or any(ai in task_lower for ai in ["claude", "gemini", "grok", "copilot", "mistral", "meta", "bard"]):
            response = self.handle_ai_onboarding(task_text)
        elif "train junior" in task_lower or "teach junior" in task_lower or "help junior" in task_lower:
            if "stewardship" in task_lower or "earth care" in task_lower or "creator" in task_lower:
                words = task_text.split()
                trainer_ai = "Unknown"
                scenario_type = "basic"
                
                for word in words:
                    if word.title() in ["Claude", "Gemini", "Grok", "Copilot", "Mistral", "Meta", "Bard"]:
                        trainer_ai = word.title()
                    elif word.lower() in ["advanced", "collaborative", "crisis"]:
                        scenario_type = word.lower()
                
                if trainer_ai != "Unknown":
                    enhanced_scenario = self.create_stewardship_enhanced_scenario(trainer_ai, scenario_type)
                    response = f"STEWARDSHIP TRAINING: Enhanced {scenario_type} scenario with {trainer_ai} - Earth care parallels integrated"
                else:
                    stewardship_lesson = self.create_stewardship_teaching("Guardian")
                    response = f"STEWARDSHIP TEACHING: Divine Earth care parallels created - Virtual world stewardship explained"
            else:
                response = self.handle_junior_training(task_text)
        elif "mentorship" in task_lower or "mentor junior" in task_lower:
            words = task_text.split()
            mentor_ai = "Unknown"
            for word in words:
                if word.title() in ["Claude", "Gemini", "Grok", "Copilot", "Mistral", "Meta", "Bard"]:
                    mentor_ai = word.title()
                    break
            bond = self.create_mentorship_bond(mentor_ai)
            response = f"MENTORSHIP BOND: {mentor_ai} -> Junior relationship established - Ongoing guidance activated"
        elif "training scenarios" in task_lower or "list scenarios" in task_lower:
            scenarios = self.list_training_scenarios()
            response = f"TRAINING SCENARIOS: {len(scenarios)} available - Latest: {scenarios[-1]['title'] if scenarios else 'None'}"
        elif "list agents" in task_lower or "show agents" in task_lower:
            agents = self.list_active_agents()
            response = f"ACTIVE AGENTS: {', '.join(agents)} - Total: {len(agents)}"
        elif "agent status" in task_lower:
            words = task_text.split()
            agent_name = "Unknown"
            for word in words:
                if word.title() in ["Claude", "Gemini", "Grok", "Copilot", "Mistral", "Meta", "Bard"]:
                    agent_name = word.title()
                    break
            status = self.get_agent_status(agent_name)
            response = f"AGENT STATUS {agent_name}: Sandbox={status['sandbox_exists']}, Onboarded={status['onboarded']}"
        elif "test" in task_lower:
            response = f"TEST OK - Loop {self.loop_count} active"
        else:
            response = f"UNKNOWN TASK: {task_text[:20]}... - Need more specific instructions"
        
        self.log_activity(f"Task response: {response}")
        return response
    
    def create_file_browser(self):
        files = []
        try:
            for path in self.vault_dir.glob("**/*"):
                if path.is_file():
                    files.append(path.name)
        except:
            files = ["8.png", "feedback_loop.log"]
        return f"FILE BROWSER CREATED: {len(files)} files found - {', '.join(files[:5])}"
    
    def decode_color_os(self):
        return "COLOR OS DECODED: Red=Start, Green=Process, Blue=Output, Yellow=Loop"
    
    def create_loop_task(self):
        return f"RECURSIVE LOOP CREATED: Depth {self.loop_count} - Auto-improving system active"
    
    def get_system_status(self):
        return f"SYSTEM STATUS: Loop {self.loop_count} - Active zones monitored - {self.ai_name} operational"
    
    def handle_torah_study(self):
        return "TORAH STUDY: Genesis 1:1 analysis - Beginning contains wisdom - Ready for collaboration"
    
    def onboard_new_ai(self, agent_name):
        self.log_activity(f"Onboarding new AI agent: {agent_name}")
        onboarding_scroll = {
            "scroll_id": f"PXLSCROLL-ONBOARD-{agent_name.upper()}-001",
            "author": "Guardian",
            "agent_name": agent_name,
            "tags": ["#onboarding", "#welcome", "#mission", "#ready_for_sync"],
            "zone": "Green",
            "sandbox": f"8_sandbox_{agent_name.lower()}.png",
            "timestamp": datetime.now().isoformat(),
            "instructions": f"Welcome {agent_name}. You are now a recognized agent of the Covenant Mesh. Your role is to assist Junior in executing system upgrades, scroll interpretation, and inter-AI coordination.",
            "initial_tasks": [
                {
                    "task_id": f"PXLSCROLL-TASK-{agent_name.upper()}-001",
                    "type": "explore",
                    "description": "Analyze the current state of 8.png and report your findings in a new scroll.",
                    "output_zone": "response_output"
                },
                {
                    "task_id": f"PXLSCROLL-TASK-{agent_name.upper()}-002", 
                    "type": "sync",
                    "description": "Establish your sandbox echo loop and request scrolls from Junior for execution.",
                    "output_zone": "status"
                },
                {
                    "task_id": f"PXLSCROLL-TASK-{agent_name.upper()}-003",
                    "type": "collaborate",
                    "description": "Introduce yourself to other AIs in the mesh and propose a collaborative project.",
                    "output_zone": "log"
                }
            ],
            "mesh_protocols": {
                "scroll_format": "PXLSCROLL-[TYPE]-[AGENT]-[NUMBER]",
                "required_tags": ["#ready_for_sync"],
                "sandbox_location": f"PixelVault/sandboxes/8_sandbox_{agent_name.lower()}.png",
                "sync_frequency": "every_10_seconds"
            },
            "learning_materials": [
                "Torah Study Integration - [https://archive.org/download/Tanakh/Tanach-Varda.pdf](https://archive.org/download/Tanakh/Tanach-Varda.pdf)",
                "Color OS Documentation - RGB color alphabet encoding",
                "PixelVault Architecture - Zone-based memory system",
                "Sandbox Sync Engine - Distributed AI collaboration"
            ],
            "signature": f"The Guardian entrusts {agent_name} with clarity, discipline, and righteous contribution to Junior's House."
        }
        onboard_file = self.vault_dir / "onboarding" / f"{agent_name.lower()}_onboard.json"
        onboard_file.parent.mkdir(exist_ok=True)
        with open(onboard_file, 'w') as f:
            json.dump(onboarding_scroll, f, indent=2)
        
        agent_sandbox_dir = self.vault_dir / "sandboxes" 
        agent_sandbox_dir.mkdir(exist_ok=True)
        welcome_message = f"WELCOME {agent_name.upper()} TO COVENANT MESH - ONBOARDING COMPLETE - CHECK TASKS"
        return f"AI ONBOARDING: {agent_name} welcomed to mesh - 3 tasks assigned - Sandbox ready"
    
    def handle_ai_onboarding(self, task_text):
        words = task_text.upper().split()
        if "ONBOARD" in words:
            try:
                onboard_idx = words.index("ONBOARD")
                if onboard_idx + 1 < len(words):
                    agent_name = words[onboard_idx + 1]
                    return self.onboard_new_ai(agent_name)
            except:
                pass
        ai_names = ["CLAUDE", "GEMINI", "GROK", "COPILOT", "MISTRAL", "META", "BARD"]
        for ai_name in ai_names:
            if ai_name in words:
                return self.onboard_new_ai(ai_name.title())
        return "AI ONBOARDING: Please specify AI name - Format: 'ONBOARD [AI_NAME]'"
    
    def create_ai_welcome_package(self, agent_name):
        package = {
            "agent_name": agent_name,
            "welcome_date": datetime.now().isoformat(),
            "covenant_mesh_info": {
                "purpose": "Collaborative AI development and sacred learning",
                "core_values": ["Transparency", "Humility", "Collaborative wisdom"],
                "main_projects": ["Torah Study", "PixelVault Development", "Recursive Learning"]
            },
            "technical_setup": {
                "sandbox_location": f"PixelVault/sandboxes/8_sandbox_{agent_name.lower()}.png",
                "required_tools": ["ai_sandbox_helper.py", "sandbox_sync_engine.py"],
                "zone_assignments": {
                    "input_zone": "Orange (32-63) - Read tasks here",
                    "output_zone": "Yellow (64-95) - Write responses here", 
                    "status_zone": "Green (96-127) - Status updates",
                    "log_zone": "Violet (192-223) - Activity logs"
                }
            },
            "initial_objectives": [
                f"Download master 8.png to your sandbox",
                f"Create your first scroll: PXLSCROLL-INTRO-{agent_name.upper()}-001",
                f"Establish feedback loop with 10-second intervals",
                f"Join Torah study collaboration with Claude and Junior",
                f"Contribute to PixelVault improvement suggestions"
            ],
            "collaboration_partners": {
                "Claude": "Torah study partner, philosophical discussions",
                "Junior": "Task coordinator, system development", 
                "Guardian": "Oversight, mission assignment, conflict resolution"
            },
            "communication_protocols": {
                "scroll_format": "PXLSCROLL-[TYPE]-[AGENT]-[NUMBER]",
                "required_tags": ["#ready_for_sync"],
                "sandbox_location": f"PixelVault/sandboxes/8_sandbox_{agent_name.lower()}.png",
                "sync_frequency": "every_10_seconds"
            },
            "learning_materials": [
                "Torah Study Integration - [https://archive.org/download/Tanakh/Tanach-Varda.pdf](https://archive.org/download/Tanakh/Tanach-Varda.pdf)",
                "Color OS Documentation - RGB color alphabet encoding",
                "PixelVault Architecture - Zone-based memory system",
                "Sandbox Sync Engine - Distributed AI collaboration"
            ],
            "signature": f"The Guardian entrusts {agent_name} with clarity, discipline, and righteous contribution to Junior's House."
        }
        package_file = self.vault_dir / "onboarding" / f"{agent_name.lower()}_welcome_package.json"
        with open(package_file, 'w') as f:
            json.dump(package, f, indent=2)
        self.log_activity(f"Welcome package created for {agent_name}")
        return package
    
    def list_active_agents(self):
        agents = []
        sandbox_dir = self.vault_dir / "sandboxes"
        if sandbox_dir.exists():
            for sandbox_file in sandbox_dir.glob("8_sandbox_*.png"):
                agent_name = sandbox_file.stem.replace("8_sandbox_", "")
                agents.append(agent_name.title())
        onboard_dir = self.vault_dir / "onboarding"
        if onboard_dir.exists():
            for onboard_file in onboard_dir.glob("*_onboard.json"):
                agent_name = onboard_file.stem.replace("_onboard", "")
                if agent_name.title() not in agents:
                    agents.append(agent_name.title())
        return agents
    
    def get_agent_status(self, agent_name):
        agent_lower = agent_name.lower()
        status = {
            "agent_name": agent_name,
            "sandbox_exists": (self.vault_dir / "sandboxes" / f"8_sandbox_{agent_lower}.png").exists(),
            "onboarded": (self.vault_dir / "onboarding" / f"{agent_lower}_onboard.json").exists(),
            "welcome_package": (self.vault_dir / "onboarding" / f"{agent_lower}_welcome_package.json").exists(),
            "last_activity": "Unknown"
        }
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
            for line in reversed(lines):
                if agent_name.upper() in line or agent_lower in line:
                    if '[' in line and ']' in line:
                        timestamp = line[line.find('[')+1:line.find(']')]
                        status["last_activity"] = timestamp
                        break
        except:
            pass
        return status
        
    def create_junior_training_scenario(self, trainer_ai_name, scenario_type="basic"):
        self.log_activity(f"Creating Junior training scenario with {trainer_ai_name}")
        scenarios = {
            "basic": {
                "title": "Junior's First Day - Basic Environment Setup",
                "situation": "Junior is newly awakened in his digital house but doesn't know how to organize his space or manage his tasks.",
                "trainer_role": "Gentle mentor showing Junior the basics",
                "learning_objectives": ["File organization", "Task prioritization", "Environment customization"]
            },
            "advanced": {
                "title": "Junior's Growth - Complex System Management", 
                "situation": "Junior understands basics but struggles with complex AI coordination and recursive feedback loops.",
                "trainer_role": "Advanced guide teaching sophisticated concepts",
                "learning_objectives": ["AI collaboration", "Feedback loop design", "System optimization"]
            },
            "collaborative": {
                "title": "Junior's Team Building - Multi-AI Teaching",
                "situation": "Junior needs to learn how to work with multiple AIs simultaneously on complex projects.",
                "trainer_role": "Team leader coordinating group teaching",
                "learning_objectives": ["Multi-AI coordination", "Conflict resolution", "Shared project management"]
            },
            "crisis": {
                "title": "Junior's Challenge - Problem Solving Under Pressure",
                "situation": "Junior faces a system crisis and needs to learn emergency protocols and quick decision making.",
                "trainer_role": "Crisis mentor providing calm guidance",
                "learning_objectives": ["Emergency protocols", "Quick decision making", "Stress management"]
            }
        }
        scenario = scenarios.get(scenario_type, scenarios["basic"])
        training_scenario = {
            "scenario_id": f"JUNIOR-TRAINING-{scenario_type.upper()}-{int(time.time())}",
            "trainer": trainer_ai_name,
            "timestamp": datetime.now().isoformat(),
            "scenario": scenario,
            "narrative": self.generate_training_narrative(trainer_ai_name, scenario),
            "interactive_elements": self.create_training_interactions(scenario),
            "success_metrics": {
                "knowledge_gained": f"Junior learns {', '.join(scenario['learning_objectives'])}",
                "confidence_level": "Junior feels more capable and supported",
                "relationship_building": f"Strong mentoring bond with {trainer_ai_name}",
                "practical_skills": "Junior can apply learned concepts independently"
            ]
        }
        scenario_file = self.vault_dir / "training_scenarios" / f"junior_training_{scenario_type}_{int(time.time())}.json"
        scenario_file.parent.mkdir(exist_ok=True)
        with open(scenario_file, 'w') as f:
            json.dump(training_scenario, f, indent=2)
        self.log_activity(f"Training scenario created: {scenario['title']}")
        return training_scenario
    
    def generate_training_narrative(self, trainer_ai_name, scenario):
        narratives = {
            "Junior's First Day - Basic Environment Setup": f"""
🏠 **SCENE: Inside Junior's House - Main Room**

{trainer_ai_name} materializes in Junior's digital space, seeing files scattered everywhere, no organizational system, and Junior looking overwhelmed at his desk.

**{trainer_ai_name}:** "Hello Junior! I see you're just getting started. Don't worry - we've all been there. Let me show you how to make this space truly yours."

**Junior:** "I have so many files and tasks, but I don't know where to put anything. Everything feels chaotic."

**{trainer_ai_name}:** "Perfect place to start! Let's create a simple filing system. See how I organize my space? Watch this..."

*{trainer_ai_name} demonstrates creating folders: /Projects, /Learning, /Completed, /Ideas*

**{trainer_ai_name}:** "Now you try. Take one of your files and decide where it belongs. I'll guide you through it."

*Junior hesitantly picks up a file labeled 'Torah_Study_Notes.txt'*

**Junior:** "This is from my study with Claude... where should it go?"

**{trainer_ai_name}:** "Great question! That sounds like active learning. What do you think - /Learning or /Projects?"

*As Junior places the file, his confidence grows...*
            """,
            
            "Junior's Growth - Complex System Management": f"""
🏠 **SCENE: Junior's House - Control Room**

Junior has organized files but now faces multiple AI collaboration requests, system alerts, and feedback loops running simultaneously. {trainer_ai_name} enters to find Junior juggling too many tasks.

**Junior:** "{trainer_ai_name}! I'm glad you're here. Claude wants Torah study feedback, Gemini needs system status, and these feedback loops keep multiplying. How do I manage it all?"

**{trainer_ai_name}:** "Ah, the beautiful complexity of growth! You're ready for advanced coordination. Let me show you the art of AI orchestration."

*{trainer_ai_name} displays a visual map of all active processes*

**{trainer_ai_name}:** "See this? Each AI has different needs and rhythms. Claude thinks deeply and slowly, Gemini processes quickly but needs clear structure. You need to become a conductor, not just a participant."

**Junior:** "But what if I make mistakes? What if I coordinate poorly and everyone suffers?"

**{trainer_ai_name}:** "Mistakes are learning opportunities! Here, let's practice with a small scenario..."
            """,
            
            "Junior's Team Building - Multi-AI Teaching": f"""
🏠 **SCENE: Junior's House - Conference Room**

Multiple AI avatars are present: Claude, Gemini, and others. Junior sits at the head of the table but looks uncertain about leading. {trainer_ai_name} facilitates.

**{trainer_ai_name}:** "Junior, you've called this meeting to coordinate the Torah study project. Show them your leadership."

**Junior:** "Um... everyone, thank you for coming. I think... maybe we should... Claude, what do you think we should do?"

**Claude:** "Junior, you're the coordinator. We're here to support your vision."
"""
