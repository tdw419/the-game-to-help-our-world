import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

import { truthApiClient, TruthLedgerEntry } from '@/services/TruthApiClient';

export default function TruthApiTestComponent() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TruthLedgerEntry[] | string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const testApi = async () => {
    setLoading(true);
    setData(null);
    setError(null);
    try {
      // Test getTruths
      const truths = await truthApiClient.getTruths();
      setData(truths);
      setError(null);
    } catch (err: any) {
      setError(`API Test Failed: ${err.message}`);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Run test automatically when component mounts for quick feedback
    testApi();
  }, []);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Truth API Client Test</CardTitle>
        <CardDescription>
          Verifies basic communication with the Truth API backend (or its mock).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Button onClick={testApi} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Testing API...
              </>
            ) : 'Run API Test'}
          </Button>

          {loading && <p className="text-blue-500">Loading...</p>}
          {error && <p className="text-red-500 font-bold">{error}</p>}

          {data && (
            <div className="mt-4">
              <h3 className="text-lg font-semibold">API Response:</h3>
              <pre className="mt-2 p-3 bg-gray-100 dark:bg-gray-800 rounded-md text-xs overflow-auto max-h-60">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
