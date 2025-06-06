# pde_kernel_v1.0.py

import os
import json
import datetime

# Setup paths
LOG_FILE = "pde_log.json"
SCRIPTS_DIR = "scripts"
os.makedirs(SCRIPTS_DIR, exist_ok=True)

def save_log(entry):
    log_data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                log_data = json.load(f)
            except:
                log_data = []
    log_data.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

def list_scripts():
    files = os.listdir(SCRIPTS_DIR)
    return [f for f in files if f.endswith(".py")]

def save_script(name, code):
    path = os.path.join(SCRIPTS_DIR, name + ".py")
    with open(path, "w") as f:
        f.write(code)
    return f"Script '{name}' saved."

def load_script(name):
    path = os.path.join(SCRIPTS_DIR, name + ".py")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read()

def run_code(code):
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        return "Code executed successfully."
    except Exception as e:
        return f"Error: {e}"

def handle_command(cmd):
    parts = cmd.strip().split(" ", 1)
    action = parts[0].upper()

    if action == "HELP":
        return (
            "Commands:\n"
            "RUN <code> - Execute Python code\n"
            "SAVE <name> - Save last code\n"
            "LOAD <name> - Load and print script\n"
            "LIST - List saved scripts\n"
            "LOG - Show previous commands\n"
            "HELP - Show this help"
        )
    elif action == "LIST":
        return "\n".join(list_scripts())
    elif action == "LOG":
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
                return json.dumps(logs[-5:], indent=2)
        return "No logs found."
    elif action == "SAVE" and len(parts) > 1:
        if not last_code.strip():
            return "No code to save."
        return save_script(parts[1], last_code)
    elif action == "LOAD" and len(parts) > 1:
        loaded = load_script(parts[1])
        return loaded if loaded else "Script not found."
    elif action == "RUN" and len(parts) > 1:
        global last_code
        last_code = parts[1]
        result = run_code(last_code)
        save_log({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "command": "RUN",
            "code": last_code,
            "result": result
        })
        return result
    else:
        return "Invalid command. Type HELP for options."

# Initialize
last_code = ""

if __name__ == "__main__":
    print("🧠 PDE Kernel v1.0 – Python Development Environment Runtime")
    print("Type HELP for commands.\n")

    while True:
        try:
            cmd = input(">> ")
            output = handle_command(cmd)
            print(output)
        except KeyboardInterrupt:
            print("\nExiting PDE Kernel.")
            break
