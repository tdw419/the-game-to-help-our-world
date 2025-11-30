# backend/simulator/unified_abstraction.py

from typing import Dict, Any, List
# Local imports for the abstraction layer components
from .intent_compiler import LDBVIntentCompiler
from .vector_simulator_builder import VectorSimulatorBuilder
from .visual_abstraction import VisualLDBVBuilder

class LDBVAbstractionLayer:
    """Unified abstraction layer for easy LDB-V usage"""
    
    def __init__(self, ldb_v_system):
        # ldb_v_system is expected to be an instance of ComputationalIdeaSimulator
        self.ldb_v = ldb_v_system 
        self.intent_compiler = LDBVIntentCompiler(ldb_v_system)
        self.simulator_builder = VectorSimulatorBuilder(ldb_v_system, self.intent_compiler)
        self.visual_builder = VisualLDBVBuilder(ldb_v_system)
        
        # Pre-built simulators for common tasks
        self.simulators = self._initialize_prebuilt_simulators()

    def _initialize_prebuilt_simulators(self) -> Dict[str, Any]:
        """Initialize pre-built simulators for instant use"""
        return {
            "idea_evolver": self.simulator_builder.create_simulator("idea_evolution", {}),
            "concept_clusterer": self.simulator_builder.create_simulator("concept_clustering", {}),
            "research_explorer": self.simulator_builder.create_simulator("research_exploration", {}),
            "algorithm_designer": self.simulator_builder.create_simulator("algorithm_design", {}),
            "knowledge_synthesizer": self.simulator_builder.create_simulator("knowledge_synthesis", {})
        }

    def think(self, natural_language: str) -> Dict[str, Any]:
        """High-level thinking interface - just describe what you want"""
        print(f"🤔 THINKING: {natural_language}")
        
        # Compile intent to LDB-V operations
        compilation = self.intent_compiler.compile_intent(natural_language)
        
        # Generate visual workflow
        workflow = self.visual_builder.generate_visual_workflow(natural_language)
        
        # Execute using appropriate simulator or direct operations
        result = self._execute_thought(compilation, workflow)
        
        return {
            "input": natural_language,
            "compilation": compilation,
            "workflow": workflow,
            "result": result,
            "summary": self._generate_thought_summary(result)
        }

    def _execute_thought(self, compilation: Dict, workflow: Dict) -> Dict[str, Any]:
        """Execute the compiled thought"""
        # Try to use a pre-built simulator if the workflow type matches
        workflow_type = workflow.get("type", "general_workflow")
        
        # Mapping workflow types to simulator methods
        simulator_method_map = {
            "evolution_workflow": "evolve_idea", # Example, assumes evolve_idea takes natural language input
            "comparison_workflow": "compare_concepts", # Placeholder
            "synthesis_workflow": "synthesize_knowledge", # Placeholder
            "analysis_workflow": "analyze_concepts", # Placeholder
            "general_workflow": "general_analysis" # Placeholder
        }

        # Determine which simulator to use and which method to call
        if workflow_type == "evolution_workflow" and "idea_evolver" in self.simulators:
            idea_to_evolve = compilation["input"] # Simple extraction for now
            return self.simulators["idea_evolver"].evolve_idea(idea_to_evolve)
        elif workflow_type == "synthesis_workflow" and "knowledge_synthesizer" in self.simulators:
            # Need to extract concepts from natural_language or compilation
            concepts_to_synthesize = self.intent_compiler._extract_ideas_from_query(compilation["input"])
            return self.simulators["knowledge_synthesizer"].synthesize_knowledge(concepts_to_synthesize)
        elif workflow_type == "comparison_workflow" and "research_explorer" in self.simulators:
             # This would need more complex parsing to get two concepts to compare
             # For now, let's just make a mock
             print(f"Executing mock comparison for: {compilation['input']}")
             return {"comparison_result": f"Mock comparison of {compilation['input']}", "score": 0.75}

        # Fallback to direct operation execution if no specific simulator/method matches
        return self._execute_direct_operations(compilation["operation_sequence"])

    def _execute_direct_operations(self, operations: List[Dict]) -> Dict[str, Any]:
        """Execute LDB-V operations directly (mocked for now)"""
        results = []
        for op in operations:
            # Mock execution - in production would call actual LDB-V methods on self.ldb_v
            # e.g., getattr(self.ldb_v, op["operation"])(**op["parameters"])
            result = {
                "operation": op["operation"],
                "description": op["description"],
                "output": f"Result of {op['operation']} with params {op['parameters']}",
                "success": True
            }
            results.append(result)
            
        return {
            "execution_results": results,
            "success_rate": len([r for r in results if r["success"]]) / len(results) if results else 0,
            "final_output": results[-1]["output"] if results else "No operations executed"
        }

    def _generate_thought_summary(self, result: Dict) -> str:
        """Generate human-readable thought summary"""
        if "summary" in result: # For simulator results
            return f"Thought completed: {result['summary']}"
        elif "final_output" in result: # For direct execution
            return f"Executed {len(result['execution_results'])} operations with {result['success_rate']:.0%} success rate. Final: {result['final_output']}"
        else:
            return "Thought processing completed"

    def create_simulator(self, description: str, config: Dict = None) -> Any:
        """Create a custom simulator from description"""
        # Classify simulator type from description
        simulator_type = self._classify_simulator_type(description)
        
        return self.simulator_builder.create_simulator(simulator_type, config or {})

    def _classify_simulator_type(self, description: str) -> str:
        """Classify simulator type from description"""
        desc_lower = description.lower()
        
        if any(word in desc_lower for word in ["evolve", "improve", "optimize"]):
            return "idea_evolution"
        elif any(word in desc_lower for word in ["cluster", "group", "organize"]):
            return "concept_clustering"
        elif any(word in desc_lower for word in ["research", "explore", "discover"]):
            return "research_exploration"
        elif any(word in desc_lower for word in ["algorithm", "design", "create"]):
            return "algorithm_design"
        elif any(word in desc_lower for word in ["synthesize", "combine", "integrate"]):
            return "knowledge_synthesis"
        else:
            return "idea_evolution" # Default

    def get_abstraction_metrics(self) -> Dict[str, Any]:
        """Get metrics about abstraction layer usage"""
        return {
            "prebuilt_simulators": list(self.simulators.keys()),
            "intent_patterns_count": len(self.intent_compiler.intent_patterns),
            "visual_components_count": len(self.visual_builder.visual_components),
            "workflow_templates_count": len(self.visual_builder.workflow_templates) # This was a mistake in original prompt. Should be a count.
        }