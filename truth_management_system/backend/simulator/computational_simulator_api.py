from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import time

# Local imports from our simulator and the new abstraction layer
from .idea_simulator import ComputationalIdeaSimulator
from .unified_abstraction import LDBVAbstractionLayer

app = FastAPI(title="Vector Computational Universe API")

# Configure CORS
origins = [
    "http://localhost:3000", # Allow your React frontend to connect
    "http://localhost",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    # Add any other origins where your frontend might be hosted
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

simulator = ComputationalIdeaSimulator()
abstraction_layer = LDBVAbstractionLayer(simulator)


# --- Pydantic Models for existing API ---
class IdeaSimulationRequest(BaseModel):
    idea_description: str
    simulation_steps: int = 10
    mutation_rate: float = 0.1

class CrossoverRequest(BaseModel):
    idea1_id: str
    idea2_id: str
    crossover_strength: float = 0.5

class BatchSimulationRequest(BaseModel):
    ideas: List[str]
    simulations_per_idea: int = 5

class MutateIdeaRequest(BaseModel):
    idea_id: str
    mutation_strength: float = 0.1
    description_seed: Optional[str] = None

class AdjustComplexityRequest(BaseModel):
    idea_id: str
    delta: float

# --- Pydantic Models for Vector Command Interpretation ---
class InterpretVectorCommandRequest(BaseModel):
    vector_data: List[float]
    vector_id: Optional[str] = None

class InterpretVectorCommandResponse(BaseModel):
    generated_prompt: str
    llm_response: str
    interpretation_details: Dict[str, Any] = {}

# --- Pydantic Models for LDB-V Abstraction Layer API ---
class ThinkRequest(BaseModel):
    query: str

class CreateSimulatorRequest(BaseModel):
    description: str
    config: Dict[str, Any] = {}

# --- Existing API Endpoints ---
@app.get("/universe/status")
async def get_universe_status_endpoint():
    """Get current state of the computational universe"""
    return simulator.get_universe_status()

@app.post("/simulate/idea")
async def simulate_idea_evolution_endpoint(request: IdeaSimulationRequest):
    """Simulate the evolution of a computational idea"""
    try:
        result = simulator.simulate_idea_evolution(
            request.idea_description,
            request.simulation_steps,
            request.mutation_rate
        )
        return {"status": "success", "simulation_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/crossover")
async def simulate_idea_crossover_endpoint(request: CrossoverRequest):
    """Simulate crossover between two ideas"""
    try:
        result = simulator.simulate_idea_crossover(
            request.idea1_id,
            request.idea2_id,
            request.crossover_strength
        )
        return {"status": "success", "crossover_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/batch")
async def batch_simulate_ideas_endpoint(request: BatchSimulationRequest):
    """Batch simulate multiple computational ideas"""
    try:
        results = simulator.batch_simulate_ideas(
            request.ideas,
            request.simulations_per_idea
        )
        return {"status": "success", "batch_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/mutate")
async def mutate_idea_endpoint(request: MutateIdeaRequest):
    """Mutate an existing idea (placeholder for now)"""
    print(f"Mock Mutate: Idea {request.idea_id} with strength {request.mutation_strength}")
    idea_details = simulator.idea_library.get(request.idea_id)
    if not idea_details:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    original_vector = np.array(idea_details["final_state"])
    mutated_vector = (original_vector + (np.random.rand(original_vector.size) - 0.5) * request.mutation_strength).tolist()
    
    simulator.idea_library[request.idea_id]["final_state"] = mutated_vector
    simulator.idea_library[request.idea_id]["last_updated"] = time.time()

    return {
        "message": f"Idea {request.idea_id} mutated successfully (mock)",
        "idea_id": request.idea_id,
        "initial_vector_state": original_vector.tolist(),
        "mutated_vector_state": mutated_vector,
        "description_of_change": "Random mutation applied"
    }

@app.post("/simulate/complexity")
async def adjust_idea_complexity_endpoint(request: AdjustComplexityRequest):
    """Adjust the complexity of an existing idea (placeholder for now)"""
    print(f"Mock Complexity Adjust: Idea {request.idea_id} by delta {request.delta}")
    idea_details = simulator.idea_library.get(request.idea_id)
    if not idea_details:
        raise HTTPException(status_code=404, detail="Idea not found")

    old_complexity = idea_details["final_complexity"]
    new_complexity = max(0.1, min(1.0, old_complexity + request.delta))
    
    simulator.idea_library[request.idea_id]["final_complexity"] = new_complexity
    simulator.idea_library[request.idea_id]["last_updated"] = time.time()

    return {
        "message": f"Complexity of idea {request.idea_id} adjusted (mock)",
        "idea_id": request.idea_id,
        "old_complexity_score": old_complexity,
        "new_complexity_score": new_complexity,
        "description_of_change": f"Complexity adjusted by {request.delta}"
    }

@app.get("/ideas") # Endpoint to get all idea summaries
async def get_all_ideas_summary_endpoint():
    """Get summaries of all simulated ideas"""
    ideas_list = []
    for idea_id, details in simulator.idea_library.items():
        ideas_list.append({
            "idea_id": idea_id,
            "name": details.get("idea_description", "Unknown Idea"),
            "current_complexity": details.get("final_complexity", 0.0),
            "last_updated": time.ctime(details.get("last_updated", time.time()))
        })
    return {"status": "success", "idea_library": ideas_list}

@app.get("/ideas/{idea_id}")
async def get_idea_details_endpoint(idea_id: str):
    """Get details for a specific idea from library"""
    idea_details = simulator.idea_library.get(idea_id)
    if not idea_details:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    return {
        "idea_id": idea_id,
        "name": idea_details.get("idea_description", "Unknown Idea"),
        "initial_description_seed": idea_details.get("idea_description"),
        "current_vector_state": idea_details.get("final_state", []),
        "current_complexity": idea_details.get("final_complexity", 0.0),
        "creation_timestamp": time.ctime(idea_details.get("last_updated", time.time())),
        "last_updated": time.ctime(idea_details.get("last_updated", time.time())),
        "evolution_trace": [{"step": i, "vector_state": v, "timestamp": time.ctime(idea_details.get("last_updated", time.time()))} 
                            for i, v in enumerate(idea_details.get("evolution_trace", []))],
        "parent_ideas": [],
        "child_ideas": [],
    }

@app.delete("/ideas/{idea_id}")
async def delete_idea_endpoint(idea_id: str):
    """Delete a specific idea from the library"""
    if idea_id in simulator.idea_library:
        del simulator.idea_library[idea_id]
        return {"message": f"Idea {idea_id} deleted successfully", "deleted_idea_id": idea_id}
    else:
        raise HTTPException(status_code=404, detail="Idea not found")

# --- Vector Command Interpretation Endpoint ---
@app.post("/universe/interpret_vector_command", response_model=InterpretVectorCommandResponse)
async def interpret_vector_command_endpoint(request: InterpretVectorCommandRequest):
    """
    Interprets a given numerical vector as a command/intent within the universe
    and returns a generated prompt and a mock LLM response.
    """
    try:
        vector_np = np.array(request.vector_data)
        generated_prompt = simulator._vector_to_text_prompt(vector_np)
        
        mock_llm_response = (
            f"LLM Response (mock): Based on the interpretation:\n"
            f"'{generated_prompt}'\n\n"
            f"I suggest the following action: 'Initiate further exploration of this conceptual subspace to "
            f"identify potential correlations with existing highly novel ideas.'"
        )

        return InterpretVectorCommandResponse(
            generated_prompt=generated_prompt,
            llm_response=mock_llm_response,
            interpretation_details={"vector_id": request.vector_id, "vector_length": len(request.vector_data)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to interpret vector command: {str(e)}")

# --- LDB-V Abstraction Layer Endpoints ---
@app.post("/abstraction/think")
async def think_endpoint(request: ThinkRequest):
    """Natural language thinking interface for the LDB-V Abstraction Layer"""
    try:
        result = abstraction_layer.think(request.query)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abstraction layer 'think' failed: {str(e)}")

@app.post("/abstraction/simulator/create")
async def create_simulator_endpoint(request: CreateSimulatorRequest):
    """Create a custom simulator via the LDB-V Abstraction Layer"""
    try:
        abstraction_layer.create_simulator(request.description, request.config)
        return {"status": "success", "message": f"Simulator for '{request.description}' created/configured."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Abstraction layer 'create_simulator' failed: {str(e)}")

@app.get("/abstraction/simulators/prebuilt")
async def get_prebuilt_simulators_endpoint():
    """Get list of pre-built simulators and abstraction metrics from LDB-V Abstraction Layer"""
    try:
        metrics = abstraction_layer.get_abstraction_metrics()
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pre-built simulators: {str(e)}")

@app.get("/abstraction/workflow/generate")
async def generate_workflow_endpoint(query: str):
    """Generate visual workflow from query via LDB-V Abstraction Layer"""
    try:
        workflow = abstraction_layer.visual_builder.generate_visual_workflow(query)
        return {"status": "success", "workflow": workflow}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate workflow: {str(e)}")