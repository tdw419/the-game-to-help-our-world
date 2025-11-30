import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Cpu,
  Brain,
  Network,
  Database,
  Activity,
  Zap,
  Users,
  Shield,
  Terminal,
  PlayCircle,
  PauseCircle,
  Sparkles,
} from 'lucide-react';

// Type Definitions
interface LLMProcess {
  pid: string;
  name: string;
  state: 'RUNNING' | 'THINKING' | 'BLOCKED' | 'SUSPENDED' | 'TERMINATED';
  priority: number;
  tokenBudget: {
    allocated: number;
    consumed: number;
    remaining: number;
  };
  contextWindow: {
    maxLength: number;
    currentLength: number;
  };
  type: 'USER' | 'SYSTEM' | 'SPECIALIST' | 'META';
  createdAt: number;
  cpuTime: number;
}

interface VectorMessage {
  id: string;
  from: string;
  to: string;
  messageType: 'REQUEST' | 'RESPONSE' | 'NOTIFICATION' | 'BROADCAST';
  content: string;
  timestamp: number;
}

interface SystemMetrics {
  tokenThroughput: number;
  inferenceLatency: number;
  contextSwitchRate: number;
  memoryUtilization: number;
  activeAgents: number;
}

/**
 * LLMOSVisualizer Component
 * Visualizes an operating system for LLMs, showing process management,
 * resource allocation, inter-agent communication, and system metrics.
 */
export default function LLMOSVisualizer() {
  const [isRunning, setIsRunning] = useState(false);
  const [processes, setProcesses] = useState<LLMProcess[]>([]);
  const [messages, setMessages] = useState<VectorMessage[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    tokenThroughput: 0,
    inferenceLatency: 0,
    contextSwitchRate: 0,
    memoryUtilization: 0,
    activeAgents: 0,
  });

  // Initialize system with sample processes
  useEffect(() => {
    const initialProcesses: LLMProcess[] = [
      {
        pid: 'proc_001',
        name: 'architect-agent',
        state: 'RUNNING',
        priority: 5,
        tokenBudget: { allocated: 1000, consumed: 450, remaining: 550 },
        contextWindow: { maxLength: 4096, currentLength: 1850 },
        type: 'SPECIALIST',
        createdAt: Date.now() - 5000,
        cpuTime: 2.5,
      },
      {
        pid: 'proc_002',
        name: 'coder-agent',
        state: 'THINKING',
        priority: 10,
        tokenBudget: { allocated: 5000, consumed: 2200, remaining: 2800 },
        contextWindow: { maxLength: 8192, currentLength: 3100 },
        type: 'SPECIALIST',
        createdAt: Date.now() - 8000,
        cpuTime: 4.2,
      },
      {
        pid: 'proc_003',
        name: 'reviewer-agent',
        state: 'BLOCKED',
        priority: 10,
        tokenBudget: { allocated: 2000, consumed: 800, remaining: 1200 },
        contextWindow: { maxLength: 4096, currentLength: 950 },
        type: 'SPECIALIST',
        createdAt: Date.now() - 3000,
        cpuTime: 1.8,
      },
      {
        pid: 'sys_001',
        name: 'kernel-monitor',
        state: 'RUNNING',
        priority: 0,
        tokenBudget: { allocated: 500, consumed: 120, remaining: 380 },
        contextWindow: { maxLength: 2048, currentLength: 450 },
        type: 'SYSTEM',
        createdAt: Date.now() - 15000,
        cpuTime: 0.5,
      },
      {
        pid: 'meta_001',
        name: 'orchestrator-agent',
        state: 'RUNNING',
        priority: 3,
        tokenBudget: { allocated: 3000, consumed: 1100, remaining: 1900 },
        contextWindow: { maxLength: 16384, currentLength: 5200 },
        type: 'META',
        createdAt: Date.now() - 12000,
        cpuTime: 3.8,
      },
    ];
    setProcesses(initialProcesses);

    const initialMessages: VectorMessage[] = [
      {
        id: 'msg_001',
        from: 'meta_001',
        to: 'proc_001',
        messageType: 'REQUEST',
        content: 'Design architecture for web server project',
        timestamp: Date.now() - 4000,
      },
      {
        id: 'msg_002',
        from: 'proc_001',
        to: 'proc_002',
        messageType: 'REQUEST',
        content: 'Implement Express.js server with JWT auth',
        timestamp: Date.now() - 2000,
      },
    ];
    setMessages(initialMessages);
  }, []);

  // Simulate system activity
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      // Update metrics
      setMetrics((prev) => ({
        tokenThroughput: Math.floor(Math.random() * 1000) + 500,
        inferenceLatency: Math.random() * 200 + 50,
        contextSwitchRate: Math.random() * 10 + 2,
        memoryUtilization: Math.random() * 30 + 60,
        activeAgents: processes.filter((p) => p.state === 'RUNNING').length,
      }));

      // Randomly update process states
      setProcesses((prev) =>
        prev.map((proc) => {
          const random = Math.random();
          if (random > 0.8 && proc.state !== 'TERMINATED') {
            const states: LLMProcess['state'][] = ['RUNNING', 'THINKING', 'BLOCKED'];
            return { ...proc, state: states[Math.floor(Math.random() * states.length)] };
          }
          return proc;
        })
      );

      // Occasionally add a new message
      if (Math.random() > 0.7 && processes.length > 1) {
        const from = processes[Math.floor(Math.random() * processes.length)];
        const to = processes[Math.floor(Math.random() * processes.length)];
        if (from.pid !== to.pid) {
          const newMessage: VectorMessage = {
            id: `msg_${Date.now()}`,
            from: from.pid,
            to: to.pid,
            messageType: 'REQUEST',
            content: `Inter-agent communication from ${from.name} to ${to.name}`,
            timestamp: Date.now(),
          };
          setMessages((prev) => [newMessage, ...prev].slice(0, 10));
        }
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning, processes]);

  const getStateColor = (state: LLMProcess['state']) => {
    switch (state) {
      case 'RUNNING':
        return 'bg-green-500';
      case 'THINKING':
        return 'bg-blue-500';
      case 'BLOCKED':
        return 'bg-yellow-500';
      case 'SUSPENDED':
        return 'bg-gray-500';
      case 'TERMINATED':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  const getTypeIcon = (type: LLMProcess['type']) => {
    switch (type) {
      case 'USER':
        return <Users className="h-4 w-4" />;
      case 'SYSTEM':
        return <Shield className="h-4 w-4" />;
      case 'SPECIALIST':
        return <Brain className="h-4 w-4" />;
      case 'META':
        return <Sparkles className="h-4 w-4" />;
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 space-y-4">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-900 to-blue-900 text-white">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-3xl font-bold flex items-center gap-3">
                <Terminal className="h-8 w-8" />
                LLMOS: Operating System for LLMs
              </CardTitle>
              <CardDescription className="text-gray-200">
                A vector-native OS managing cognitive processes, semantic memory, and inter-agent communication
              </CardDescription>
            </div>
            <Button
              onClick={() => setIsRunning(!isRunning)}
              variant={isRunning ? 'destructive' : 'default'}
              size="lg"
              className="gap-2"
            >
              {isRunning ? (
                <>
                  <PauseCircle className="h-5 w-5" /> Pause
                </>
              ) : (
                <>
                  <PlayCircle className="h-5 w-5" /> Start
                </>
              )}
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Token/sec</p>
                <p className="text-2xl font-bold">{metrics.tokenThroughput}</p>
              </div>
              <Zap className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Latency</p>
                <p className="text-2xl font-bold">{metrics.inferenceLatency.toFixed(0)}ms</p>
              </div>
              <Activity className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Switches/sec</p>
                <p className="text-2xl font-bold">{metrics.contextSwitchRate.toFixed(1)}</p>
              </div>
              <Cpu className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Memory</p>
                <p className="text-2xl font-bold">{metrics.memoryUtilization.toFixed(0)}%</p>
              </div>
              <Database className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Active Agents</p>
                <p className="text-2xl font-bold">{metrics.activeAgents}</p>
              </div>
              <Brain className="h-8 w-8 text-pink-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="processes" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="processes">Process Manager</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
        </TabsList>

        {/* Process Manager Tab */}
        <TabsContent value="processes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                LLM Processes
              </CardTitle>
              <CardDescription>Active cognitive processes and their resource allocation</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {processes.map((proc) => (
                  <Card key={proc.pid} className="border-l-4 border-l-purple-500">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`w-3 h-3 rounded-full ${getStateColor(proc.state)}`} />
                          {getTypeIcon(proc.type)}
                          <div>
                            <p className="font-bold">{proc.name}</p>
                            <p className="text-xs text-gray-500">PID: {proc.pid}</p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline">{proc.state}</Badge>
                          <Badge variant="secondary">Priority: {proc.priority}</Badge>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Token Budget</span>
                            <span>
                              {proc.tokenBudget.consumed}/{proc.tokenBudget.allocated}
                            </span>
                          </div>
                          <Progress
                            value={(proc.tokenBudget.consumed / proc.tokenBudget.allocated) * 100}
                            className="h-2"
                          />
                        </div>

                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span>Context Window</span>
                            <span>
                              {proc.contextWindow.currentLength}/{proc.contextWindow.maxLength}
                            </span>
                          </div>
                          <Progress
                            value={(proc.contextWindow.currentLength / proc.contextWindow.maxLength) * 100}
                            className="h-2"
                          />
                        </div>

                        <div className="flex justify-between text-xs text-gray-500 pt-2">
                          <span>CPU Time: {proc.cpuTime.toFixed(2)}s</span>
                          <span>Uptime: {Math.floor((Date.now() - proc.createdAt) / 1000)}s</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Communication Tab */}
        <TabsContent value="communication" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5" />
                Inter-Agent Communication
              </CardTitle>
              <CardDescription>Vector Message Protocol (VMP) activity</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {messages.map((msg) => {
                  const fromProc = processes.find((p) => p.pid === msg.from);
                  const toProc = processes.find((p) => p.pid === msg.to);
                  return (
                    <div key={msg.id} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <Network className="h-5 w-5 mt-1 text-blue-500" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline">{msg.messageType}</Badge>
                          <span className="text-sm font-medium">{fromProc?.name || msg.from}</span>
                          <span className="text-gray-400">→</span>
                          <span className="text-sm font-medium">{toProc?.name || msg.to}</span>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{msg.content}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {messages.length === 0 && (
                  <p className="text-center text-gray-500 py-8">No messages yet. Start the system to see activity.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Memory Tab */}
        <TabsContent value="memory" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Semantic Memory Manager
              </CardTitle>
              <CardDescription>Vector embeddings, context pages, and memory hierarchy</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-500">L1 Cache (Active Context)</p>
                      <Progress value={85} className="mt-2" />
                      <p className="text-xs text-gray-400 mt-1">3.2 GB / 4.0 GB</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-500">L2 Cache (Recent)</p>
                      <Progress value={62} className="mt-2" />
                      <p className="text-xs text-gray-400 mt-1">12.4 GB / 20.0 GB</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-500">Semantic RAM</p>
                      <Progress value={45} className="mt-2" />
                      <p className="text-xs text-gray-400 mt-1">90 GB / 200 GB</p>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-3">Context Pages</h3>
                    <div className="grid grid-cols-4 gap-2">
                      {Array.from({ length: 16 }).map((_, i) => (
                        <div
                          key={i}
                          className={`h-12 rounded ${
                            i < 6
                              ? 'bg-green-500'
                              : i < 10
                              ? 'bg-yellow-500'
                              : i < 14
                              ? 'bg-blue-500'
                              : 'bg-gray-300'
                          }`}
                          title={
                            i < 6
                              ? 'Active'
                              : i < 10
                              ? 'Cached'
                              : i < 14
                              ? 'Swapped'
                              : 'Free'
                          }
                        />
                      ))}
                    </div>
                    <div className="flex gap-4 mt-3 text-xs">
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-green-500 rounded" />
                        <span>Active</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-yellow-500 rounded" />
                        <span>Cached</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-blue-500 rounded" />
                        <span>Swapped</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <div className="w-3 h-3 bg-gray-300 rounded" />
                        <span>Free</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Architecture Tab */}
        <TabsContent value="architecture" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>LLMOS System Architecture</CardTitle>
              <CardDescription>Four-layer architecture for cognitive process management</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Card className="bg-purple-50 dark:bg-purple-950 border-purple-200">
                  <CardContent className="pt-4">
                    <h3 className="font-bold mb-2">Layer 4: System Interface</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Natural Language Shell (nlsh), Vector API, Agent Control Protocol
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200">
                  <CardContent className="pt-4">
                    <h3 className="font-bold mb-2">Layer 3: Agent Process Layer</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      User-space LLM processes, System Agents, Specialist Agents, Meta-Agents
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-green-50 dark:bg-green-950 border-green-200">
                  <CardContent className="pt-4">
                    <h3 className="font-bold mb-2">Layer 2: Cognitive Services</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Reasoning Engine, Knowledge Graph, Attention Multiplexer, Embedding Store
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-red-50 dark:bg-red-950 border-red-200">
                  <CardContent className="pt-4">
                    <h3 className="font-bold mb-2">Layer 1: Vector Kernel (VectorK)</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Process Scheduler, Memory Manager, Communication Bus, Resource Allocator, Security Engine
                    </p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
