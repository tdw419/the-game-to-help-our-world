# PXOS Launcher

A pixel-based operating system launcher with a Pygame UI, file menu, and pixel programming tools.

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run the launcher: `python launcher.py`
3. Or build an executable: `pyinstaller --onefile --add-data "apps;apps" launcher.py`

## Usage
- Double-click `dist/launcher.exe` (Windows) or `dist/launcher` (macOS/Linux).
- Press Enter to input commands (e.g., `detect_pci`, `pxbot:create:pixel_art:hello_world`).
- Press F1 to open the file menu (navigate with Up/Down, select with Enter).
- Use arrow keys for command history, Tab for autocompletion.
- Type `launch_gui` to open the Tkinter interface.
- Check `pxbot_code/pxos_log.txt` for errors if the launcher closes unexpectedly.

## File Menu
- **Open App**: Browse and load apps from `apps/`.
- **Recent Apps**: Access up to 5 recently loaded apps.
- **Exit**: Close the launcher.

## Commands
- `detect_pci`: List PCI devices.
- `pxbot:save:[name]:[code]`: Save code as PNG.
- `pxbot:create:pixel_art:[code_name]`: Generate pixel art.
- `pxbot:create:pattern:[type]:[size]`: Create patterns (gradient, checkerboard, spiral, diamond).
- `px://[command]`: Pixel-native commands.

## Files
- `pxbot_code/`: Stores PNGs, logs (`pxos_log.txt`), AI state (`ai_state.json`), and recent apps (`recent_apps.json`).
- `apps/`: Contains application modules (e.g., `pxos_app.py`).