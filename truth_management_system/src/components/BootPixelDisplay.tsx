import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Hexagon, Pixel } from 'lucide-react'; // Using Hexagon as a placeholder for a 'hash' icon, Pixel for the boot pixel itself

interface BootPixelDisplayProps {
  /**
   * The unique SHA256 hash representing the system's "boot pixel".
   * This hash acts as a universal pointer to the system's entire state.
   */
  bootPixelHash: string;
  /**
   * An optional label or name for the system being displayed.
   */
  systemName?: string;
}

/**
 * Converts a SHA256 hash string into an RGB color string.
 * This is a simplified visualization to represent the "color" of a boot pixel.
 * Takes the first 6 hex characters and converts them to R, G, B values.
 */
const hashToRgb = (hash: string): string => {
  if (!hash || hash.length < 6) {
    // Fallback to a default color if hash is too short or invalid
    return 'rgb(128, 128, 128)'; // Gray
  }
  const r = parseInt(hash.substring(0, 2), 16);
  const g = parseInt(hash.substring(2, 4), 16);
  const b = parseInt(hash.substring(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
};

/**
 * A component to display a PXOS "Boot Pixel", which represents a system's
 * entire state through a cryptographic hash and its visual (color) representation.
 * This component visualizes the core concept of PXOS's fractal data representation.
 */
export default function BootPixelDisplay({ bootPixelHash, systemName = "PXOS System" }: BootPixelDisplayProps) {
  const pixelColor = hashToRgb(bootPixelHash);

  return (
    <Card className="w-full max-w-md mx-auto shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xl font-semibold flex items-center gap-2">
          <Hexagon className="h-5 w-5 text-purple-600" />
          {systemName} Boot Pixel
        </CardTitle>
        <Badge variant="secondary" className="px-3 py-1 text-xs">
          RAG Loop 1/5
        </Badge>
      </CardHeader>
      <CardContent className="pt-4 flex flex-col items-center gap-4">
        <div
          className="w-24 h-24 rounded-lg border-2 border-gray-300 flex items-center justify-center transition-all duration-300 hover:scale-105"
          style={{ backgroundColor: pixelColor }}
          title={`RGB: ${pixelColor}`}
        >
          <Pixel className="h-12 w-12 text-white opacity-70" />
        </div>
        <div className="text-center">
          <p className="text-sm text-gray-500">Master Hash:</p>
          <p className="font-mono text-xs break-all bg-gray-100 p-2 rounded-md dark:bg-gray-800">
            {bootPixelHash || "N/A"}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
