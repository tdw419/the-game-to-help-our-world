import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from '@/components/ui/breadcrumb';
import { ArrowUpToLine, FolderOpen, Files, FileSearch } from 'lucide-react';
import DirectoryPixelCluster from './DirectoryPixelCluster';
import PixelContentPreview from './PixelContentPreview'; // Import the new component
import { mockPxfsRoot, MockPxfsItem } from '@/lib/pxfs-utils';

/**
 * Recursively finds an item in the mock file system based on a path array.
 */
const findItemByPath = (root: MockPxfsItem, path: string[]): MockPxfsItem | null => {
  let current: MockPxfsItem | undefined = root;
  for (const segment of path) {
    current = current?.children?.find(child => child.name === segment);
    if (!current) return null;
  }
  return current || null;
};

export default function PixelNavigator() {
  const [currentPath, setCurrentPath] = useState<string[]>([]);
  const [currentDirectory, setCurrentDirectory] = useState<MockPxfsItem | null>(null);
  const [selectedFileForPreview, setSelectedFileForPreview] = useState<MockPxfsItem | null>(null); // New state for preview

  useEffect(() => {
    const item = findItemByPath(mockPxfsRoot, currentPath);
    setCurrentDirectory(item && item.isDirectory ? item : null);
  }, [currentPath]);

  const navigateTo = (pathSegment: string) => {
    setCurrentPath(prevPath => [...prevPath, pathSegment]);
    setSelectedFileForPreview(null); // Clear preview when navigating directories
  };

  const navigateUp = () => {
    if (currentPath.length > 0) {
      setCurrentPath(prevPath => prevPath.slice(0, -1));
      setSelectedFileForPreview(null); // Clear preview when navigating up
    }
  };

  const navigateToBreadcrumb = (index: number) => {
    setCurrentPath(currentPath.slice(0, index));
    setSelectedFileForPreview(null); // Clear preview when navigating via breadcrumb
  };

  const handleItemClick = (item: MockPxfsItem) => {
    if (item.isDirectory) {
      navigateTo(item.name);
    } else {
      setSelectedFileForPreview(item); // Set file for preview
    }
  };

  // Prepare items for DirectoryPixelCluster based on currentDirectory
  const clusterItems = currentDirectory?.children?.map(child => ({
    name: child.name,
    hash: child.hash,
    isDirectory: child.isDirectory,
    type: child.type || (child.isDirectory ? 'folder' : 'unknown'),
  })) || [];

  return (
    <Card className="w-full max-w-4xl mx-auto shadow-lg bg-card text-card-foreground p-4">
      <CardHeader className="pb-4 border-b flex flex-row items-center justify-between">
        <CardTitle className="text-2xl font-bold flex items-center gap-2">
          <FolderOpen className="h-6 w-6 text-yellow-500" />
          PXFS Pixel Navigator
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={navigateUp}
            disabled={currentPath.length === 0}
            className="flex items-center gap-1"
          >
            <ArrowUpToLine className="h-4 w-4" /> Up
          </Button>
          <Button variant="outline" size="sm" className="flex items-center gap-1" disabled>
            <Files className="h-4 w-4" /> Search (Future)
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-4 space-y-4">
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink onClick={() => setCurrentPath([])} className="cursor-pointer">
                Root
              </BreadcrumbLink>
            </BreadcrumbItem>
            {currentPath.map((segment, index) => (
              <React.Fragment key={index}>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  {index === currentPath.length - 1 ? (
                    <BreadcrumbPage>{segment}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink onClick={() => navigateToBreadcrumb(index + 1)} className="cursor-pointer">
                      {segment}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
              </React.Fragment>
            ))}
          </BreadcrumbList>
        </Breadcrumb>

        {currentDirectory ? (
          <div
            className="border-2 border-dashed border-primary/20 rounded-lg p-4 flex flex-col gap-4"
            style={{ minHeight: '300px' }}
          >
            <h3 className="text-lg font-semibold flex items-center gap-2 text-primary">
              <FolderOpen className="h-5 w-5" /> Current View: /{currentPath.join('/')}
            </h3>
            <DirectoryPixelCluster
              directoryName={currentDirectory.name}
              items={clusterItems}
              directoryHash={currentDirectory.hash}
              onItemClick={handleItemClick} // Use the new handler
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-[300px] text-muted-foreground">
            <FileSearch className="h-12 w-12 mb-4" />
            <p>Could not find directory or it is not a directory.</p>
            <Button onClick={() => setCurrentPath([])} variant="link" className="mt-2">Go to Root</Button>
          </div>
        )}
      </CardContent>

      <PixelContentPreview
        file={selectedFileForPreview}
        onClose={() => setSelectedFileForPreview(null)}
      />
    </Card>
  );
}