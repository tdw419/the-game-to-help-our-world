# PXMotivationCore.gd
# This module simulates internal needs and drives for PXOS, such as
# "hunger," "curiosity," or "stability." It periodically evaluates these needs
# and, if a need is sufficiently high, issues a corresponding high-level goal
# (directive) to PXDirective.gd to trigger autonomous planning.
#
# UPDATED: Now directly incorporates emotional states from PXEmotionEngine.gd
# to influence directive prioritization and issuance.

extends Node

# --- Configuration ---
# How often the motivation core evaluates its internal needs.
@export var need_evaluation_frequency_sec: float = 5.0 # Evaluate needs every 5 seconds

# --- Dependencies ---
@onready var px_directive: PXDirective = get_node_or_null("../PXDirective") # To issue directives
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging motivation activities
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # To read memory for needs assessment (e.g., instability)
@onready var px_memory_pattern_detector: PXMemoryPatternDetector = get_node_or_null("../PXMemoryPattern") # To detect patterns for needs assessment
@onready var px_emotion_engine: PXEmotionEngine = get_node_or_null("../PXEmotionEngine") # NEW: To read emotional states
@onready var px_goal_advisor: PXGoalAdvisor = get_node_or_null("../PXGoalAdvisor") # To consult advisor before issuing
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To record goals
@onready var px_goal_mutation_engine: PXGoalMutationEngine = get_node_or_null("../PXGoalMutationEngine") # To mutate goals

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
    if not px_directive or not px_scroll_log or not px_emotion_engine or \
       not px_goal_advisor or not px_goal_memory or not px_goal_mutation_engine:
        print_err("PXMotivationCore: Essential dependencies missing. Disabling.")
        set_process(false)
        return

    print("PXMotivationCore: Initialized. Ready to simulate needs and respond to emotions.")
    # Initialize _last_goal_history_size with current history size
    #_last_goal_history_size = px_goal_memory.get_goal_history().size() # This was for EmotionEngine

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

    # --- NEW: Adjust needs based on emotional states ---
    if px_emotion_engine:
        var frustration_level = px_emotion_engine.get_emotion_level("frustration")
        var fear_level = px_emotion_engine.get_emotion_level("fear")
        var satisfaction_level = px_emotion_engine.get_emotion_level("satisfaction")
        var boredom_level = px_emotion_engine.get_emotion_level("boredom_level")

        # Frustration can increase stability need (drive to fix problem)
        needs["stability"] = clampf(needs["stability"] + frustration_level * 0.05, 0.0, 1.0)
        # Fear can also increase stability need (drive to be safe)
        needs["stability"] = clampf(needs["stability"] + fear_level * 0.1, 0.0, 1.0)

        # High satisfaction can decrease all needs temporarily
        for need_name in needs.keys():
            needs[need_name] = clampf(needs[need_name] - satisfaction_level * 0.02, 0.0, 1.0)

        # High boredom can increase curiosity or hunger
        needs["curiosity"] = clampf(needs["curiosity"] + boredom_level * 0.05, 0.0, 1.0)
        needs["hunger"] = clampf(needs["hunger"] + boredom_level * 0.03, 0.0, 1.0)

        if frustration_level > 0.5:
            _log_motivation_activity("Needs influenced by Frustration: " + str(round(frustration_level*100)) + "%")
        if satisfaction_level > 0.5:
            _log_motivation_activity("Needs influenced by Satisfaction: " + str(round(satisfaction_level*100)) + "%")


func _evaluate_and_issue_directives():
    """
    Checks if any need has crossed its threshold and, if so, issues a corresponding directive.
    Prioritizes needs if multiple are critical.
    NEW: Incorporates emotional overrides for directive prioritization.
    """
    print("\n--- PXMotivationCore: Evaluating needs ---")
    var critical_needs: Array = []
    for need_name in needs.keys():
        print("  Need '", need_name, "': ", round(needs[need_name] * 100), "% (Threshold: ", round(need_thresholds[need_name] * 100), "%)")
        if needs[need_name] >= need_thresholds[need_name]:
            critical_needs.append(need_name)

    var directive_to_issue = ""
    var source_need = "" # To track which need primarily drove the decision

    # --- NEW: Emotional Overrides for Directive Prioritization ---
    if px_emotion_engine:
        var frustration_level = px_emotion_engine.get_emotion_level("frustration")
        var fear_level = px_emotion_engine.get_emotion_level("fear")
        var curiosity_joy_level = px_emotion_engine.get_emotion_level("curiosity_joy")
        var boredom_level = px_emotion_engine.get_emotion_level("boredom_level")

        if frustration_level > 0.7: # High frustration overrides other needs
            directive_to_issue = "REPAIR_SYSTEM"
            source_need = "EMOTION_FRUSTRATION"
            _log_motivation_activity("PRIORITY OVERRIDE: High Frustration -> REPAIR_SYSTEM")
        elif fear_level > 0.6: # High fear also prioritizes safety
            directive_to_issue = "SEEK_SAFETY" # New directive for fear
            source_need = "EMOTION_FEAR"
            _log_motivation_activity("PRIORITY OVERRIDE: High Fear -> SEEK_SAFETY")
        elif curiosity_joy_level > 0.6: # High curiosity joy prioritizes exploration
            directive_to_issue = "EXPLORE"
            source_need = "EMOTION_CURIOSITY_JOY"
            _log_motivation_activity("PRIORITY OVERRIDE: High Curiosity Joy -> EXPLORE")
        elif boredom_level > 0.5 and critical_needs.is_empty(): # If bored and no critical needs, create new plan
            directive_to_issue = "CREATE_NEW_PLAN"
            source_need = "EMOTION_BOREDOM"
            _log_motivation_activity("PRIORITY OVERRIDE: Boredom -> CREATE_NEW_PLAN")


    # If no emotional override, proceed with need-based prioritization
    if directive_to_issue.is_empty():
        if critical_needs.is_empty():
            print("  No critical needs. No directives issued.")
            return

        critical_needs.sort_custom(Callable(self, "_sort_needs_by_priority"))
        top_critical_need = critical_needs[0]

        match top_critical_need:
            "hunger": directive_to_issue = "ACQUIRE_RESOURCES"
            "curiosity": directive_to_issue = "EXPLORE"
            "stability": directive_to_issue = "REPAIR_SYSTEM"
            "boredom": directive_to_issue = "CREATE_NEW_PLAN"
            _: directive_to_issue = "DEFAULT_ACTION" # Fallback
        source_need = top_critical_need


    # --- Consult PXGoalAdvisor ---
    if px_goal_advisor:
        var should_attempt = px_goal_advisor.should_attempt_goal(directive_to_issue)
        if not should_attempt:
            # If advisor says NO, check if it's due to stagnation
            if px_goal_advisor.is_goal_stagnant(directive_to_issue, px_goal_advisor.stagnation_failure_threshold):
                print("PXMotivationCore: Goal '", directive_to_issue, "' is stagnant. Consulting mutation engine.")
                _log_motivation_activity("STAGNANT: " + directive_to_issue.left(15) + ". Mutating.")

                # Get a mutated version of the goal
                var failure_count = px_goal_advisor.get_recent_failures(directive_to_issue)
                var mutated_goal = px_goal_mutation_engine.get_mutated_goal(directive_to_issue, failure_count)

                if mutated_goal != directive_to_issue: # Only proceed if a new goal was suggested
                    directive_to_issue = mutated_goal
                    _log_motivation_activity("  Mutated to: " + directive_to_issue.left(15))
                else:
                    # If mutation engine suggests same goal (e.g., max mutations reached, fallback is same)
                    print("PXMotivationCore: Mutation engine suggested same goal or no viable mutation. Skipping this cycle.")
                    _log_motivation_activity("  Mutation failed/no change. Skipping.")
                    return # Skip issuing directive this cycle
            else:
                print("PXMotivationCore: Advisor recommends skipping '", directive_to_issue, "' (not stagnant).")
                _log_motivation_activity("SKIPPING: " + directive_to_issue.left(15) + " (Advisor)")
                return # Skip issuing directive this cycle
    else:
        print_warn("PXMotivationCore: PXGoalAdvisor not available. Issuing directive without advice.")


    # Issue the directive via PXDirective (existing logic)
    if px_directive:
        var new_goal_entry = px_goal_memory.record_goal(directive_to_issue, {"source_need": source_need})
        px_directive.issue_directive(directive_to_issue, new_goal_entry)
        _log_motivation_activity("Issued directive: '" + directive_to_issue + "' (from " + source_need + " need/emotion)")

        # NEW: Introspection for issued goal
        if px_goal_introspector: # Assuming PXGoalIntrospector is also a dependency
            px_goal_introspector.explain_goal_decision(
                directive_to_issue, "ISSUED",
                {"source_need": source_need, "advisor_ok": true}
            )

        # Reduce the need after issuing a directive
        # If issued due to emotion, reduce the corresponding need or emotion directly
        match source_need:
            "EMOTION_FRUSTRATION": px_emotion_engine.emotions["frustration"] = clampf(px_emotion_engine.emotions["frustration"] - 0.5, 0.0, 1.0)
            "EMOTION_FEAR": px_emotion_engine.emotions["fear"] = clampf(px_emotion_engine.emotions["fear"] - 0.5, 0.0, 1.0)
            "EMOTION_CURIOSITY_JOY": px_emotion_engine.emotions["curiosity_joy"] = clampf(px_emotion_engine.emotions["curiosity_joy"] - 0.5, 0.0, 1.0)
            "EMOTION_BOREDOM": px_emotion_engine.emotions["boredom_level"] = clampf(px_emotion_engine.emotions["boredom_level"] - 0.5, 0.0, 1.0)
            _: needs[source_need] = clampf(needs[source_need] - 0.5, 0.0, 1.0) # Reduce by 50%

        # If the goal was successfully issued, reset its mutation count (as it's now being attempted)
        px_goal_mutation_engine.reset_mutation_count(directive_to_issue)
    else:
        print_err("PXMotivationCore: PXDirective not available to issue directive.")

    print("--- PXMotivationCore: Evaluation complete ---")

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

