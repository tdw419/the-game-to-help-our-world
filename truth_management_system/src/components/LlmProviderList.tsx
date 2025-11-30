import React, { useState } from 'react';
import { LlmProvider } from '@/types/llm-config';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Loader2, MoreHorizontal } from 'lucide-react'; // Added MoreHorizontal icon
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { DialogTrigger } from '@/components/ui/dialog'; // Import DialogTrigger
import EditLlmProviderDialog from '@/components/EditLlmProviderDialog'; // New component import

interface LlmProviderListProps {
  providers: LlmProvider[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void; // Added onRefresh prop to trigger parent refresh
}

export default function LlmProviderList({ providers, loading, error, onRefresh }: LlmProviderListProps) {
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState<LlmProvider | null>(null);

  const handleEditClick = (provider: LlmProvider) => {
    setSelectedProvider(provider);
    setIsEditDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-48">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <p className="ml-2 text-lg text-gray-600">Loading providers...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-500 p-4">
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border bg-card text-card-foreground shadow-sm">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Base URL</TableHead>
            <TableHead className="text-center">Active</TableHead>
            <TableHead>Created At</TableHead>
            <TableHead>Updated At</TableHead>
            <TableHead className="text-right">Actions</TableHead> {/* New Actions column */}
          </TableRow>
        </TableHeader>
        <TableBody>
          {providers.length > 0 ? (
            providers.map((provider) => (
              <TableRow key={provider.id}>
                <TableCell className="font-medium">{provider.name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{provider.type}</Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground max-w-[200px] truncate">{provider.baseUrl}</TableCell>
                <TableCell className="text-center">
                  <Badge variant={provider.isActive ? 'default' : 'destructive'}>
                    {provider.isActive ? 'Yes' : 'No'}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(provider.createdAt).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {new Date(provider.updatedAt).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Actions</DropdownMenuLabel>
                      <DropdownMenuItem onSelect={() => handleEditClick(provider)}>
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem className="text-red-600 focus:bg-red-50 focus:text-red-700">
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground"> {/* Updated colspan */}
                No LLM providers found.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {selectedProvider && (
        <EditLlmProviderDialog
          isOpen={isEditDialogOpen}
          onOpenChange={setIsEditDialogOpen}
          initialData={selectedProvider}
          onProviderUpdated={onRefresh} // Pass onRefresh to Edit dialog
        />
      )}
    </div>
  );
}
