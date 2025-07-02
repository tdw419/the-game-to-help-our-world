
PXOS Interactive Debug Loop (Godot + Python)

Files Included:
- pxos_feature_debugger.gd: Godot 4 visual debugger for PXOS memory.
- pxos_host_runtime.py: Simulated PXOS runner that handles interaction signals.
- pxos_constants.pxtalk (optional): Simulated constants used in memory labeling.
- README.txt: This file.

Instructions:
1. Open the Godot project (you must create a basic scene with a TextureRect named "MemoryTextureRect"
   and a Label named "HoverDisplayLabel" to attach pxos_feature_debugger.gd).
2. Run pxos_host_runtime.py in your terminal.
3. Interact with the memory map in Godot. Clicks will signal the Python runtime to trigger agent behavior.
