import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Folder, FileText, FileImage, FileCode, Square, FileQuestion } from 'lucide-react'; // Icons for different file types
import { hashToRgb, MockPxfsItem } from '@/lib/pxfs-utils'; // Import from shared utils

interface PixelItem extends MockPxfsItem {
  // Inherits name, hash, isDirectory, type from MockPxfsItem
  // No additional properties needed for this component, but keeping the interface specific
}

interface DirectoryPixelClusterProps {
  /**
   * The name of the directory being displayed.
   */
  directoryName: string;
  /**
   * An array of pixel items (files or subdirectories) within this directory.
   */
  items: PixelItem[];
  /**
   * The hash of the directory itself (can be used for its "anchor pixel" color).
   */
  directoryHash?: string;
  /**
   * Callback function when a pixel item is clicked.
   */
  onItemClick?: (item: PixelItem) => void;
}

/**
 * A component to display a PXOS directory as a cluster of pixel-like representations for its contents.
 * Each item (file or subdirectory) is represented by a colored square derived from its hash,
 * with an icon indicating its type. This visualizes the "Directory Tree as Pixel Cluster" concept
 * and serves as a step towards "Visual Expansion Algorithms".
 */
export default function DirectoryPixelCluster({ directoryName, items, directoryHash, onItemClick }: DirectoryPixelClusterProps) {
  const getIcon = (type: PixelItem['type'], isDirectory?: boolean) => {
    if (isDirectory || type === 'folder') return Folder;
    switch (type) {
      case 'text': return FileText;
      case 'image': return FileImage;
      case 'code': return FileCode;
      default: return FileQuestion;
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-lg bg-card text-card-foreground">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-semibold flex items-center gap-2">
          <Folder className="h-5 w-5 text-blue-500" />
          {directoryName}
        </CardTitle>
        <Badge variant="secondary" className="px-3 py-1 text-xs">
          RAG Loop 1/5 - Directory View
        </Badge>
      </CardHeader>
      <CardContent className="pt-4 flex flex-col gap-4">
        {items.length === 0 ? (
          <p className="text-center text-muted-foreground p-4">This directory is empty.</p>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-4 p-2 rounded-md border border-dashed border-gray-300">
            {items.map((item, index) => {
              const pixelColor = hashToRgb(item.hash);
              const IconComponent = getIcon(item.type, item.isDirectory);
              return (
                <div
                  key={item.hash + item.name + index} // Added item.name for better key uniqueness
                  className="flex flex-col items-center justify-center p-2 rounded-md hover:bg-muted/50 transition-colors cursor-pointer group"
                  title={`${item.name} (${item.isDirectory ? 'Directory' : 'File'}) - Hash: ${item.hash}`}
                  onClick={() => onItemClick && onItemClick(item)} // Call onItemClick when clicked
                >
                  <div
                    className="w-12 h-12 rounded-lg border-2 border-gray-200 flex items-center justify-center transition-all duration-200 group-hover:scale-110"
                    style={{ backgroundColor: pixelColor }}
                  >
                    <IconComponent className="h-6 w-6 text-white opacity-80 group-hover:opacity-100" />
                  </div>
                  <p className="text-xs text-center mt-1 truncate w-full px-1">{item.name}</p>
                </div>
              );
            })}
          </div>
        )}
        {directoryHash && (
          <div className="text-center border-t pt-4 mt-4">
            <p className="text-sm text-muted-foreground">Directory Hash:</p>
            <p className="font-mono text-xs break-all bg-muted p-2 rounded-md">
              {directoryHash}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}