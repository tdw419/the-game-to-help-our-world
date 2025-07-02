# PXRoadmapConditionChecker.gd
# This script provides a mechanism for evaluating conditions based on PXOS's
# memory state and detected patterns. It allows roadmap steps to execute
# conditionally, adding decision-making capabilities to the RRE.

extends Node

# --- Dependencies ---
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # For memory value checks
@onready var px_memory_pattern_detector: PXMemoryPatternDetector = get_node_or_null("../PXMemoryPattern") # For pattern checks
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging condition checks

# --- Condition Definition ---
# Represents a single condition to be checked.
class_name Condition
var type: String          # "MEMORY_VALUE", "MEMORY_PATTERN", "SCROLL_CONTAINS"
var target: Variant       # Vector2 for MEMORY_VALUE, Array[int] for MEMORY_PATTERN, String for SCROLL_CONTAINS
var operator: String      # "==", "!=", ">", "<", ">=", "<=", "CONTAINS", "NOT_CONTAINS"
var value: Variant        # Expected value for MEMORY_VALUE, or null for patterns/scrolls
var description: String   # A human-readable description of the condition

func _init(_type: String, _target: Variant, _operator: String, _value: Variant = null, _description: String = ""):
    type = _type
    target = _target
    operator = _operator
    value = _value
    description = _description

# --- Internal State ---
var active_conditions: Array[Condition] = []

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_memory:
        print_warn("PXRoadmapConditionChecker: PXMemoryRegion not found. Memory value conditions will be limited.")
    if not px_memory_pattern_detector:
        print_warn("PXRoadmapConditionChecker: PXMemoryPatternDetector not found. Memory pattern conditions will be limited.")
    if not px_scroll_log:
        print_warn("PXRoadmapConditionChecker: PXScrollLog not found. Condition logs will go to console.")

    print("PXRoadmapConditionChecker: Initialized.")

# --- API for Adding Conditions ---

func add_memory_value_condition(coord: Vector2, operator: String, value: int, description: String = ""):
    """Adds a condition to check a specific memory byte value."""
    var condition = Condition.new("MEMORY_VALUE", coord, operator, value, description)
    active_conditions.append(condition)
    print("PXRoadmapConditionChecker: Added memory value condition: ", description)

func add_memory_pattern_condition(pattern: Array[int], operator: String, description: String = ""):
    """Adds a condition to check for a specific memory pattern."""
    # Operator should typically be "CONTAINS" or "NOT_CONTAINS" for patterns
    var condition = Condition.new("MEMORY_PATTERN", pattern, operator, null, description)
    active_conditions.append(condition)
    print("PXRoadmapConditionChecker: Added memory pattern condition: ", description)

func add_scroll_contains_condition(text_to_find: String, operator: String, description: String = ""):
    """Adds a condition to check if the scroll log contains specific text."""
    # Operator should be "CONTAINS" or "NOT_CONTAINS"
    var condition = Condition.new("SCROLL_CONTAINS", text_to_find, operator, null, description)
    active_conditions.append(condition)
    print("PXRoadmapConditionChecker: Added scroll contains condition: ", description)

func clear_conditions():
    """Clears all active conditions."""
    active_conditions.clear()
    print("PXRoadmapConditionChecker: All conditions cleared.")

# --- Core Evaluation Logic ---

func evaluate_condition(condition_text: String) -> bool:
    """
    Evaluates a single condition string. This is the primary interface for PXRoadmapExecutor.
    Condition string format examples:
    "MEM(X,Y) == VALUE"
    "MEM(X,Y) > VALUE"
    "PATTERN(P1,P2,P3) CONTAINS"
    "SCROLL CONTAINS 'TEXT'"

    Returns:
        bool: True if the condition is met, false otherwise.
    """
    var result = false
    var log_message = "EVAL: " + condition_text.left(20) # Truncate for log

    # --- MEMORY_VALUE ---
    var mem_match = condition_text.regexp_match("MEM\\((\\d+),(\\d+)\\)\\s*([!=<>]+)\\s*(\\d+)")
    if mem_match and px_memory:
        var x = mem_match.get_string(1).to_int()
        var y = mem_match.get_string(2).to_int()
        var op = mem_match.get_string(3)
        var val = mem_match.get_string(4).to_int()
        var current_byte = px_memory.read_byte(x, y)
        if current_byte != -1:
            result = _evaluate_numeric_condition(current_byte, op, val)
            log_message += " MEM(" + str(x) + "," + str(y) + ") = " + str(current_byte) + " " + op + " " + str(val) + " -> " + str(result)
        else:
            print_warn("PXRoadmapConditionChecker: Could not read memory at (", x, ",", y, ") for condition.")
            log_message += " MEM_READ_FAIL -> FALSE"

    # --- MEMORY_PATTERN ---
    var pattern_match = condition_text.regexp_match("PATTERN\\(([^)]+)\\)\\s*(CONTAINS|NOT_CONTAINS)")
    if pattern_match and px_memory_pattern_detector:
        var pattern_str = pattern_match.get_string(1)
        var op = pattern_match.get_string(2)
        var pattern_array = _parse_pattern_string(pattern_str) # Helper to convert "P1,P2,P3" to [P1,P2,P3]

        if not pattern_array.is_empty():
            var pattern_found = px_memory_pattern_detector.search_for_pattern(pattern_array) # Returns Vector2.INF or coord
            if op == "CONTAINS":
                result = (pattern_found != Vector2.INF)
            elif op == "NOT_CONTAINS":
                result = (pattern_found == Vector2.INF)
            log_message += " PATTERN(" + pattern_str + ") " + op + " -> " + str(result)
        else:
            print_warn("PXRoadmapConditionChecker: Invalid pattern string: ", pattern_str)
            log_message += " PATTERN_PARSE_FAIL -> FALSE"

    # --- SCROLL_CONTAINS ---
    var scroll_match = condition_text.regexp_match("SCROLL\\s*(CONTAINS|NOT_CONTAINS)\\s*'([^']+)'")
    if scroll_match and px_scroll_log:
        var op = scroll_match.get_string(1)
        var text_to_find = scroll_match.get_string(2)
        var scroll_content = px_scroll_log.get_all_lines_as_string() # Need a new method in PXScrollLog for this

        if op == "CONTAINS":
            result = (scroll_content.find(text_to_find) != -1)
        elif op == "NOT_CONTAINS":
            result = (scroll_content.find(text_to_find) == -1)
        log_message += " SCROLL '" + text_to_find + "' " + op + " -> " + str(result)

    _log_condition_activity(log_message)
    return result

# --- Helper for Numeric Conditions ---
func _evaluate_numeric_condition(current_value: int, operator: String, target_value: int) -> bool:
    match operator:
        "==": return current_value == target_value
        "!=": return current_value != target_value
        ">": return current_value > target_value
        "<": return current_value < target_value
        ">=": return current_value >= target_value
        "<=": return current_value <= target_value
        _:
            print_warn("PXRoadmapConditionChecker: Unknown numeric operator: ", operator)
            return false

# --- Helper for Pattern String Parsing ---
func _parse_pattern_string(pattern_str: String) -> Array[int]:
    var parts = pattern_str.split(",", false)
    var pattern_array: Array[int] = []
    for p in parts:
        var val = p.strip_edges()
        if val == "null" or val == "-1": # Allow "null" or -1 for wildcard
            pattern_array.append(-1)
        elif val.is_valid_int():
            pattern_array.append(val.to_int())
        else:
            print_warn("PXRoadmapConditionChecker: Invalid pattern element: ", val)
            return [] # Return empty array on error
    return pattern_array

# --- Logging ---
func _log_condition_activity(message: String):
    if px_scroll_log:
        px_scroll_log.add_line("COND: " + message)
    else:
        print("PXRoadmapConditionChecker (Console Log): ", message)

