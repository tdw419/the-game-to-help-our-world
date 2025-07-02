# pxos_host_runtime.py
import struct
import time
import os

# --- PXOS Simulation Configuration (adjust based on your setup) ---
PXOS_RAM_SIZE = 0x10000  # 64 KB
PXOS_RAM = bytearray(PXOS_RAM_SIZE) # Simulate PXOS's main RAM
DUMP_FILE = "pxos_ram_dump.bin"
LOG_FILE = "pxlogs/agent_activity.pxtalk" # Path to PXOS's activity log
INTERACTION_SIGNAL_FILE = "pxos_interaction_signal.log" # File Godot writes to

# --- Simulate PXOS Global Variables (mirroring pxos_constants.pxtalk for the host) ---
# In a real setup, PXOS might expose these via shared memory or a custom IPC.
# Here, we'll just conceptually set values in PXOS_RAM that PXOS agents would read.
# Assuming PXOS reads these from specific RAM locations.
PXOS_GLOBAL_VAR_ADDRS = {
    "_agent_msg_type": 0x0000, # Example: Global message type
    "_agent_msg_target_id": 0x0001, # Example: Message target
    "_agent_msg_payload_ptr": 0x0002, # Example: Message payload (address)
    "MSG_REQUEST_AGENT_HELP": 0x45, # Example message type constant
    "AGENT_ID_FUNCTION_SCANNER": 0x0C, # Example agent ID
}

def set_pxos_global_var(var_name, value):
    """Conceptually sets a global variable within PXOS's simulated RAM."""
    if var_name in PXOS_GLOBAL_VAR_ADDRS:
        addr = PXOS_GLOBAL_VAR_ADDRS[var_name]
        PXOS_RAM[addr] = value # Assuming 1-byte variables for simplicity
    else:
        print(f"[HOST] Warning: PXOS global variable '{var_name}' address not mapped.")

def get_pxos_global_var(var_name):
    """Conceptually gets a global variable's value from PXOS's simulated RAM."""
    if var_name in PXOS_GLOBAL_VAR_ADDRS:
        addr = PXOS_GLOBAL_VAR_ADDRS[var_name]
        return PXOS_RAM[addr]
    return 0 # Default

def handle_pxos_log(log_line):
    # ... (existing RAM Dumper handling) ...
    if "PXTOOL: RAM Dumper complete." in log_line:
        print("[HOST] Dump command received. Saving RAM...")
        save_ram_dump()

# --- Monitor Godot's Interaction Signals ---
_last_interaction_file_pos = 0

def monitor_godot_interactions():
    global _last_interaction_file_pos
    if not os.path.exists(INTERACTION_SIGNAL_FILE):
        return

    try:
        with open(INTERACTION_SIGNAL_FILE, "r") as f:
            f.seek(_last_interaction_file_pos)
            new_lines = f.readlines()
            for line in new_lines:
                _process_godot_signal(line.strip())
            _last_interaction_file_pos = f.tell()
    except Exception as e:
        print(f"[HOST] Error reading interaction file: {e}")

def _process_godot_signal(signal_data):
    print(f"[HOST] Received Godot signal: {signal_data}")
    parts = signal_data.split(':')
    if len(parts) == 3:
        signal_type = parts[0]
        address = int(parts[1], 16)
        value = int(parts[2], 16)

        if signal_type == "CLICK":
            print(f"[HOST] User clicked memory at 0x{address:X}, value 0x{value:X}. Signaling PXOS...")
            # --- Signal PXOS RRE to act on user intent ---
            # Set global PXOS variables that agents monitor
            set_pxos_global_var("_agent_msg_type", PXOS_GLOBAL_VAR_ADDRS["MSG_REQUEST_AGENT_HELP"]) # Signal a help request
            set_pxos_global_var("_agent_msg_target_id", PXOS_GLOBAL_VAR_ADDRS["AGENT_ID_FUNCTION_SCANNER"]) # Request func scanner
            set_pxos_global_var("_agent_msg_payload_ptr", address) # Payload is the clicked address
            print("[HOST] PXOS globals updated for user click intent.")
            # Clear the signal file after processing to avoid re-processing on next tick
            with open(INTERACTION_SIGNAL_FILE, "w") as f:
                f.write("") # Clear the file
            _last_interaction_file_pos = 0 # Reset file pointer

# ... (save_ram_dump function, pxos_runtime_sim function) ...

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    # Ensure interaction file exists and is cleared on start
    with open(INTERACTION_SIGNAL_FILE, "w") as f:
        f.write("")
    
    # Initialize some dummy RAM data
    PXOS_RAM[PXOS_GLOBAL_VAR_ADDRS["_qemu_mem_base"] + 0] = PXOS_GLOBAL_VAR_ADDRS["FUNC_PROLOGUE_BYTE_1"]
    PXOS_RAM[PXOS_GLOBAL_VAR_ADDRS["_qemu_mem_base"] + 1] = PXOS_GLOBAL_VAR_ADDRS["FUNC_PROLOGUE_BYTE_2"]
    PXOS_RAM[PXOS_GLOBAL_VAR_ADDRS["_qemu_mem_base"] + 2] = PXOS_GLOBAL_VAR_ADDRS["FUNC_PROLOGUE_BYTE_3"]
    PXOS_RAM[PXOS_GLOBAL_VAR_ADDRS["_qemu_mem_base"] + 10] = PXOS_GLOBAL_VAR_ADDRS["PX_OP_HALT"]


    # Simulate main PXOS loop
    _tick_counter = 0
    while True:
        _tick_counter += 1
        # Simulate PXOS activity
        PXOS_RAM[0] = (_tick_counter % 256) # Simple RAM change
        PXOS_RAM[PXOS_GLOBAL_VAR_ADDRS["_agent_state"]] = (_tick_counter % 9) # Simulate agent state changes

        # Simulate PXOS writing logs (e.g., from an agent)
        if _tick_counter % 5 == 0:
            with open(LOG_FILE, "a") as f:
                f.write(f"AGENT_LOG: Tick {_tick_counter}, Agent State: {get_pxos_global_var('_agent_state')}, Msg: {get_pxos_global_var('_agent_msg_type')}\n")
                if _tick_counter % 20 == 0: # Simulate a function discovery log
                     f.write(f"FUNC_SCANNER: Function start found at: 0x{PXOS_GLOBAL_VAR_ADDRS['_qemu_mem_base']:X}\n")
                if _tick_counter % 30 == 0: # Simulate a memory diff log
                     f.write(f"MEM_COMPARE: Diff @ address: 0x{PXOS_GLOBAL_VAR_ADDRS['_sandbox_base'] + 10:X} | Val1:0xAA Val2:0xBB\n")

        # Dump RAM periodically for Godot
        if _tick_counter % 10 == 0:
            handle_pxos_log("PXTOOL: RAM Dumper complete. Signal host to save buffer at: 0xE000 to file ID: 25")

        # Monitor Godot's interaction signals
        monitor_godot_interactions()

        time.sleep(0.1) # Simulate PXOS tick