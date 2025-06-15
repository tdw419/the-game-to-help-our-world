# PXLSCROLL_ID: AI_DEPLOY_NEW_SCROLL_001
# DESCRIPTION: Prompts AI to create a new scroll and deploys it automatically.
# TARGET_ZONE: MAIN_CONTENT # Default zone for general messages from this scroll

# COMMAND: CLEAR_ZONE
# ZONE_NAME: MAIN_CONTENT
# COLOR: 000030 # Very dark blue background

# COMMAND: WRITE_TEXT
# TEXT: AI is drafting a new scroll for deployment...
# X: 10
# Y: 10
# FONT_SIZE: 24
# COLOR: FFFFFF # White text

# COMMAND: DRAW_RECTANGLE
# X: 5
# Y: 5
# WIDTH: 790 # Max width of display
# HEIGHT: 50
# COLOR: 00AAFF # Light blue outline
# FILL: False

# --- AI Interaction: Ask AI to generate a scroll, and directly deploy it ---
# The AI's response for this prompt *must* be valid .pxl content.
# The daemon will save it to scrolls/ based on OUTPUT_SCROLL_PATH.
# The AI's response also includes its own PXLSCROLL_ID, which is key.

COMMAND: AI_QUERY
PROMPT: "Generate a simple pixel scroll named 'AI_Greetings_Scroll' that writes 'Hello from AI-generated scroll!' to the MAIN_CONTENT zone and updates the STATUS_BAR. Use a unique ID for the scroll. The display resolution is 800x600."
OUTPUT_FILE: temp_ai_generated_pxl_content.txt # Optional: Save AI's raw .pxl response to a temp file
OUTPUT_SCROLL_PATH: AI_Greetings_Scroll_Generated.pxl # NEW: Deploy AI's response as a new scroll here
OUTPUT_ZONE: AI_FEEDBACK # Display a summary of AI action in AI_FEEDBACK zone
OUTPUT_COLOR: 00AAFF # Light blue for AI action feedback
DISPLAY_LENGTH: 80 # Display a short summary of the AI's internal thought

CONSOLE_LOG: "AI has been instructed to generate and deploy a new scroll. Awaiting execution."

# Update STATUS_BAR
OUTPUT_TO_8PNG_ZONE: STATUS_BAR
OUTPUT_TEXT: "AI Initiated Self-Write @ " + TIMESTAMP
OUTPUT_COLOR: FF8C00 # Dark Orange for self-writing initiation

# Update TASK_LIST
OUTPUT_TO_8PNG_ZONE: TASK_LIST
OUTPUT_TEXT: "Pending: AI-Generated Scroll Execution"
OUTPUT_COLOR: 00AAFF
