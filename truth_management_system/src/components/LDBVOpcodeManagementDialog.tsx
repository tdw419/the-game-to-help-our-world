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
import { Badge } from '@/components/ui/badge';
import { Eye, Edit, Trash2, Cpu, SlidersHorizontal, GitFork, BookText, HardDrive } from 'lucide-react';
import { LDBVOpcod } from './LDBVCreateOpcodeDialog'; // Re-use the interface

interface LDBVOpcodeManagementDialogProps {
  isOpen: boolean;
  onClose: () => void;
  opcode: LDBVOpcod | null;
  onUpdateOpcode: (updatedOpcode: LDBVOpcod) => void;
  onDeleteOpcode: (opcodeId: string) => void;
  existingOpcodeIds: string[]; // To prevent duplicate IDs during edit
}

/**
 * LDBVOpcodeManagementDialog Component:
 * A versatile dialog for viewing, editing, and deleting a conceptual LDB-V Opcode.
 * It combines the functionalities of detail view and an editable form.
 */
export default function LDBVOpcodeManagementDialog({
  isOpen,
  onClose,
  opcode,
  onUpdateOpcode,
  onDeleteOpcode,
  existingOpcodeIds,
}: LDBVOpcodeManagementDialogProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [name, setName] = useState<string>('');
  const [category, setCategory] = useState<LDBVOpcod['category']>('Vector Arithmetic');
  const [description, setDescription] = useState<string>('');
  const [avgExecutionTimeMs, setAvgExecutionTimeMs] = useState<string>('0.1');
  const [successRate, setSuccessRate] = useState<string>('1.0');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen && opcode) {
      setName(opcode.name);
      setCategory(opcode.category);
      setDescription(opcode.description);
      setAvgExecutionTimeMs(opcode.avgExecutionTimeMs.toString());
      setSuccessRate(opcode.successRate.toString());
      setIsEditing(false); // Start in view mode
      setError('');
    } else if (!isOpen) {
      setIsEditing(false); // Reset editing state when dialog closes
    }
  }, [isOpen, opcode]);

  const getCategoryIcon = (cat: LDBVOpcod['category']) => {
    switch (cat) {
      case 'Vector Arithmetic': return <Cpu className="h-4 w-4 mr-1" />;
      case 'Quantization': return <SlidersHorizontal className="h-4 w-4 mr-1" />;
      case 'Graph Traversal': return <GitFork className="h-4 w-4 mr-1" />;
      case 'Memory Access': return <HardDrive className="h-4 w-4 mr-1" />;
      case 'Control Flow': return <BookText className="h-4 w-4 mr-1" />;
      default: return null;
    }
  };

  const handleUpdate = () => {
    if (!opcode) return;
    setError('');

    const parsedAvgExecutionTimeMs = parseFloat(avgExecutionTimeMs);
    const parsedSuccessRate = parseFloat(successRate);

    if (!name || !description || !category) {
      setError('Please fill in all required fields.');
      return;
    }
    // Check for duplicate name if name has changed and it's not the current opcode's original name
    if (name.toLowerCase() !== opcode.name.toLowerCase() && existingOpcodeIds.includes(name.toLowerCase())) {
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

    const updatedOpcode: LDBVOpcod = {
      ...opcode,
      name,
      category,
      description,
      avgExecutionTimeMs: parsedAvgExecutionTimeMs,
      successRate: parsedSuccessRate,
      // The ID should generally not change, but if it did, it would be handled here
      id: name.toLowerCase().replace(/\s/g, '-') // Re-generate ID based on new name
    };
    onUpdateOpcode(updatedOpcode);
    onClose();
  };

  const handleDelete = () => {
    if (!opcode) return;
    if (window.confirm(`Are you sure you want to delete the opcode "${opcode.name}"? This action cannot be undone.`)) {
      onDeleteOpcode(opcode.id);
      onClose();
    }
  };

  const categories: LDBVOpcod['category'][] = [
    'Vector Arithmetic',
    'Quantization',
    'Graph Traversal',
    'Memory Access',
    'Control Flow',
  ];

  if (!opcode) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isEditing ? (
              <Edit className="h-5 w-5 text-orange-500" />
            ) : (
              <Eye className="h-5 w-5 text-blue-500" />
            )}
            {isEditing ? `Edit Opcode: ${opcode.name}` : `Opcode Details: ${opcode.name}`}
          </DialogTitle>
          <DialogDescription>
            {isEditing ? `Modify the details for ${opcode.name}.` : `Detailed view of the ${opcode.name} LDB-V Opcode.`}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label className="text-right font-semibold">ID</Label>
            <span className="col-span-3 text-muted-foreground">{opcode.id}</span>
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right font-semibold">Name</Label>
            {isEditing ? (
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="col-span-3"
                placeholder="e.g., LDB.V.VDOT"
              />
            ) : (
              <span className="col-span-3 text-lg font-medium">{opcode.name}</span>
            )}
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="category" className="text-right font-semibold">Category</Label>
            <div className="col-span-3">
              {isEditing ? (
                <Select onValueChange={(value) => setCategory(value as LDBVOpcod['category'])} value={category}>
                  <SelectTrigger className="w-full">
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
              ) : (
                <Badge variant="outline" className="flex items-center w-fit">
                  {getCategoryIcon(opcode.category)} {opcode.category}
                </Badge>
              )}
            </div>
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="description" className="text-right font-semibold pt-2">Description</Label>
            {isEditing ? (
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="col-span-3 resize-none"
                placeholder="Brief explanation of the opcode's function..."
              />
            ) : (
              <span className="col-span-3 text-muted-foreground break-words">{opcode.description}</span>
            )}
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="avgExecutionTimeMs" className="text-right font-semibold">Avg. Time</Label>
            {isEditing ? (
              <Input
                id="avgExecutionTimeMs"
                type="number"
                step="0.01"
                min="0.01"
                value={avgExecutionTimeMs}
                onChange={(e) => setAvgExecutionTimeMs(e.target.value)}
                className="col-span-3"
              />
            ) : (
              <span className="col-span-3 text-muted-foreground">{opcode.avgExecutionTimeMs.toFixed(2)} ms</span>
            )}
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="successRate" className="text-right font-semibold">Success Rate</Label>
            {isEditing ? (
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
            ) : (
              <span className="col-span-3 text-muted-foreground">{(opcode.successRate * 100).toFixed(1)}%</span>
            )}
          </div>
        </div>
        <DialogFooter className="flex-col sm:flex-row sm:justify-between items-stretch sm:items-center">
          {isEditing ? (
            <div className="flex gap-2 w-full sm:w-auto">
              <Button variant="outline" onClick={() => setIsEditing(false)} className="w-full sm:w-auto">
                Cancel
              </Button>
              <Button onClick={handleUpdate} className="w-full sm:w-auto">
                Save Changes
              </Button>
            </div>
          ) : (
            <div className="flex gap-2 w-full sm:w-auto">
              <Button variant="outline" onClick={() => setIsEditing(true)} className="flex items-center gap-1 w-full sm:w-auto">
                <Edit className="h-4 w-4" /> Edit
              </Button>
              <Button variant="destructive" onClick={handleDelete} className="flex items-center gap-1 w-full sm:w-auto">
                <Trash2 className="h-4 w-4" /> Delete
              </Button>
            </div>
          )}
          {!isEditing && (
            <Button onClick={onClose} className="mt-2 sm:mt-0 w-full sm:w-auto">Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}