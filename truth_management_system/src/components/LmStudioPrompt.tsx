import React, { useState } from 'react';
import { Button, Input, Textarea, Label, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui';
import { Loader2, Send } from 'lucide-react';

const LmStudioPrompt: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateText = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const token = 'token_your_username'; // Replace with actual token retrieval logic
      const response = await fetch('http://localhost:8001/llm/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token,
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate text.');
      }

      const data = await response.json();
      setResponse(data.generated_text);
    } catch (err) {
      setError(err.message || 'An error occurred while generating text.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Prompt LM Studio</CardTitle>
        <CardDescription>Enter a prompt to generate text using LM Studio.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid w-full gap-4">
          <Label htmlFor="prompt">Prompt</Label>
          <Textarea
            id="prompt"
            placeholder="Enter your prompt here..."
            rows={4}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          onClick={handleGenerateText}
          disabled={loading || !prompt.trim()}
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" /> Generate Text
            </>
          )}
        </Button>
      </CardFooter>
      {response && (
        <CardContent>
          <div className="bg-gray-100 p-4 rounded">
            <p>{response}</p>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default LmStudioPrompt;
