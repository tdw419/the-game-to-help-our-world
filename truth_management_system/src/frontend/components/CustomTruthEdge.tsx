// src/frontend/components/CustomTruthEdge.tsx
import React from 'react';
import { EdgeProps, getBezierPath } from 'reactflow';
import { TruthSpectrumBadge } from './TruthSpectrumBadge';

export interface CustomTruthEdgeData {
  confidence: number;
  relationType: string;
}

export const CustomTruthEdge: React.FC<EdgeProps<CustomTruthEdgeData>> = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  data,
  markerEnd,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  if (!data) {
    console.warn(`CustomTruthEdge: No data provided for edge ${id}. Falling back to default.`);
    return (
      <path
        id={id}
        style={style}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
    );
  }

  const { confidence, relationType } = data;
  const isLowConfidence = confidence <= 0.25;

  return (
    <>
      <path
        id={id}
        style={style}
        className={`react-flow__edge-path ${isLowConfidence ? 'custom-animated-edge' : ''}`}
        d={edgePath}
        markerEnd={markerEnd}
      />
      <g
        transform={`translate(${labelX}, ${labelY})`}
        className="nodrag nopan"
      >
        {/* Background rect for readability */}
        <rect
          x={-55}
          y={-30}
          width={110}
          height={50}
          fill="white"
          stroke="#e0e0e0"
          rx="5" ry="5"
          className="shadow-sm"
        />
        <text
          x="0"
          y="-10"
          textAnchor="middle"
          className="text-[0.65rem] fill-gray-700 font-medium"
        >
          {relationType}
        </text>
        <foreignObject
          width={100}
          height={20}
          x={-50}
          y={5}
          className="flex items-center justify-center"
        >
          <TruthSpectrumBadge confidence={confidence} className="!px-1 !py-0.5 !text-[0.6rem]" />
        </foreignObject>
      </g>
    </>
  );
};