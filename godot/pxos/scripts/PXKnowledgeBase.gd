# PXKnowledgeBase.gd
# This module acts as a persistent repository for PXOS's learned knowledge,
# specifically storing high-fitness roadmap fragments or full roadmaps.
# It enables the synthesis of new, effective strategies by recombining
# successful logic and provides a foundation for "reasoned creation."

extends Node

# --- Configuration ---
# The filename within PXFS where the knowledge base will be stored.
@export var knowledge_base_filename: String = "knowledge_base.json"

# Minimum fitness score for a roadmap/fragment to be considered "knowledge" and stored.
@export var knowledge_min_fitness_score: float = 5.0

# --- Dependencies ---
@onready var px_fs_writer: PXFSWriter = get_node_or_null("../PXFSWriter") # To write to PXFS
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read from PXFS
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging KB activity

# --- Internal State ---
# Cache of knowledge entries: Array[Dictionary]
# Each entry: { "name": str, "type": str, "content": Array[str], "fitness_score": float, "timestamp": float, "metadata": dict }
var _knowledge_cache: Array[Dictionary] = []

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_fs_writer or not px_fs_reader or not px_scroll_log:
        print_err("PXKnowledgeBase: Essential dependencies missing. Knowledge Base disabled.")
        set_process(false)
        return

    print("PXKnowledgeBase: Initialized. Ready to store and retrieve knowledge.")
    # Ensure the KB file exists and load its content into cache
    _ensure_kb_file_exists_and_load()

# --- Core Knowledge Base API ---

func store_knowledge(
    name: String,
    type: String, # "roadmap", "fragment", "pattern"
    content: Array[String], # The roadmap steps or fragment lines
    fitness_score: float,
    metadata: Dictionary = {} # Additional context like goal_type, source_roadmap, etc.
) -> bool:
    """
    Stores a piece of knowledge (roadmap, fragment, etc.) into the knowledge base.
    Only stores if fitness_score meets the minimum threshold.

    Args:
        name (String): A unique name for this piece of knowledge.
        type (String): The type of knowledge ("roadmap", "fragment", "pattern").
        content (Array[String]): The actual content (e.g., roadmap steps).
        fitness_score (float): The fitness score associated with this knowledge.
        metadata (Dictionary): Optional metadata for the knowledge entry.

    Returns:
        bool: True if knowledge was stored, false otherwise (e.g., score too low).
    """
    if fitness_score < knowledge_min_fitness_score:
        _log_kb_activity("SKIPPING: Score too low for '" + name + "' (" + str(snapped(fitness_score,0.01)) + ").")
        return false

    var entry = {
        "name": name,
        "type": type,
        "content": content,
        "fitness_score": snapped(fitness_score, 0.01),
        "timestamp": OS.get_unix_time_from_system(),
        "metadata": metadata
    }

    # Check for existing entry with the same name and update if new one is better
    var existing_index = -1
    for i in range(_knowledge_cache.size()):
        if _knowledge_cache[i].name == name:
            existing_index = i
            break
    
    if existing_index != -1:
        if _knowledge_cache[existing_index].fitness_score < fitness_score:
            _knowledge_cache[existing_index] = entry # Overwrite with better version
            _log_kb_activity("UPDATED: '" + name + "' (Score: " + str(snapped(fitness_score,0.01)) + ").")
        else:
            _log_kb_activity("EXISTING: '" + name + "' is better or equal. Not updating.")
            return false # Existing knowledge is better or equal
    else:
        _knowledge_cache.append(entry)
        _log_kb_activity("STORED: '" + name + "' (Score: " + str(snapped(fitness_score,0.01)) + ").")
    
    _save_kb_to_pxfs() # Persist to PXFS
    return true

func retrieve_knowledge(name: String) -> Dictionary:
    """
    Retrieves a piece of knowledge by its name.

    Returns:
        Dictionary: The knowledge entry, or an empty dictionary if not found.
    """
    for entry in _knowledge_cache:
        if entry.name == name:
            _log_kb_activity("RETRIEVED: '" + name + "'.")
            return entry.duplicate(true) # Return a copy
    _log_kb_activity("NOT FOUND: '" + name + "'.")
    return {}

func get_all_knowledge_by_type(type_filter: String = "") -> Array[Dictionary]:
    """
    Retrieves all knowledge entries, optionally filtered by type.
    """
    var filtered_list: Array[Dictionary] = []
    for entry in _knowledge_cache:
        if type_filter.is_empty() or entry.type == type_filter:
            filtered_list.append(entry.duplicate(true))
    return filtered_list

func get_best_knowledge_for_goal(goal_type: String, type_filter: String = "roadmap") -> Dictionary:
    """
    Retrieves the best piece of knowledge (e.g., roadmap) for a given goal,
    based on fitness score.
    """
    var best_entry: Dictionary = {}
    var highest_score = -INF
    
    for entry in _knowledge_cache:
        if entry.type == type_filter and entry.metadata.has("goal_type") and entry.metadata.goal_type == goal_type:
            if entry.fitness_score > highest_score:
                highest_score = entry.fitness_score
                best_entry = entry.duplicate(true)
    
    if not best_entry.is_empty():
        _log_kb_activity("BEST FOR GOAL '" + goal_type + "': '" + best_entry.name + "' (Score: " + str(snapped(best_entry.fitness_score,0.01)) + ").")
    else:
        _log_kb_activity("No best knowledge found for goal '" + goal_type + "'.")
    return best_entry


# --- Internal File Management ---

func _ensure_kb_file_exists_and_load():
    """Ensures the knowledge base file exists and loads its content into cache."""
    var content = px_fs_reader.read_file_by_name(knowledge_base_filename)
    if content.is_empty() or JSON.parse_string(content) == null:
        _log_kb_activity("Knowledge base file not found or invalid. Creating new one.")
        px_fs_writer.write_file_auto(knowledge_base_filename, "[]", Color(0.0, 0.8, 0.8), Color(0.0, 0.0, 1.0), Color(0.0, 0.5, 0.5)) # Cyan=KB
        _knowledge_cache = []
    else:
        var parse_result = JSON.parse_string(content)
        if parse_result is Array:
            _knowledge_cache = parse_result
            _log_kb_activity("Loaded " + str(_knowledge_cache.size()) + " knowledge entries from PXFS.")
        else:
            print_err("PXKnowledgeBase: Loaded KB file content is not a valid JSON array. Resetting.")
            _knowledge_cache = []
            px_fs_writer.write_file_auto(knowledge_base_filename, "[]", Color(0.0, 0.8, 0.8), Color(0.0, 0.0, 1.0), Color(0.0, 0.5, 0.5))


func _save_kb_to_pxfs():
    """Saves the current cache of knowledge entries to PXFS."""
    var json_content = JSON.stringify(_knowledge_cache, "\t")
    var success = px_fs_writer.write_file_auto(knowledge_base_filename, json_content, Color(0.0, 0.8, 0.8), Color(0.0, 0.0, 1.0), Color(0.0, 0.5, 0.5))
    if success:
        # _log_kb_activity("Knowledge base saved to PXFS.") # Too chatty
        pass
    else:
        _log_kb_activity("ERROR: Failed to save knowledge base to PXFS.")


# --- Logging ---

func _log_kb_activity(message: String):
    """
    Helper function to log knowledge base activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("KB: " + message)
    else:
        print("PXKnowledgeBase (Console Log): ", message)

