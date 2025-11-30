// src/backend/interfaces/auth-dtos.ts
// New DTOs for Authentication
export interface UserDTO {
  id: string;
  username: string;
  // passwordHash: string; // Should not be exposed in DTO
}

export interface RegisterRequestDTO {
  username: string;
  password: string;
}

export interface LoginRequestDTO {
  username: string;
  password: string;
}

export interface AuthResponseDTO {
  user: UserDTO;
  token: string;
}