# backend/simulator/visual_abstraction.py

from typing import Dict, List, Any

class VisualLDBVBuilder:
    """Provides visual programming abstractions for LDB-V"""
    
    def __init__(self, ldb_v_system):
        # ldb_v_system is expected to be an instance of ComputationalIdeaSimulator
        self.ldb_v = ldb_v_system 
        self.visual_components = self._initialize_visual_components()
        self.workflow_templates = self._initialize_workflow_templates()

    def create_workflow(self, workflow_type: str, nodes: List[Dict]) -> Dict[str, Any]:
        """Create a visual workflow from node definitions"""
        workflow = {
            "type": workflow_type,
            "nodes": nodes,
            "connections": self._infer_connections(nodes),
            "execution_plan": self._generate_execution_plan(nodes)
        }
        
        return workflow

    def _initialize_workflow_templates(self) -> Dict[str, List[Dict]]:
        """Initialize pre-built workflow templates"""
        return {
            "evolution_workflow": [
                {"id": "input", "type": "embedding_node"},
                {"id": "evolve", "type": "evolution_node"},
                {"id": "analyze", "type": "analysis_node"}
            ],
            "comparison_workflow": [
                {"id": "input1", "type": "embedding_node"},
                {"id": "input2", "type": "embedding_node"},
                {"id": "similarity", "type": "similarity_node"},
                {"id": "analyze", "type": "analysis_node"}
            ],
            "synthesis_workflow": [
                {"id": "input1", "type": "embedding_node"},
                {"id": "input2", "type": "embedding_node"},
                {"id": "crossover", "type": "crossover_node"},
                {"id": "analyze", "type": "analysis_node"}
            ],
            "analysis_workflow": [
                {"id": "input", "type": "embedding_node"},
                {"id": "analyze", "type": "analysis_node"}
            ]
        }

    def _initialize_visual_components(self) -> Dict[str, Dict]:
        """Initialize visual components for common LDB-V operations"""
        return {
            "embedding_node": {
                "type": "input",
                "description": "Convert text to vector",
                "inputs": ["text"],
                "outputs": ["vector"],
                "icon": "📊",
                "color": "blue"
            },
            "similarity_node": {
                "type": "processing",
                "description": "Calculate vector similarity",
                "inputs": ["vector1", "vector2"],
                "outputs": ["similarity_score"],
                "icon": "🔍",
                "color": "green"
            },
            "evolution_node": {
                "type": "processing",
                "description": "Evolve vector through mutations",
                "inputs": ["input_vector"],
                "outputs": ["evolved_vector"],
                "icon": "🧬",
                "color": "purple"
            },
            "crossover_node": {
                "type": "processing",
                "description": "Combine two vectors",
                "inputs": ["vector_a", "vector_b"],
                "outputs": ["hybrid_vector"],
                "icon": "⚡",
                "color": "orange"
            },
            "analysis_node": {
                "type": "output",
                "description": "Analyze vector properties",
                "inputs": ["vector"],
                "outputs": ["complexity", "entropy", "stability"],
                "icon": "📈",
                "color": "red"
            }
        }

    def _infer_connections(self, nodes: List[Dict]) -> List[Dict]:
        """Infer connections between nodes based on input/output types"""
        connections = []
        
        # Simple sequential connection for now
        for i, node in enumerate(nodes):
            if i < len(nodes) - 1:
                next_node = nodes[i + 1]
                connections.append({
                    "from_node": node["id"],
                    "from_output": "vector",  # Default output
                    "to_node": next_node["id"],
                    "to_input": "input_vector"  # Default input
                })
                
        return connections

    def _generate_execution_plan(self, nodes: List[Dict]) -> List[Dict]:
        """Generate LDB-V execution plan from visual nodes"""
        execution_plan = []
        
        for node in nodes:
            component = self.visual_components.get(node["type"])
            if component:
                execution_plan.append({
                    "operation": self._map_node_to_operation(node["type"]),
                    "parameters": node.get("parameters", {}),
                    "description": component["description"],
                    "node_id": node["id"]
                })
                
        return execution_plan

    def _map_node_to_operation(self, node_type: str) -> str:
        """Map visual node type to LDB-V operation"""
        mapping = {
            "embedding_node": "vector_embed",
            "similarity_node": "cosine_similarity",
            "evolution_node": "idea_evolve",
            "crossover_node": "idea_crossover",
            "analysis_node": "complexity_analyze"
        }
        return mapping.get(node_type, "vector_embed") # Default to vector_embed

    def generate_visual_workflow(self, natural_language: str) -> Dict[str, Any]:
        """Generate visual workflow from natural language description"""
        # Simple keyword-based workflow generation
        workflow_type = self._classify_workflow_type(natural_language)
        
        nodes = self._generate_nodes_for_workflow(workflow_type, natural_language)
        
        return self.create_workflow(workflow_type, nodes)

    def _classify_workflow_type(self, description: str) -> str:
        """Classify workflow type from natural language"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["evolve", "improve", "optimize"]):
            return "evolution_workflow"
        elif any(word in desc_lower for word in ["compare", "difference", "versus"]):
            return "comparison_workflow"
        elif any(word in desc_lower for word in ["combine", "merge", "hybrid"]):
            return "synthesis_workflow"
        elif any(word in desc_lower for word in ["analyze", "understand", "explore"]):
            return "analysis_workflow"
        else:
            return "general_workflow"

    def _generate_nodes_for_workflow(self, workflow_type: str, description: str) -> List[Dict]:
        """Generate nodes for specific workflow type"""
        # Node IDs are simple for now, would need a more robust ID system in a real visual editor
        base_nodes = [
            {"id": "input_1", "type": "embedding_node", "parameters": {"text": description}}
        ]
        
        if workflow_type == "evolution_workflow":
            base_nodes.extend([
                {"id": "evolve_1", "type": "evolution_node", "parameters": {"mutation_rate": 0.1}},
                {"id": "analyze_1", "type": "analysis_node", "parameters": {}}
            ])
        elif workflow_type == "comparison_workflow":
            base_nodes.extend([
                {"id": "input_2", "type": "embedding_node", "parameters": {"text": "comparison target"}}, # Placeholder
                {"id": "similarity_1", "type": "similarity_node", "parameters": {}},
                {"id": "analyze_1", "type": "analysis_node", "parameters": {}}
            ])
        elif workflow_type == "synthesis_workflow":
            base_nodes.extend([
                {"id": "input_2", "type": "embedding_node", "parameters": {"text": "partner concept"}}, # Placeholder
                {"id": "crossover_1", "type": "crossover_node", "parameters": {}},
                {"id": "analyze_1", "type": "analysis_node", "parameters": {}}
            ])
        elif workflow_type == "analysis_workflow":
             base_nodes.extend([
                {"id": "analyze_1", "type": "analysis_node", "parameters": {}}
            ])
        # general_workflow already covered by base_nodes
                
        return base_nodes
