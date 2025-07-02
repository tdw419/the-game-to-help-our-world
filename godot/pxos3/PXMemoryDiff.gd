# PXMemoryDiff.gd
# This module compares two dictionary-based memory states (e.g., current PXOS memory
# vs. simulated final memory) and identifies additions, deletions, and changes.
# It provides a formatted string suitable for display in a RichTextLabel.

extends Node

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging diff activities

# --- Core Diffing Logic ---

func compare_memory_states(initial_state: Dictionary, final_state: Dictionary) -> Dictionary:
    """
    Compares an initial memory state with a final memory state.
    Returns a dictionary containing categorized changes:
    {
        "added": {key: value, ...},
        "removed": {key: value, ...},
        "changed": {key: {old_value: ..., new_value: ...}, ...},
        "unchanged": {key: value, ...}
    }
    """
    _log_diff_activity("Starting memory state comparison.")
    var diff_result = {
        "added": {},
        "removed": {},
        "changed": {},
        "unchanged": {}
    }

    # Identify removed and unchanged keys from initial_state
    for key in initial_state.keys():
        if not final_state.has(key):
            diff_result.removed[key] = initial_state[key]
        elif initial_state[key] == final_state[key]:
            diff_result.unchanged[key] = initial_state[key]
        else:
            diff_result.changed[key] = {
                "old_value": initial_state[key],
                "new_value": final_state[key]
            }

    # Identify added keys from final_state
    for key in final_state.keys():
        if not initial_state.has(key):
            diff_result.added[key] = final_state[key]
            
    _log_diff_activity("Memory state comparison complete. Added: %d, Removed: %d, Changed: %d." % [
        diff_result.added.size(), diff_result.removed.size(), diff_result.changed.size()
    ])
    return diff_result

func format_diff_for_display(diff_data: Dictionary) -> String:
    """
    Formats the diff data into a human-readable string with BBCode for RichTextLabel.
    """
    var display_text = "[b]Memory State Changes:[/b]\n"

    if diff_data.added.is_empty() and diff_data.removed.is_empty() and diff_data.changed.is_empty():
        display_text += "[color=gray]  No significant memory changes detected.[/color]\n"
        return display_text

    # Added
    if not diff_data.added.is_empty():
        display_text += "\n[color=green][b]Added Keys:[/b][/color]\n"
        for key in diff_data.added.keys():
            display_text += "  [color=green]+ %s: %s[/color]\n" % [key, str(diff_data.added[key])]

    # Removed
    if not diff_data.removed.is_empty():
        display_text += "\n[color=red][b]Removed Keys:[/b][/color]\n"
        for key in diff_data.removed.keys():
            display_text += "  [color=red]- %s: %s[/color]\n" % [key, str(diff_data.removed[key])]

    # Changed
    if not diff_data.changed.is_empty():
        display_text += "\n[color=orange][b]Changed Keys:[/b][/color]\n"
        for key in diff_data.changed.keys():
            var old_val = str(diff_data.changed[key].old_value)
            var new_val = str(diff_data.changed[key].new_value)
            display_text += "  [color=orange]~ %s: %s -> %s[/color]\n" % [key, old_val, new_val]

    # Unchanged (optional to display, usually omitted for brevity)
    # if not diff_data.unchanged.is_empty():
    #     display_text += "\n[color=gray][b]Unchanged Keys:[/b][/color]\n"
    #     for key in diff_data.unchanged.keys():
    #         display_text += "  [color=gray]= %s: %s[/color]\n" % [key, str(diff_data.unchanged[key])]

    return display_text

# --- Logging ---

func _log_diff_activity(message: String):
    """
    Helper function to log diff activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXMEMORY_DIFF: " + message)
    else:
        print("PXMemoryDiff (Console Log): ", message)

