import React from 'react';
import { Button } from '@/components/ui/button';

const Greeting: React.FC = () => {
  const [message, setMessage] = React.useState<string>('Hello!');

  const changeGreeting = () => {
    setMessage('Welcome to the Vector Universe!');
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-4xl font-bold mb-4">{message}</h1>
      <Button onClick={changeGreeting}>Change Greeting</Button>
    </div>
  );
};

export default Greeting;
