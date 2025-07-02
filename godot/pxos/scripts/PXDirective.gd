# PXDirective.gd
# This module acts as a centralized decision-making unit for PXOS.
# It observes the system's environmental state (memory, patterns, logs)
# and issues high-level goals or "directives" to guide PXOS's behavior
# by triggering roadmap generation and execution.

extends Node

# --- Configuration ---
# How often the directive module evaluates the system state and potentially issues a directive.
@export var evaluation_frequency_sec: float = 2.0 # Evaluate every 2 seconds

# --- Dependencies ---
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory")
@onready var px_memory_pattern_detector: PXMemoryPatternDetector = get_node_or_null("../PXMemoryPattern")
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog")
@onready var px_roadmap_generator: PXRoadmapGenerator = get_node_or_null("../PXRoadmapGenerator")
@onready var px_roadmap_memory: PXRoadmapMemoryRegion = get_node_or_null("../PXRoadmapMemory")
@onready var px_roadmap_executor: PXRoadmapExecutor = get_node_or_null("../PXRoadmapExecutor")

# --- Internal State ---
var time_since_last_evaluation: float = 0.0
var last_issued_directive: String = "" # To prevent issuing the same directive repeatedly
var directive_queue: Array = [] # A queue for directives if multiple conditions are met

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_memory or not px_memory_pattern_detector or not px_scroll_log or \
       not px_roadmap_generator or not px_roadmap_memory or not px_roadmap_executor:
        print_err("PXDirective: One or more essential dependencies missing. Disabling directive module.")
        set_process(false) # Disable _process if dependencies are not met
        return

    print("PXDirective: Initialized. Ready to issue directives.")

func _process(delta):
    time_since_last_evaluation += delta
    if time_since_last_evaluation >= evaluation_frequency_sec:
        time_since_last_evaluation = 0.0
        evaluate_system_state()
        process_directive_queue() # Process any queued directives

# --- Core Directive Logic ---

func evaluate_system_state():
    """
    Observes the current system state (memory, patterns, logs) and decides
    whether to issue a high-level directive.
    This is where the "intelligence" of PXOS's planning comes from.
    """
    print("\n--- PXDirective: Evaluating system state ---")
    var current_directive_candidate = ""

    # --- Example Condition 1: Memory Value Check ---
    # If the first byte of PXMemory is 0, issue an "EXPLORE" directive
    if px_memory:
        var first_mem_byte = px_memory.read_byte(px_memory.memory_region_rect.position.x, px_memory.memory_region_rect.position.y)
        if first_mem_byte == 0:
            current_directive_candidate = "EXPLORE"
            _log_directive_activity("Condition Met: Memory(0,0) == 0. Suggesting 'EXPLORE'.")

    # --- Example Condition 2: Pattern Detection Check ---
    # If a "REPAIR_NEEDED" pattern is detected, issue a "REPAIR" directive
    # (You would define "REPAIR_NEEDED" pattern in PXMemoryPatternDetector)
    # For this scaffold, let's simulate a pattern detection.
    # if px_memory_pattern_detector.search_for_pattern([1,2,3]) != Vector2.INF: # Example pattern
    #     current_directive_candidate = "REPAIR"
    #     _log_directive_activity("Condition Met: 'REPAIR_NEEDED' pattern detected. Suggesting 'REPAIR'.")

    # --- Example Condition 3: Scroll Log Content Check ---
    # If the scroll log contains "ERROR", issue a "DEBUG" directive
    if px_scroll_log:
        var scroll_content = px_scroll_log.get_all_lines_as_string()
        if scroll_content.find("ERROR") != -1:
            current_directive_candidate = "DEBUG"
            _log_directive_activity("Condition Met: Scroll log contains 'ERROR'. Suggesting 'DEBUG'.")

    # --- Issue Directive if a new candidate is found ---
    if current_directive_candidate and current_directive_candidate != last_issued_directive:
        directive_queue.append(current_directive_candidate)
        print("PXDirective: Queued new directive: '", current_directive_candidate, "'")
        last_issued_directive = current_directive_candidate # Update last issued to prevent immediate re-queueing
    elif not current_directive_candidate:
        last_issued_directive = "" # Reset if no directive is currently suggested

    print("--- PXDirective: Evaluation complete ---")

func process_directive_queue():
    """
    Processes directives from the queue.
    """
    if directive_queue.is_empty():
        return

    var directive_to_process = directive_queue.pop_front()
    issue_directive(directive_to_process)


func issue_directive(goal_text: String):
    """
    Issues a high-level directive (goal). This triggers the roadmap generation
    and execution process.

    Args:
        goal_text (String): The symbolic goal or directive (e.g., "HELLO", "REPAIR").
    """
    print("PXDirective: Issuing directive: '", goal_text, "'")
    _log_directive_activity("DIRECTIVE: " + goal_text.left(15)) # Log the issued directive

    # 1. Generate a roadmap for the goal
    var generated_roadmap = px_roadmap_generator.generate_roadmap_from_goal(goal_text)

    if generated_roadmap.is_empty():
        print_warn("PXDirective: Roadmap generation failed for directive: '", goal_text, "'.")
        _log_directive_activity("GEN_FAIL: " + goal_text.left(15))
        return

    # 2. Store the new roadmap in pixel memory
    if px_roadmap_memory.write_roadmap_to_memory(generated_roadmap):
        _log_directive_activity("Plan stored in memory.")
    else:
        print_err("PXDirective: Failed to store roadmap for directive: '", goal_text, "'.")
        _log_directive_activity("STORE_FAIL: " + goal_text.left(15))
        return

    # 3. Tell the roadmap executor to load and run the new plan
    px_roadmap_executor.load_and_execute_roadmap_from_memory()
    _log_directive_activity("Plan execution initiated.")

# --- Logging ---

func _log_directive_activity(message: String):
    """
    Helper function to log directive activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("DIR: " + message)
    else:
        print("PXDirective (Console Log): ", message)

