# PXRoadmapMutator.gd
# This module provides the core logic for mutating RRE roadmaps.
# It can load a roadmap, apply various mutation rules to its steps,
# and return a new, mutated version of the roadmap.

extends Node

# --- Configuration ---
# Chance (0.0 to 1.0) for each step to be mutated.
@export var step_mutation_chance: float = 0.3

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging mutation activity

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_warn("PXRoadmapMutator: PXScrollLog not found. Mutation logs will go to console.")

    print("PXRoadmapMutator: Initialized. Ready to mutate roadmaps.")
    # Seed random number generator
    seed(hash(str(OS.get_unix_time_from_system())))

# --- Core Mutation API ---

func mutate_roadmap(original_roadmap_steps: Array[String], mutation_context: Dictionary = {}) -> Array[String]:
    """
    Applies various mutation rules to a roadmap and returns a new, mutated version.

    Args:
        original_roadmap_steps (Array[String]): The original roadmap steps.
        mutation_context (Dictionary): Optional context (e.g., "failure_count", "emotion_state")
                                       to influence mutation strategy.

    Returns:
        Array[String]: The new, mutated roadmap steps.
    """
    _log_mutator_activity("Initiating roadmap mutation (original size: " + str(original_roadmap_steps.size()) + ").")
    var mutated_roadmap: Array[String] = []
    var mutations_applied = 0

    for i in range(original_roadmap_steps.size()):
        var original_step = original_roadmap_steps[i]
        var mutated_step = original_step
        var applied_mutation_type = "none"

        if randf() < step_mutation_chance:
            # Apply a random mutation type
            var mutation_types = ["delay_adjust", "log_append", "command_scramble", "insert_export"]
            var chosen_mutation = random.choice(mutation_types) # Godot's random.choice

            match chosen_mutation:
                "delay_adjust":
                    if original_step.begins_with(":: EXECUTE DELAY "):
                        var current_delay_str = original_step.replace(":: EXECUTE DELAY ", "").strip_edges()
                        if current_delay_str.is_valid_float():
                            var current_delay = current_delay_str.to_float()
                            var new_delay = max(0.1, current_delay + randf() * 2.0 - 1.0) # Adjust by +/- 1.0
                            mutated_step = ":: EXECUTE DELAY " + str(snapped(new_delay, 0.1))
                            applied_mutation_type = "delay_adjust"
                "log_append":
                    if original_step.begins_with(":: EXECUTE LOG:"):
                        var append_char = random.choice([" •", " ✓", " ✗", " ~"])
                        mutated_step = original_step + append_char
                        applied_mutation_type = "log_append"
                "command_scramble":
                    # Simple conceptual scramble: change WRITE to LOG, or vice-versa
                    if original_step.begins_with(":: EXECUTE WRITE "):
                        mutated_step = original_step.replace(":: EXECUTE WRITE ", ":: EXECUTE LOG:MUTATED_WRITE ")
                        applied_mutation_type = "command_scramble"
                    elif original_step.begins_with(":: EXECUTE LOG:"):
                        mutated_step = original_step.replace(":: EXECUTE LOG:", ":: EXECUTE WRITE ")
                        applied_mutation_type = "command_scramble"
                "insert_export":
                    # Insert an EXPORT_STATE command before this step
                    mutated_roadmap.append(":: EXECUTE EXPORT_STATE:Mutation_Check_" + str(OS.get_unix_time_from_system()))
                    applied_mutation_type = "insert_export"
                    # Note: The current step will also be added after this insertion.

            if applied_mutation_type != "none":
                mutations_applied += 1
                _log_mutator_activity("  Step " + str(i) + " mutated (" + applied_mutation_type + "): " + original_step.left(15) + " -> " + mutated_step.left(15))
        
        mutated_roadmap.append(mutated_step)

    _log_mutator_activity("Roadmap mutation complete. Applied " + str(mutations_applied) + " mutations.")
    return mutated_roadmap

# --- Logging ---

func _log_mutator_activity(message: String):
    """
    Helper function to log mutator activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MUTATOR: " + message)
    else:
        print("PXRoadmapMutator (Console Log): ", message)

