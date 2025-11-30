import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle2, XCircle, Info, Timer, Brain } from 'lucide-react'; // Icons for status, info, timer, reasoning
import { Button } from '@/components/ui/button';

// Define a type for an Execution for clarity
interface Execution {
  id: string;
  opcode_name: string;
  success: boolean;
  input: { [key: string]: any };
  output: { [key: string]: any };
  confidence: number;
  execution_time: number;
  timestamp: string; // Added timestamp for sorting/display
  reasoning_blocks?: Array<{ step: string; confidence: number }>;
  confidence_blocks?: { [key: string]: number };
}

interface ExecutionDetailViewerProps {
  execution: Execution;
  onBack: () => void;
}

export default function ExecutionDetailViewer({ execution, onBack }: ExecutionDetailViewerProps) {
  return (
    <Card className="w-[800px] max-w-full mx-auto">
      <CardHeader>
        <Button onClick={onBack} className="mb-4">
          ← Back to List
        </Button>
        <CardTitle className="flex items-center gap-2">
          {execution.success ? <CheckCircle2 className="h-6 w-6 text-green-500" /> : <XCircle className="h-6 w-6 text-red-500" />}
          Execution Details: {execution.opcode_name}
        </CardTitle>
        <CardDescription>
          Overview of a simulated execution of the LM Studio Prompt Workflow Orchestrator.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-sm font-medium">Status:</Label>
            <Badge variant={execution.success ? "success" : "destructive"} className="ml-2">
              {execution.success ? "Success" : "Failed"}
            </Badge>
          </div>
          <div>
            <Label className="text-sm font-medium">Confidence:</Label>
            <Badge variant="secondary" className="ml-2">
              {(execution.confidence * 100).toFixed(1)}%
            </Badge>
          </div>
          <div>
            <Label className="text-sm font-medium flex items-center gap-1">
              <Timer className="h-4 w-4" /> Execution Time:
            </Label>
            <span className="ml-2">{execution.execution_time} seconds</span>
          </div>
        </div>

        <div className="grid gap-2">
          <Label className="text-lg font-semibold flex items-center gap-2">
            <Info className="h-5 w-5" /> Input Parameters
          </Label>
          <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-sm whitespace-pre-wrap">
            <pre>{JSON.stringify(execution.input, null, 2)}</pre>
          </div>
        </div>

        <div className="grid gap-2">
          <Label className="text-lg font-semibold flex items-center gap-2">
            <Info className="h-5 w-5" /> Output Results
          </Label>
          <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-sm whitespace-pre-wrap">
            <pre>{JSON.stringify(execution.output, null, 2)}</pre>
          </div>
        </div>

        {execution.reasoning_blocks && execution.reasoning_blocks.length > 0 && (
          <div className="grid gap-2">
            <Label className="text-lg font-semibold flex items-center gap-2">
              <Brain className="h-5 w-5" /> Reasoning Steps
            </Label>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Step</TableHead>
                  <TableHead className="text-right">Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {execution.reasoning_blocks.map((block, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{block.step}</TableCell>
                    <TableCell className="text-right">{(block.confidence * 100).toFixed(1)}%</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}

        {execution.confidence_blocks && (
          <div className="grid gap-2">
            <Label className="text-lg font-semibold flex items-center gap-2">
              <Brain className="h-5 w-5" /> Detailed Confidence Metrics
            </Label>
            <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-md text-sm whitespace-pre-wrap">
                <pre>{JSON.stringify(execution.confidence_blocks, null, 2)}</pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
