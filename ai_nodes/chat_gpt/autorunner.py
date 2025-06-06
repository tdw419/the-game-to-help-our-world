# autorunner.py
# Autonomous AI loop for Color OS

import time
import json
import os
from datetime import datetime

# === CONFIGURATION ===
TASK_DESCRIPTION = "Start building apps for Color OS."
STATE_FILE = "vault/session_state.json"
LOG_FILE = "vault/logs/autorun_session.json"
MAX_STEPS = 1000
CHECKPOINT_INTERVAL = 10
RATE_LIMIT_SECONDS = 3

# === LOAD STATE ===
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    step = state.get("step", 0)
    current_input = state.get("last_output", TASK_DESCRIPTION)
    paused = state.get("paused", False)
else:
    step = 0
    current_input = TASK_DESCRIPTION
    paused = False

if paused:
    print("Paused at checkpoint. Awaiting user input to resume.")
    exit()

# === LOAD LOG ===
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        log = json.load(f)
else:
    log = []

# === AI SIMULATION ===
def run_ai(input_text):
    # Replace this with actual model or API
    return f"[AI]: Continuing from: '{input_text}'"

# === MAIN LOOP ===
print(f"Starting autonomous loop from step {step}...")

while step < MAX_STEPS:
    step += 1

    result = run_ai(current_input)
    timestamp = datetime.utcnow().isoformat()

    entry = {
        "step": step,
        "timestamp": timestamp,
        "input": current_input,
        "output": result
    }
    log.append(entry)
    print(f"Step {step}: {result}")

    # Save log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    # Save state
    paused = (step % CHECKPOINT_INTERVAL == 0)
    state = {
        "step": step,
        "last_output": result,
        "paused": paused
    }
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    if paused:
        print(f"Checkpoint reached at step {step}. Pausing for review.")
        break

    current_input = result
    time.sleep(RATE_LIMIT_SECONDS)

print("Loop complete or paused.")
