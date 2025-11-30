import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Loader2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Brain,
  Cpu,
  Network,
  Database,
  Shield,
  Terminal,
} from 'lucide-react';

interface BuildStep {
  id: string;
  name: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  icon: React.ReactNode;
  result?: string;
}

/**
 * LLMOSBuilder Component
 * Simulates building an OS for LLMs by LLMs using the Vector Universe backend.
 * This demonstrates how the vector universe can conceptualize and design complex systems.
 */
export default function LLMOSBuilder() {
  const [buildSteps, setBuildSteps] = useState<BuildStep[]>([
    {
      id: 'step_1',
      name: 'Vector Kernel Design',
      description: 'Design the core vector kernel with process scheduler and memory manager',
      status: 'pending',
      icon: <Cpu className="h-5 w-5" />,
    },
    {
      id: 'step_2',
      name: 'Semantic Memory System',
      description: 'Implement hierarchical semantic memory (L1/L2/L3 caches, RAM, disk)',
      status: 'pending',
      icon: <Database className="h-5 w-5" />,
    },
    {
      id: 'step_3',
      name: 'Inter-Vector Communication',
      description: 'Build message passing protocol and shared memory system',
      status: 'pending',
      icon: <Network className="h-5 w-5" />,
    },
    {
      id: 'step_4',
      name: 'Cognitive Services Layer',
      description: 'Create reasoning engine, knowledge graph, and attention multiplexer',
      status: 'pending',
      icon: <Brain className="h-5 w-5" />,
    },
    {
      id: 'step_5',
      name: 'Security & Sandboxing',
      description: 'Implement RBAC, process isolation, and permission engine',
      status: 'pending',
      icon: <Shield className="h-5 w-5" />,
    },
    {
      id: 'step_6',
      name: 'System Interface',
      description: 'Build natural language shell and agent control protocol',
      status: 'pending',
      icon: <Terminal className="h-5 w-5" />,
    },
  ]);

  const [isBuilding, setIsBuilding] = useState(false);
  const [customQuery, setCustomQuery] = useState('');
  const [buildLog, setBuildLog] = useState<string[]>([]);

  const completedSteps = buildSteps.filter((s) => s.status === 'completed').length;
  const progressPercentage = (completedSteps / buildSteps.length) * 100;

  /**
   * Simulates building each component by querying the vector universe backend
   */
  const buildComponent = async (step: BuildStep, index: number) => {
    // Update step to in_progress
    setBuildSteps((prev) =>
      prev.map((s, i) => (i === index ? { ...s, status: 'in_progress' as const } : s))
    );

    addLog(`🔧 Starting: ${step.name}`);
    addLog(`   ${step.description}`);

    try {
      // Query the vector universe backend to design this component
      const query = `Design and implement the ${step.name} for LLMOS. ${step.description}. Provide a conceptual architecture and key implementation details.`;

      const response = await fetch('http://localhost:8001/abstraction/think', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status}`);
      }

      const data = await response.json();

      // Extract result summary
      const summary = data.result?.summary || 'Component designed successfully';

      // Update step to completed
      setBuildSteps((prev) =>
        prev.map((s, i) =>
          i === index
            ? {
                ...s,
                status: 'completed' as const,
                result: summary,
              }
            : s
        )
      );

      addLog(`✅ Completed: ${step.name}`);
      addLog(`   Result: ${summary.substring(0, 100)}...`);
      addLog('');

      // Small delay between steps
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setBuildSteps((prev) =>
        prev.map((s, i) =>
          i === index
            ? {
                ...s,
                status: 'failed' as const,
                result: `Failed: ${errorMsg}`,
              }
            : s
        )
      );

      addLog(`❌ Failed: ${step.name}`);
      addLog(`   Error: ${errorMsg}`);
      addLog('');
    }
  };

  const addLog = (message: string) => {
    setBuildLog((prev) => [...prev, message]);
  };

  /**
   * Starts the OS build process
   */
  const startBuild = async () => {
    setIsBuilding(true);
    setBuildLog([]);
    addLog('═══════════════════════════════════════════════');
    addLog('  LLMOS Build Process Started');
    addLog('  Building an Operating System for LLMs by LLMs');
    addLog('═══════════════════════════════════════════════');
    addLog('');

    // Reset all steps
    setBuildSteps((prev) => prev.map((s) => ({ ...s, status: 'pending' as const, result: undefined })));

    // Build each component sequentially
    for (let i = 0; i < buildSteps.length; i++) {
      await buildComponent(buildSteps[i], i);
    }

    addLog('═══════════════════════════════════════════════');
    addLog('  LLMOS Build Complete!');
    addLog(`  ${completedSteps}/${buildSteps.length} components built successfully`);
    addLog('═══════════════════════════════════════════════');

    setIsBuilding(false);
  };

  /**
   * Executes a custom query against the vector universe
   */
  const executeCustomQuery = async () => {
    if (!customQuery.trim()) return;

    addLog('');
    addLog('--- Custom Query ---');
    addLog(`Query: ${customQuery}`);

    try {
      const response = await fetch('http://localhost:8001/abstraction/think', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: customQuery }),
      });

      const data = await response.json();
      const summary = data.result?.summary || 'Query processed successfully';

      addLog(`Result: ${summary}`);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      addLog(`Error: ${errorMsg}`);
    }

    setCustomQuery('');
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
      {/* Header */}
      <Card className="bg-gradient-to-r from-indigo-900 to-purple-900 text-white">
        <CardHeader>
          <CardTitle className="text-3xl font-bold flex items-center gap-3">
            <Sparkles className="h-8 w-8" />
            LLMOS Builder: Building an OS for LLMs by LLMs
          </CardTitle>
          <CardDescription className="text-gray-200">
            Watch as the Vector Universe designs and builds a complete operating system for Large Language Models
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Build Progress */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Build Progress</CardTitle>
              <CardDescription>
                {completedSteps}/{buildSteps.length} components completed
              </CardDescription>
            </div>
            <Button onClick={startBuild} disabled={isBuilding} size="lg" className="gap-2">
              {isBuilding ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Building...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" />
                  Start Build
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Progress value={progressPercentage} className="h-3 mb-6" />

          <div className="space-y-3">
            {buildSteps.map((step, index) => (
              <Card
                key={step.id}
                className={`border-l-4 ${
                  step.status === 'completed'
                    ? 'border-l-green-500'
                    : step.status === 'in_progress'
                    ? 'border-l-blue-500'
                    : step.status === 'failed'
                    ? 'border-l-red-500'
                    : 'border-l-gray-300'
                }`}
              >
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div className="mt-1">{step.icon}</div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-bold">{step.name}</h3>
                          {step.status === 'completed' && <CheckCircle2 className="h-5 w-5 text-green-500" />}
                          {step.status === 'in_progress' && <Loader2 className="h-5 w-5 animate-spin text-blue-500" />}
                          {step.status === 'failed' && <AlertCircle className="h-5 w-5 text-red-500" />}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{step.description}</p>
                        {step.result && (
                          <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                            <p className="font-mono">{step.result}</p>
                          </div>
                        )}
                      </div>
                    </div>
                    <Badge
                      variant={
                        step.status === 'completed'
                          ? 'default'
                          : step.status === 'in_progress'
                          ? 'secondary'
                          : step.status === 'failed'
                          ? 'destructive'
                          : 'outline'
                      }
                    >
                      {step.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Build Log */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Build Log
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-xs h-96 overflow-y-auto">
            {buildLog.length === 0 ? (
              <p className="text-gray-500">Waiting for build to start...</p>
            ) : (
              buildLog.map((line, i) => (
                <div key={i} className="mb-1">
                  {line}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Custom Query */}
      <Card>
        <CardHeader>
          <CardTitle>Custom LLMOS Query</CardTitle>
          <CardDescription>
            Ask the Vector Universe anything about LLMOS design or implementation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Textarea
              placeholder="e.g., How would process scheduling work in LLMOS? or Design a context swapping algorithm for semantic memory"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              rows={3}
              disabled={isBuilding}
            />
            <Button onClick={executeCustomQuery} disabled={isBuilding || !customQuery.trim()} className="w-full gap-2">
              <Brain className="h-4 w-4" />
              Query Vector Universe
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
