// src/frontend/components/TruthSpectrumBadge.tsx
import React from 'react';
import { Badge } from ' @/components/ui/badge';
import { cn } from ' @/lib/utils';

interface TruthSpectrumBadgeProps {
  confidence: number; // 0.0 to 1.0
  className?: string;
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'bg-green-500 hover:bg-green-600';
  if (confidence >= 0.6) return 'bg-lime-500 hover:bg-lime-600';
  if (confidence >= 0.4) return 'bg-yellow-500 hover:bg-yellow-600';
  return 'bg-red-500 hover:bg-red-600';
};

export const TruthSpectrumBadge: React.FC<TruthSpectrumBadgeProps> = ({ confidence, className }) => {
  const confidencePercent = Math.round(confidence * 100);
  const colorClass = getConfidenceColor(confidence);

  return (
    <Badge className={cn(colorClass, 'text-white px-2 py-1 text-xs font-semibold', className)}>
      Confidence: {confidencePercent}%
    </Badge>
  );
};