# PXReflexKernel.gd
# This script represents the core of the PXKernel, designed to observe
# and interact with the Godot viewport's pixel data, treating it as
# the primary memory and instruction bus for the PXOS.
#
# UPDATED: Includes logic to bootstrap the RRE self-evolution roadmap
# and the specific 'RRE_UPGRADE_TO_V8' and 'RRE_MUTATION_ENGINE_V1' roadmaps.

extends Node

# --- Configuration ---
# The frequency at which the kernel will analyze and inject logic (in frames).
# A value of 60 means it will run approximately once per second at 60 FPS.
const KERNEL_CYCLE_FREQUENCY = 60

# --- Internal State ---
# Image object to hold the pixel data read from the viewport.
# This is the "framebuffer" that the kernel "observes".
var framebuffer_image: Image = null

# Image object that the kernel "writes" to. This simulates the kernel's
# ability to inject new pixel data back into the display.
var kernel_output_image: Image = null

# A simple frame counter to control the kernel's processing cycle.
var frame_counter = 0

# A flag to indicate if the kernel is ready to perform its analysis and injection.
# This becomes true once the viewport texture data is successfully acquired.
var ready_to_think = false

# Reference to the TextureRect node that displays the PXOS output.
@onready var display_screen: TextureRect = get_node_or_null("../DisplayScreen")

# --- Dependencies for RRE Bootstrap ---
@onready var px_ztxt_memory: PXZTXTMemory = get_node_or_null("../PXZTXTMemory")
@onready var px_roadmap_watcher: PXRoadmapWatcher = get_node_or_null("../PXRoadmapWatcher")
@onready var px_scroll_log: PXScrollRegion = get_node_or_null("../PXScrollLog")

# Flags to ensure roadmaps are injected only once.
var rre_self_evolution_bootstrap_injected: bool = false
var godot_rre_upgrade_v1_injected: bool = false
var rre_upgrade_to_v8_injected: bool = false
var rre_mutation_engine_v1_injected: bool = false # NEW: Flag for Mutation Engine V1

# --- Opcode Definitions ---
# Defines the mapping from specific pixel colors to conceptual opcodes.
# These are normalized RGB values (0.0 to 1.0).
const PXL_HALT = Color(1.0, 0.0, 0.0)        # Red pixel: Stop execution
const PXL_PRINT_HELLO = Color(0.0, 1.0, 0.0) # Green pixel: Print "Hello"
const PXL_JUMP_TO_X = Color(0.0, 0.0, 1.0)   # Blue pixel: Jump to a new X coordinate

# --- Godot Lifecycle Methods ---

func _ready():
    # Ensure the Node is added to the scene tree before trying to access the viewport.
    call_deferred("initialize_kernel")

func initialize_kernel():
    # Attempt to get the viewport's texture data.
    if display_screen and display_screen.texture:
        framebuffer_image = display_screen.texture.get_data()
        if framebuffer_image:
            framebuffer_image.lock()

            kernel_output_image = Image.new()
            kernel_output_image.create(framebuffer_image.get_width(), framebuffer_image.get_height(), false, Image.FORMAT_RGBA8)
            kernel_output_image.lock()
            kernel_output_image.blit_rect(framebuffer_image, Rect2(0, 0, framebuffer_image.get_width(), framebuffer_image.get_height()), Vector2(0, 0))

            print("PXKernel: Initialized with framebuffer size: ", framebuffer_image.get_width(), "x", framebuffer_image.get_height())
            ready_to_think = true
        else:
            print_err("PXKernel: Failed to get image data from display_screen texture.")
    else:
        print_err("PXKernel: DisplayScreen TextureRect or its texture not found. Ensure 'DisplayScreen' node exists and has a texture.")

    # --- RRE Self-Evolution Bootstrap (Initial RRE setup) ---
    if px_ztxt_memory and px_roadmap_watcher and px_scroll_log and not rre_self_evolution_bootstrap_injected:
        var self_evolution_roadmap = [
            ":: EXECUTE LOG:Starting PX_RRE_SELF_EVOLUTION_BOOTSTRAP",
            ":: EXECUTE INSTALL PXRoadmapWatcher.gd",
            ":: EXECUTE INSTALL PXAgentLoopDebugger.gd",
            ":: EXECUTE ENABLE PXScrollLibrarySync.gd",
            ":: EXECUTE ENABLE PXRoadmapAutoloader.gd",
            ":: EXECUTE INJECT SELF ROADMAP :: PX_RRE_SELF_EVOLUTION_BOOTSTRAP",
            ":: EXECUTE RECORD PX_RRE_SELF_EVOLUTION_BOOTSTRAP",
            ":: EXECUTE SAVE PX_RRE_SELF_EVOLUTION_BOOTSTRAP TO SCROLL LIBRARY",
            ":: EXECUTE ACTIVATE PXReflexFeedbackLogger",
            ":: EXECUTE SAVE CURRENT MEMORY SNAPSHOT",
            ":: EXECUTE DONE"
        ]
        var success = px_ztxt_memory.write_ztxt(px_roadmap_watcher.watched_roadmap_region, "\n".join(self_evolution_roadmap))
        if success:
            _log_kernel_activity("RRE Bootstrap Roadmap injected into watcher region.")
            rre_self_evolution_bootstrap_injected = true
        else:
            _log_kernel_activity("ERROR: Failed to inject RRE Bootstrap Roadmap.")
    elif rre_self_evolution_bootstrap_injected:
        _log_kernel_activity("RRE Bootstrap Roadmap already injected.")
    else:
        _log_kernel_activity("RRE Bootstrap dependencies not found.")

    # --- Godot RRE Upgrade v1 Roadmap Submission (Previous Upgrade) ---
    if px_ztxt_memory and px_roadmap_watcher and px_scroll_log and not godot_rre_upgrade_v1_injected:
        get_tree().create_timer(5.0).timeout.connect(Callable(self, "_inject_godot_rre_upgrade_v1"))
        _log_kernel_activity("Scheduled Godot RRE Upgrade v1 roadmap injection.")

    # --- RRE_UPGRADE_TO_V8 Roadmap Submission (Previous Upgrade) ---
    if px_ztxt_memory and px_roadmap_watcher and px_scroll_log and not rre_upgrade_to_v8_injected:
        get_tree().create_timer(10.0).timeout.connect(Callable(self, "_inject_rre_upgrade_to_v8"))
        _log_kernel_activity("Scheduled RRE_UPGRADE_TO_V8 roadmap injection.")

    # --- RRE_MUTATION_ENGINE_V1 Roadmap Submission (NEW) ---
    if px_ztxt_memory and px_roadmap_watcher and px_scroll_log and not rre_mutation_engine_v1_injected:
        get_tree().create_timer(15.0).timeout.connect(Callable(self, "_inject_rre_mutation_engine_v1"))
        _log_kernel_activity("Scheduled RRE_MUTATION_ENGINE_V1 roadmap injection.")


func _inject_godot_rre_upgrade_v1():
    """Injects the godot_rre_upgrade_v1 roadmap into the watcher region."""
    var godot_rre_upgrade_v1_roadmap = [
        ":: EXECUTE LOG:Starting Godot RRE Upgrade v1 Roadmap",
        ":: EXECUTE ACTIVATE PXReflexDaemon",
        ":: EXECUTE INSTALL map.py_module",
        ":: EXECUTE ENABLE PXDigestExporter_FileSave",
        ":: EXECUTE CREATE PXRoadmapLoader.gd",
        ":: EXECUTE VERIFY PXRoadmapExecutor.gd",
        ":: EXECUTE UPGRADE PXRoadmapExecutor.gd",
        ":: EXECUTE ADD support for nested steps, macros",
        ":: EXECUTE ENABLE RRE goal progress tracking",
        ":: EXECUTE INJECT PXScrollFeedbackLogger.gd",
        ":: EXECUTE RECORD roadmap execution results to .pxdigest",
        ":: EXECUTE SAVE PXRoadmapExecutionSnapshot TO SCROLL LIBRARY",
        ":: EXECUTE INSTALL PXAutoRoadmapMutator.gd",
        ":: EXECUTE ENABLE reflexive roadmap upgrades via feedback",
        ":: EXECUTE INJECT SELF ROADMAP :: godot_rre_core_upgrade_v1",
        ":: EXECUTE SAVE CURRENT MEMORY SNAPSHOT",
        ":: EXECUTE EXPORT RRE Upgrade Snapshot",
        ":: EXECUTE DONE"
    ]
    var success = px_ztxt_memory.write_ztxt(px_roadmap_watcher.watched_roadmap_region, "\n".join(godot_rre_upgrade_v1_roadmap))
    if success:
        _log_kernel_activity("Godot RRE Upgrade v1 Roadmap injected into watcher region.")
        godot_rre_upgrade_v1_injected = true
    else:
        _log_kernel_activity("ERROR: Failed to inject Godot RRE Upgrade v1 Roadmap.")

func _inject_rre_upgrade_to_v8():
    """Injects the RRE_UPGRADE_TO_V8 roadmap into the watcher region."""
    var rre_upgrade_to_v8_roadmap = [
        ":: EXECUTE LOG:Beginning RRE_UPGRADE_TO_V8: Autonomy Bootstrap",
        ":: EXECUTE INSTALL ReflexSelfScheduler",
        ":: EXECUTE ENABLE AutonomousTickLoop",
        ":: EXECUTE ADD ScheduleWatcher for StalledRoadmaps",
        ":: EXECUTE CREATE Module:RoadmapAutoLoader",
        ":: EXECUTE CREATE Module:RoadmapSelfHealer",
        ":: EXECUTE ACTIVATE Module:ReflexSelfScheduler",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Installing error awareness subsystem",
        ":: EXECUTE INSTALL ErrorSentinel",
        ":: EXECUTE ADD ErrorRecovery for FileNotFound",
        ":: EXECUTE ADD ConditionCheck for EmptyRoadmap",
        ":: EXECUTE ENABLE AutoRecoveryMode",
        ":: EXECUTE ACTIVATE ErrorSentinel",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Enabling mutation engine for roadmap regeneration",
        ":: EXECUTE ENABLE RoadmapArchiver",
        ":: EXECUTE ENABLE RoadmapMutator",
        ":: EXECUTE INJECT SELF ROADMAP :: RRE_MUTATION_ENGINE_V1",
        ":: EXECUTE INSTALL PXRoadmapMutator",
        ":: EXECUTE ACTIVATE PXRoadmapMutator",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Installing reflexive feedback for evolution tracking",
        ":: EXECUTE CREATE Module:PXReflexFeedback",
        ":: EXECUTE ADD FeedbackLoop for RoadmapSuccessRate",
        ":: EXECUTE ADD AutoTrigger for REFLEX_UPGRADE on MutationSuccess",
        ":: EXECUTE ENABLE FeedbackInjection into pxlogs/roadmap_feedback",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Upgrading persistence via digest and scroll",
        ":: EXECUTE SAVE CURRENT MEMORY SNAPSHOT",
        ":: EXECUTE SAVE Roadmap Log TO SCROLL LIBRARY",
        ":: EXECUTE EXPORT RRE_UPGRADE_TO_V8_SNAPSHOT",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Building self-replicating execution flow",
        ":: EXECUTE CREATE Module:PXExecutionSpawner",
        ":: EXECUTE ENABLE AutoRun Roadmaps from pxfs/autoexec/",
        ":: EXECUTE ADD Loop Trigger for AutoRun detection",
        ":: EXECUTE ACTIVATE PXExecutionSpawner",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:Validate & Archive",
        ":: EXECUTE VERIFY Module:ReflexSelfScheduler",
        ":: EXECUTE VERIFY Module:ErrorSentinel",
        ":: EXECUTE VERIFY Module:PXReflexFeedback",
        ":: EXECUTE ARCHIVE_ROADMAP:RRE_UPGRADE_TO_V8_ARCHIVE.txt",
        "", # Blank line for readability in zTXT
        ":: EXECUTE LOG:RRE_UPGRADE_TO_V8 complete: Entering self-sustaining mode.",
        ":: EXECUTE DONE"
    ]
    var success = px_ztxt_memory.write_ztxt(px_roadmap_watcher.watched_roadmap_region, "\n".join(rre_upgrade_to_v8_roadmap))
    if success:
        _log_kernel_activity("RRE_UPGRADE_TO_V8 Roadmap injected into watcher region.")
        rre_upgrade_to_v8_injected = true
    else:
        _log_kernel_activity("ERROR: Failed to inject RRE_UPGRADE_TO_V8 Roadmap.")

func _inject_rre_mutation_engine_v1():
    """Injects the RRE_MUTATION_ENGINE_V1 roadmap into the watcher region."""
    var rre_mutation_engine_v1_roadmap = [
        ":: EXECUTE LOG:Beginning RRE_MUTATION_ENGINE_V1: Activating Self-Mutation Loop",
        ":: EXECUTE LOAD_ROADMAP_FROM_FS:bootloader_v2.txt", # Placeholder, ensure this file exists or is created
        ":: EXECUTE MUTATE_ROADMAP:bootloader_v2.txt:emotion=curious&failure_count=1",
        ":: EXECUTE LOG:Mutated bootloader_v2.txt.",
        ":: EXECUTE LOAD_ROADMAP_FROM_FS:mutated_bootloader_v2_*.txt", # Placeholder for loading the specific mutated version
        ":: EXECUTE ARCHIVE_ROADMAP:mutated_bootloader_v2_executed.txt",
        ":: EXECUTE SAVE CURRENT MEMORY SNAPSHOT",
        ":: EXECUTE LOG:RRE_MUTATION_ENGINE_V1 Complete.",
        ":: EXECUTE DONE"
    ]
    var success = px_ztxt_memory.write_ztxt(px_roadmap_watcher.watched_roadmap_region, "\n".join(rre_mutation_engine_v1_roadmap))
    if success:
        _log_kernel_activity("RRE_MUTATION_ENGINE_V1 Roadmap injected into watcher region.")
        rre_mutation_engine_v1_injected = true
    else:
        _log_kernel_activity("ERROR: Failed to inject RRE_MUTATION_ENGINE_V1 Roadmap.")


func _process(delta):
    # Only run the kernel's main loop if it's initialized and ready.
    if ready_to_think:
        frame_counter += 1
        if frame_count >= KERNEL_CYCLE_FREQUENCY:
            frame_count = 0 # Reset counter
            analyze_display_stack()
            inject_logic()

# --- Kernel Core Logic ---

func analyze_display_stack():
    # This function simulates the kernel "reading" instructions and data
    # directly from the visual display (framebuffer_image).
    if not framebuffer_image or not framebuffer_image.is_locked():
        print_err("PXKernel: Framebuffer image not available or not locked for reading.")
        return

    var instructions_found = 0
    for y in range(framebuffer_image.get_height()):
        for x in range(framebuffer_image.get_width()):
            var color = framebuffer_image.get_pixel(x, y)

            match color:
                PXL_HALT: instructions_found += 1
                PXL_PRINT_HELLO: instructions_found += 1
                PXL_JUMP_TO_X:
                    instructions_found += 1
                    if x + 1 < framebuffer_image.get_width():
                        var arg_pixel = framebuffer_image.get_pixel(x + 1, y)
                        var jump_x_val = int(arg_pixel.r * 255.0)


func inject_logic():
    # This function simulates the kernel "writing" new instructions or data
    # back onto the display, thus influencing the next cycle's behavior.
    if not kernel_output_image or not kernel_output_image.is_locked():
        print_err("PXKernel: Kernel output image not available or not locked for writing.")
        return
    if not display_screen:
        print_err("PXKernel: 'DisplayScreen' TextureRect not found. Cannot inject logic visually.")
        return

    # Update the display
    var new_texture = ImageTexture.new()
    new_texture.create_from_image(kernel_output_image, 0)
    display_screen.texture = new_texture

# --- Logging ---

func _log_kernel_activity(message: String):
    """
    Helper function to log kernel activities to the PXScrollLog.
    """
    if px_scroll_log:
        px_scroll_log.add_line("KERNEL: " + message)
    else:
        print("PXKernel (Console Log): ", message)

