import numpy as np
from typing import Dict, List, Any
from enum import Enum
# Assuming vector_computational_universe.py is in the same directory
from .vector_computational_universe import VectorComputationalUniverse, VectorComputation, ComputationalState

class VectorVirtualMachine:
    """A virtual machine that executes computations in vector space"""

    def __init__(self, universe: VectorComputationalUniverse):
        self.universe = universe
        self.running_processes = {}
        self.scheduler = VectorScheduler(universe)
        self.memory_manager = VectorMemoryManager(universe)

    def create_process(self, idea_description: str,
                       priority: float = 1.0) -> str:
        """Create a new computational process"""
        process_id = f"proc_{len(self.running_processes)}_{hash(idea_description)}"

        computation_id = self.universe.create_computation(idea_description)
        process = {
            "process_id": process_id,
            "computation_id": computation_id,
            "priority": priority,
            "status": ComputationalState.INITIALIZED.value,
            "created_at": np.datetime64('now').astype(str),
            "resources_allocated": {},
            "execution_history": []
        }

        self.running_processes[process_id] = process
        self.scheduler.register_process(process_id, priority)

        return process_id

    def execute_process(self, process_id: str,
                        operation_plan: List[str] = None) -> Dict[str, Any]:
        """Execute a computational process"""
        if process_id not in self.running_processes:
            raise ValueError(f"Process {process_id} not found")

        process = self.running_processes[process_id]
        process["status"] = ComputationalState.EXECUTING.value

        # Use default operation plan if none provided
        if not operation_plan:
            operation_plan = ["vector_evolve", "entropy_maximize", "convergence_check"]

        # Allocate computational resources
        resources = self.memory_manager.allocate_resources(process_id)
        process["resources_allocated"] = resources

        try:
            # Execute computation
            results = self.universe.execute_computation(
                process["computation_id"], operation_plan
            )

            process["status"] = ComputationalState.COMPLETED.value
            process["execution_history"].append({
                "timestamp": np.datetime64('now').astype(str),
                "operations": operation_plan,
                "results": results
            })

            # Release resources
            self.memory_manager.release_resources(process_id)

            return results

        except Exception as e:
            process["status"] = ComputationalState.ERROR.value
            process["error"] = str(e)
            # Release resources even on error
            self.memory_manager.release_resources(process_id)
            raise

    def parallel_execute(self, process_ids: List[str],
                         operation_plan: List[str] = None) -> Dict[str, Any]:
        """Execute multiple processes in parallel (vectorized)"""
        # Batch execution using LDB-V GPU acceleration
        batch_results = {}

        for process_id in process_ids:
            if process_id in self.running_processes:
                try:
                    result = self.execute_process(process_id, operation_plan)
                    batch_results[process_id] = result
                except Exception as e:
                    # Capture error for individual process in batch
                    batch_results[process_id] = {"error": str(e)}
            else:
                batch_results[process_id] = {"error": f"Process {process_id} not found."}

        return batch_results

    def get_process_state(self, process_id: str) -> Dict[str, Any]:
        """Get current state of a computational process"""
        if process_id not in self.running_processes:
            return {"error": "Process not found"}

        process = self.running_processes[process_id]
        computation = self.universe.computations.get(process["computation_id"])

        return {
            "process_id": process_id,
            "status": process["status"],
            "computation_state": computation.state_vector.tolist() if computation else None,
            "complexity": computation.metadata["complexity"] if computation else 0,
            "execution_count": len(process["execution_history"]),
            "resources": process["resources_allocated"]
        }

class VectorScheduler:
    """Schedules computational processes in vector space"""

    def __init__(self, universe: VectorComputationalUniverse):
        self.universe = universe
        self.process_queue = []
        self.scheduling_policy = "priority_based"

    def register_process(self, process_id: str, priority: float):
        """Register a process for scheduling"""
        self.process_queue.append({"process_id": process_id, "priority": priority})
        # Sort by priority (higher priority first)
        self.process_queue.sort(key=lambda x: x["priority"], reverse=True)

    def schedule_next_batch(self, batch_size: int = 10) -> List[str]:
        """Schedule next batch of processes for execution"""
        scheduled = []
        for i in range(min(batch_size, len(self.process_queue))):
            scheduled.append(self.process_queue[i]["process_id"])

        # Remove scheduled processes from queue
        self.process_queue = self.process_queue[batch_size:]

        return scheduled

class VectorMemoryManager:
    """Manages computational memory in vector space"""

    def __init__(self, universe: VectorComputationalUniverse):
        self.universe = universe
        self.allocated_memory = {}
        self.memory_blocks = {}

    def allocate_resources(self, process_id: str) -> Dict[str, Any]:
        """Allocate computational resources for a process"""
        # In vector space, "memory" is subspace allocation
        subspace_size = self.universe.dimensionality // 100  # 1% of total space
        start_pos = len(self.allocated_memory) * subspace_size

        resources = {
            "subspace_start": start_pos,
            "subspace_size": subspace_size,
            "energy_budget": 100.0,
            "computation_quota": 1000
        }

        self.allocated_memory[process_id] = resources
        return resources

    def release_resources(self, process_id: str):
        """Release resources allocated to a process"""
        if process_id in self.allocated_memory:
            del self.allocated_memory[process_id]