import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, FileImage, FileCode, FileQuestion, Hash, Info } from 'lucide-react';
import { MockPxfsItem } from '@/lib/pxfs-utils'; // Import the shared interface

interface PixelContentPreviewProps {
  /**
   * The file item to display a preview for.
   * If null, the dialog will be closed.
   */
  file: MockPxfsItem | null;
  /**
   * Callback to close the preview dialog.
   */
  onClose: () => void;
}

const renderContentPreview = (file: MockPxfsItem) => {
  switch (file.type) {
    case 'text':
      return (
        <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-md border border-dashed text-muted-foreground max-h-60 overflow-y-auto">
          {`// Simulated text content for ${file.name}
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

This file's hash is: ${file.hash.substring(0, 32)}...
`}
        </pre>
      );
    case 'image':
      return (
        <div className="flex flex-col items-center justify-center bg-muted p-4 rounded-md border border-dashed min-h-[150px]">
          <FileImage className="h-16 w-16 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">Image Preview: {file.name}</p>
          {/* In a real app, this would be a dynamically loaded image */}
          <div className="w-full h-32 bg-gray-200 dark:bg-gray-700 mt-2 rounded-md flex items-center justify-center text-xs text-gray-500">
            [Placeholder Image]
          </div>
        </div>
      );
    case 'code':
      return (
        <pre className="whitespace-pre-wrap font-mono text-sm bg-muted p-4 rounded-md border border-dashed text-muted-foreground max-h-60 overflow-y-auto">
          {`// Simulated code content for ${file.name}
function main() {
  console.log("Hello, PXOS!");
  // This is a mock function, representing code in the system.
  // The hash for this file is: "${file.hash.substring(0, 32)}..."
  const data = [1, 2, 3];
  data.forEach(item => {
    console.log("Processing item:", item);
  });
}
main();
`}
        </pre>
      );
    default:
      return (
        <div className="flex flex-col items-center justify-center bg-muted p-4 rounded-md border border-dashed min-h-[150px]">
          <FileQuestion className="h-16 w-16 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">No specific preview available for "{file.type || 'unknown'}" type.</p>
        </div>
      );
  }
};

/**
 * Displays a content preview for a selected PXFS file.
 * Integrates into the PixelNavigator to provide "Scale 3: Content Preview" functionality.
 */
export default function PixelContentPreview({ file, onClose }: PixelContentPreviewProps) {
  if (!file) return null;

  return (
    <Dialog open={!!file} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Info className="h-5 w-5 text-blue-500" />
            File Preview: {file.name}
          </DialogTitle>
          <DialogDescription>
            A glimpse into the content of this PXFS file.
          </DialogDescription>
        </DialogHeader>
        <Card className="border-none shadow-none">
          <CardHeader className="p-0 pb-2">
            <div className="flex items-center justify-between">
              <Badge variant="secondary" className="capitalize">Type: {file.type || 'unknown'}</Badge>
              <Badge variant="outline" className="flex items-center gap-1">
                <Hash className="h-3 w-3" />
                Hash: {file.hash.substring(0, 8)}...
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {renderContentPreview(file)}
          </CardContent>
          <CardFooter className="p-0 pt-4 text-sm text-muted-foreground">
            This is a simulated preview. In a real PXOS, content would be retrieved via hash.
          </CardFooter>
        </Card>
      </DialogContent>
    </Dialog>
  );
}