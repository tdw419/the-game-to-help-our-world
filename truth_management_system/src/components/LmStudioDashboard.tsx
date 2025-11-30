import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import LmStudioPrompt from './LmStudioPrompt';
import ExecutionListComponent from './ExecutionListComponent';
import ExecutionDetailViewer from './ExecutionDetailViewer';

const LmStudioDashboard: React.FC = () => {
  return (
    <div className="flex flex-col md:flex-row gap-6 p-6">
      <Tabs defaultValue="simulate" className="w-full md:w-1/2">
        <TabsList>
          <TabsTrigger value="simulate">Simulate</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="simulate" className="mt-4">
          <LmStudioPrompt />
        </TabsContent>

        <TabsContent value="history" className="mt-4">
          <ExecutionListComponent />
        </TabsContent>
      </Tabs>

      <div className="w-full md:w-1/2">
        <ExecutionDetailViewer />
      </div>
    </div>
  );
};

export default LmStudioDashboard;
