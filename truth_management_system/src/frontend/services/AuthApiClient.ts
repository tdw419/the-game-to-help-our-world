// src/frontend/services/AuthApiClient.ts
import { RegisterRequestDTO, LoginRequestDTO, AuthResponseDTO } from '../interfaces/auth-dtos';

const AUTH_API_BASE_URL = 'http://localhost:3000/api/auth';

export const AuthApiClient = {
  register: async (userData: RegisterRequestDTO): Promise<UserDTO> => {
    const response = await fetch(`${AUTH_API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Registration failed: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },

  login: async (loginData: LoginRequestDTO): Promise<AuthResponseDTO> => {
    const response = await fetch(`${AUTH_API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(loginData),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`Login failed: ${errorData.message || response.statusText}`);
    }
    return response.json();
  },
};
