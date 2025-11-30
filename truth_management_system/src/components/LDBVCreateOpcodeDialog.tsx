import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { PlusCircle } from 'lucide-react';

// Re-export the interface for consistent typing across components
export interface LDBVOpcod {
  id: string;
  name: string;
  category: 'Vector Arithmetic' | 'Quantization' | 'Graph Traversal' | 'Memory Access' | 'Control Flow';
  description: string;
  avgExecutionTimeMs: number;
  successRate: number; // 0.0 - 1.0
}

interface LDBVCreateOpcodeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateOpcode: (newOpcode: LDBVOpcod) => void;
  existingOpcodeIds: string[]; // To prevent duplicate IDs
}

/**
 * LDBVCreateOpcodeDialog Component:
 * A modal dialog for creating a new conceptual LDB-V Opcode.
 * It collects details such as name, category, description, and performance metrics.
 */
export default function LDBVCreateOpcodeDialog({
  isOpen,
  onClose,
  onCreateOpcode,
  existingOpcodeIds,
}: LDBVCreateOpcodeDialogProps) {
  const [name, setName] = useState<string>('');
  const [category, setCategory] = useState<LDBVOpcod['category']>('Vector Arithmetic');
  const [description, setDescription] = useState<string>('');
  const [avgExecutionTimeMs, setAvgExecutionTimeMs] = useState<string>('0.1');
  const [successRate, setSuccessRate] = useState<string>('1.0');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setName('');
      setCategory('Vector Arithmetic');
      setDescription('');
      setAvgExecutionTimeMs('0.1');
      setSuccessRate('1.0');
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = () => {
    setError(''); // Clear previous errors

    const parsedAvgExecutionTimeMs = parseFloat(avgExecutionTimeMs);
    const parsedSuccessRate = parseFloat(successRate);

    if (!name || !description || !category) {
      setError('Please fill in all required fields.');
      return;
    }
    if (existingOpcodeIds.includes(name.toLowerCase())) {
      setError('Opcode name already exists. Please choose a unique name.');
      return;
    }
    if (isNaN(parsedAvgExecutionTimeMs) || parsedAvgExecutionTimeMs <= 0) {
      setError('Average Execution Time must be a positive number.');
      return;
    }
    if (isNaN(parsedSuccessRate) || parsedSuccessRate < 0 || parsedSuccessRate > 1) {
      setError('Success Rate must be a number between 0.0 and 1.0.');
      return;
    }

    const newOpcode: LDBVOpcod = {
      id: name.toLowerCase().replace(/\s/g, '-'), // Generate a simple ID from the name
      name,
      category,
      description,
      avgExecutionTimeMs: parsedAvgExecutionTimeMs,
      successRate: parsedSuccessRate,
    };

    onCreateOpcode(newOpcode);
    onClose();
  };

  const categories: LDBVOpcod['category'][] = [
    'Vector Arithmetic',
    'Quantization',
    'Graph Traversal',
    'Memory Access',
    'Control Flow',
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-green-500" /> Create New LDB-V Opcode
          </DialogTitle>
          <DialogDescription>
            Define a new conceptual instruction for the LDB-V Vector Programming Language.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="col-span-3"
              placeholder="e.g., LDB.V.VDOT"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="category" className="text-right">
              Category
            </Label>
            <Select onValueChange={(value) => setCategory(value as LDBVOpcod['category'])} value={category}>
              <SelectTrigger className="col-span-3">
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="description" className="text-right pt-2">
              Description
            </Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="col-span-3 resize-none"
              placeholder="Brief explanation of the opcode's function..."
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="avgExecutionTimeMs" className="text-right">
              Avg. Time (ms)
            </Label>
            <Input
              id="avgExecutionTimeMs"
              type="number"
              step="0.01"
              min="0.01"
              value={avgExecutionTimeMs}
              onChange={(e) => setAvgExecutionTimeMs(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="successRate" className="text-right">
              Success Rate (0-1)
            </Label>
            <Input
              id="successRate"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={successRate}
              onChange={(e) => setSuccessRate(e.target.value)}
              className="col-span-3"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit}>Create Opcode</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}