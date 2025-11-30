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
import { Edit } from 'lucide-react';

interface RenameProposalDialogProps {
  isOpen: boolean;
  onClose: () => void;
  elementId: string;
  currentName: string;
  onSaveProposal: (elementId: string, newName: string, rationale: string) => void;
}

/**
 * Dialog component for proposing a new name for a metric element.
 */
export default function RenameProposalDialog({
  isOpen,
  onClose,
  elementId,
  currentName,
  onSaveProposal,
}: RenameProposalDialogProps) {
  const [newName, setNewName] = useState<string>(currentName);
  const [rationale, setRationale] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setNewName(currentName);
      setRationale('');
    }
  }, [isOpen, currentName]);

  const handleSubmit = () => {
    if (newName && rationale) {
      onSaveProposal(elementId, newName, rationale);
      onClose();
    } else {
      alert('Please enter a new name and a rationale for the proposal.');
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="h-5 w-5 text-blue-500" /> Propose New Name for "{currentName}"
          </DialogTitle>
          <DialogDescription>
            Submit a proposal to rename this metric element. Provide a clear rationale.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="current-name" className="text-right">
              Current Name
            </Label>
            <Input id="current-name" value={currentName} disabled className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="new-name" className="text-right">
              New Name
            </Label>
            <Input
              id="new-name"
              placeholder="e.g., Velocity-Weighted Confidence"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-start gap-4">
            <Label htmlFor="rationale" className="text-right pt-2">
              Rationale
            </Label>
            <Textarea
              id="rationale"
              placeholder="Explain why this new name is better..."
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              className="col-span-3 resize-none"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Submit Proposal</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}