# PXAI_DropResponder.gd
# This module provides an intelligent, context-aware response in the PXScrollLog
# when a file is dropped into PXOS. It analyzes the file type and potentially
# its content to generate a relevant AI-driven message.

extends Node

# --- Dependencies ---
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog") # For logging AI responses
@onready var px_drop_zone: PXDropZone = get_node_or_null("../PXDropZone") # To listen for file drops
@onready var px_fs_reader: PXFSReader = get_node_or_null("../PXFSReader") # To read file content for analysis
@onready var px_mutant_explorer_ai: PXMutantExplorerAI = get_node_or_null("../PXMutantExplorerAI") # For potential deeper AI insights
@onready var px_digest_inspector: PXDigestInspector = get_node_or_null("../PXDigestInspector") # To leverage its parsing capabilities

# --- Internal State ---
# No significant internal state needed for this initial scaffold,
# but could store learned patterns or user preferences in the future.

# --- Godot Lifecycle Methods ---

func _ready():
    # Check for essential dependencies
    if not px_scroll_log or not px_drop_zone or not px_fs_reader:
        print_err("PXAI_DropResponder: Essential dependencies missing. AI responses may be limited.")
        set_process_mode(Node.PROCESS_MODE_DISABLED)
        return

    # Connect to PXDropZone's file_dropped signal
    if px_drop_zone:
        px_drop_zone.file_dropped.connect(Callable(self, "_on_file_dropped"))
        _log_responder_activity("Connected to PXDropZone for intelligent responses.")

    _log_responder_activity("Initialized. Ready to respond to file drops with deeper intelligence.")

# --- Core AI Response Logic ---

func _on_file_dropped(file_path: String, file_type: String):
    """
    Callback when a file is dropped into PXDropZone.
    Generates and logs an intelligent response based on file type and content analysis.
    """
    var file_name = file_path.get_file()
    var ai_response_message: String = ""
    var file_content_raw: String = px_fs_reader.read_file_by_name(file_path)

    match file_type.to_lower():
        "iso", "img":
            ai_response_message = "🧠 Detected '%s' (%s file) — possible bootable image. Preparing to launch in PXQEMU." % [file_name, file_type.to_upper()]
        "pxdigest":
            ai_response_message = _analyze_pxdigest_content(file_name, file_content_raw)
        "txt", "ztxt":
            ai_response_message = _analyze_text_content(file_name, file_content_raw)
        "elf":
            ai_response_message = "⚙️ Executable file ('%s') detected. Preparing for native execution or emulation." % file_name
        _:
            ai_response_message = "❓ Unknown file type ('%s') for '%s'. Attempting to process..." % [file_type, file_name]
    
    _log_ai_response(ai_response_message)
    _log_responder_activity("Generated enhanced response for: " + file_name)

func _analyze_pxdigest_content(file_name: String, content: String) -> String:
    """
    Analyzes .pxdigest content using PXDigestInspector's parsing logic
    and generates an AI interpretation.
    """
    if not px_digest_inspector:
        return "🤖 .pxdigest file detected ('%s') — parsing pixel header and verifying memory map... (Inspector not available for deep analysis)" % file_name

    var parsed_data = px_digest_inspector._parse_pxdigest_content(content)
    var metadata = parsed_data.get("metadata", {})
    var pixel_data_size = parsed_data.get("pixel_data", []).size()

    var response = "🤖 .pxdigest file detected ('%s'). " % file_name
    
    if not metadata.is_empty():
        response += "Metadata found: "
        var meta_parts = []
        if metadata.has("pxnet/role"):
            meta_parts.append("Role: '%s'" % metadata["pxnet/role"])
        if metadata.has("pxroadmap/status"):
            meta_parts.append("Status: '%s'" % metadata["pxroadmap/status"])
        if metadata.has("author"):
            meta_parts.append("Author: '%s'" % metadata["author"])
        
        if not meta_parts.is_empty():
            response += "(" + ", ".join(meta_parts) + "). "
            
            # Deeper AI interpretation based on metadata
            if metadata.get("pxnet/role") == "Kernel":
                response += "This appears to be a core system kernel digest. High importance."
            elif metadata.get("pxnet/role") == "BootAgent":
                response += "Looks like a boot agent, likely to initialize system components."
            elif metadata.get("pxroadmap/status") == "Incomplete":
                response += "Warning: Roadmap status is 'Incomplete'. Proceed with caution."
            elif metadata.get("pxroadmap/status") == "SystemUpgrade":
                response += "This digest is tagged as a system upgrade. Preparing for critical update sequence."
        else:
            response += "Generic metadata present. "
    else:
        response += "No specific metadata found. "

    response += "Pixel data size: %d pixels. " % pixel_data_size
    
    if pixel_data_size == 0:
        response += "Warning: No pixel boot data found."
    elif pixel_data_size < px_digest_inspector.pixel_preview_width * px_digest_inspector.pixel_preview_height:
        response += "Pixel data may be incomplete for full preview."
    
    return response

func _analyze_text_content(file_name: String, content: String) -> String:
    """
    Analyzes text (.txt, .ztxt) content to provide AI interpretation.
    Looks for roadmap headers, common keywords, etc.
    """
    var response = "📄 Text file ('%s') dropped. " % file_name
    
    # Check for roadmap headers
    var is_roadmap = false
    if content.begins_with("# RECORDED_SCROLL:") or content.find("# GOAL:") != -1:
        is_roadmap = true
        response += "Detected as a PXOS roadmap. "
        
        var lines = content.split("\n")
        var goal = ""
        var strategy = ""
        for line in lines:
            if line.begins_with("# GOAL:"):
                goal = line.replace("# GOAL:", "").strip_edges()
            if line.begins_with("# STRATEGY:"):
                strategy = line.replace("# STRATEGY:", "").strip_edges()
            if not line.begins_with("#") and not line.strip_edges().is_empty(): # Stop after headers
                break
        
        if not goal.is_empty():
            response += "Goal: '%s'. " % goal
        if not strategy.is_empty():
            response += "Strategy: '%s'. " % strategy
            
        # Example of deeper AI insight based on content keywords
        if strategy.to_lower().find("reflex") != -1 or goal.to_lower().find("autonomous") != -1:
            response += "This roadmap appears to be part of the autonomous reflex chain. High impact potential."
        elif content.to_lower().find("install") != -1 and content.to_lower().find("module") != -1:
            response += "Contains module installation directives."
            
    elif content.to_lower().find("error") != -1 or content.to_lower().find("fail") != -1:
        response += "Content suggests a log file or error report. Reviewing for anomalies."
    elif content.length() < 100:
        response += "Short text file. Could be a command script or simple note."
    else:
        response += "Generic text content detected. "

    # Optional: Integrate with PXMutantExplorerAI for pattern analysis if it were designed for text content
    # if px_mutant_explorer_ai and is_roadmap:
    #     var ai_insight = px_mutant_explorer_ai.get_insight_for_roadmap_content(content)
    #     if not ai_insight.is_empty():
    #         response += "AI Insight: " + ai_insight

    return response

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

