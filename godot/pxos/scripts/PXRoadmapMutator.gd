# PXRoadmapMutator.gd
# This script enables PXOS to dynamically modify its own roadmaps,
# allowing for self-evolution and adaptation directly in pixel memory.
# It provides functions to insert, remove, or modify roadmap steps.

extends Node

# --- Dependencies ---
@onready var px_roadmap_memory: PXRoadmapMemoryRegion = get_node_or_null("../PXRoadmapMemory") # Reference to the roadmap storage
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging mutations

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_roadmap_memory:
        print_err("PXRoadmapMutator: PXRoadmapMemoryRegion node not found. Mutation capabilities disabled.")
        set_process(false)
        return
    if not px_scroll_log:
        print_warn("PXRoadmapMutator: PXScrollLog not found. Mutation logs will go to console.")

    print("PXRoadmapMutator: Initialized. Ready to mutate roadmaps.")

# --- Core Mutation API ---

func insert_step(step_index: int, new_step: String) -> bool:
    """
    Inserts a new roadmap step at a specific index in the currently stored roadmap.

    Args:
        step_index (int): The index at which to insert the new step.
        new_step (String): The new roadmap step string (e.g., "WRITE HELLO").

    Returns:
        bool: True if the step was successfully inserted and written, false otherwise.
    """
    if not px_roadmap_memory: return false

    var current_roadmap = px_roadmap_memory.read_roadmap_from_memory()
    step_index = clamp(step_index, 0, current_roadmap.size()) # Clamp to valid range

    current_roadmap.insert(step_index, new_step)

    _log_mutation_activity("INSERT at " + str(step_index) + ": " + new_step.left(10))
    return px_roadmap_memory.write_roadmap_to_memory(current_roadmap)


func remove_step(step_index: int) -> bool:
    """
    Removes a roadmap step at a specific index from the currently stored roadmap.

    Args:
        step_index (int): The index of the step to remove.

    Returns:
        bool: True if the step was successfully removed and written, false otherwise.
    """
    if not px_roadmap_memory: return false

    var current_roadmap = px_roadmap_memory.read_roadmap_from_memory()
    if step_index < 0 or step_index >= current_roadmap.size():
        print_warn("PXRoadmapMutator: Cannot remove step. Index ", step_index, " out of bounds (roadmap size: ", current_roadmap.size(), ").")
        return false

    var removed_step = current_roadmap.pop_at(step_index)
    _log_mutation_activity("REMOVE at " + str(step_index) + ": " + removed_step.left(10))
    return px_roadmap_memory.write_roadmap_to_memory(current_roadmap)


func modify_step(step_index: int, new_step_content: String) -> bool:
    """
    Modifies an existing roadmap step at a specific index.

    Args:
        step_index (int): The index of the step to modify.
        new_step_content (String): The new content for the roadmap step.

    Returns:
        bool: True if the step was successfully modified and written, false otherwise.
    """
    if not px_roadmap_memory: return false

    var current_roadmap = px_roadmap_memory.read_roadmap_from_memory()
    if step_index < 0 or step_index >= current_roadmap.size():
        print_warn("PXRoadmapMutator: Cannot modify step. Index ", step_index, " out of bounds (roadmap size: ", current_roadmap.size(), ").")
        return false

    var old_step_content = current_roadmap[step_index]
    current_roadmap[step_index] = new_step_content
    _log_mutation_activity("MODIFY at " + str(step_index) + ": '" + old_step_content.left(10) + "' -> '" + new_step_content.left(10) + "'")
    return px_roadmap_memory.write_roadmap_to_memory(current_roadmap)


func clear_roadmap() -> bool:
    """
    Clears the entire roadmap stored in memory.

    Returns:
        bool: True if the roadmap was successfully cleared, false otherwise.
    """
    if not px_roadmap_memory: return false
    _log_mutation_activity("CLEAR entire roadmap.")
    return px_roadmap_memory.write_roadmap_to_memory([]) # Write an empty roadmap


# --- Helper Functions ---

func _log_mutation_activity(message: String):
    """
    Helper function to log mutation activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MUTATE: " + message)
    else:
        print("PXRoadmapMutator (Console Log): ", message)

