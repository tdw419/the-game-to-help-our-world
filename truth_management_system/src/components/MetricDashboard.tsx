import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PlusCircle, LayoutDashboard } from 'lucide-react';
import MetricDisplayCard, { MetricElement, UsageEvent, MetricUtils } from './MetricDisplayCard';

export default function MetricDashboard() {
  const [elements, setElements] = useState<MetricElement[]>([
    { id: 'User Intent Clarification', baseConfidence: 0.99, usageEvents: [] },
    { id: 'Dynamic Metric Evolution', baseConfidence: 0.85, usageEvents: [] },
    { id: 'Collaborative Governance', baseConfidence: 0.70, usageEvents: [] },
  ]);

  const [minRAISystem, setMinRAISystem] = useState<number>(0);
  const [maxRAISystem, setMaxRAISystem] = useState<number>(0);

  const [newElementId, setNewElementId] = useState<string>('');
  const [newElementBaseConfidence, setNewElementBaseConfidence] = useState<string>('0.5');

  // Constants for all cards - could be made configurable in the dashboard later
  const K_USAGE = 0.1;
  const LAMBDA_DECAY = 0.01;

  // Calculate system-wide min/max Raw Amplified Importance
  const calculateSystemRAIRange = useCallback(() => {
    const currentRAIs: number[] = [];
    const currentTime = new Date();

    elements.forEach(element => {
      const effectiveUsage = MetricUtils.calculateEffectiveUsageScore(element.usageEvents, currentTime, LAMBDA_DECAY);
      const rai = MetricUtils.calculateRawAmplifiedImportance(element.baseConfidence, effectiveUsage, K_USAGE);
      currentRAIs.push(rai);
    });

    if (currentRAIs.length > 0) {
      setMinRAISystem(Math.min(...currentRAIs));
      setMaxRAISystem(Math.max(...currentRAIs));
    } else {
      setMinRAISystem(0);
      setMaxRAISystem(0);
    }
  }, [elements, K_USAGE, LAMBDA_DECAY]);

  useEffect(() => {
    calculateSystemRAIRange();
    // Re-calculate periodically to account for time decay across all elements
    const interval = setInterval(calculateSystemRAIRange, 60 * 60 * 1000); // Every hour
    return () => clearInterval(interval);
  }, [calculateSystemRAIRange]);

  const handleSimulateUsage = useCallback((elementId: string) => {
    setElements(prevElements =>
      prevElements.map(el =>
        el.id === elementId
          ? { ...el, usageEvents: [...el.usageEvents, { timestamp: new Date(), contributionWeight: 1.0 }] }
          : el
      )
    );
  }, []);

  const handleAddElement = () => {
    if (newElementId && newElementBaseConfidence) {
      const baseConf = parseFloat(newElementBaseConfidence);
      if (!isNaN(baseConf) && baseConf >= 0 && baseConf <= 1) {
        if (elements.some(el => el.id === newElementId)) {
          alert('An element with this ID already exists.');
          return;
        }
        setElements(prevElements => [
          ...prevElements,
          { id: newElementId, baseConfidence: baseConf, usageEvents: [] },
        ]);
        setNewElementId('');
        setNewElementBaseConfidence('0.5');
      } else {
        alert('Base Confidence must be a number between 0 and 1.');
      }
    } else {
      alert('Please enter both an element ID and a base confidence.');
    }
  };

  return (
    <Card className="w-full p-4 mx-auto shadow-lg bg-card text-card-foreground">
      <CardHeader className="pb-4 border-b">
        <CardTitle className="text-3xl font-bold flex items-center gap-2">
          <LayoutDashboard className="h-7 w-7 text-blue-500" />
          PXOS Metric Dashboard
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {elements.map((element) => (
            <MetricDisplayCard
              key={element.id}
              element={element}
              K_usage={K_USAGE}
              lambda_decay={LAMBDA_DECAY}
              minRAISystem={minRAISystem}
              maxRAISystem={maxRAISystem}
              onSimulateUsage={handleSimulateUsage}
            />
          ))}
        </div>

        <div className="border-t pt-6 mt-6">
          <h3 className="text-xl font-semibold flex items-center gap-2 mb-4">
            <PlusCircle className="h-5 w-5 text-green-500" /> Add New Metric Element
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
            <div className="col-span-1 md:col-span-1">
              <Label htmlFor="newElementId">Element ID</Label>
              <Input
                id="newElementId"
                placeholder="e.g., New Concept A"
                value={newElementId}
                onChange={(e) => setNewElementId(e.target.value)}
              />
            </div>
            <div className="col-span-1 md:col-span-1">
              <Label htmlFor="newElementBaseConfidence">Base Confidence (0-1)</Label>
              <Input
                id="newElementBaseConfidence"
                type="number"
                step="0.01"
                min="0"
                max="1"
                placeholder="e.g., 0.75"
                value={newElementBaseConfidence}
                onChange={(e) => setNewElementBaseConfidence(e.target.value)}
              />
            </div>
            <div className="col-span-1 md:col-span-1">
              <Button onClick={handleAddElement} className="w-full">
                Add Element
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
