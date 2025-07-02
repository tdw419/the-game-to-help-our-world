# PXRoadmapMutator.gd
# This module provides the core logic for mutating RRE roadmaps.
# It can load a roadmap, apply various mutation rules to its steps,
# and return a new, mutated version of the roadmap.
#
# UPDATED: Designed to respond to fitness degradation alerts and
# to store mutated variants with new names.

extends Node

# --- Configuration ---
# Chance (0.0 to 1.0) for each step to be mutated.
@export var step_mutation_chance: float = 0.3

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging mutation activity
@onready var px_scroll_library: PXScrollLibrary = get_node_or_null("../PXScrollLibrary") # To load/save roadmaps
@onready var px_fs_writer: PXFSWriter = get_node_or_null("../PXFSWriter") # To write mutated roadmaps to PXFS

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log or not px_scroll_library or not px_fs_writer:
        print_err("PXRoadmapMutator: Essential dependencies missing. Mutator disabled.")
        set_process(false)
        return

    print("PXRoadmapMutator: Initialized. Ready to mutate roadmaps.")
    # Seed random number generator
    seed(hash(str(OS.get_unix_time_from_system())))

# --- Core Mutation API ---

func mutate_and_save_roadmap(original_roadmap_name: String, mutation_context: Dictionary = {}) -> String:
    """
    Loads an existing roadmap, applies mutations, and saves the new variant to PXFS.

    Args:
        original_roadmap_name (String): The name of the roadmap to load from PXScrollLibrary.
        mutation_context (Dictionary): Context to influence mutation (e.g., "fitness_score", "alert_type").

    Returns:
        String: The name of the newly created mutated roadmap, or empty string on failure.
    """
    _log_mutator_activity("Initiating mutation for roadmap: '" + original_roadmap_name + "'")

    var original_roadmap_steps = px_scroll_library.load_scroll(original_roadmap_name)
    if original_roadmap_steps.is_empty():
        _log_mutator_activity("ERROR: Original roadmap '" + original_roadmap_name + "' not found.")
        return ""

    var mutated_roadmap_steps = _apply_mutation_rules(original_roadmap_steps, mutation_context)
    
    # Generate a new name for the mutated roadmap
    var new_roadmap_name = original_roadmap_name + "_mutated_" + str(int(OS.get_unix_time_from_system() % 10000))
    
    # Save the mutated roadmap to PXScrollLibrary
    var success = px_scroll_library.save_scroll(new_roadmap_name, mutated_roadmap_steps)
    
    if success:
        _log_mutator_activity("Roadmap '" + original_roadmap_name + "' mutated to '" + new_roadmap_name + "' and saved.")
        return new_roadmap_name
    else:
        _log_mutator_activity("FAILED to save mutated roadmap '" + new_roadmap_name + "'.")
        return ""

# --- Internal Mutation Rules ---

func _apply_mutation_rules(original_roadmap_steps: Array[String], mutation_context: Dictionary) -> Array[String]:
    """
    Applies various mutation rules to a roadmap based on context.
    """
    var mutated_roadmap: Array[String] = []
    var mutations_applied = 0
    var current_step_mutation_chance = step_mutation_chance

    # Adjust mutation chance based on context
    if mutation_context.has("alert_type"):
        if mutation_context["alert_type"] == "DEGRADATION" or mutation_context["alert_type"] == "PLATEAU":
            current_step_mutation_chance = min(0.8, step_mutation_chance * 1.5) # Increase mutation chance
            _log_mutator_activity("  Increased mutation chance due to " + mutation_context["alert_type"] + " alert.")
    if mutation_context.has("fitness_score") and mutation_context["fitness_score"] < 0: # If fitness is negative
        current_step_mutation_chance = min(0.9, step_mutation_chance * 2.0) # More aggressive mutation
        _log_mutator_activity("  Aggressive mutation due to low fitness score: " + str(snapped(mutation_context["fitness_score"], 0.01)))
    
    # Track original step indices to avoid modifying the same step multiple times in complex mutations
    var original_indices_to_process = Array(range(original_roadmap_steps.size()))
    
    for i in original_indices_to_process:
        var original_step = original_roadmap_steps[i]
        var mutated_step = original_step
        var applied_mutation_type = "none"

        if randf() < current_step_mutation_chance:
            var mutation_types = ["delay_adjust", "log_append", "command_scramble", "insert_export", "remove_step", "duplicate_step"] # Added duplicate_step
            var chosen_mutation = random.choice(mutation_types)

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
                "remove_step":
                    if original_roadmap_steps.size() > 1: # Don't remove if only one step
                        mutated_step = "" # Mark for removal
                        applied_mutation_type = "remove_step"
                "duplicate_step": # NEW mutation type
                    mutated_roadmap.append(original_step) # Duplicate the current step
                    applied_mutation_type = "duplicate_step"
                    _log_mutator_activity("  Step " + str(i) + " duplicated.")
            
            if applied_mutation_type != "none" and applied_mutation_type != "remove_step" and applied_mutation_type != "insert_export" and applied_mutation_type != "duplicate_step":
                _log_mutator_activity("  Step " + str(i) + " mutated (" + applied_mutation_type + "): " + original_step.left(15) + " -> " + mutated_step.left(15))
            
            if applied_mutation_type != "remove_step": # Only append if not removed
                mutated_roadmap.append(mutated_step)
        else:
            mutated_roadmap.append(original_step) # Add original step if not mutated

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

