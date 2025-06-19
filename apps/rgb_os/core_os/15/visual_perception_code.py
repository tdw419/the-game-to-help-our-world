import numpy as np
import random
from PIL import Image
import math

class FramebufferEmulator:
    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height
        self.pixels = np.zeros((height, width, 3), dtype=np.uint8)
        self.previous_pixels = np.copy(self.pixels)
        self.original_house_colors = {}  # Store original colors for brightness restoration

    def set_pixel(self, x, y, rgb_color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y, x] = rgb_color

    def get_pixel(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y, x].tolist()
        return None

    def get_region_average_color(self, x1, y1, x2, y2):
        """Get average color of a rectangular region"""
        if not (0 <= x1 < self.width and 0 <= y1 < self.height and 
                0 <= x2 < self.width and 0 <= y2 < self.height):
            return None
        
        region = self.pixels[y1:y2+1, x1:x2+1]
        return np.mean(region, axis=(0, 1)).astype(int).tolist()

    def detect_horizontal_line(self, start_x, start_y, color_threshold=50):
        """Detect horizontal line starting from a point"""
        if not (0 <= start_x < self.width and 0 <= start_y < self.height):
            return 0
        
        start_color = self.get_pixel(start_x, start_y)
        if not start_color:
            return 0
            
        length = 0
        for x in range(start_x, self.width):
            current_color = self.get_pixel(x, start_y)
            if current_color and all(abs(a - b) <= color_threshold for a, b in zip(start_color, current_color)):
                length += 1
            else:
                break
        return length

    def apply_brightness_filter(self, brightness_factor=0.5):
        """Apply brightness filter to entire image"""
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.original_house_colors and not all(self.pixels[y, x] == [0, 0, 0]):
                    self.original_house_colors[(x, y)] = self.pixels[y, x].copy()
                
                if (x, y) in self.original_house_colors:
                    original = self.original_house_colors[(x, y)]
                    dimmed = (original * brightness_factor).astype(np.uint8)
                    self.pixels[y, x] = dimmed

    def restore_brightness(self):
        """Restore original brightness"""
        for (x, y), original_color in self.original_house_colors.items():
            self.pixels[y, x] = original_color

    def get_diffs(self):
        diffs = []
        changed_indices = np.where(self.pixels != self.previous_pixels)
        changed_coords = list(zip(changed_indices[0], changed_indices[1]))
        unique_changed_coords = sorted(list(set(changed_coords)))

        for y, x in unique_changed_coords:
            old_color = self.previous_pixels[y, x].tolist()
            new_color = self.pixels[y, x].tolist()
            if old_color != new_color:
                diffs.append((x, y, old_color, new_color))
        return diffs

    def update_previous_state(self):
        self.previous_pixels = np.copy(self.pixels)

    def save_png(self, filename="8.png"):
        img = Image.fromarray(self.pixels, 'RGB')
        img.save(filename)

class PXTalkVM:
    def __init__(self):
        self.registers = {'REGISTER_A': 0}
        self.memory = {}
        self.output_buffer = []
        self.states = {
            'HOUSE_INITIATED': False, 'FOUNDATION_DRAWN': False, 
            'WALLS_DRAWN': False, 'ROOF_DRAWN': False,
            'LIGHT_ON': False, 'SLEEPING': False,
            'DIMMED': False  # Track visual dimming state
        }
        self.needs = {'ENERGY': 100, 'CLEANLINESS': 100}
        self.mood = 'NEUTRAL'  # HAPPY, NEUTRAL, TIRED, ANGRY
        self.perceived_features = {}  # Store perceived environmental features

    def execute(self, command):
        parts = command.split()
        if not parts:
            return
            
        opcode = parts[0]
        
        if opcode == "PX_SET_PIXEL":
            x, y, r, g, b = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
            framebuffer.set_pixel(x, y, [r, g, b])
            
        elif opcode == "PX_DRAW_RECT":
            x1, y1, x2, y2, r, g, b = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6]), int(parts[7])
            color = [r, g, b]
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    framebuffer.set_pixel(x, y, color)
                    
        elif opcode == "PX_INC":
            reg = parts[1]
            val = int(parts[2])
            if reg in self.registers:
                self.registers[reg] += val
                
        elif opcode == "PX_DEC":
            reg = parts[1]
            val = int(parts[2])
            if reg in self.registers:
                self.registers[reg] -= val
                
        elif opcode == "PX_SET_STATE":
            state_key = parts[1]
            state_value = True if parts[2].upper() == 'TRUE' else False
            if state_key in self.states:
                self.states[state_key] = state_value
                print(f"PXTalkVM: State '{state_key}' set to {state_value}")
                
        elif opcode == "PX_TOGGLE_LIGHT":
            self.states['LIGHT_ON'] = not self.states['LIGHT_ON']
            print(f"PXTalkVM: Light toggled. LIGHT_ON: {self.states['LIGHT_ON']}")
            light_color = [255, 255, 0] if self.states['LIGHT_ON'] else [0, 0, 0]
            framebuffer.set_pixel(30, 30, light_color)
            framebuffer.set_pixel(31, 30, light_color)
            framebuffer.set_pixel(30, 31, light_color)
            framebuffer.set_pixel(31, 31, light_color)
            
        elif opcode == "PX_IF_PIXEL":
            x, y = int(parts[1]), int(parts[2])
            r, g, b = int(parts[3]), int(parts[4]), int(parts[5])
            expected_color = [r, g, b]
            then_command = " ".join(parts[7:])  # Skip "THEN"
            
            current_pixel_color = framebuffer.get_pixel(x, y)
            if current_pixel_color == expected_color:
                print(f"PXTalkVM: PX_IF_PIXEL condition met. Executing: {then_command}")
                self.emit_pxtalk(then_command)
                
        elif opcode == "PX_DECREASE_NEED":
            need_key = parts[1]
            amount = int(parts[2])
            if need_key in self.needs:
                self.needs[need_key] = max(0, self.needs[need_key] - amount)
                print(f"PXTalkVM: {need_key} decreased by {amount}. Current: {self.needs[need_key]}")
                
        elif opcode == "PX_INCREASE_NEED":
            need_key = parts[1]
            amount = int(parts[2])
            if need_key in self.needs:
                self.needs[need_key] = min(100, self.needs[need_key] + amount)
                print(f"PXTalkVM: {need_key} increased by {amount}. Current: {self.needs[need_key]}")
                
        elif opcode == "PX_SET_MOOD":
            new_mood = parts[1]
            self.mood = new_mood
            print(f"PXTalkVM: Mood set to {new_mood}")
            self.update_mood_visualization()
            
        elif opcode == "PX_PERCEIVE_WATER_FEATURE":
            self.perceived_features['WATER'] = True
            print("PXTalkVM: Perceived water feature!")
            # Could trigger need for cleanliness increase
            self.emit_pxtalk("PX_INCREASE_NEED CLEANLINESS 5")
            
        elif opcode == "PX_MEASURE_LINE_LENGTH":
            length = int(parts[1])
            self.perceived_features['PATH_LENGTH'] = length
            print(f"PXTalkVM: Measured path length: {length}")
            
        elif opcode == "PX_DIM_HOUSE":
            if not self.states['DIMMED']:
                framebuffer.apply_brightness_filter(0.3)
                self.states['DIMMED'] = True
                print("PXTalkVM: House dimmed for sleep mode")
                
        elif opcode == "PX_BRIGHTEN_HOUSE":
            if self.states['DIMMED']:
                framebuffer.restore_brightness()
                self.states['DIMMED'] = False
                print("PXTalkVM: House brightness restored")

    def update_mood_visualization(self):
        """Update mood indicator in the house"""
        mood_colors = {
            'HAPPY': [0, 255, 0],      # Green
            'NEUTRAL': [128, 128, 128], # Gray
            'TIRED': [64, 64, 64],     # Dark gray
            'ANGRY': [255, 0, 0]       # Red
        }
        
        mood_color = mood_colors.get(self.mood, [128, 128, 128])
        # Draw mood indicator in top-right corner of house
        framebuffer.set_pixel(50, 15, mood_color)
        framebuffer.set_pixel(51, 15, mood_color)
        framebuffer.set_pixel(50, 16, mood_color)
        framebuffer.set_pixel(51, 16, mood_color)

    def update_mood_based_on_needs(self):
        """Update mood based on current needs"""
        if self.needs['ENERGY'] < 20:
            self.execute("PX_SET_MOOD TIRED")
        elif self.needs['ENERGY'] > 80 and self.needs['CLEANLINESS'] > 80:
            self.execute("PX_SET_MOOD HAPPY")
        elif self.needs['CLEANLINESS'] < 30:
            self.execute("PX_SET_MOOD ANGRY")
        else:
            self.execute("PX_SET_MOOD NEUTRAL")

    def emit_pxtalk(self, command):
        self.output_buffer.append(command)

    def update_visuals_based_on_states(self):
        if self.states['HOUSE_INITIATED'] and not self.states['FOUNDATION_DRAWN']:
            print("PXTalkVM: Drawing foundation...")
            pxtalk_render("PX_DRAW_RECT 5 5 58 58 100 100 100")
            self.emit_pxtalk("PX_SET_STATE FOUNDATION_DRAWN TRUE")

        if self.states['FOUNDATION_DRAWN'] and not self.states['WALLS_DRAWN']:
            print("PXTalkVM: Drawing walls...")
            pxtalk_render("PX_DRAW_RECT 7 7 56 56 200 0 0")
            self.emit_pxtalk("PX_SET_STATE WALLS_DRAWN TRUE")

        if self.states['WALLS_DRAWN'] and not self.states['ROOF_DRAWN']:
            print("PXTalkVM: Drawing roof...")
            pxtalk_render("PX_DRAW_RECT 10 0 53 10 150 75 0")
            self.emit_pxtalk("PX_SET_STATE ROOF_DRAWN TRUE")

    def tick(self):
        print(f"\n--- PXTalkVM TICK Cycle ---")
        
        # 1. Decrease Energy and Cleanliness
        energy_decrease = random.randint(1, 3)
        cleanliness_decrease = random.randint(1, 2)
        self.execute(f"PX_DECREASE_NEED ENERGY {energy_decrease}")
        self.execute(f"PX_DECREASE_NEED CLEANLINESS {cleanliness_decrease}")

        # 2. Update mood based on needs
        self.update_mood_based_on_needs()

        # 3. Decide on actions based on needs and states
        if self.states['HOUSE_INITIATED']:
            if self.needs['ENERGY'] < 20 and not self.states['SLEEPING']:
                print("Junior is tired. Entering sleep mode...")
                self.execute("PX_SET_STATE SLEEPING TRUE")
                self.execute("PX_DIM_HOUSE")
                if self.states['LIGHT_ON']:
                    self.execute("PX_TOGGLE_LIGHT")

            elif self.states['SLEEPING']:
                print("Junior is sleeping... regaining energy.")
                self.execute("PX_INCREASE_NEED ENERGY 8")
                if self.needs['ENERGY'] >= 80:
                    print("Junior has enough energy. Waking up.")
                    self.execute("PX_SET_STATE SLEEPING FALSE")
                    self.execute("PX_BRIGHTEN_HOUSE")

        # 4. Process emitted commands
        for cmd in self.output_buffer:
            self.execute(cmd)
        self.output_buffer = []

        # 5. Update visuals and interpret screen
        self.update_visuals_based_on_states()
        screen_interpreter_agent()

def screen_interpreter_agent():
    """Enhanced screen interpreter with pattern recognition"""
    diffs = framebuffer.get_diffs()

    for x, y, old_color, new_color in diffs:
        # House initiation pattern (2x2 white square at 0,0)
        if x == 0 and y == 1 and new_color == [255, 255, 255]:
            if (framebuffer.get_pixel(0,0) == [255,255,255] and 
                framebuffer.get_pixel(1,0) == [255,255,255] and 
                framebuffer.get_pixel(1,1) == [255,255,255]):
                pxtalk_vm.emit_pxtalk("PX_SET_STATE HOUSE_INITIATED TRUE")
                print("Interpreter: Detected 'INITIATE_HOUSE' pattern.")

        # Light switch detection (red pixel at 2,2)
        if x == 2 and y == 2:
            if new_color == [255, 0, 0] and old_color != [255, 0, 0]:
                pxtalk_vm.emit_pxtalk("PX_TOGGLE_LIGHT")
                print("Interpreter: Light switch activated.")
            elif old_color == [255, 0, 0] and new_color != [255, 0, 0]:
                pxtalk_vm.emit_pxtalk("PX_TOGGLE_LIGHT")
                print("Interpreter: Light switch deactivated.")

    # Region-based pattern detection
    # Check for water feature (blue region at 40,40)
    water_region_color = framebuffer.get_region_average_color(40, 40, 49, 49)
    if water_region_color and water_region_color[2] > 200 and water_region_color[0] < 50 and water_region_color[1] < 50:
        if 'WATER' not in pxtalk_vm.perceived_features:
            pxtalk_vm.emit_pxtalk("PX_PERCEIVE_WATER_FEATURE")

    # Check for horizontal path (line detection)
    path_length = framebuffer.detect_horizontal_line(10, 60)
    if path_length > 5:  # Significant line detected
        if 'PATH_LENGTH' not in pxtalk_vm.perceived_features or pxtalk_vm.perceived_features['PATH_LENGTH'] != path_length:
            pxtalk_vm.emit_pxtalk(f"PX_MEASURE_LINE_LENGTH {path_length}")

    framebuffer.update_previous_state()

def pxtalk_render(command_string):
    pxtalk_vm.execute(command_string)

# Global instances
framebuffer = FramebufferEmulator()
pxtalk_vm = PXTalkVM()

def initialize_juniors_house():
    """Initialize and build Junior's House"""
    print("--- Initializing Junior's House ---")
    
    # Initial trigger pattern
    pxtalk_render("PX_SET_PIXEL 0 0 255 255 255")
    pxtalk_render("PX_SET_PIXEL 1 0 255 255 255")
    pxtalk_render("PX_SET_PIXEL 0 1 255 255 255")
    pxtalk_render("PX_SET_PIXEL 1 1 255 255 255")
    
    # Run build cycles
    for i in range(4):
        screen_interpreter_agent()
        for cmd in pxtalk_vm.output_buffer:
            pxtalk_vm.execute(cmd)
        pxtalk_vm.output_buffer = []
        pxtalk_vm.update_visuals_based_on_states()
    
    framebuffer.save_png("8_house_built_phase4.png")
    print("--- Junior's House Built! ---")

def run_simulation(ticks=15):
    """Run the enhanced simulation with Phase 4 features"""
    print("--- Starting Enhanced Simulation ---")
    
    for tick_count in range(ticks):
        print(f"\n=== SIMULATION TICK {tick_count} ===")
        
        # Add some environmental features for Junior to perceive
        if tick_count == 3:
            # Add water feature
            pxtalk_render("PX_DRAW_RECT 40 40 49 49 0 0 255")
            print("External: Water feature added")
            
        if tick_count == 7:
            # Add horizontal path
            for x in range(10, 25):
                pxtalk_render(f"PX_SET_PIXEL {x} 60 139 69 19")  # Brown path
            print("External: Path added")
        
        if tick_count == 10:
            # Toggle light switch
            pxtalk_render("PX_SET_PIXEL 2 2 255 0 0")
            print("External: Light switch activated")
        
        # Run Junior's autonomous cycle
        pxtalk_vm.tick()
        
        # Save state
        framebuffer.save_png(f"8_enhanced_tick_{tick_count}.png")
        print(f"Energy: {pxtalk_vm.needs['ENERGY']}, Cleanliness: {pxtalk_vm.needs['CLEANLINESS']}")
        print(f"Mood: {pxtalk_vm.mood}, Sleeping: {pxtalk_vm.states['SLEEPING']}")
        print(f"Perceived Features: {pxtalk_vm.perceived_features}")

if __name__ == "__main__":
    # Initialize Junior's House
    initialize_juniors_house()
    
    # Run enhanced simulation
    run_simulation()
    
    print("\n=== PHASE 4 COMPLETE ===")
    print("Junior's House now features:")
    print("- Enhanced visual perception (region and pattern detection)")
    print("- Full house dimming/brightening based on sleep state")
    print("- Mood visualization system")
    print("- Environmental feature recognition")
    print("- Complex autonomous behavior patterns")