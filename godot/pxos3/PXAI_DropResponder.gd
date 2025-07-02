# PXAI_DropResponder.gd
# This module provides an intelligent, context-aware response in the PXScrollLog
# when a file is dropped into PXOS. It analyzes the file type and potentially
# its content to generate a relevant AI-driven message.

extends Node

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging AI responses
@onready var px_drop_zone: PXDropZone = get_node_or_null("../PXDropZone") # To listen for file drops
@onready var px_mutant_explorer_ai: PXMutantExplorerAI = get_node_or_null("../PXMutantExplorerAI") # For potential deeper AI insights

# --- Internal State ---
# No significant internal state needed for this initial scaffold,
# but could store learned patterns or user preferences in the future.

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_drop_zone:
        print_err("PXAI_DropResponder: Essential dependencies missing. AI responses may be limited.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Connect to PXDropZone's file_dropped signal
    if px_drop_zone:
        px_drop_zone.file_dropped.connect(Callable(self, "_on_file_dropped"))
        _log_responder_activity("Connected to PXDropZone for intelligent responses.")

    _log_responder_activity("Initialized. Ready to respond to file drops.")

# --- Core AI Response Logic ---

func _on_file_dropped(file_path: String, file_type: String):
    """
    Callback when a file is dropped into PXDropZone.
    Generates and logs an intelligent response based on file type.
    """
    var file_name = file_path.get_file()
    var ai_response_message: String = ""

    match file_type.to_lower():
        "iso", "img":
            ai_response_message = "🧠 Detected '%s' (%s file) — possible bootable image. Preparing to launch in PXQEMU." % [file_name, file_type.to_upper()]
        "pxdigest":
            ai_response_message = "🤖 .pxdigest file detected — parsing pixel header and verifying memory map for '%s'..." % file_name
            # In a more advanced version, you might call PXDigestInspector here
            # to get a quick summary before generating the response.
        "txt", "ztxt":
            ai_response_message = "📄 Text file ('%s') dropped — loading as PXTalkScript or roadmap for analysis." % file_name
            # Could add logic here to peek at content for more specific responses
        "elf":
            ai_response_message = "⚙️ Executable file ('%s') detected. Preparing for native execution or emulation." % file_name
        _:
            ai_response_message = "❓ Unknown file type ('%s') for '%s'. Attempting to process..." % [file_type, file_name]
    
    _log_ai_response(ai_response_message)
    _log_responder_activity("Generated response for: " + file_name)

func _log_ai_response(message: String):
    """
    Logs the AI's intelligent response to the PXScrollLog with a distinct tag.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXAI_RESPONDER: " + message)
    else:
        print("PXAI_DropResponder (Console Log): ", message)

# --- Logging ---

func _log_responder_activity(message: String):
    """
    Helper function to log internal activities of the responder module.
    """
    if px_scroll_log:
        px_scroll_log.add_line("PXAI_DROP_RESPONDER_ACTIVITY: " + message)
    else:
        print("PXAI_DropResponder (Console Log): ", message)

