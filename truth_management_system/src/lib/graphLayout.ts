// src/lib/graphLayout.ts
import dagre from 'dagre';
import { Node, Edge, Position } from 'reactflow';

// Initialize a new dagre graph
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({})); // Required to avoid errors for edges without labels

// This function takes a list of nodes and edges, applies the dagre layout,
// and returns the nodes with updated position data.
export const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  // Set graph properties: rankdir (direction), ranksep (vertical spacing), nodesep (horizontal spacing)
  dagreGraph.setGraph({ rankdir: direction, ranksep: 100, nodesep: 50 }); // 'TB' for Top-Bottom, 'LR' for Left-Right

  // Add nodes to the dagre graph with estimated dimensions
  nodes.forEach((node) => {
    // Assuming CustomTruthNode has a fixed width (w-64 = 256px) and estimated height (approx 120px)
    dagreGraph.setNode(node.id, { width: 256, height: 120 });
  });

  // Add edges to the dagre graph
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Run the dagre layout algorithm
  dagre.layout(dagreGraph);

  // Update reactflow nodes with the positions calculated by dagre
  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);

    // dagre returns center positions, reactflow uses top-left. Adjust accordingly.
    node.position = {
      x: nodeWithPosition.x - nodeWithPosition.width / 2,
      y: nodeWithPosition.y - nodeWithPosition.height / 2,
    };

    // Explicitly set source/target positions for handles for consistent edge routing
    // This is optional but can lead to cleaner edge paths.
    node.sourcePosition = Position.Bottom;
    node.targetPosition = Position.Top;

    return node;
  });
};