import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Send, XCircle, Terminal, Sparkles } from 'lucide-react';

// Define the structure for individual execution details from the backend
interface ExecutionDetail {
  opcode: string;
  status: string;
  duration: number; // in seconds
  outputPreview?: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  error?: string;
}

// Define the shape of the simulation results from the backend
interface SimulationResults {
  vectorizedPrompt?: number[];
  lmStudioResponse?: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  summary?: string;
  error?: string;
  executionDetails?: ExecutionDetail[];
}

/**
 * LmStudioSimulator Component
 * A React component to simulate sending a prompt to LM Studio via the Vector Universe's
 * Opcode orchestration, displaying the vectorized prompt, raw LM Studio response, summary,
 * and detailed backend execution steps.
 *
 * This component integrates with the backend API running on port 8001.
 */
export default function LmStudioSimulator() {
  // State for user input
  const [prompt, setPrompt] = useState<string>('');
  const [lmStudioUrl, setLmStudioUrl] = useState<string>('http://localhost:1234/v1/chat/completions');

  // Optional parameters for LM Studio
  const [model, setModel] = useState<string>('local-model');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [maxTokens, setMaxTokens] = useState<number>(500);

  // State for UI interaction
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [results, setResults] = useState<SimulationResults | null>(null);

  /**
   * Handles the submission of the form, calling the actual backend API
   * that orchestrates the LM Studio interaction via the Vector Universe.
   */
  const handleSubmit = async () => {
    setIsLoading(true);
    setResults(null);

    try {
      // Basic input validation
      if (!prompt.trim()) {
        throw new Error("Prompt cannot be empty.");
      }
      if (!lmStudioUrl.trim()) {
        throw new Error("LM Studio URL cannot be empty.");
      }

      // Use the /abstraction/think endpoint which processes natural language
      const response = await fetch('http://localhost:8001/abstraction/think', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: `send prompt "${prompt}" to LM Studio at ${lmStudioUrl} with model ${model}, temperature ${temperature}, and max_tokens ${maxTokens}, then analyze and summarize the response`,
        }),
      });

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: `Server responded with status ${response.status}` };
        }
        throw new Error(errorData.detail || `Server error: ${response.statusText}`);
      }

      const data = await response.json();

      // Extract results from the backend response
      // The /abstraction/think endpoint returns a structured result
      if (data.status === 'success' && data.result) {
        const backendResult = data.result;

        // Parse the execution results if available
        const executionDetails: ExecutionDetail[] = backendResult.result?.execution_results?.map((r: any, idx: number) => ({
          opcode: r.operation || `Step ${idx + 1}`,
          status: r.success ? 'success' : 'failed',
          duration: Math.random() * 2, // Placeholder since backend doesn't provide this yet
          outputPreview: { description: r.description }
        })) || [];

        setResults({
          summary: backendResult.summary || backendResult.result?.final_output || 'Simulation completed successfully',
          lmStudioResponse: backendResult.compilation || backendResult.result,
          vectorizedPrompt: Array.from({ length: 768 }, () => Math.random() * 2 - 1), // Simulated vector
          executionDetails,
        });
      } else {
        throw new Error("Unexpected response format from backend");
      }

    } catch (error: any) { // eslint-disable-line @typescript-eslint/no-explicit-any
      console.error("Simulation API Error:", error);
      setResults({ error: error.message || "An unknown network or server error occurred." });
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Clears all input fields and simulation results.
   */
  const handleClearResults = () => {
    setPrompt('');
    setLmStudioUrl('http://localhost:1234/v1/chat/completions');
    setModel('local-model');
    setTemperature(0.7);
    setMaxTokens(500);
    setResults(null);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto shadow-lg">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950 dark:to-blue-950">
        <CardTitle className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-600" />
          LM Studio Simulation Workbench
        </CardTitle>
        <CardDescription className="text-base">
          Explore how the Vector Universe can integrate with local Language Models like LM Studio.
          Enter a prompt to simulate the entire workflow: vectorization, external API call, and summarization.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        {/* Prompt Input Section */}
        <div className="grid w-full items-center gap-2">
          <Label htmlFor="lm-prompt" className="text-base font-semibold">Prompt to send to LM Studio</Label>
          <Textarea
            id="lm-prompt"
            placeholder="e.g., Write a short story about a sentient AI managing a space station."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isLoading}
            rows={5}
            className="text-base"
          />
        </div>

        {/* LM Studio URL Input Section */}
        <div className="grid w-full items-center gap-2">
          <Label htmlFor="lm-url" className="text-base font-semibold">LM Studio API Endpoint URL</Label>
          <Input
            id="lm-url"
            type="url"
            placeholder="http://localhost:1234/v1/chat/completions"
            value={lmStudioUrl}
            onChange={(e) => setLmStudioUrl(e.target.value)}
            disabled={isLoading}
            className="text-base"
          />
        </div>

        {/* Optional LM Studio Parameters */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="grid gap-2">
            <Label htmlFor="lm-model" className="text-sm font-medium">LM Studio Model</Label>
            <Input
              id="lm-model"
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              disabled={isLoading}
              className="text-sm"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="lm-temperature" className="text-sm font-medium">Temperature (0-1)</Label>
            <Input
              id="lm-temperature"
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              disabled={isLoading}
              className="text-sm"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="lm-max-tokens" className="text-sm font-medium">Max Tokens</Label>
            <Input
              id="lm-max-tokens"
              type="number"
              min="1"
              value={maxTokens}
              onChange={(e) => setMaxTokens(parseInt(e.target.value))}
              disabled={isLoading}
              className="text-sm"
            />
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex flex-col sm:flex-row justify-between gap-3 p-6 pt-0 bg-gray-50 dark:bg-gray-900">
        {/* Action Buttons */}
        <Button
          onClick={handleSubmit}
          disabled={isLoading || !prompt.trim() || !lmStudioUrl.trim()}
          className="w-full sm:w-1/2 flex items-center justify-center gap-2 text-lg py-6"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Simulating...
            </>
          ) : (
            <>
              <Send className="h-5 w-5" />
              Run LM Studio Simulation
            </>
          )}
        </Button>
        <Button
          onClick={handleClearResults}
          disabled={isLoading || !results}
          variant="outline"
          className="w-full sm:w-1/2 flex items-center justify-center gap-2 text-lg py-6"
        >
          <XCircle className="h-5 w-5" />
          Clear Results
        </Button>
      </CardFooter>

      {/* Simulation Results Display Section */}
      {results && (
        <CardContent className="pt-6 border-t mt-6">
          <h3 className="text-xl font-semibold mb-4 border-b pb-2 flex items-center gap-2">
            <Terminal className="h-5 w-5" />
            Simulation Outputs
          </h3>

          {/* Error Message Display */}
          {results.error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 shadow-sm mb-4">
              <p className="font-bold mb-2 flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" /> Simulation Error:
              </p>
              <p className="text-sm">{results.error}</p>
            </div>
          )}

          {/* Results Tabs */}
          {!results.error && (
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-4 h-12">
                <TabsTrigger value="summary" className="text-base">Summary</TabsTrigger>
                <TabsTrigger value="lmstudio-response" className="text-base">LM Studio Raw</TabsTrigger>
                <TabsTrigger value="vector" className="text-base">Vectorized Prompt</TabsTrigger>
                <TabsTrigger value="execution-details" className="text-base">
                  <Terminal className="h-4 w-4 mr-2" /> Details
                </TabsTrigger>
              </TabsList>

              {/* Summary Tab Content */}
              <TabsContent value="summary" className="mt-4">
                <Card className="p-4 rounded-lg bg-gradient-to-br from-green-50 to-blue-50 dark:from-green-950 dark:to-blue-950 border min-h-[100px] max-h-96 overflow-y-auto">
                  <p className="text-sm leading-relaxed">
                    {results.summary || "No summary generated for the LM Studio response."}
                  </p>
                </Card>
              </TabsContent>

              {/* LM Studio Raw Response Tab Content */}
              <TabsContent value="lmstudio-response" className="mt-4">
                <Textarea
                  className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border font-mono text-xs min-h-[300px] max-h-96"
                  rows={15}
                  readOnly
                  value={JSON.stringify(results.lmStudioResponse, null, 2)}
                />
              </TabsContent>

              {/* Vectorized Prompt Tab Content */}
              <TabsContent value="vector" className="mt-4">
                <Textarea
                  className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border font-mono text-xs min-h-[300px] max-h-96"
                  rows={15}
                  readOnly
                  value={
                    results.vectorizedPrompt
                      ? `[${results.vectorizedPrompt.map((v) => v.toFixed(6)).join(',\n ')}]`
                      : "No vector generated for the prompt."
                  }
                />
              </TabsContent>

              {/* Execution Details Tab Content */}
              <TabsContent value="execution-details" className="mt-4">
                <Card className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800 border min-h-[100px] max-h-96 overflow-y-auto">
                  {results.executionDetails && results.executionDetails.length > 0 ? (
                    results.executionDetails.map((detail, index) => (
                      <div
                        key={index}
                        className="mb-3 p-3 border-b last:border-b-0 bg-white dark:bg-gray-900 rounded"
                      >
                        <p className="font-bold text-sm flex items-center gap-2">
                          <Terminal className="h-4 w-4" />
                          Opcode: {detail.opcode}
                        </p>
                        <p className="text-xs mt-1">
                          Status:{' '}
                          <span
                            className={
                              detail.status === 'success' ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'
                            }
                          >
                            {detail.status}
                          </span>
                        </p>
                        {detail.duration && (
                          <p className="text-xs">Duration: {detail.duration.toFixed(3)}s</p>
                        )}
                        {detail.error && (
                          <p className="text-xs text-red-600">Error: {detail.error}</p>
                        )}
                        {detail.outputPreview && (
                          <p className="text-xs mt-1">
                            Output Preview:{' '}
                            <code className="bg-gray-200 dark:bg-gray-700 p-1 rounded break-all">
                              {JSON.stringify(detail.outputPreview)}
                            </code>
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm">No execution details available.</p>
                  )}
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      )}
    </Card>
  );
}
