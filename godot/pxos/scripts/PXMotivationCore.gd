# PXMotivationCore.gd
# This module simulates internal needs and drives for PXOS, such as
# "hunger," "curiosity," or "stability." It periodically evaluates these needs
# and, if a need is sufficiently high, issues a corresponding high-level goal
# (directive) to PXDirective.gd to trigger autonomous planning.

extends Node

# --- Configuration ---
# How often the motivation core evaluates its internal needs.
@export var need_evaluation_frequency_sec: float = 5.0 # Evaluate needs every 5 seconds

# --- Dependencies ---
@onready var px_directive: PXDirective = get_node_or_null("../PXDirective") # To issue directives
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging motivation activities
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # To read memory for needs assessment (e.g., instability)
@onready var px_memory_pattern_detector: PXMemoryPatternDetector = get_node_or_null("../PXMemoryPattern") # To detect patterns for needs assessment

# --- Internal Needs State ---
# Dictionary to hold the current level of various needs (0.0 to 1.0).
# Needs will increase over time or based on system state.
var needs: Dictionary = {
    "hunger": 0.0,      # Drive to "consume" or "acquire" (e.g., write specific bytes)
    "curiosity": 0.0,   # Drive to "explore" new memory regions or patterns
    "stability": 0.0,   # Drive to "repair" or "balance" system state (e.g., if errors in log)
    "boredom": 0.0      # Drive to "do something new" if activity is low
}

# Rates at which needs naturally increase over time (per second).
var need_growth_rates: Dictionary = {
    "hunger": 0.01,
    "curiosity": 0.005,
    "stability": 0.002,
    "boredom": 0.008
}

# Thresholds at which a need becomes critical and triggers a directive.
var need_thresholds: Dictionary = {
    "hunger": 0.8,
    "curiosity": 0.7,
    "stability": 0.9,
    "boredom": 0.6
}

# --- Internal State ---
var time_since_last_need_evaluation: float = 0.0

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_directive or not px_scroll_log:
        print_err("PXMotivationCore: Essential dependencies (PXDirective, PXScrollLog) missing. Disabling.")
        set_process(false)
        return

    print("PXMotivationCore: Initialized. Ready to simulate needs.")

func _process(delta):
    # Update needs based on time and system state
    _update_needs(delta)

    time_since_last_need_evaluation += delta
    if time_since_last_need_evaluation >= need_evaluation_frequency_sec:
        time_since_last_need_evaluation = 0.0
        _evaluate_and_issue_directives()

# --- Need Management ---

func _update_needs(delta: float):
    """
    Increases needs over time and adjusts them based on current system state.
    """
    for need_name in needs.keys():
        # Increase need over time
        needs[need_name] += need_growth_rates[need_name] * delta
        needs[need_name] = clampf(needs[need_name], 0.0, 1.0) # Clamp between 0 and 1

    # Adjust needs based on specific system conditions
    _adjust_needs_based_on_system_state()

func _adjust_needs_based_on_system_state():
    """
    Adjusts need levels based on observations from other PXOS modules.
    This is where the internal needs become responsive to the system's "environment."
    """
    # Example: Stability need increases if "ERROR" is found in scroll log
    if px_scroll_log and px_scroll_log.get_all_lines_as_string().find("ERROR") != -1:
        needs["stability"] = clampf(needs["stability"] + 0.1, 0.0, 1.0) # Increase stability need
        _log_motivation_activity("Stability need increased due to ERROR in log.")
    elif px_scroll_log and px_scroll_log.get_all_lines_as_string().find("REPAIR_COMPLETE") != -1:
        needs["stability"] = clampf(needs["stability"] - 0.2, 0.0, 1.0) # Decrease stability need
        _log_motivation_activity("Stability need decreased due to REPAIR_COMPLETE.")

    # Example: Curiosity need increases if memory region is mostly zeros (unexplored)
    if px_memory:
        var zero_count = 0
        var total_pixels = 0
        var mem_rect = px_memory.memory_region_rect
        for y in range(int(mem_rect.position.y), int(mem_rect.position.y + mem_rect.size.y)):
            for x in range(int(mem_rect.position.x), int(mem_rect.position.x + mem_rect.size.x)):
                total_pixels += 1
                if px_memory.read_byte(x, y) == 0:
                    zero_count += 1
        if total_pixels > 0 and float(zero_count) / total_pixels > 0.8: # If >80% is zero
            needs["curiosity"] = clampf(needs["curiosity"] + 0.05, 0.0, 1.0)
            _log_motivation_activity("Curiosity need increased due to unexplored memory.")


func _evaluate_and_issue_directives():
    """
    Checks if any need has crossed its threshold and, if so, issues a corresponding directive.
    Prioritizes needs if multiple are critical.
    """
    print("\n--- PXMotivationCore: Evaluating needs ---")
    var critical_needs: Array = []
    for need_name in needs.keys():
        print("  Need '", need_name, "': ", round(needs[need_name] * 100), "% (Threshold: ", round(need_thresholds[need_name] * 100), "%)")
        if needs[need_name] >= need_thresholds[need_name]:
            critical_needs.append(need_name)

    if critical_needs.is_empty():
        print("  No critical needs. No directives issued.")
        return

    # Prioritize needs (e.g., stability > hunger > curiosity > boredom)
    critical_needs.sort_custom(Callable(self, "_sort_needs_by_priority"))

    var top_critical_need = critical_needs[0]
    var directive_to_issue = ""

    match top_critical_need:
        "hunger": directive_to_issue = "ACQUIRE_RESOURCES" # Example directive
        "curiosity": directive_to_issue = "EXPLORE"
        "stability": directive_to_issue = "REPAIR_SYSTEM"
        "boredom": directive_to_issue = "CREATE_NEW_PLAN"
        _: directive_to_issue = "DEFAULT_ACTION" # Fallback

    # Issue the directive via PXDirective
    if px_directive:
        px_directive.issue_directive(directive_to_issue)
        _log_motivation_activity("Issued directive: '" + directive_to_issue + "' (from " + top_critical_need + " need)")
        # Reduce the need after issuing a directive
        needs[top_critical_need] = clampf(needs[top_critical_need] - 0.5, 0.0, 1.0) # Reduce by 50%
    else:
        print_err("PXMotivationCore: PXDirective not available to issue directive.")

# --- Helper for Need Prioritization ---

func _sort_needs_by_priority(need_a: String, need_b: String) -> bool:
    # Define a simple priority order (higher index means higher priority)
    var priority_order = ["boredom", "curiosity", "hunger", "stability"]
    var priority_a = priority_order.find(need_a)
    var priority_b = priority_order.find(need_b)
    return priority_a > priority_b # Sort in descending order of priority

# --- Logging ---

func _log_motivation_activity(message: String):
    """
    Helper function to log motivation activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("MOTIVE: " + message)
    else:
        print("PXMotivationCore (Console Log): ", message)

