import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { TrendingUp, Gauge, Zap, Clock, Info, Edit, ThumbsUp } from 'lucide-react';

export interface UsageEvent {
  timestamp: Date;
  contributionWeight: number;
}

export interface MetricElement {
  id: string; // The current/agreed-upon name
  baseConfidence: number;
  usageEvents: UsageEvent[];
}

export interface RenameProposal {
  id: string; // Unique ID for the proposal
  elementId: string; // ID of the element being renamed
  oldName: string;
  newName: string;
  rationale: string;
  votes: number;
  status: 'pending' | 'adopted' | 'rejected'; // New status field
}

export interface MetricDisplayCardProps {
  /**
   * The metric element data to display.
   */
  element: MetricElement;
  /**
   * Tunable scaling constant for usage amplification. Default: 0.1
   */
  K_usage?: number;
  /**
   * Decay constant for time-based usage (e.g., 0.01 per day if delta_t is in days). Default: 0.01
   */
  lambda_decay?: number;
  /**
   * Optional: Minimum RawAmplifiedImportance across the entire system for normalization.
   */
  minRAISystem?: number;
  /**
   * Optional: Maximum RawAmplifiedImportance across the entire system for normalization.
   */
  maxRAISystem?: number;
  /**
   * Callback to update the parent's state when usage is simulated.
   */
  onSimulateUsage: (elementId: string) => void;
  /**
   * Callback to open the rename proposal dialog for this element.
   */
  onProposeRename: (elementId: string) => void;
  /**
   * Active rename proposals relevant to this element (filtered by status === 'pending').
   */
  activeRenameProposals: RenameProposal[];
  /**
   * Callback to vote on a specific proposal.
   */
  onVoteOnProposal: (proposalId: string) => void;
}

/**
 * Utility functions for metric calculation, based on the elaborated mathematical formulations.
 */
export const MetricUtils = { // Export MetricUtils for use in Dashboard
  calculateEffectiveUsageScore: (
    usageEvents: UsageEvent[],
    currentTime: Date,
    lambda_decay: number
  ): number => {
    let effectiveScore = 0.0;
    for (const event of usageEvents) {
      const delta_t_ms = currentTime.getTime() - event.timestamp.getTime();
      const delta_t_days = delta_t_ms / (1000 * 60 * 60 * 24); // time in days
      const decayFactor = Math.exp(-lambda_decay * delta_t_days);
      effectiveScore += event.contributionWeight * decayFactor;
    }
    return effectiveScore;
  },

  calculateRawAmplifiedImportance: (
    baseConfidence: number,
    effectiveUsageScore: number,
    K_usage: number
  ): number => {
    // Ensure that if effective_usage is very small (near zero), ln(effective_usage + 1) behaves gracefully
    // and base_confidence remains the primary driver.
    return baseConfidence + (K_usage * Math.log(effectiveUsageScore + 1));
  },

  normalizeImportance: (
    rawAmplifiedImportance: number,
    minRAI: number,
    maxRAI: number
  ): number => {
    if (maxRAI <= minRAI) {
      // If min/max are equal (only one element, or all have same RAI), handle gracefully
      // For single element: normalize based on a conceptual 0-2 range.
      return (rawAmplifiedImportance - 0.0) / (2.0 - 0.0);
    }
    return (rawAmplifiedImportance - minRAI) / (maxRAI - minRAI);
  }
};

/**
 * MetricDisplayCard component:
 * Displays dynamic importance metrics for an element based on usage,
 * time decay, and base confidence, as per the "Velocity-Weighted Confidence" model.
 */
export default function MetricDisplayCard({
  element,
  K_usage = 0.1,
  lambda_decay = 0.01,
  minRAISystem,
  maxRAISystem,
  onSimulateUsage,
  onProposeRename,
  activeRenameProposals,
  onVoteOnProposal,
}: MetricDisplayCardProps) {
  const { id, baseConfidence, usageEvents } = element;

  const [effectiveUsageScore, setEffectiveUsageScore] = useState<number>(0);
  const [rawAmplifiedImportance, setRawAmplifiedImportance] = useState<number>(baseConfidence);
  const [normalizedImportance, setNormalizedImportance] = useState<number>(baseConfidence);

  const updateMetrics = useCallback(() => {
    const currentTime = new Date();
    const eus = MetricUtils.calculateEffectiveUsageScore(usageEvents, currentTime, lambda_decay);
    setEffectiveUsageScore(eus);

    const rai = MetricUtils.calculateRawAmplifiedImportance(baseConfidence, eus, K_usage);
    setRawAmplifiedImportance(rai);

    // Use system-wide min/max if provided, otherwise fallback to local assumptions for visualization
    const minRAIForNormalization = minRAISystem !== undefined ? minRAISystem : baseConfidence;
    const maxRAIForNormalization = maxRAISystem !== undefined ? maxRAISystem : 2.0; // Assuming 2.0 as a generous max for local display

    let ni = MetricUtils.normalizeImportance(rai, minRAIForNormalization, maxRAIForNormalization);

    // If minRAIForNormalization and maxRAIForNormalization are equal, and we are not provided system min/max
    // (i.e., this card is likely standalone or the only element), set normalized importance to base confidence.
    if (minRAISystem === undefined && minRAIForNormalization === maxRAIForNormalization) {
      ni = baseConfidence;
    }

    setNormalizedImportance(Math.max(0, Math.min(1, ni))); // Ensure it's clamped between 0 and 1
  }, [baseConfidence, usageEvents, K_usage, lambda_decay, minRAISystem, maxRAISystem]);

  useEffect(() => {
    updateMetrics();
    // Refresh metrics periodically to reflect time decay, e.g., every hour
    const interval = setInterval(updateMetrics, 60 * 60 * 1000); // Every hour
    return () => clearInterval(interval);
  }, [updateMetrics]);

  const rounded = (value: number) => parseFloat(value.toFixed(3));

  return (
    <Card className="w-full max-w-sm shadow-lg bg-card text-card-foreground">
      <CardHeader className="pb-3">
        <CardTitle className="text-xl font-bold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-500" />
            Metric: {id}
          </div>
          <Button variant="outline" size="sm" onClick={() => onProposeRename(id)} className="text-xs h-6">
            <Edit className="h-3 w-3 mr-1" /> Rename
          </Button>
        </CardTitle>
        <CardDescription>Dynamic importance metrics.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1 text-muted-foreground">
            <Info className="h-4 w-4" /> Base Confidence:
          </span>
          <Badge variant="outline" className="font-mono text-xs">{rounded(baseConfidence)}</Badge>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-1 text-muted-foreground">
            <Clock className="h-4 w-4" /> Effective Usage Score:
          </span>
          <Badge variant="secondary" className="font-mono text-xs">{rounded(effectiveUsageScore)}</Badge>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <TrendingUp className="h-4 w-4" /> Raw Amplified Importance:
            </span>
            <Badge className="font-mono text-xs">{rounded(rawAmplifiedImportance)}</Badge>
          </div>
          {/* Progress bar max value for RAI is illustrative; in reality, it's relative. */}
          <Progress value={Math.min(100, (rawAmplifiedImportance / (maxRAISystem !== undefined ? maxRAISystem * 1.2 : 2.0)) * 100)} className="h-2" />
          <p className="text-xs text-muted-foreground text-right mt-1">
            (Relative within system, or capped at ~2.0)
          </p>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Gauge className="h-4 w-4" /> Normalized Importance:
            </span>
            <Badge variant="default" className="font-mono text-xs">{rounded(normalizedImportance)}</Badge>
          </div>
          <Progress value={normalizedImportance * 100} className="h-2 bg-green-200" indicatorClassName="bg-green-600" />
          <p className="text-xs text-muted-foreground text-right mt-1">
            (System-wide relative importance, 0.0-1.0)
          </p>
        </div>

        <Button onClick={() => onSimulateUsage(id)} className="w-full mt-4">
          Simulate Usage
        </Button>

        {activeRenameProposals.length > 0 && (
          <div className="border-t pt-4 mt-4 space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-1">
              <Edit className="h-4 w-4" /> Active Rename Proposals:
            </h4>
            {activeRenameProposals.map(proposal => (
              <div key={proposal.id} className="flex justify-between items-center bg-muted p-2 rounded-md">
                <div className="flex flex-col">
                  <p className="text-xs text-muted-foreground">
                    "From <span className="font-medium text-foreground">{proposal.oldName}</span> to <span className="font-medium text-blue-500">{proposal.newName}</span>"
                  </p>
                  <p className="text-xs italic text-gray-500">
                    Rationale: {proposal.rationale}
                  </p>
                </div>
                <Button size="sm" variant="ghost" onClick={() => onVoteOnProposal(proposal.id)} className="flex items-center gap-1">
                  <ThumbsUp className="h-4 w-4" /> {proposal.votes}
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
