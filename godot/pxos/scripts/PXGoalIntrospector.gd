# PXGoalIntrospector.gd
# This module provides PXOS with the ability to articulate its reasoning
# for goal-related decisions, such as why a goal was issued, mutated,
# or skipped. It logs these insights into the PXScrollLog, making
# the system's cognitive processes more transparent.

extends Node

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging introspective insights
@onready var px_goal_memory: PXGoalMemory = get_node_or_null("../PXGoalMemory") # To retrieve goal history for context
@onready var px_goal_advisor: PXGoalAdvisor = get_node_or_null("../PXGoalAdvisor") # To get advisor's current state/rules
@onready var px_goal_mutation_engine: PXGoalMutationEngine = get_node_or_null("../PXGoalMutationEngine") # To get mutation context

# --- Godot Lifecycle Methods ---

func _ready():
    if not px_scroll_log:
        print_err("PXGoalIntrospector: PXScrollLog not found. Introspection logs will go to console.")
    if not px_goal_memory or not px_goal_advisor or not px_goal_mutation_engine:
        print_warn("PXGoalIntrospector: Some core dependencies missing. Introspection might be limited.")

    print("PXGoalIntrospector: Initialized. Ready to provide insights.")

# --- Core Introspection API ---

func explain_goal_decision(goal_type: String, decision_type: String, context_data: Dictionary = {}):
    """
    Generates and logs an explanation for a goal-related decision.

    Args:
        goal_type (String): The goal type involved in the decision (e.g., "EXPLORE").
        decision_type (String): What kind of decision it was ("ISSUED", "SKIPPED", "MUTATED", "FALLBACK").
        context_data (Dictionary): Additional data relevant to the explanation (e.g., "reason", "failures").
    """
    var explanation = ""
    var log_prefix = "INTROSPECT: "

    match decision_type:
        "ISSUED":
            explanation = "I decided to pursue '" + goal_type + "'."
            if context_data.has("source_need"):
                explanation += " My need for " + context_data["source_need"] + " was high."
            if context_data.has("advisor_ok"):
                explanation += " The advisor confirmed it was a good time."
        "SKIPPED":
            explanation = "I decided NOT to pursue '" + goal_type + "'."
            if context_data.has("reason"):
                explanation += " Reason: " + context_data["reason"] + "."
            if context_data.has("cooldown_left"):
                explanation += " Cooldown remaining: " + str(round(context_data["cooldown_left"])) + "s."
        "MUTATED":
            explanation = "I mutated goal '" + goal_type + "'."
            if context_data.has("new_goal_type"):
                explanation += " New goal: '" + context_data["new_goal_type"] + "'."
            if context_data.has("failures"):
                explanation += " This was after " + str(context_data["failures"]) + " previous failures."
            if context_data.has("mutation_num"):
                explanation += " This is mutation attempt #" + str(context_data["mutation_num"]) + "."
        "FALLBACK":
            explanation = "I shifted to a fallback goal for '" + goal_type + "'."
            if context_data.has("fallback_goal_type"):
                explanation += " New goal: '" + context_data["fallback_goal_type"] + "'."
            if context_data.has("max_mutations_reached"):
                explanation += " This was after " + str(context_data["max_mutations_reached"]) + " mutations."
        "OUTCOME":
            explanation = "Goal '" + goal_type + "' had outcome: " + context_data.get("outcome", "UNKNOWN") + "."
            if context_data.has("details"):
                explanation += " Details: " + str(context_data["details"]) + "."
        _:
            explanation = "I made a decision about '" + goal_type + "' (Type: " + decision_type + ")."

    _log_introspection(log_prefix + explanation)
    print("PXGoalIntrospector: ", explanation)

# --- Logging ---

func _log_introspection(message: String):
    """
    Helper function to log introspection activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line(message)
    else:
        print("PXGoalIntrospector (Console Log): ", message)

