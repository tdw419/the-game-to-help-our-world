import numpy as np
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
import networkx as nx

class ComputationalState(Enum):
    INITIALIZED = "initialized"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"
    SUSPENDED = "suspended"

class VectorComputation:
    """A computational idea represented in vector space"""

    def __init__(self, idea_id: str, initial_state_vector: np.ndarray):
        self.idea_id = idea_id
        self.state_vector = initial_state_vector  # Current computational state
        self.execution_trace = []  # History of state transitions
        self.dependencies = []  # Other computations this depends on
        self.resources = {}  # Computational resources allocated
        self.metadata = {
            "created_at": np.datetime64('now').astype(str), # Convert to string for JSON serialization
            "complexity": self._calculate_complexity(initial_state_vector),
            "dimensionality": initial_state_vector.shape[0]
        }

    def _calculate_complexity(self, vector: np.ndarray) -> float:
        """Calculate computational complexity based on vector properties"""
        # More complex ideas have higher entropy in their state vectors
        if np.std(vector) == 0:
            return 0.0
        return float(np.sum(np.abs(np.fft.fft(vector))) / len(vector))

    def evolve_state(self, transformation: Callable, parameters: Dict = None):
        """Evolve the computational idea using LDB-V operations"""
        previous_state = self.state_vector.copy()

        try:
            # Apply transformation (LDB-V operation)
            new_state = transformation(self.state_vector, **(parameters or {}))
            self.state_vector = new_state

            # Record transition
            transition = {
                "from_state": previous_state.tolist(), # Convert to list for JSON
                "to_state": new_state.tolist(),       # Convert to list for JSON
                "transformation": transformation.__name__,
                "parameters": parameters,
                "entropy_change": self._calculate_entropy_change(previous_state, new_state)
            }
            self.execution_trace.append(transition)

        except Exception as e:
            self.metadata["error"] = str(e)
            raise

    def _calculate_entropy_change(self, old_state: np.ndarray, new_state: np.ndarray) -> float:
        """Calculate information entropy change during state transition"""
        # Ensure states are normalized and non-negative for entropy calculation
        old_state_norm = old_state / (np.sum(old_state) + 1e-10)
        new_state_norm = new_state / (np.sum(new_state) + 1e-10)

        old_entropy = -np.sum(old_state_norm * np.log(old_state_norm + 1e-10))
        new_entropy = -np.sum(new_state_norm * np.log(new_state_norm + 1e-10))
        return new_entropy - old_entropy

class VectorComputationalUniverse:
    """The main environment for simulating computational ideas"""

    def __init__(self, dimensionality: int = 1024):
        self.dimensionality = dimensionality
        self.computations = {}  # idea_id -> VectorComputation
        self.ldb_v_operations = self._initialize_ldb_v_operations()
        self.computational_graph = nx.DiGraph()
        self.global_state = np.random.random(dimensionality)
        self.energy_budget = 1000.0  # Computational energy available

    def _initialize_ldb_v_operations(self) -> Dict[str, Callable]:
        """Initialize LDB-V operations for computational simulation"""
        return {
            "vector_evolve": self._op_vector_evolve,
            "idea_crossover": self._op_idea_crossover,
            "computational_mutate": self._op_computational_mutate,
            "state_superpose": self._op_state_superpose,
            "entropy_maximize": self._op_entropy_maximize,
            "complexity_reduce": self._op_complexity_reduce,
            "convergence_check": self._op_convergence_check
        }

    def create_computation(self, idea_description: str,
                           initial_conditions: Dict = None) -> str:
        """Create a new computational idea from description"""
        # Simple ID generation
        idea_id = f"comp_{len(self.computations)}_{hash(idea_description)}"

        # Convert idea description to initial state vector
        initial_vector = self._idea_to_vector(idea_description, initial_conditions)

        computation = VectorComputation(idea_id, initial_vector)
        self.computations[idea_id] = computation
        self.computational_graph.add_node(idea_id, computation=computation)

        return idea_id

    def _idea_to_vector(self, idea: str, conditions: Dict = None) -> np.ndarray:
        """Convert natural language idea to computational state vector"""
        # Simple embedding - in production would use proper semantic embedding
        words = idea.lower().split()
        vector = np.zeros(self.dimensionality)

        for i, word in enumerate(words):
            # Simple hash-based positioning
            pos = hash(word) % self.dimensionality
            vector[pos] += 1.0 / (i + 1)  # Decreasing influence for later words

        # Normalize
        if np.linalg.norm(vector) > 0:
            vector = vector / np.linalg.norm(vector)

        # Apply initial conditions if provided
        if conditions:
            for key, value in conditions.items():
                cond_pos = hash(str(key)) % self.dimensionality
                vector[cond_pos] += float(value) * 0.1

        return vector

    def execute_computation(self, idea_id: str,
                            operation_sequence: List[str],
                            max_iterations: int = 100) -> Dict[str, Any]:
        """Execute a sequence of LDB-V operations on a computation"""
        if idea_id not in self.computations:
            raise ValueError(f"Computation {idea_id} not found")

        computation = self.computations[idea_id]
        results = {
            "initial_state": computation.state_vector.tolist(), # Convert to list for JSON
            "final_state": None,
            "iterations": 0,
            "energy_used": 0.0,
            "converged": False,
            "complexity_evolution": []
        }

        for iteration in range(max_iterations):
            current_energy_cost = 0.0

            for op_name in operation_sequence:
                if op_name not in self.ldb_v_operations:
                    raise ValueError(f"Unknown operation: {op_name}")

                # Execute LDB-V operation
                operation = self.ldb_v_operations[op_name]
                energy_cost = self._calculate_energy_cost(op_name, computation)

                if current_energy_cost + energy_cost > self.energy_budget:
                    break

                try:
                    # Pass default empty dict for parameters for now,
                    # as current frontend doesn't send specific op parameters.
                    operation(computation, {}) # Updated to pass empty dict for params
                    current_energy_cost += energy_cost
                except Exception as e:
                    computation.metadata["error"] = str(e)
                    break

            results["energy_used"] += current_energy_cost
            self.energy_budget -= current_energy_cost

            # Update complexity evolution
            results["complexity_evolution"].append(computation.metadata["complexity"])


            # Check for convergence
            if self._op_convergence_check(computation):
                results["converged"] = True
                break

        results["final_state"] = computation.state_vector.tolist() # Convert to list for JSON
        results["iterations"] = iteration + 1

        return results

    # LDB-V Operations for Computational Simulation
    def _op_vector_evolve(self, computation: VectorComputation, params: Dict = None):
        """Evolve computation using gradient-like dynamics"""
        params = params or {}
        learning_rate = params.get("learning_rate", 0.1)
        gradient = np.random.random(computation.state_vector.shape) - 0.5
        new_state = computation.state_vector + learning_rate * gradient
        new_state = new_state / (np.linalg.norm(new_state) + 1e-10) # Normalize
        computation.evolve_state(lambda x, **p: new_state, parameters={"learning_rate": learning_rate})

    def _op_idea_crossover(self, computation: VectorComputation, params: Dict = None):
        """Combine with another computational idea"""
        params = params or {}
        other_idea_id = params.get("other_idea_id")
        alpha = params.get("alpha", 0.3)

        if other_idea_id and other_idea_id in self.computations:
            other_comp = self.computations[other_idea_id]
            new_state = (1 - alpha) * computation.state_vector + alpha * other_comp.state_vector
        else:
            # Crossover with global state if no other_idea_id provided or found
            new_state = (1 - alpha) * computation.state_vector + alpha * self.global_state

        new_state = new_state / (np.linalg.norm(new_state) + 1e-10) # Normalize
        computation.evolve_state(lambda x, **p: new_state, parameters={"alpha": alpha, "other_idea_id": other_idea_id})
        if other_idea_id:
            self.computational_graph.add_edge(computation.idea_id, other_idea_id)

    def _op_computational_mutate(self, computation: VectorComputation, params: Dict = None):
        """Introduce random mutations"""
        params = params or {}
        mutation_rate = params.get("mutation_rate", 0.05)
        mutation_strength = params.get("mutation_strength", 0.1)

        mutation_mask = np.random.random(computation.state_vector.shape) < mutation_rate
        mutations = np.random.normal(0, mutation_strength, computation.state_vector.shape)
        new_state = computation.state_vector + mutation_mask * mutations
        new_state = new_state / (np.linalg.norm(new_state) + 1e-10) # Normalize
        computation.evolve_state(lambda x, **p: new_state, parameters={"mutation_rate": mutation_rate, "mutation_strength": mutation_strength})

    def _op_state_superpose(self, computation: VectorComputation, params: Dict = None):
        """Create quantum-like superposition of computational states"""
        params = params or {}
        superposition_strength = params.get("superposition_strength", 0.2)

        orthogonal = np.random.random(computation.state_vector.shape)
        # Gram-Schmidt to make it orthogonal to current state
        if np.linalg.norm(computation.state_vector) > 1e-10:
            orthogonal = orthogonal - np.dot(orthogonal, computation.state_vector) * computation.state_vector / (np.linalg.norm(computation.state_vector)**2)
        if np.linalg.norm(orthogonal) > 1e-10:
            orthogonal = orthogonal / np.linalg.norm(orthogonal)
        else: # if orthogonal is zero vector, generate another random vector
            orthogonal = np.random.random(computation.state_vector.shape)
            if np.linalg.norm(computation.state_vector) > 1e-10:
                orthogonal = orthogonal - np.dot(orthogonal, computation.state_vector) * computation.state_vector / (np.linalg.norm(computation.state_vector)**2)
            orthogonal = orthogonal / (np.linalg.norm(orthogonal) + 1e-10)

        new_state = computation.state_vector + superposition_strength * orthogonal
        new_state = new_state / (np.linalg.norm(new_state) + 1e-10)
        computation.evolve_state(lambda x, **p: new_state, parameters={"superposition_strength": superposition_strength})

    def _op_entropy_maximize(self, computation: VectorComputation, params: Dict = None):
        """Increase computational entropy/information content"""
        params = params or {}
        increase_factor = params.get("increase_factor", 1.1)
        step_size = params.get("step_size", 0.05)

        # Avoid log of zero or negative
        state_for_log = np.maximum(computation.state_vector, 1e-10)
        current_entropy = -np.sum(state_for_log * np.log(state_for_log))

        # Aim for entropy increase
        # This is a simplified gradient ascent. Real entropy maximization is complex.
        # Here, we push values towards a more uniform distribution.
        new_state = computation.state_vector + step_size * (np.random.random(computation.state_vector.shape) - 0.5)
        new_state = np.clip(new_state, 1e-10, None) # Ensure non-negative
        new_state = new_state / (np.sum(new_state) + 1e-10) # Normalize
        computation.evolve_state(lambda x, **p: new_state, parameters={"increase_factor": increase_factor, "step_size": step_size})

    def _op_complexity_reduce(self, computation: VectorComputation, params: Dict = None):
        """Reduce computational complexity while preserving information"""
        params = params or {}
        cutoff_factor = params.get("cutoff_factor", 0.25) # 0.25 means keep lowest 25% frequencies

        freq_domain = np.fft.fft(computation.state_vector)
        cutoff_idx = int(len(freq_domain) * cutoff_factor)

        # Zero out high frequencies (complexity reduction)
        freq_domain[cutoff_idx:-cutoff_idx] = 0
        new_state = np.real(np.fft.ifft(freq_domain))
        new_state = new_state / (np.linalg.norm(new_state) + 1e-10) # Normalize
        computation.evolve_state(lambda x, **p: new_state, parameters={"cutoff_factor": cutoff_factor})


    def _op_convergence_check(self, computation: VectorComputation) -> bool:
        """Check if computation has converged to stable state"""
        if len(computation.execution_trace) < 3: # Need at least 3 steps to compare changes
            return False

        # Consider recent changes in metadata (e.g., complexity, entropy)
        recent_complexities = [
            comp_meta["complexity"] for comp_meta in computation.execution_trace[-3:]
        ]
        # Check if changes in complexity are small
        if all(abs(recent_complexities[i] - recent_complexities[i-1]) < 0.001 for i in range(1, len(recent_complexities))):
            return True
        return False


    def _calculate_energy_cost(self, operation: str, computation: VectorComputation) -> float:
        """Calculate energy cost of LDB-V operation"""
        base_costs = {
            "vector_evolve": 1.0,
            "idea_crossover": 2.0,
            "computational_mutate": 1.5,
            "state_superpose": 3.0,
            "entropy_maximize": 2.5,
            "complexity_reduce": 2.0,
            "convergence_check": 0.5 # Cheaper to check than to execute
        }

        # Energy cost scales with complexity (more complex ideas cost more to operate on)
        complexity_factor = computation.metadata["complexity"]
        return base_costs.get(operation, 1.0) * (1 + complexity_factor)