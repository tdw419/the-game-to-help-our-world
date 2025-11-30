import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Hammer, Eye, BookOpen } from 'lucide-react';
import LLMOSBuilder from './LLMOSBuilder';
import LLMOSVisualizer from './LLMOSVisualizer';

/**
 * LLMOSDashboard Component
 * Main dashboard for exploring LLMOS - an operating system for LLMs built by LLMs.
 * Combines the builder (simulation) and visualizer (live demo) components.
 */
export default function LLMOSDashboard() {
  const [activeTab, setActiveTab] = useState<string>('builder');

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Hero Section */}
        <Card className="border-0 shadow-2xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 text-white overflow-hidden">
          <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
          <CardHeader className="relative z-10 pb-8">
            <CardTitle className="text-5xl font-black mb-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-200">
              LLMOS
            </CardTitle>
            <CardDescription className="text-2xl text-gray-100 font-light">
              An Operating System for Large Language Models
            </CardDescription>
            <p className="text-gray-200 mt-4 max-w-3xl text-lg">
              Explore a revolutionary OS designed to manage cognitive processes, semantic memory, and inter-agent
              communication—built entirely by LLMs using the Vector Universe.
            </p>
          </CardHeader>
        </Card>

        {/* Main Content Tabs */}
        <Card className="shadow-xl">
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3 h-14 mb-6">
                <TabsTrigger value="builder" className="text-base gap-2">
                  <Hammer className="h-5 w-5" />
                  Build Process
                </TabsTrigger>
                <TabsTrigger value="visualizer" className="text-base gap-2">
                  <Eye className="h-5 w-5" />
                  Live Demo
                </TabsTrigger>
                <TabsTrigger value="architecture" className="text-base gap-2">
                  <BookOpen className="h-5 w-5" />
                  Architecture
                </TabsTrigger>
              </TabsList>

              {/* Builder Tab */}
              <TabsContent value="builder" className="mt-0">
                <LLMOSBuilder />
              </TabsContent>

              {/* Visualizer Tab */}
              <TabsContent value="visualizer" className="mt-0">
                <LLMOSVisualizer />
              </TabsContent>

              {/* Architecture Tab */}
              <TabsContent value="architecture" className="mt-0">
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>What is LLMOS?</CardTitle>
                    </CardHeader>
                    <CardContent className="prose dark:prose-invert max-w-none">
                      <p>
                        <strong>LLMOS</strong> (Large Language Model Operating System) is a conceptual operating system
                        designed specifically for managing, orchestrating, and optimizing multiple LLM processes. Unlike
                        traditional operating systems that manage CPU processes and memory, LLMOS manages:
                      </p>
                      <ul>
                        <li>
                          <strong>Cognitive Processes</strong>: LLM inference tasks, reasoning chains, and thought
                          processes
                        </li>
                        <li>
                          <strong>Semantic Memory</strong>: Vector embeddings, knowledge graphs, and contextual state
                        </li>
                        <li>
                          <strong>Inter-Agent Communication</strong>: Message passing, shared attention, and
                          collaborative reasoning
                        </li>
                        <li>
                          <strong>Resource Scheduling</strong>: Token budgets, GPU allocation, and inference priority
                        </li>
                      </ul>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle>Core Components</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="border-l-4 border-l-purple-500 pl-4">
                            <h3 className="font-bold">Vector Kernel (VectorK)</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Process scheduler, memory manager, communication bus, and security engine operating in
                              vector space
                            </p>
                          </div>
                          <div className="border-l-4 border-l-blue-500 pl-4">
                            <h3 className="font-bold">Cognitive Services Layer</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Reasoning engine, knowledge graph manager, attention multiplexer, and embedding store
                            </p>
                          </div>
                          <div className="border-l-4 border-l-green-500 pl-4">
                            <h3 className="font-bold">Agent Process Layer</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              User agents, system agents, specialist agents, and meta-agents for orchestration
                            </p>
                          </div>
                          <div className="border-l-4 border-l-yellow-500 pl-4">
                            <h3 className="font-bold">System Interface</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Natural language shell (nlsh), Vector API, and monitoring dashboard
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle>Key Innovations</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div>
                            <h3 className="font-bold mb-1">Semantic Memory Hierarchy</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              L1/L2/L3 caches for active context, with semantic RAM and persistent vector storage
                            </p>
                          </div>
                          <div>
                            <h3 className="font-bold mb-1">Vector Message Protocol</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Inter-agent communication using semantic vectors for efficient message passing
                            </p>
                          </div>
                          <div>
                            <h3 className="font-bold mb-1">Token Scheduling</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Fair resource allocation with priority queuing and dynamic budget management
                            </p>
                          </div>
                          <div>
                            <h3 className="font-bold mb-1">Context Swapping</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Intelligent compression and swapping of conversation history based on semantic similarity
                            </p>
                          </div>
                          <div>
                            <h3 className="font-bold mb-1">VectorFS</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              File system with semantic navigation - cd to concepts, ls by similarity, grep by meaning
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>System Calls (Natural Language Syscalls)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Process Management</div>
                          <div>llm.spawn("Create code-writer agent")</div>
                          <div>llm.kill(pid)</div>
                          <div>llm.suspend(pid)</div>
                          <div>llm.resume(pid)</div>
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Memory Management</div>
                          <div>llm.malloc("User preferences")</div>
                          <div>llm.free(memoryId)</div>
                          <div>llm.share(memoryId, targetPid)</div>
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Communication</div>
                          <div>llm.send(pid, "Analyze this")</div>
                          <div>llm.receive()</div>
                          <div>llm.broadcast("System alert")</div>
                        </div>
                        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                          <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">Vector File System</div>
                          <div>llm.embed("Store knowledge")</div>
                          <div>llm.search("neural networks")</div>
                          <div>llm.index("/knowledge")</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Example Workflow: Multi-Agent Code Generation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-start gap-3">
                          <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            1
                          </div>
                          <div>
                            <p className="font-semibold">User Request</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              "Create a web server with authentication and logging"
                            </p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3">
                          <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            2
                          </div>
                          <div>
                            <p className="font-semibold">Kernel Response</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              Spawns 3 specialist agents: architect-agent, coder-agent, reviewer-agent
                            </p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3">
                          <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold flex-shrink-0">
                            3
                          </div>
                          <div>
                            <p className="font-semibold">Inter-Agent Communication</p>
                            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1 mt-1">
                              <div>architect → coder: "Use Express.js, JWT auth, Winston logging"</div>
                              <div>coder → reviewer: "Code complete, please review"</div>
                              <div>reviewer → coder: "Found 2 issues, sending patches"</div>
                              <div>coder → user: "Web server ready, deployed to /apps/webserver"</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Footer */}
        <Card className="bg-gradient-to-r from-gray-800 to-gray-900 text-white border-0">
          <CardContent className="pt-6 text-center">
            <p className="text-lg">
              <strong>LLMOS</strong> represents a paradigm shift in computing: instead of managing silicon processes,
              we manage cognitive processes. Instead of RAM and disk, we manage embeddings and context. Instead of
              threads and mutexes, we have agents and shared attention.
            </p>
            <p className="mt-4 text-gray-400 italic">Welcome to the future of semantic, self-organizing computing.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
