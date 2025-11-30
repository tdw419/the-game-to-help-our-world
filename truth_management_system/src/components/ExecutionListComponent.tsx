import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CheckCircle2, XCircle, Clock, Search } from 'lucide-react'; // Icons
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

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

interface ExecutionListComponentProps {
  executions: Execution[];
  onSelectExecution: (execution: Execution) => void;
}

export default function ExecutionListComponent({ executions, onSelectExecution }: ExecutionListComponentProps) {
  // Function to format timestamp for display
  const formatTimestamp = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString(); // Adjust as needed for specific locale/format
  };

  return (
    <Card className="w-[1000px] max-w-full mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-6 w-6 text-primary" /> Execution History: LM Studio Workflow
        </CardTitle>
        <CardDescription>
          A log of all simulated executions for the `LM_STUDIO_PROMPT_WORKFLOW_ORCHESTRATOR`.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        {executions.length === 0 ? (
          <p className="text-center text-gray-500">No executions found for this workflow.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Input Summary</TableHead>
                <TableHead>Time</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {executions.map((exec) => (
                <TableRow key={exec.id} className={!exec.success ? "bg-red-50/20 dark:bg-red-900/10" : ""}>
                  <TableCell>
                    <Badge variant={exec.success ? "success" : "destructive"} className="flex items-center gap-1 w-fit">
                      {exec.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                      {exec.success ? "Success" : "Failed"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="cursor-help line-clamp-1 max-w-[300px] block">
                            {exec.input.initial_prompt_text || "N/A"}
                          </span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p>{exec.input.initial_prompt_text || "No prompt provided."}</p>
                          {exec.input.summarize_response && <p> (Summarization requested)</p>}
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="cursor-help">
                            {exec.execution_time.toFixed(2)}s ({formatTimestamp(exec.timestamp)})
                          </span>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Executed at: {formatTimestamp(exec.timestamp)}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onSelectExecution(exec)}
                    >
                      <Search className="h-4 w-4 mr-2" /> View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
