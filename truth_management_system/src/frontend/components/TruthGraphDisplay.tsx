// src/frontend/components/TruthGraphDisplay.tsx
import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  Node,
  Edge,
  MarkerType,
  NodeChange,
  EdgeChange,
  Position,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { BackendTruthLedgerEntryDTO, getTruths } from ' @/frontend/services/TruthApiClient';
import { AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from ' @/components/ui/alert';
import { CustomTruthNode, CustomTruthNodeData } from './CustomTruthNode';
import { CustomTruthEdge, CustomTruthEdgeData } from './CustomTruthEdge';
import { getLayoutedElements } from ' @/lib/graphLayout';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from ' @/components/ui/sheet'; // Import Sheet components
import { Button } from ' @/components/ui/button'; // Import Button for SheetClose

// Define node types for ReactFlow
const nodeTypes = {
  customTruthNode: CustomTruthNode,
};

// Define edge types for ReactFlow
const edgeTypes = {
  customTruthEdge: CustomTruthEdge,
};

export default function TruthGraphDisplay() {
  const [nodes, setNodes] = useState<Node<CustomTruthNodeData>[]>([]);
  const [edges, setEdges] = useState<Edge<CustomTruthEdgeData>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showDetailsPanel, setShowDetailsPanel] = useState(false); // New state for sheet visibility
  const [detailsNode, setDetailsNode] = useState<Node<CustomTruthNodeData> | null>(null); // Node whose details are shown
  const { fitView } = useReactFlow();

  useEffect(() => {
    const fetchTruthData = async () => {
      try {
        setLoading(true);
        setError(null);
        const fetchedTruths: BackendTruthLedgerEntryDTO[] = await getTruths();

        let initialNodes: Node<CustomTruthNodeData>[] = [];
        const initialEdges: Edge<CustomTruthEdgeData>[] = [];

        fetchedTruths.forEach((truth) => {
          initialNodes.push({
            id: truth.id,
            type: 'customTruthNode',
            data: {
              label: truth.content.substring(0, 50) + (truth.content.length > 50 ? '...' : ''),
              confidence: truth.confidence,
              fullContent: truth.content, // Pass full content for 'View Details'
              isSelected: false, // Initial state, will be updated in renderNodes map
              onNodeClick: () => {}, // Placeholder, will be replaced in renderNodes map
              onViewDetailsRequest: () => {}, // Placeholder, will be replaced in renderNodes map
            },
            sourcePosition: Position.Bottom,
            targetPosition: Position.Top,
          });
        });

        fetchedTruths.forEach((truth) => {
          truth.relationships.forEach((rel) => {
            // Ensure the target node exists before creating an edge to it
            if (initialNodes.some(node => node.id === rel.targetTruthId)) {
              const isLowConfidence = rel.confidence <= 0.25;
              initialEdges.push({
                id: `e-${truth.id}-${rel.targetTruthId}`,
                source: truth.id,
                target: rel.targetTruthId,
                type: 'customTruthEdge',
                data: {
                  confidence: rel.confidence,
                  relationType: rel.type,
                },
                style: {
                  strokeWidth: 2,
                  stroke: isLowConfidence ? 'red' : 'gray',
                },
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  color: isLowConfidence ? 'red' : 'gray',
                },
              });
            }
          });
        });

        const layoutedNodes = getLayoutedElements(initialNodes, initialEdges);

        setNodes(layoutedNodes);
        setEdges(initialEdges);

        requestAnimationFrame(() => {
          fitView({ padding: 0.2, duration: 200 });
        });

      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred.');
        console.error("Failed to fetch truth data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTruthData();
  }, [fitView]);

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes],
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    [setEdges],
  );

  // Callback for when a CustomTruthNode is clicked (left-click)
  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId); // Select the clicked node
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setDetailsNode(node); // Set node for details panel
      setShowDetailsPanel(true); // Open details panel
    }
  }, [nodes]); // Depend on 'nodes' to ensure `find` works with current state

  // Callback for opening details panel from context menu (or explicitly)
  const handleViewDetailsRequest = useCallback((nodeId: string) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      setDetailsNode(node);
      setShowDetailsPanel(true);
      setSelectedNodeId(nodeId); // Also select the node if details are requested via context menu
    }
  }, [nodes]); // Depend on 'nodes' to ensure `find` works with current state

  // Callback for when the ReactFlow pane (background) is clicked
  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null); // Deselect any node
    setShowDetailsPanel(false); // Close details panel
    setDetailsNode(null); // Clear details node
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-lg text-gray-700">Loading truths...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            Failed to load truth graph: {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="w-full h-[600px] border rounded-lg shadow-sm relative"> {/* Added relative for sheet positioning */}
      <ReactFlow
        nodes={nodes.map(node => ({
          ...node,
          // Augment node data with interactive properties for CustomTruthNode
          data: {
            ...node.data,
            isSelected: node.id === selectedNodeId,
            onNodeClick: handleNodeClick,
            onViewDetailsRequest: handleViewDetailsRequest, // Pass the new callback
          },
        }))}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onPaneClick={handlePaneClick} // Handle clicks on the background
        proOptions={{ hideAttribution: true }} // Hide React Flow attribution for cleaner UI
      >
        <Controls />
        <Background />
      </ReactFlow>

      {/* Details Side Panel */}
      <Sheet open={showDetailsPanel} onOpenChange={(open) => {
        setShowDetailsPanel(open);
        if (!open) { // When sheet closes
          setDetailsNode(null); // Clear details
          setSelectedNodeId(null); // Deselect node
        }
      }}>
        <SheetContent side="right" className="w-full sm:w-[500px] flex flex-col">
          <SheetHeader>
            <SheetTitle>Truth Details: {detailsNode?.data.label}</SheetTitle>
            <SheetDescription>
              ID: {detailsNode?.data.id}
            </SheetDescription>
          </SheetHeader>
          <div className="flex-1 overflow-y-auto py-4">
            {detailsNode ? (
              <>
                <p className="text-sm text-gray-700 mb-4">{detailsNode.data.fullContent}</p>
                <p className="text-sm text-gray-600">
                  Confidence: <span className="font-semibold">{Math.round(detailsNode.data.confidence * 100)}%</span>
                </p>
                {/* Potentially display more details here, like related truths, timestamp, etc. */}
                {/* Example for timestamp (if added to CustomTruthNodeData) */}
                {/* <p className="text-sm text-gray-600">Timestamp: {new Date(detailsNode.data.timestamp).toLocaleString()}</p> */}
              </>
            ) : (
              <p className="text-gray-500">Select a node to view details.</p>
            )}
          </div>
          <div className="mt-auto pt-4 border-t">
            {/* Additional actions for the selected node could go here */}
            <SheetClose asChild>
              <Button variant="outline" className="w-full">Close</Button>
            </SheetClose>
          </div>
        </SheetContent>
      </Sheet>

      <style jsx global>{`
        /* Styles applied to the path element within CustomTruthEdge */
        .custom-animated-edge {
          stroke-dasharray: 5 5;
          animation: dashoffset 1s linear infinite;
        }
        @keyframes dashoffset {
          to {
            stroke-dashoffset: -10;
          }
        }
      `}</style>
    </div>
  );
}