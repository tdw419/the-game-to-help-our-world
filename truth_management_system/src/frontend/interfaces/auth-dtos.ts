// src/frontend/interfaces/auth-dtos.ts
// Re-defining DTOs for frontend clarity, assuming these would be in a shared lib or copied
export interface UserDTO {
  id: string;
  username: string;
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