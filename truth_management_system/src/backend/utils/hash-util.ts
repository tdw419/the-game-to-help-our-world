// src/backend/utils/hash-util.ts
import crypto from 'crypto';

export const generateContentHash = (content: string): string => {
  return crypto.createHash('sha256').update(content).digest('hex');
};