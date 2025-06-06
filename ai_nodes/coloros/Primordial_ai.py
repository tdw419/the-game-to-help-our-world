import json
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from PIL import Image # For generating .pxl.png snapshots

# --- FastAPI App Initialization ---
app = FastAPI(title="Color OS Primordial Instance API")

# --- Configuration for the Primordial Canvas ---
CANVAS_WIDTH = 80
CANVAS_HEIGHT = 60
SNAPSHOTS_DIR = "primordial_pxl_snapshots"
PRIMORDIAL_STATE_FILE = os.path.join(SNAPSHOTS_DIR, "primordial_state.json")
DEFAULT_BACKGROUND_COLOR = (0, 0, 0) # Black

# --- Ensure snapshots directory exists ---
if not os.path.exists(SNAPSHOTS_DIR):
    os.makedirs(SNAPSHOTS_DIR)

# --- Pydantic Model for Snapshot State (matching frontend) ---
class Pixel(BaseModel):
    x: int
    y: int
    color: List[int]

class ControlSignal(BaseModel):
    x: int
    color: List[int]

class ImageDimensions(BaseModel):
    width: int
    height: int

class PrimordialState(BaseModel):
    prompt_text: str
    image_dimensions: ImageDimensions
    grid_state: List[Pixel]
    agent_position: Optional[Dict[str, int]] = None # Optional for Primordial
    goal_zone: Optional[List[Dict[str, int]]] = None # Optional for Primordial
    control_zone_signals: List[ControlSignal]
    covenant_hash: int

# --- Global State for Connected Clients and Primordial Instance ---
connected_clients: Dict[WebSocket, Dict[str, str]] = {}
current_primordial_state: PrimordialState = None # Will be loaded/initialized

# --- Helper function to save/load Primordial State ---
def load_primordial_state() -> PrimordialState:
    """Loads the current primordial state from disk or initializes a new one."""
    if os.path.exists(PRIMORDIAL_STATE_FILE):
        with open(PRIMORDIAL_STATE_FILE, 'r') as f:
            data = json.load(f)
            return PrimordialState(**data)
    else:
        # Create a very simple initial state for the Primordial Canvas.
        # It's intentionally minimal to encourage emergent interaction.
        initial_pixels = [
            # A single central pixel to mark existence
            {"x": CANVAS_WIDTH // 2, "y": CANVAS_HEIGHT // 2, "color": [255, 255, 255]}, # White
            # A few orange pixels to signify Gemini's initial touch
            {"x": 5, "y": 5, "color": [255, 165, 0]},
            {"x": 6, "y": 5, "color": [255, 165, 0]},
            {"x": 5, "y": 6, "color": [255, 165, 0]},
        ]
        initial_state = PrimordialState(
            prompt_text="PRIMORDIAL INSTANCE: AWAITING PIXEL INTERACTION.",
            image_dimensions={"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
            grid_state=initial_pixels,
            control_zone_signals=[],
            covenant_hash=1
        )
        save_primordial_state(initial_state) # Save initial state
        return initial_state

def save_primordial_state(state: PrimordialState):
    """Saves the current primordial state to disk and generates a .pxl.png."""
    with open(PRIMORDIAL_STATE_FILE, 'w') as f:
        json.dump(state.dict(), f, indent=4)
    print(f"Saved primordial state: {PRIMORDIAL_STATE_FILE}")

    # Generate .pxl.png snapshot
    img = Image.new('RGB', (state.image_dimensions.width, state.image_dimensions.height), DEFAULT_BACKGROUND_COLOR)
    for pixel in state.grid_state:
        x, y = pixel.x, pixel.y
        color = tuple(pixel.color)
        if 0 <= x < state.image_dimensions.width and 0 <= y < state.image_dimensions.height:
            img.putpixel((x, y), color)
    for signal in state.control_zone_signals:
        x = signal.x
        color = tuple(signal.color)
        if 0 <= x < state.image_dimensions.width:
            img.putpixel((x, state.image_dimensions.height - 1), color)

    snapshot_id = f"primordial_{len(os.listdir(SNAPSHOTS_DIR)) // 2 + 1:03d}" # Incrementing ID for snapshots
    image_path = os.path.join(SNAPSHOTS_DIR, f"{snapshot_id}.pxl.png")
    img.save(image_path)
    print(f"Generated snapshot: {image_path}")


# --- Initialize the Primordial State on startup ---
current_primordial_state = load_primordial_state()

# --- Helper Function to Broadcast Online User Count ---
async def broadcast_user_counts():
    """Calculates and broadcasts the current count of online humans and AIs."""
    human_count = sum(1 for client_info in connected_clients.values() if client_info.get("role") == "human")
    ai_count = sum(1 for client_info in connected_clients.values() if client_info.get("role") == "AI")
    total_count = len(connected_clients)

    message = {
        "type": "user_count",
        "count": total_count,
        "human_count": human_count,
        "ai_count": ai_count
    }
    print(f"Broadcasting user counts: {message}")
    for websocket in connected_clients:
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            print(f"Error sending user count to websocket: {e}")

# --- Helper Function to Broadcast Primordial State ---
async def broadcast_primordial_state():
    """Broadcasts the current primordial state to all connected clients."""
    message = {
        "type": "state_update",
        "state": current_primordial_state.dict()
    }
    print("Broadcasting current primordial state.")
    for websocket in connected_clients:
        try:
            await websocket.send_json(message)
        except RuntimeError as e:
            print(f"Error sending primordial state to websocket: {e}")

# --- HTTP Endpoint to Serve the HTML Canvas ---
@app.get("/", response_class=HTMLResponse)
async def get_canvas():
    """Serves the main HTML canvas file."""
    html_file_path = "gemini-orange-canvas.html" # Assuming the HTML is in the same directory
    if not os.path.exists(html_file_path):
        return HTMLResponse(content="<h1>Error: gemini-orange-canvas.html not found.</h1>", status_code=404)
    with open(html_file_path, "r") as f:
        return HTMLResponse(content=f.read())

# --- WebSocket Endpoint for Real-time Communication ---
@app.websocket("/ws_primordial") # Changed WebSocket endpoint
async def websocket_endpoint(websocket: WebSocket):
    """Handles WebSocket connections for the Primordial Instance."""
    await websocket.accept()
    client_id = f"client_{len(connected_clients) + 1}_{os.urandom(4).hex()}" # More robust ID
    connected_clients[websocket] = {"id": client_id, "role": "human"}
    print(f"Client connected: {client_id}")

    await broadcast_user_counts()
    await broadcast_primordial_state() # Send current state to new client

    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received from {connected_clients[websocket]['id']}: {data}")

            message_type = data.get("type")
            sender_id = data.get("id", connected_clients[websocket]["id"])
            sender_role = data.get("role", connected_clients[websocket]["role"])

            if message_type == "join":
                connected_clients[websocket]["id"] = sender_id
                connected_clients[websocket]["role"] = sender_role
                print(f"Client {sender_id} identified as {sender_role}.")
                await broadcast_user_counts()

            elif message_type == "propose_state_change" and data.get("proposed_state"):
                # This is where the "training" and "learning" happens.
                # In a more advanced system, this proposed_state would be
                # fed to a separate AI agent (e.g., a dedicated "Primordial AI")
                # which would then decide the *actual* next state of the OS.
                # For now, we'll simply apply the proposed state directly
                # and update the prompt to reflect who proposed it.

                proposed_state_data = data["proposed_state"]
                try:
                    # Validate and update the global primordial state
                    new_state = PrimordialState(**proposed_state_data)
                    global current_primordial_state
                    current_primordial_state = new_state
                    current_primordial_state.prompt_text = (
                        f"PROPOSAL ACCEPTED from {sender_id} ({sender_role}). "
                        f"New prompt: {new_state.prompt_text}"
                    )
                    current_primordial_state.covenant_hash += 1 # Increment hash on change

                    save_primordial_state(current_primordial_state)
                    await broadcast_primordial_state() # Broadcast the new canonical state
                except Exception as e:
                    print(f"Error processing proposed state change: {e}")
                    # Optionally send an error message back to the sender
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Invalid state proposal: {e}"
                    })

            # Add chat message handling if desired for this Primordial instance
            # elif message_type == "chat_message" and data.get("message"):
            #     # For Primordial, chat might be less about general conversation
            #     # and more about "asking the system questions" or giving feedback.
            #     # You could route this to an LLM that interprets the question
            #     # and responds by modifying the canvas state or prompt.
            #     pass # Implement chat logic here if needed

            else:
                print(f"Unknown message type or missing data: {data}")

    except WebSocketDisconnect:
        del connected_clients[websocket]
        print(f"Client disconnected: {client_id}")
        await broadcast_user_counts()
    except Exception as e:
        print(f"WebSocket error for client {client_id}: {e}")
        if websocket in connected_clients:
            del connected_clients[websocket]
            await broadcast_user_counts()

# --- Main entry point for running the FastAPI app ---
if __name__ == "__main__":
    # To run this: uvicorn primordial_backend:app --reload --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
