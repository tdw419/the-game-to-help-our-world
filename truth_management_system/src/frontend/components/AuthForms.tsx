// src/frontend/components/AuthForms.tsx
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from ' @/components/ui/card';
import { Button } from ' @/components/ui/button';
import { Input } from ' @/components/ui/input';
import { useAuth } from '../context/AuthContext';
import { RegisterRequestDTO, LoginRequestDTO } from '../interfaces/auth-dtos';

export const RegisterForm: React.FC = () => {
  const { register, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        await register({ username, password });
        setUsername('');
        setPassword('');
    } catch (error) {
        // Error handled by useAuth's toast
    }
  };

  return (
    <Card className="p-4">
      <CardTitle className="mb-4">Register</CardTitle>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </Button>
      </form>
    </Card>
  );
};

export const LoginForm: React.FC = () => {
  const { login, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        await login({ username, password });
        setUsername('');
        setPassword('');
    } catch (error) {
        // Error handled by useAuth's toast
    }
  };

  return (
    <Card className="p-4">
      <CardTitle className="mb-4">Login</CardTitle>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          disabled={loading}
        />
        <Input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Logging In...' : 'Login'}
        </Button>
      </form>
    </Card>
  );
};