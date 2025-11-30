import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  ListTree,
  Code,
  Timer,
  Gauge,
  Thermometer,
  PlaySquare,
  CheckCircle,
  XCircle,
  Package,
  Info,
} from 'lucide-react';

// Interface for Opcode structure - mirroring the backend schema as much as possible
interface Opcode {
  id: string;
  name: string;
  category: string;
  prompt_template: string;
  avg_execution_time?: number;
  success_rate?: number;
  confidence_threshold?: number;
  simulation_enabled?: boolean;
  temperature?: number;
  input_schema?: object;
  output_schema?: object;
}

interface LDBVOpcodesListProps {
  opcodes: Opcode[];
}

const LDBVOpcodesList: React.FC<LDBVOpcodesListProps> = ({ opcodes }) => {
  return (
    <Card className="w-full shadow-lg">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-3xl">
          <ListTree className="h-8 w-8 text-indigo-600" /> LDB-V System Primitives (Opcodes)
        </CardTitle>
        <CardDescription>
          A comprehensive list of all available Vector-Native LDB-V Opcodes.
          These are the foundational building blocks for AI-driven development and system operations.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          {opcodes.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">No Opcodes found. Start creating new primitives!</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[150px]">Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Prompt Template</TableHead>
                  <TableHead className="text-center">Avg. Time (s)</TableHead>
                  <TableHead className="text-center">Success Rate</TableHead>
                  <TableHead className="text-center">Confidence</TableHead>
                  <TableHead className="text-center">Sim. Enabled</TableHead>
                  <TableHead className="text-center">Temp.</TableHead>
                  <TableHead className="text-center">Schemas</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {opcodes.map((opcode) => (
                  <TableRow key={opcode.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4 text-gray-500" />
                        {opcode.name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="capitalize">
                        {opcode.category?.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-[300px] truncate text-sm text-muted-foreground">
                      {opcode.prompt_template}
                    </TableCell>
                    <TableCell className="text-center">
                      {opcode.avg_execution_time !== undefined ? (
                        <div className="flex items-center justify-center gap-1">
                          <Timer className="h-4 w-4 text-blue-500" />
                          {opcode.avg_execution_time.toFixed(2)}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {opcode.success_rate !== undefined ? (
                        <div className="flex items-center justify-center gap-1">
                          <Gauge className="h-4 w-4 text-green-500" />
                          {(opcode.success_rate * 100).toFixed(0)}%
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {opcode.confidence_threshold !== undefined ? (
                        <div className="flex items-center justify-center gap-1">
                          <Info className="h-4 w-4 text-yellow-500" />
                          {(opcode.confidence_threshold * 100).toFixed(0)}%
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {opcode.simulation_enabled !== undefined ? (
                        opcode.simulation_enabled ? (
                          <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                        )
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {opcode.temperature !== undefined ? (
                        <div className="flex items-center justify-center gap-1">
                          <Thermometer className="h-4 w-4 text-orange-500" />
                          {opcode.temperature.toFixed(1)}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex justify-center gap-2">
                        {opcode.input_schema && Object.keys(opcode.input_schema).length > 0 ? (
                          <Badge variant="outline" className="bg-blue-100 text-blue-800">In</Badge>
                        ) : (
                          <Badge variant="outline" className="bg-gray-100 text-gray-500">No In</Badge>
                        )}
                        {opcode.output_schema && Object.keys(opcode.output_schema).length > 0 ? (
                          <Badge variant="outline" className="bg-purple-100 text-purple-800">Out</Badge>
                        ) : (
                          <Badge variant="outline" className="bg-gray-100 text-gray-500">No Out</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="outline" size="sm">
                        <Code className="h-4 w-4 mr-2" /> View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default LDBVOpcodesList;