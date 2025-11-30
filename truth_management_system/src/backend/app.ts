// src/backend/app.ts
import express from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import truthRoutes from './routes/truthRoutes';
import authRoutes from './routes/authRoutes'; // Import auth routes

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(bodyParser.json());

app.get('/', (req, res) => {
  res.send('Truth Service Backend is running!');
});

app.use('/api/auth', authRoutes); // Add authentication routes
app.use('/api/truths', truthRoutes); // Truth routes might have their own middleware for specific endpoints

app.listen(PORT, () => {
  console.log(`Truth Service Backend listening on port ${PORT}`);
});