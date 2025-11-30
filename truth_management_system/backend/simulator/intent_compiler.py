# backend/simulator/intent_compiler.py

from typing import Dict, List, Any, Callable
from dataclasses import dataclass
import re
import numpy as np # Added for potential future use or if needed by LDB-V System

@dataclass
class IntentPattern:
    pattern: str
    operation_sequence: List[str]
    parameters: Dict[str, Any]
    confidence: float

class LDBVIntentCompiler:
    """Compiles natural language intent to LDB-V operations"""
    
    def __init__(self, ldb_v_system):
        # ldb_v_system is expected to be an instance of ComputationalIdeaSimulator
        self.ldb_v = ldb_v_system 
        self.intent_patterns = self._initialize_intent_patterns()
        self.operation_templates = self._initialize_operation_templates()

    def _initialize_intent_patterns(self) -> List[IntentPattern]:
        """Initialize common intent patterns"""
        return [
            # Similarity and search patterns
            IntentPattern(
                pattern=r"(find|search|similar).*?(neural|network|model)",
                operation_sequence=["semantic_search", "complexity_analyze"],
                parameters={"search_width": 16, "complexity_threshold": 0.7},
                confidence=0.92
            ),
            IntentPattern(
                pattern=r"(compare|difference).*?(algorithm|method|approach)",
                operation_sequence=["vector_compare", "difference_highlight"],
                parameters={"comparison_metric": "cosine", "highlight_threshold": 0.3},
                confidence=0.88
            ),
            
            # Evolution and optimization patterns
            IntentPattern(
                pattern=r"(evolve|improve|optimize).*?(idea|concept|algorithm)",
                operation_sequence=["idea_evolve", "entropy_maximize", "convergence_check"],
                parameters={"mutation_rate": 0.1, "max_iterations": 50},
                confidence=0.85
            ),
            IntentPattern(
                pattern=r"(combine|merge|hybrid).*?(concept|approach|method)",
                operation_sequence=["idea_crossover", "complexity_balance"],
                parameters={"crossover_strength": 0.3, "balance_threshold": 0.8},
                confidence=0.90
            ),
            
            # Analysis and insight patterns
            IntentPattern(
                pattern=r"(analyze|understand).*?(complexity|structure)",
                operation_sequence=["complexity_analyze", "structure_decompose"],
                parameters={"depth_analysis": True, "decomposition_levels": 3},
                confidence=0.87
            ),
            IntentPattern(
                pattern=r"(cluster|group).*?(similar|related).*?(ideas|concepts)",
                operation_sequence=["vector_cluster", "relationship_map"],
                parameters={"cluster_count": 5, "map_connections": True},
                confidence=0.83
            )
        ]

    def _initialize_operation_templates(self) -> Dict[str, Callable]:
        """Initialize operation templates that generate LDB-V sequences"""
        return {
            "semantic_search": self._template_semantic_search,
            "vector_compare": self._template_vector_compare,
            "idea_evolve": self._template_idea_evolve,
            "idea_crossover": self._template_idea_crossover,
            "complexity_analyze": self._template_complexity_analyze,
            "vector_cluster": self._template_vector_cluster
        }

    def compile_intent(self, natural_language: str, context: Dict = None) -> Dict[str, Any]:
        """Compile natural language to LDB-V operation sequence"""
        # print(f"🔍 Compiling: '{natural_language}'") # Removed for cleaner output in tool env

        # Find matching intent patterns
        matches = []
        for pattern in self.intent_patterns:
            if re.search(pattern.pattern, natural_language.lower()):
                matches.append(pattern)

        if not matches:
            # Default to basic analysis
            return self._default_operations(natural_language)

        # Use highest confidence match
        best_match = max(matches, key=lambda x: x.confidence)

        # Generate operation sequence using template
        # Note: The operation_sequence in IntentPattern is a list of strings, but
        # _initialize_operation_templates maps these to Callables.
        # This means best_match.operation_sequence[0] is used to pick a template function.
        # This implies a single dominant operation for the primary intent.
        template_func = self.operation_templates.get(best_match.operation_sequence[0])
        if template_func:
            operation_sequence = template_func(natural_language, best_match.parameters, context)
        else:
            # Fallback if the primary operation in pattern is not templated
            # or if it's a sequence of non-templated operations
            operation_sequence = [{"operation": op, "parameters": {}, "description": f"Perform {op}"} 
                                  for op in best_match.operation_sequence]


        compilation_result = {
            "input": natural_language,
            "matched_intent": best_match.pattern,
            "confidence": best_match.confidence,
            "operation_sequence": operation_sequence,
            "parameters": best_match.parameters,
            "expected_output": self._predict_output_type(natural_language)
        }

        # print(f"   ✅ Compiled to {len(operation_sequence)} LDB-V operations") # Removed for cleaner output in tool env
        return compilation_result

    def _template_semantic_search(self, query: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for semantic search operations"""
        return [
            {
                "operation": "vector_embed",
                "parameters": {"text": query, "purpose": "search_query"},
                "description": f"Embed query '{query}' for semantic search"
            },
            {
                "operation": "similarity_search",
                "parameters": {
                    "query_vector": "previous_result",
                    "search_width": params.get("search_width", 10),
                    "similarity_threshold": 0.7
                },
                "description": "Find similar concepts in vector space"
            },
            {
                "operation": "complexity_analyze",
                "parameters": {"complexity_threshold": params.get("complexity_threshold", 0.5)},
                "description": "Analyze complexity of found concepts"
            }
        ]

    def _template_idea_evolve(self, idea: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for idea evolution operations"""
        return [
            {
                "operation": "vector_embed",
                "parameters": {"text": idea, "purpose": "evolution_start"},
                "description": f"Embed initial idea: {idea}"
            },
            {
                "operation": "idea_evolve",
                "parameters": {
                    "mutation_rate": params.get("mutation_rate", 0.1),
                    "evolution_strength": 0.3
                },
                "description": "Evolve idea through vector mutations"
            },
            {
                "operation": "entropy_maximize",
                "parameters": {"target_entropy_increase": 0.2},
                "description": "Increase information content"
            },
            {
                "operation": "convergence_check",
                "parameters": {"stability_threshold": 0.01},
                "description": "Check if idea has stabilized"
            }
        ]

    def _template_idea_crossover(self, query: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for idea crossover operations"""
        # Extract multiple ideas from query
        ideas = self._extract_ideas_from_query(query)

        operations = []
        for i, idea in enumerate(ideas):
            operations.append({
                "operation": "vector_embed",
                "parameters": {"text": idea, "purpose": f"crossover_input_{i}"},
                "description": f"Embed idea {i+1}: {idea}"
            })

        operations.extend([
            {
                "operation": "idea_crossover",
                "parameters": {
                    # This would need to be dynamically resolved from previous_result in a real system
                    "input_vectors": ["previous_result"] * len(ideas), 
                    "crossover_strength": params.get("crossover_strength", 0.3)
                },
                "description": "Combine ideas through vector crossover"
            },
            {
                "operation": "complexity_balance",
                "parameters": {"balance_threshold": params.get("balance_threshold", 0.8)},
                "description": "Balance complexity of hybrid idea"
            }
        ])

        return operations

    def _template_vector_compare(self, query: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for vector comparison operations"""
        # This template would need more sophisticated NLP to extract the two items to compare
        # For now, it's a placeholder based on the pattern
        return [
            {
                "operation": "vector_embed",
                "parameters": {"text": query, "purpose": "comparison_item_1"},
                "description": f"Embed first item for comparison: {query}"
            },
            {
                "operation": "vector_embed",
                "parameters": {"text": "second item from query", "purpose": "comparison_item_2"}, # Placeholder
                "description": f"Embed second item for comparison"
            },
            {
                "operation": "calculate_similarity",
                "parameters": {
                    "vector1": "previous_result_1",
                    "vector2": "previous_result_2",
                    "metric": params.get("comparison_metric", "cosine")
                },
                "description": "Calculate similarity between the two items"
            },
            {
                "operation": "difference_highlight",
                "parameters": {"threshold": params.get("highlight_threshold", 0.3)},
                "description": "Highlight differences based on similarity"
            }
        ]

    def _template_complexity_analyze(self, query: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for complexity analysis operations"""
        return [
            {
                "operation": "vector_embed",
                "parameters": {"text": query, "purpose": "analysis_target"},
                "description": f"Embed target for complexity analysis: {query}"
            },
            {
                "operation": "complexity_analyze",
                "parameters": {
                    "depth_analysis": params.get("depth_analysis", False),
                    "decomposition_levels": params.get("decomposition_levels", 1)
                },
                "description": "Perform detailed complexity analysis"
            },
            {
                "operation": "structure_decompose",
                "parameters": {},
                "description": "Decompose structure if possible"
            }
        ]

    def _template_vector_cluster(self, query: str, params: Dict, context: Dict) -> List[Dict]:
        """Template for vector clustering operations"""
        return [
            {
                "operation": "load_vectors_for_clustering",
                "parameters": {"criteria": query},
                "description": f"Load relevant vectors for clustering based on: {query}"
            },
            {
                "operation": "vector_cluster",
                "parameters": {
                    "num_clusters": params.get("cluster_count", 5),
                    "method": "kmeans" # Example
                },
                "description": "Cluster vectors into groups"
            },
            {
                "operation": "relationship_map",
                "parameters": {"show_connections": params.get("map_connections", False)},
                "description": "Map relationships within clusters"
            }
        ]

    def _extract_ideas_from_query(self, query: str) -> List[str]:
        """Extract multiple ideas from natural language query"""
        # Simple extraction - in production would use more sophisticated NLP
        ideas = []
        if "and" in query.lower():
            parts = query.lower().split(" and ")
            ideas.extend([p.strip() for p in parts if len(p.split()) > 2])
        elif "with" in query.lower():
            parts = query.lower().split(" with ")
            ideas.extend([p.strip() for p in parts if len(p.split()) > 2])

        return ideas if ideas else [query]

    def _predict_output_type(self, query: str) -> str:
        """Predict the type of output expected"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["find", "search", "locate"]):
            return "search_results"
        elif any(word in query_lower for word in ["compare", "difference", "versus"]):
            return "comparison_analysis"

        elif any(word in query_lower for word in ["evolve", "improve", "optimize"]):
            return "evolved_concept"
        elif any(word in query_lower for word in ["combine", "merge", "hybrid"]):
            return "hybrid_concept"
        elif any(word in query_lower for word in ["analyze", "understand", "explain"]):
            return "insight_analysis"
        else:
            return "general_analysis"

    def _default_operations(self, query: str) -> Dict[str, Any]:
        """Default operations for unmatched intents"""
        return {
            "input": query,
            "matched_intent": "default_analysis",
            "confidence": 0.7,
            "operation_sequence": [
                {
                    "operation": "vector_embed",
                    "parameters": {"text": query, "purpose": "general_analysis"},
                    "description": f"Embed query for general analysis"
                },
                {
                    "operation": "complexity_analyze",
                    "parameters": {},
                    "description": "Analyze concept complexity"
                },
                {
                    "operation": "semantic_expand",
                    "parameters": {"expansion_factor": 0.2},
                    "description": "Expand semantic understanding"
                }
            ],
            "parameters": {},
            "expected_output": "general_analysis"
        }