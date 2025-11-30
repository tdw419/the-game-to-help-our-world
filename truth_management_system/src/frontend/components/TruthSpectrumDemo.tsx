import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { TruthSpectrumBadge } from "@/components/TruthSpectrumBadge";

interface DemoTruth {
  content: string;
  confidence: number;
}

const demoTruths: DemoTruth[] = [
  { content: "The Earth is a perfect sphere.", confidence: 0.90 }, // Highly True, but not absolute
  { content: "All dogs are golden retrievers.", confidence: 0.05 }, // Highly False
  { content: "Eating chocolate everyday prevents all diseases.", confidence: 0.00 }, // Absolute Lie
  { content: "A balanced diet contributes to overall health.", confidence: 1.00 }, // Absolute Truth
  { content: "Working 8 hours a day is optimal for productivity.", confidence: 0.49 }, // Neutral / Unverified
  { content: "Regular exercise significantly improves cardiovascular health.", confidence: 0.95 }, // Absolute Truth (or very close)
  { content: "The moon landing was faked.", confidence: 0.01 }, // Absolute Lie
  { content: "Spending time in nature reduces stress.", confidence: 0.70 }, // Mostly True
];

export default function TruthSpectrumDemo() {
  return (
    <Card className="w-full max-w-4xl mx-auto p-6 shadow-lg">
      <CardHeader>
        <CardTitle className="text-2xl font-bold">Truth Spectrum in Action</CardTitle>
        <CardDescription>
          Observe how different statements are categorized across the truth-lie spectrum based on their confidence levels.
          Hover over the badges to see detailed explanations.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {demoTruths.map((demo, index) => (
          <div key={index} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 border rounded-lg">
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{demo.content}</p>
            </div>
            <div className="ml-0 sm:ml-4 mt-2 sm:mt-0 flex-shrink-0">
              <TruthSpectrumBadge
                confidence={demo.confidence}
                showPercentage={true}
                size="lg"
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
