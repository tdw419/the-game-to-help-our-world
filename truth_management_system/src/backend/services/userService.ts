import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { UserDTO, RegisterRequestDTO, LoginRequestDTO, AuthResponseDTO } from '../interfaces/auth-dtos';

// Extend Request type to include user
declare global {
  namespace Express {
    interface Request {
      user?: UserDTO;
    }
  }
}

// In-memory store for users (for demonstration)
const users: { [id: string]: { id: string; username: string; passwordHash: string } } = {};

// JWT Secret (should be in environment variables in production)
const JWT_SECRET = process.env.JWT_SECRET || 'supersecretjwtkey';
const JWT_EXPIRES_IN = '1h';

export const userService = {
  register: async (userData: RegisterRequestDTO): Promise<UserDTO> => {
    if (Object.values(users).some(user => user.username === userData.username)) {
      throw new Error('Username already exists.');
    }

    const id = uuidv4();
    const passwordHash = await bcrypt.hash(userData.password, 10);

    const newUser = { id, username: userData.username, passwordHash };
    users[id] = newUser;

    console.log('Registered user:', { id: newUser.id, username: newUser.username });
    return { id: newUser.id, username: newUser.username };
  },

  login: async (loginData: LoginRequestDTO): Promise<AuthResponseDTO> => {
    const user = Object.values(users).find(u => u.username === loginData.username);
    if (!user) {
      throw new Error('Invalid credentials.');
    }

    const isPasswordValid = await bcrypt.compare(loginData.password, user.passwordHash);
    if (!isPasswordValid) {
      throw new Error('Invalid credentials.');
    }

    const token = jwt.sign({ id: user.id, username: user.username }, JWT_SECRET, {
      expiresIn: JWT_EXPIRES_IN,
    });

    console.log('User logged in:', { id: user.id, username: user.username });
    return { user: { id: user.id, username: user.username }, token };
  },

  getUserById: (id: string): UserDTO | undefined => {
    const user = users[id];
    return user ? { id: user.id, username: user.username } : undefined;
  },
};