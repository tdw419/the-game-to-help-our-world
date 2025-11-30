import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Loader2, Send } from 'lucide-react'; // Using Loader2 for loading indicator and Send for the button icon

// Placeholder for base44 SDK interaction. In a real scenario, base44 would provide
// a client to interact with the backend to execute opcodes.
// For demonstration, we'll simulate an async call.
interface Base44Client {
  executeOpcode: (opcodeName: string, input: any) => Promise<any>;
}

// Mock Base44 client for simulation purposes
const mockBase44Client: Base44Client = {
  executeOpcode: async (opcodeName: string, input: any) => {
    console.log(`Simulating execution of opcode: ${opcodeName} with input:`, input);
    // Simulate API delay
    await new Promise(resolve => setTimeout(Math.random() * 2000 + 1000, resolve));

    if (opcodeName === "LM_STUDIO_PROMPT_WORKFLOW_ORCHESTRATOR") {
      if (!input.initial_prompt_text || input.initial_prompt_text.trim() === "") {
        throw new Error("Prompt text cannot be empty.");
      }
      // Simulate success
      const simulatedResponse = `LM Studio generated text for: "${input.initial_prompt_text}".\n\n` +
                                `Summary requested: ${input.summarize_response ? 'Yes' : 'No'}.` +
                                `\n\nThis is a placeholder response from the simulated LM Studio interaction.`;
      return {
        final_output: simulatedResponse,
        workflow_status: "completed"
      };
    } else {
      throw new Error(`Unknown opcode: ${opcodeName}`);
    }
  }
};

export default function LmStudioPromptSimulator() {
  const [promptText, setPromptText] = useState<string>('');
  const [summarizeResponse, setSummarizeResponse] = useState<boolean>(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async () => {
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      if (!promptText.trim()) {
        throw new Error("Please enter a prompt to send to LM Studio.");
      }

      const response = await mockBase44Client.executeOpcode("LM_STUDIO_PROMPT_WORKFLOW_ORCHESTRATOR", {
        initial_prompt_text: promptText,
        summarize_response: summarizeResponse,
      });

      if (response && response.workflow_status === "completed") {
        setResult(response.final_output);
      } else {
        setError("Workflow did not complete successfully or returned an unexpected format.");
      }
    } catch (err) {
      console.error("Failed to execute LM Studio workflow:", err);
      setError(err instanceof Error ? err.message : "An unknown error occurred during workflow execution.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-[600px] max-w-full mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-6 w-6 text-primary" /> Simulate LM Studio Prompt
        </CardTitle>
        <CardDescription>
          Send a prompt to a simulated LM Studio instance and process its response within the Vector Universe.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="grid gap-2">
          <Label htmlFor="prompt">Prompt for LM Studio</Label>
          <Textarea
            id="prompt"
            placeholder="E.g., Write a short story about an AI exploring a new planet."
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            rows={5}
            disabled={loading}
          />
        </div>
        <div className="flex items-center space-x-2">
          <Checkbox
            id="summarize"
            checked={summarizeResponse}
            onCheckedChange={(checked) => setSummarizeResponse(checked as boolean)}
            disabled={loading}
          />
          <Label htmlFor="summarize" className="cursor-pointer">Summarize LM Studio Response</Label>
        </div>
        {error && (
          <div className="text-red-500 text-sm p-2 bg-red-50 rounded-md border border-red-200">
            Error: {error}
          </div>
        )}
        {result && (
          <div className="grid gap-2">
            <Label>LM Studio Workflow Output:</Label>
            <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-md text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">
              {result}
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button
          onClick={handleSubmit}
          className="w-full"
          disabled={loading || !promptText.trim()}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Sending to LM Studio...
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" /> Send Prompt
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
