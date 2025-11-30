import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { getTruthSpectrumIcon, TRUTH_SPECTRUM } from "@/utils/truthSpectrum";
import { cn } from "@/lib/utils"; // Assuming a utility for classname concatenation
import { Separator } from "@/components/ui/separator";
import { Plus } from 'lucide-react';

export default function TruthSpectrumVisualizer() {
  const spectrumEntries = Object.entries(TRUTH_SPECTRUM);

  return (
    <Card className="w-full max-w-4xl mx-auto p-6 shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl font-bold">Understanding the Truth-Lie Spectrum</CardTitle>
        <CardDescription>
          This visualizer explains the different confidence levels used in the system, ranging from absolute lie to absolute truth.
          Each level has a unique meaning, visual representation, and confidence score range.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {spectrumEntries.map(([key, info], index) => {
          const IconComponent = getTruthSpectrumIcon(info.min + (info.max - info.min) / 2); // Get icon for the middle of the range
          return (
            <React.Fragment key={key}>
              <div className="flex items-start gap-4">
                <div className={cn(
                  "flex-shrink-0 p-3 rounded-full",
                  info.bgColorClass.replace('bg-', 'bg-'), // Ensure it's just the bg class
                  info.colorClass.replace('text-', 'text-') // Ensure it's just the text class
                )}>
                  <IconComponent className="h-6 w-6" />
                </div>
                <div>
                  <h4 className={cn("font-semibold text-lg", info.colorClass)}>{info.label}</h4>
                  <p className="text-gray-700 mt-1">{info.description}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    Confidence Range: {info.min.toFixed(2)} - {info.max.toFixed(2)} (
                    {(info.min * 100).toFixed(0)}% - {(info.max * 100).toFixed(0)}%)
                  </p>
                </div>
              </div>
              {index < spectrumEntries.length - 1 && <Separator className="my-4" />}
            </React.Fragment>
          );
        })}
      </CardContent>
    </Card>
  );
}
