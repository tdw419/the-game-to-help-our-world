import os
import time
from typing import Dict, Any, Tuple

# Import the interpreter and generator components
from canvas_interpreter import CanvasInterpreter
from snapshot_generator_ai_action import SnapshotGenerator, COLOR_AGENT, PIXEL_FONT_REVERSE, PIXEL_FONT, CHAR_WIDTH, CHAR_SPACING

# --- Configuration ---
SNAPSHOTS_DIR = "coloros_pxl_snapshots"
INITIAL_SNAPSHOT_FILENAME = "snapshot_001_intro.pxl.png"
LOOP_DELAY_SECONDS = 1.0 # Delay between AI steps
MAX_LOOP_ITERATIONS = 50 # Prevent infinite loops during initial testing

# --- AI's Internal State & Logic ---
class ColorOS_AI:
    def __init__(self, interpreter: CanvasInterpreter, generator: SnapshotGenerator):
        self.interpreter = interpreter
        self.generator = generator
        self.current_snapshot_path = os.path.join(SNAPSHOTS_DIR, INITIAL_SNAPSHOT_FILENAME)
        self.ai_internal_state = {} # AI's internal representation of the world
        self.loop_iteration = 0
        self.action_history = [] # For internal self-reflection (future)

    def _log(self, message: str, level: str = "INFO"):
        """Simple logging function for AI's internal thoughts."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] AI Core [{level}]: {message}")

    async def perceive(self) -> Dict[str, Any]:
        """AI perceives the current snapshot."""
        try:
            self.interpreter.image_path = self.current_snapshot_path # Update interpreter's source
            interpreted_state = self.interpreter.interpret_snapshot()
            self._log(f"Perceived snapshot: {interpreted_state['filename']}")
            return interpreted_state
        except FileNotFoundError:
            self._log(f"Error: Snapshot not found at {self.current_snapshot_path}. Halting.", "ERROR")
            return None
        except Exception as e:
            self._log(f"Error during perception: {e}. Halting.", "ERROR")
            return None

    async def decide(self, interpreted_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI makes a decision based on the interpreted state.
        This is where the AI's 'intelligence' resides.
        For now, simple rule-based logic.
        """
        self._log("Analyzing perceived state to make a decision...")

        current_agent_pos = interpreted_state.get("agent_position")
        prompt_text = interpreted_state.get("prompt_text", "").strip()
        
        new_prompt_text = prompt_text # Default to keeping old prompt
        agent_new_pos = current_agent_pos # Default to no movement
        grid_pixel_updates = []
        control_zone_new_signals = []

        if not current_agent_pos:
            self._log("No agent found. Attempting to place one.", "WARN")
            agent_new_pos = {"x": 0, "y": 0} # Place agent at (0,0) if missing
            new_prompt_text = "AGENT PLACED. STARTING."
            return {
                "new_prompt_text": new_prompt_text,
                "agent_new_pos": (agent_new_pos["x"], agent_new_pos["y"]),
                "grid_pixel_updates": grid_pixel_updates,
                "control_zone_new_signals": control_zone_new_signals
            }

        # --- Simple AI Logic Examples ---

        # Logic 1: Respond to "Describe next action" prompt (from Snapshot 001 goal)
        if "DESCRIBE YOUR NEXT ACTION" in prompt_text.upper():
            self._log("Prompt detected: Describe next action. Deciding to move right.", "DEBUG")
            agent_new_pos = (current_agent_pos["x"] + 1, current_agent_pos["y"])
            new_prompt_text = "ACTION: MOVED RIGHT. READY."
            self.ai_internal_state["last_action"] = "MOVE_RIGHT"

        # Logic 2: Move towards a goal (from Snapshot 002 goal)
        elif interpreted_state.get("goal_zone"):
            goal = interpreted_state["goal_zone"][0] # Just take the first goal
            self._log(f"Goal detected at ({goal['x']},{goal['y']}). Planning movement.", "DEBUG")
            
            dx = goal["x"] - current_agent_pos["x"]
            dy = goal["y"] - current_agent_pos["y"]
            
            if abs(dx) > abs(dy): # Move horizontally first
                if dx > 0:
                    agent_new_pos = (current_agent_pos["x"] + 1, current_agent_pos["y"])
                    new_prompt_text = f"MOVING TOWARDS GOAL. X:{agent_new_pos[0]} Y:{agent_new_pos[1]}."
                else:
                    agent_new_pos = (current_agent_pos["x"] - 1, current_agent_pos["y"])
                    new_prompt_text = f"MOVING TOWARDS GOAL. X:{agent_new_pos[0]} Y:{agent_new_pos[1]}."
            elif dy != 0: # Then vertically
                if dy > 0:
                    agent_new_pos = (current_agent_pos["x"], current_agent_pos["y"] + 1)
                    new_prompt_text = f"MOVING TOWARDS GOAL. X:{agent_new_pos[0]} Y:{agent_new_pos[1]}."
                else:
                    agent_new_pos = (current_agent_pos["x"], current_agent_pos["y"] - 1)
                    new_prompt_text = f"MOVING TOWARDS GOAL. X:{agent_new_pos[0]} Y:{agent_new_pos[1]}."
            else:
                new_prompt_text = "AT GOAL. MISSION COMPLETE."
                self._log("AI reached goal!", "SUCCESS")
                # Optionally, place a HALT opcode or signal completion
                # For now, it will just stay at the goal.

        # Logic 3: Activate ColorShim (from Snapshot 003 goal)
        elif "ACTIVATE COLORSHIM PROTOCOL" in prompt_text.upper():
            self._log("Prompt detected: Activate ColorShim. Signaling PYTHON_REQUEST.", "DEBUG")
            # Signal PYTHON_REQUEST at a fixed control zone pixel (e.g., (0,0) in control zone)
            control_zone_new_signals.append((0, 0, (255, 165, 0))) # Orange for PYTHON_REQUEST
            new_prompt_text = "COLORSHIM ACTIVATION SIGNALED."
            self.ai_internal_state["colorshim_active"] = True

        # Default: If no specific logic, just move right to explore
        else:
            self._log("No specific prompt or goal. Exploring by moving right.", "DEBUG")
            agent_new_pos = (current_agent_pos["x"] + 1, current_agent_pos["y"])
            new_prompt_text = f"EXPLORING. X:{agent_new_pos[0]} Y:{agent_new_pos[1]}."
            self.ai_internal_state["last_action"] = "EXPLORE_RIGHT"


        # Ensure agent stays within canvas bounds
        if agent_new_pos:
            agent_new_pos = (
                max(0, min(agent_new_pos[0], interpreted_state["image_dimensions"]["width"] - LEGEND_AREA_WIDTH - 1)),
                max(0, min(agent_new_pos[1], interpreted_state["image_dimensions"]["height"] - PROMPT_ROW_HEIGHT - CONTROL_ZONE_HEIGHT - LINE_SPACING - 1))
            )
            # If agent moves to the very right edge, wrap to next line
            if agent_new_pos[0] >= interpreted_state["image_dimensions"]["width"] - LEGEND_AREA_WIDTH - 1 and self.ai_internal_state.get("last_action") == "EXPLORE_RIGHT":
                 agent_new_pos = (0, agent_new_pos[1] + 1)
                 new_prompt_text += " WRAP."
                 self._log("AI wrapped to next line.", "DEBUG")

        return {
            "new_prompt_text": new_prompt_text,
            "agent_new_pos": agent_new_pos,
            "grid_pixel_updates": grid_pixel_updates,
            "control_zone_new_signals": control_zone_new_signals
        }

    async def act(self, action_plan: Dict[str, Any], initial_interpreted_state: Dict[str, Any]) -> str:
        """AI acts by generating a new snapshot."""
        self._log("Generating new snapshot based on action plan...")
        
        # Pass the original interpreted state's legend items to maintain them
        legend_items = []
        # This is a bit of a hack: the initial generator script puts legend items in the interpreted state.
        # A more robust system would have legend items as a separate configuration.
        # For now, we'll try to extract them if they are present in the initial state.
        # In a real system, the AI might also be able to modify its own legend.
        if 'legend_items' in initial_interpreted_state:
            legend_items = initial_interpreted_state['legend_items']
        else: # Fallback to a common set if not in interpreted state
            legend_items = [
                (COLOR_AGENT, "AGENT"),
                (COLOR_GOAL, "GOAL ZONE"),
                (COLOR_PROMPT_TEXT_ON, "PROMPT TEXT"),
                (COLOR_CONTROL_OPCODE, "CONTROL OP"),
                (COLOR_PYTHON_REQUEST, "PYTHON REQUEST")
            ]


        next_snapshot_filename = f"snapshot_{self.loop_iteration:03d}_ai_action.pxl.png"
        generated_path = self.generator.generate_snapshot_from_state(
            filename=next_snapshot_filename,
            interpreted_state=initial_interpreted_state, # Pass original state for context
            new_prompt_text=action_plan["new_prompt_text"],
            agent_new_pos=action_plan["agent_new_pos"],
            grid_pixel_updates=action_plan["grid_pixel_updates"],
            control_zone_new_signals=action_plan["control_zone_new_signals"]
        )
        self._log(f"Action complete. New snapshot: {generated_path}", "SUCCESS")
        return generated_path

    async def run_loop(self):
        """Runs the main autonomous AI loop."""
        self._log("Color OS AI Core Loop starting...", "SYSTEM")
        
        # Initial perception to get the first state
        initial_state = await self.perceive()
        if not initial_state:
            self._log("Initial snapshot could not be perceived. Exiting.", "ERROR")
            return

        # Ensure the initial state has legend items for the generator
        if 'legend_items' not in initial_state:
            initial_state['legend_items'] = [ # Default legend items if not present
                (COLOR_AGENT, "AGENT"),
                (COLOR_GOAL, "GOAL ZONE"),
                (COLOR_PROMPT_TEXT_ON, "PROMPT TEXT"),
                (COLOR_CONTROL_OPCODE, "CONTROL OP"),
                (COLOR_PYTHON_REQUEST, "PYTHON REQUEST")
            ]


        # Main loop
        while self.loop_iteration < MAX_LOOP_ITERATIONS:
            self.loop_iteration += 1
            self._log(f"--- Loop Iteration {self.loop_iteration} ---")

            # 1. Perceive
            interpreted_state = await self.perceive()
            if not interpreted_state:
                break # Exit loop on perception error

            # 2. Decide
            action_plan = await self.decide(interpreted_state)

            # 3. Act
            new_snapshot_path = await self.act(action_plan, interpreted_state)
            self.current_snapshot_path = new_snapshot_path # Update for next iteration

            # Check for HALT condition (AI writes HALT opcode)
            # This requires the interpreter to detect HALT and the generator to write it.
            # For now, we'll rely on MAX_LOOP_ITERATIONS.
            # In future: interpreted_state.get("halt_signal", False)

            time.sleep(LOOP_DELAY_SECONDS)

        self._log("Color OS AI Core Loop finished.", "SYSTEM")

# --- Main Execution ---
if __name__ == "__main__":
    # Create the snapshots directory if it doesn't exist
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    # Ensure initial snapshot exists
    if not os.path.exists(os.path.join(SNAPSHOTS_DIR, INITIAL_SNAPSHOT_FILENAME)):
        print(f"Initial snapshot '{INITIAL_SNAPSHOT_FILENAME}' not found.")
        print("Please run 'python snapshot_generator_code.py' first to create the initial snapshots.")
        exit()

    # Initialize components
    interpreter = CanvasInterpreter(os.path.join(SNAPSHOTS_DIR, INITIAL_SNAPSHOT_FILENAME))
    generator = SnapshotGenerator()

    # Create and run the AI
    ai_core = ColorOS_AI(interpreter, generator)
    import asyncio
    asyncio.run(ai_core.run_loop())

