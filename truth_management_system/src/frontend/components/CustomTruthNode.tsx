// src/frontend/components/CustomTruthNode.tsx
import React, { useState, useCallback } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle } from ' @/components/ui/card';
import { TruthSpectrumBadge } from './TruthSpectrumBadge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from ' @/components/ui/dropdown-menu';
import { cn } from ' @/lib/utils'; // For conditional class merging

// Augment CustomTruthNodeData to include interactive props
export interface CustomTruthNodeData {
  label: string; // Truncated content
  confidence: number;
  fullContent?: string; // Optional: for "View Details"
  isSelected: boolean; // Indicates if the node is currently selected
  onNodeClick: (nodeId: string) => void; // Callback for when the node is clicked
  onViewDetailsRequest: (nodeId: string) => void; // New: Callback to open details panel
}

// CustomTruthNode receives NodeProps with the augmented data type
export const CustomTruthNode: React.FC<NodeProps<CustomTruthNodeData>> = ({ id, data }) => {
  const { label, confidence, fullContent, isSelected, onNodeClick, onViewDetailsRequest } = data; // Destructure all data props, including new onViewDetailsRequest

  const [menuOpen, setMenuOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });

  // Handle right-click for context menu
  const handleContextMenu = useCallback((event: React.MouseEvent) => {
    event.preventDefault(); // Prevent default browser context menu
    setMenuPosition({ x: event.clientX, y: event.clientY });
    setMenuOpen(true); // Open the shadcn/ui dropdown menu
  }, []);

  const handleCloseMenu = useCallback(() => {
    setMenuOpen(false);
  }, []);

  // Modified to call the parent's handler for viewing details
  const handleViewDetails = useCallback(() => {
    onViewDetailsRequest(id); // Call the new prop to open the side panel
    handleCloseMenu();
  }, [id, onViewDetailsRequest, handleCloseMenu]);

  const handleChallengeTruth = useCallback(() => {
    alert(`Challenging Truth: ${id}`);
    handleCloseMenu();
  }, [id, handleCloseMenu]);

  const handleAddRelationship = useCallback(() => {
    alert(`Adding relationship from: ${id}`);
    handleCloseMenu();
  }, [id, handleCloseMenu]);

  // Handle left-click for selection
  const handleNodeClick = useCallback((event: React.MouseEvent) => {
    if (event.button === 0 && onNodeClick) { // Only trigger on left-click
      onNodeClick(id); // Call the parent's node click handler
    }
    handleCloseMenu(); // Close context menu if it was open from a previous right click
  }, [id, onNodeClick, handleCloseMenu]);


  return (
    <>
      <Card
        className={cn(
          "shadow-md border border-gray-300 w-64 transition-all duration-200 ease-in-out cursor-pointer",
          isSelected && "border-blue-500 ring-2 ring-blue-300 shadow-lg" // Highlight if selected
        )}
        onContextMenu={handleContextMenu}
        onClick={handleNodeClick}
      >
        <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-gray-400" />
        <CardHeader className="p-3 pb-2">
          <CardTitle className="text-sm font-semibold text-gray-800 break-words line-clamp-2">
            {label}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3 pt-0 flex justify-end">
          <TruthSpectrumBadge confidence={confidence} />
        </CardContent>
        <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-gray-400" />
      </Card>

      {menuOpen && (
        <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
          <DropdownMenuTrigger asChild>
            {/* Invisible trigger positioned at mouse click for context menu */}
            <div
              style={{
                position: 'fixed',
                top: menuPosition.y,
                left: menuPosition.x,
                width: 1,
                height: 1,
                overflow: 'hidden',
                pointerEvents: 'none', // Allow clicks to pass through to underlying elements (e.g., React Flow pane)
              }}
            />
          </DropdownMenuTrigger>
          <DropdownMenuContent
            style={{
              position: 'fixed',
              top: menuPosition.y,
              left: menuPosition.x,
            }}
            onCloseAutoFocus={e => e.preventDefault()} // Prevent focus shift that can cause unwanted scrolling
          >
            <DropdownMenuLabel>Node Actions ({id})</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleViewDetails}>View Details</DropdownMenuItem>
            <DropdownMenuItem onClick={handleChallengeTruth}>Challenge Truth</DropdownMenuItem>
            <DropdownMenuItem onClick={handleAddRelationship}>Add Relationship</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </>
  );
};