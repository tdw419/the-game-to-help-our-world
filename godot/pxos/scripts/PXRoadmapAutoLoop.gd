# PXRoadmapAutoLoop.gd
# Enables PXOS to automatically restart, mutate, or switch roadmaps
# based on execution state, time, or memory conditions.
# Acts as a loop controller for the PXRoadmapExecutor.

extends Node

# --- Dependencies ---
@onready var px_roadmap_executor: PXRoadmapExecutor = get_node_or_null("../PXRoadmapExecutor")
@onready var px_roadmap_memory: PXRoadmapMemoryRegion = get_node_or_null("../PXRoadmapMemory")
@onready var px_roadmap_mutator: PXRoadmapMutator = get_node_or_null("../PXRoadmapMutator")
@onready var px_condition_checker: PXRoadmapConditionChecker = get_node_or_null("../PXRoadmapConditionChecker")
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog")

# --- Config ---
var auto_restart: bool = true            # Re-run roadmap when it finishes
var auto_mutate_on_end: bool = true     # Trigger mutation before restarting
var cycle_delay_sec: float = 1.0        # Delay between roadmap cycles

var watchdog_check_interval: float = 3.0  # Interval to check memory conditions
var max_cycles: int = 99999              # Optional run limit
var cycle_count: int = 0

# --- State ---
var running: bool = false

# --- Godot Lifecycle ---

func _ready():
    if not px_roadmap_executor or not px_roadmap_memory:
        print_err("PXRoadmapAutoLoop: Missing roadmap executor or memory. Auto-loop disabled.")
        return

    print("PXRoadmapAutoLoop: Ready. Starting loop.")
    start_loop()


# --- Main Execution Loop ---

func start_loop():
    running = true
    _run_loop_step()


func stop_loop():
    running = false
    print("PXRoadmapAutoLoop: Stopped.")


func _run_loop_step():
    if not running: return

    if cycle_count >= max_cycles:
        print("PXRoadmapAutoLoop: Max cycles reached.")
        stop_loop()
        return

    cycle_count += 1
    _log_loop("Cycle #" + str(cycle_count))

    # Optionally mutate roadmap before each run
    if auto_mutate_on_end and px_roadmap_mutator:
        _attempt_mutation()

    # Reload and run roadmap from memory
    # This assumes PXRoadmapExecutor has a load_and_execute_roadmap_from_memory() function.
    # If not, you'd need to add it or pass the roadmap directly.
    if px_roadmap_executor:
        px_roadmap_executor.load_and_execute_roadmap_from_memory()

    # Schedule next cycle
    get_tree().create_timer(cycle_delay_sec).timeout.connect(_run_loop_step)


# --- Mutation Strategy (example) ---

func _attempt_mutation():
    if not px_roadmap_memory or not px_roadmap_mutator:
        return

    var roadmap = px_roadmap_memory.read_roadmap_from_memory()

    if roadmap.size() > 2:
        # Insert a mutation at a random position (example)
        var rand_index = randi() % roadmap.size()
        var mutated_step = "LOG MUTATE " + str(rand_index)
        px_roadmap_mutator.modify_step(rand_index, mutated_step)
        _log_loop("Mutated step " + str(rand_index))


# --- Logging ---

func _log_loop(message: String):
    if px_scroll_log:
        px_scroll_log.add_line("LOOP: " + message)
    else:
        print("PXRoadmapAutoLoop: ", message)
