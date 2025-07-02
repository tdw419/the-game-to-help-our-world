# PXMemoryTriggerRegion.gd
# Watches specific subregions of the PXMemoryRegion and triggers callbacks
# when byte conditions are met.

extends Node

# --- Dependencies ---
@onready var px_memory: PXMemoryRegion = get_node_or_null("../PXMemory") # Adjust path as needed

# --- Trigger Definition ---
class_name TriggerRule
var coord: Vector2
var condition_func: Callable
var callback_func: Callable
var persistent: bool = false
var has_fired: bool = false

func _init(_coord, _condition_func, _callback_func, _persistent := false):
    coord = _coord
    condition_func = _condition_func
    callback_func = _callback_func
    persistent = _persistent

# --- Watched Triggers ---
var trigger_rules: Array = []

# --- Lifecycle ---
func _process(_delta):
    if not px_memory: return
    for rule in trigger_rules:
        var x = int(rule.coord.x)
        var y = int(rule.coord.y)
        var value = px_memory.read_byte(x, y)
        if value == -1:
            continue # Invalid read

        if rule.condition_func.call(value):
            if not rule.has_fired or rule.persistent:
                rule.callback_func.call(value, rule.coord)
                rule.has_fired = true
        else:
            rule.has_fired = false # Reset if condition no longer met

# --- API ---

func add_trigger(coord: Vector2, condition_func: Callable, callback_func: Callable, persistent := false):
    """
    Adds a new memory trigger.

    Args:
        coord (Vector2): The (x,y) pixel coordinate in PXMemoryRegion to watch.
        condition_func (Callable): A function taking (int byte_value) -> bool
        callback_func (Callable): A function taking (int byte_value, Vector2 coord)
        persistent (bool): If true, callback fires every frame condition is true. If false, fires once.
    """
    var rule = TriggerRule.new(coord, condition_func, callback_func, persistent)
    trigger_rules.append(rule)
    print("PXMemoryTriggerRegion: Added trigger at ", coord)

func clear_triggers():
    trigger_rules.clear()
