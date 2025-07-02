# pxos_console_viewer.py
# This script provides a console-based interface for the PXOS Microkernel.
# It directly interacts with the 8.png.json file for persistent storage.

import json
import os
import datetime

# --- File System Paths ---
PXOS_DATA_FILE = "8.png.json" # The core PXOS memory file

# --- Default Initial PXOS State ---
# This data will be used if 8.png.json does not exist.
# It mirrors the structure from assets_8_png_json_pure.
DEFAULT_PXOS_STATE = {
    "conversation_history": [],
    "current_roadmap": None,
    "current_roadmap_step_index": -1,
    "is_paused": False,
    "pxos_in_memory_files": {},
    "pending_human_approval_step": None,
    "roadmaps": {
        "initial_boot": [
            {
                "phase_number": 1,
                "title": "PXOS Initial Boot Sequence",
                "description": "Establishes core system files and welcomes the user.",
                "steps": [
                    {
                        "type": "create_file",
                        "path": "/pxos/config/boot.json",
                        "content": "{\"status\": \"booted\", \"timestamp\": \"2025-07-02 13:25:00\"}"
                    },
                    {
                        "type": "pxos_command",
                        "command": "log",
                        "message": "PXOS core boot files created."
                    },
                    {
                        "type": "gui_update",
                        "update_data": {
                            "component": "welcome_message",
                            "text": "Welcome to PXOS! I am your Microkernel AI."
                        }
                    }
                ],
                "requires_human_approval": False
            },
            {
                "phase_number": 2,
                "title": "Agent System Activation",
                "description": "Activates the initial agent framework.",
                "steps": [
                    {
                        "type": "create_file",
                        "path": "/pxos/agents/pxagent_001.py",
                        "content": "# PXAgent-001: Placeholder for agent logic.\\n# This file will evolve within PXOS memory."
                    },
                    {
                        "type": "pxos_command",
                        "command": "log",
                        "message": "PXAgent-001 framework initiated."
                    }
                ],
                "requires_human_approval": True
            }
        ]
    }
}

# --- Global PXOS State (loaded from/saved to PXOS_DATA_FILE) ---
pxos_state = {}

# --- Utility Functions ---

def log_message(msg, msg_type='system'):
    """Prints a message to the console with basic color coding."""
    colors = {
        'user': '\033[94m',      # Blue
        'bot': '\033[92m',       # Green
        'system': '\033[90m',    # Dark Gray
        'warning': '\033[93m',   # Yellow
        'error': '\033[91m',     # Red
        'phase': '\033[95m',     # Magenta
        'approval': '\033[96m',  # Cyan
        'auto-proceed': '\033[90m', # Dark Gray
        'edit': '\033[93m',      # Yellow
        'reset': '\033[0m'       # Reset color
    }
    print(f"{colors.get(msg_type, colors['reset'])}> {msg}{colors['reset']}")

def load_pxos_data():
    """Loads the PXOS state from the JSON file."""
    global pxos_state
    if os.path.exists(PXOS_DATA_FILE):
        try:
            with open(PXOS_DATA_FILE, 'r') as f:
                pxos_state = json.load(f)
            log_message(f"Loaded PXOS data from: {PXOS_DATA_FILE}", 'system')
        except json.JSONDecodeError as e:
            log_message(f"ERROR: Failed to parse {PXOS_DATA_FILE}: {e}. Initializing default state.", 'error')
            pxos_state = json.loads(json.dumps(DEFAULT_PXOS_STATE)) # Deep copy
        except Exception as e:
            log_message(f"ERROR loading {PXOS_DATA_FILE}: {e}. Initializing default state.", 'error')
            pxos_state = json.loads(json.dumps(DEFAULT_PXOS_STATE)) # Deep copy
    else:
        log_message(f"No existing {PXOS_DATA_FILE} found. Initializing default state.", 'system')
        pxos_state = json.loads(json.dumps(DEFAULT_PXOS_STATE)) # Deep copy

def save_pxos_data():
    """Saves the current PXOS state to the JSON file."""
    try:
        with open(PXOS_DATA_FILE, 'w') as f:
            json.dump(pxos_state, f, indent=4)
        log_message(f"Saved PXOS data to: {PXOS_DATA_FILE}", 'system')
    except Exception as e:
        log_message(f"ERROR saving PXOS data to {PXOS_DATA_FILE}: {e}", 'error')

# --- PXOS File System (In-Memory, part of pxos_state["pxos_in_memory_files"]) ---

def pxos_command_create_file(path: str, content: str):
    """Simulates creating a file in PXOS in-memory file system."""
    pxos_state["pxos_in_memory_files"][path] = content
    save_pxos_data() # Persist changes
    return f"PXOS FS: Created in-memory file: {path}"

def pxos_command_read_file(path: str) -> str:
    """Simulates reading a file from PXOS in-memory file system."""
    return pxos_state["pxos_in_memory_files"].get(path, "")

def pxos_command_write_file(path: str, content: str) -> bool:
    """Simulates writing to a file in PXOS in-memory file system."""
    pxos_state["pxos_in_memory_files"][path] = content
    save_pxos_data() # Persist changes
    return True

# --- Roadmap Logic ---

def execute_phase(phase_data: dict) -> list:
    """Executes steps within a single roadmap phase."""
    phase_logs = []
    phase_logs.append({"msg": f"RoadmapRunner: Executing phase: {phase_data.get('title', 'Unknown Phase')}", "type": 'phase'})

    for step in phase_data.get("steps", []):
        step_desc = step.get("description", str(step))
        phase_logs.append({"msg": f"  - Step: {step_desc}", "type": 'system'})

        if step.get("type") == "create_file":
            log_msg = pxos_command_create_file(step.get("path"), step.get("content", ""))
            phase_logs.append({"msg": f"    {log_msg}", "type": 'system'})
        elif step.get("type") == "gui_update":
            # In console, GUI updates are just logged
            phase_logs.append({"msg": f"    GUI Update Requested: {json.dumps(step.get('update_data'))}", "type": 'system'})
            if step.get("update_data", {}).get("component") == "welcome_message":
                log_message(step.get("update_data").get("text", ""), 'bot')
        elif step.get("type") == "pxos_command":
            command_type = step.get("command")
            if command_type == "log":
                phase_logs.append({"msg": f"    PXOS Command Log: {step.get('message')}", "type": 'system'})
            else:
                phase_logs.append({"msg": f"    PXOS Command: Unknown command type: {command_type}", "type": 'warning'})
    return phase_logs

def execute_next_roadmap_step():
    """Executes the next step in the current roadmap."""
    global pxos_state

    if pxos_state["current_roadmap"] is None or pxos_state["current_roadmap_step_index"] >= len(pxos_state["current_roadmap"]):
        log_message("Roadmap execution finished or no roadmap loaded.", 'system')
        pxos_state["current_roadmap"] = None
        pxos_state["current_roadmap_step_index"] = -1
        pxos_state["is_paused"] = False
        pxos_state["pending_human_approval_step"] = None
        save_pxos_data()
        return

    if pxos_state["is_paused"]:
        log_message("Execution is paused. Use 'resume' or 'approve' to continue.", 'system')
        return

    current_phase = pxos_state["current_roadmap"][pxos_state["current_roadmap_step_index"]]
    log_message(f"Executing Phase {current_phase.get('phase_number')}: {current_phase.get('title')}", 'phase')

    if current_phase.get("requires_human_approval", False):
        pxos_state["is_paused"] = True
        pxos_state["pending_human_approval_step"] = current_phase
        log_message(f"PXAgent-001: Phase {current_phase.get('phase_number')} '{current_phase.get('title')}' requires human approval.", 'approval')
        log_message(f"PXAgent-001: Here are the steps for this phase:", 'approval')
        for step in current_phase.get("steps", []):
            step_desc = step.get("description", str(step))
            log_message(f"  - {step_desc} (Type: {step.get('type')})", 'approval')
        log_message(f"PXAgent-001: Please type 'Hey PXOSBot, resume' or 'Hey PXOSBot, approve' to proceed, or 'Hey PXOSBot, skip step {current_phase.get('phase_number')}' to skip this phase.", 'approval')
        save_pxos_data()
        return # Pause here, waiting for user input

    # If not paused or approval not required, execute the phase
    phase_execution_logs = execute_phase(current_phase)
    for log_line in phase_execution_logs:
        log_message(log_line["msg"], log_line["type"])

    pxos_state["current_roadmap_step_index"] += 1
    save_pxos_data() # Save state after phase execution

    # Automatically proceed to the next step if not paused and roadmap not finished
    if not pxos_state["is_paused"] and pxos_state["current_roadmap_step_index"] < len(pxos_state["current_roadmap"]):
        log_message(f"PXOSBot: Phase {current_phase.get('phase_number')} completed. Automatically proceeding to next phase...", 'auto-proceed')
        # In a console app, we can just call it directly for immediate execution
        execute_next_roadmap_step()
    elif not pxos_state["is_paused"] and pxos_state["current_roadmap_step_index"] >= len(pxos_state["current_roadmap"]):
        log_message("PXOSBot: All roadmap phases completed.", 'auto-proceed')
        pxos_state["current_roadmap"] = None
        pxos_state["current_roadmap_step_index"] = -1
        save_pxos_data()

# --- Chatbot Core Logic ---

def process_chatbot_input(input_text: str):
    """Processes user input and generates chatbot response."""
    global pxos_state

    pxos_state["conversation_history"].append({"role": "user", "text": input_text, "timestamp": datetime.datetime.now().isoformat()})
    log_message(f"User: {input_text}", 'user')

    response = ""
    command_recognized = False

    if input_text.lower().startswith("hey pxosbot,"):
        command = input_text.lower().replace("hey pxosbot,", "").strip()
        command_recognized = True

        if command.startswith("load roadmap"):
            roadmap_name = command.replace("load roadmap", "").strip()
            if pxos_state["roadmaps"].get(roadmap_name):
                pxos_state["current_roadmap"] = pxos_state["roadmaps"][roadmap_name]
                pxos_state["current_roadmap_step_index"] = -1
                pxos_state["is_paused"] = False
                pxos_state["pending_human_approval_step"] = None
                response = f"Loaded roadmap: '{roadmap_name}'. It has {len(pxos_state['current_roadmap'])} phases."
            else:
                response = f"ERROR: Roadmap '{roadmap_name}' not found in PXOS memory."
        
        elif command.startswith("begin executing phase"):
            if pxos_state["current_roadmap"] is None:
                response = "ERROR: No roadmap loaded. Please load a roadmap first."
            else:
                try:
                    phase_num = int(command.replace("begin executing phase", "").strip())
                    start_step_index = -1
                    for i, phase in enumerate(pxos_state["current_roadmap"]):
                        if phase.get("phase_number") == phase_num:
                            start_step_index = i
                            break
                    
                    if start_step_index == -1:
                        response = f"ERROR: Phase {phase_num} not found in the loaded roadmap."
                    else:
                        pxos_state["current_roadmap_step_index"] = start_step_index
                        pxos_state["is_paused"] = False
                        pxos_state["pending_human_approval_step"] = None
                        response = f"Beginning execution from Phase {phase_num}."
                        log_message(f"PXOSBot: {response}", 'bot')
                        execute_next_roadmap_step() # Execute immediately
                        response = "" # Clear response as it's handled by execute_next_roadmap_step
                except ValueError:
                    response = "Please specify a valid phase number to begin execution."

        elif command == "pause" or command == "pause execution":
            if pxos_state["current_roadmap"] is not None:
                pxos_state["is_paused"] = True
                response = f"Execution paused. Current step: Phase {pxos_state['current_roadmap'][pxos_state['current_roadmap_step_index']].get('phase_number')}."
            else:
                response = "No roadmap is currently being executed."
        
        elif command == "resume" or command == "resume execution" or command == "approve":
            if pxos_state["current_roadmap"] is not None and pxos_state["is_paused"]:
                pxos_state["is_paused"] = False
                pxos_state["pending_human_approval_step"] = None
                response = "Resuming execution."
                log_message(f"PXOSBot: {response}", 'bot')
                execute_next_roadmap_step() # Continue execution
                response = "" # Clear response as it's handled by execute_next_roadmap_step
            else:
                response = "No roadmap is paused or being executed."
        
        elif command.startswith("execute step"):
            if pxos_state["current_roadmap"] is None:
                response = "ERROR: No roadmap loaded."
            else:
                try:
                    step_num = int(command.replace("execute step", "").strip())
                    if step_num < 1 or step_num > len(pxos_state["current_roadmap"]):
                        response = f"ERROR: Invalid step number. Roadmap has {len(pxos_state['current_roadmap'])} phases."
                    else:
                        pxos_state["current_roadmap_step_index"] = step_num - 1
                        pxos_state["is_paused"] = False
                        pxos_state["pending_human_approval_step"] = None
                        response = f"Executing specific step: Phase {step_num}."
                        log_message(f"PXOSBot: {response}", 'bot')
                        execute_next_roadmap_step()
                        response = ""
                except ValueError:
                    response = "Please specify a valid step number."

        elif command.startswith("skip step"):
            if pxos_state["current_roadmap"] is None:
                response = "ERROR: No roadmap loaded."
            else:
                try:
                    step_num = int(command.replace("skip step", "").strip())
                    if step_num < 1 or step_num > len(pxos_state["current_roadmap"]):
                        response = f"ERROR: Invalid step number. Roadmap has {len(pxos_state['current_roadmap'])} phases."
                    elif pxos_state["current_roadmap_step_index"] == step_num - 1:
                        pxos_state["current_roadmap_step_index"] += 1
                        pxos_state["is_paused"] = False
                        pxos_state["pending_human_approval_step"] = None
                        response = f"Skipped step: Phase {step_num}. Proceeding to next."
                        log_message(f"PXOSBot: {response}", 'bot')
                        execute_next_roadmap_step()
                        response = ""
                    else:
                        response = f"ERROR: Cannot skip phase {step_num}. Current execution is at phase {pxos_state['current_roadmap_step_index'] + 1}."
                except ValueError:
                    response = "Please specify a valid step number."
        
        elif command.startswith("edit"):
            file_path = command.replace("edit", "").strip()
            content = pxos_command_read_file(file_path)
            if content:
                response = f"Opened '{file_path}' for manual editing. Content preview (first 100 chars):\n{content[:100]}..."
                log_message(f"PXOSBot: {response}", 'edit')
                response = f"File '{file_path}' is ready for your manual edits. (Content printed above)"
            else:
                response = f"ERROR: Could not read file '{file_path}' or it's empty/does not exist in memory."
        
        elif command == "show memory" or command == "show 8.png data":
            if not pxos_state["pxos_in_memory_files"]:
                response = "8.png data is currently empty."
            else:
                response = f"Current 8.png data:\n{json.dumps(pxos_state['pxos_in_memory_files'], indent=2)}"
        
        elif command == "save memory" or command == "save 8.png data":
            save_pxos_data()
            response = "PXOS state saved to 8.png.json."
        
        elif command == "list roadmaps":
            roadmaps = pxos_state["roadmaps"]
            if roadmaps:
                response = "Available Roadmaps: " + ", ".join(roadmaps.keys())
            else:
                response = "No roadmaps found in memory."
        
        else:
            response = f"Command not recognized: '{command}'."
    
    if not command_recognized and response == "":
        response = "I'm not sure how to respond to that yet."
    
    if response: # Only log if there's a response to display
        pxos_state["conversation_history"].append({"role": "pxosbot", "text": response, "timestamp": datetime.datetime.now().isoformat()})
        log_message(f"PXOSBot: {response}", 'bot')
    save_pxos_data() # Save state after bot response


# --- Main Loop ---
def main():
    """Main function to run the PXOS console viewer."""
    load_pxos_data()
    log_message("PXOS ready. Welcome to PXOS! I am your Microkernel AI.", 'bot')
    log_message("Type 'Hey PXOSBot, load roadmap initial_boot' to begin.", 'bot')

    while True:
        try:
            user_input = input("\nEnter command: ").strip()
            if user_input.lower() == "exit":
                log_message("Exiting PXOS. Goodbye!", 'system')
                break
            if user_input:
                process_chatbot_input(user_input)
        except EOFError: # Handle Ctrl+D or Ctrl+Z
            log_message("\nExiting PXOS. Goodbye!", 'system')
            break
        except KeyboardInterrupt: # Handle Ctrl+C
            log_message("\nExiting PXOS. Goodbye!", 'system')
            break

if __name__ == "__main__":
    main()
