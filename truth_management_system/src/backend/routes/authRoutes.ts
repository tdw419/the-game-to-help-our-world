import { Router } from 'express';
import { userService } from '../services/userService';
import { RegisterRequestDTO, LoginRequestDTO } from '../interfaces/auth-dtos';

const router = Router();

router.post('/register', async (req, res) => {
  try {
    const userData: RegisterRequestDTO = req.body;
    if (!userData.username || !userData.password) {
      return res.status(400).json({ message: 'Username and password are required.' });
    }
    const user = await userService.register(userData);
    res.status(201).json(user);
  } catch (error: any) {
    res.status(400).json({ message: error.message });
  }
});

router.post('/login', async (req, res) => {
  try {
    const loginData: LoginRequestDTO = req.body;
    if (!loginData.username || !loginData.password) {
      return res.status(400).json({ message: 'Username and password are required.' });
    }
    const authResponse = await userService.login(loginData);
    res.status(200).json(authResponse);
  } catch (error: any) {
    res.status(401).json({ message: error.message });
  }
});

export default router;