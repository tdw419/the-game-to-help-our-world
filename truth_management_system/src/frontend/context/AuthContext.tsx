// src/frontend/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { AuthApiClient } from '../services/AuthApiClient';
import { UserDTO, LoginRequestDTO, RegisterRequestDTO, AuthResponseDTO } from '../interfaces/auth-dtos';
import { useToast } from ' @/components/ui/use-toast';

interface AuthContextType {
  user: UserDTO | null;
  token: string | null;
  login: (credentials: LoginRequestDTO) => Promise<void>;
  register: (userData: RegisterRequestDTO) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserDTO | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true); // Loading for initial token check
  const { toast } = useToast();

  useEffect(() => {
    // Attempt to load token and user from localStorage on initial render
    const storedToken = localStorage.getItem('jwtToken');
    const storedUser = localStorage.getItem('authUser');
    if (storedToken && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
        setToken(storedToken);
      } catch (e) {
        console.error("Failed to parse stored user or token", e);
        logout(); // Clear invalid data
      }
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (credentials: LoginRequestDTO) => {
    setLoading(true);
    try {
      const response: AuthResponseDTO = await AuthApiClient.login(credentials);
      setUser(response.user);
      setToken(response.token);
      localStorage.setItem('jwtToken', response.token);
      localStorage.setItem('authUser', JSON.stringify(response.user));
      toast({
        title: 'Login Successful',
        description: `Welcome, ${response.user.username}!`,
      });
    } catch (error: any) {
      toast({
        title: 'Login Failed',
        description: error.message,
        variant: 'destructive',
      });
      throw error; // Re-throw to allow component to handle specific errors
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const register = useCallback(async (userData: RegisterRequestDTO) => {
    setLoading(true);
    try {
      const newUser: UserDTO = await AuthApiClient.register(userData);
      toast({
        title: 'Registration Successful',
        description: `User ${newUser.username} created. Please log in.`,
      });
    } catch (error: any) {
      toast({
        title: 'Registration Failed',
        description: error.message,
        variant: 'destructive',
      });
      throw error;
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('jwtToken');
    localStorage.removeItem('authUser');
    toast({
      title: 'Logged Out',
      description: 'You have been logged out successfully.',
    });
  }, [toast]);

  const isAuthenticated = !!user && !!token;

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isAuthenticated, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};