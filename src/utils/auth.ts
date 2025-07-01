import dotenv from 'dotenv';

dotenv.config();

export function getOptionalHeaders(): Record<string, string> {
  const apiKey = process.env.COMPOSER_API_KEY;
  const secretKey = process.env.COMPOSER_SECRET_KEY;
  
  if (!apiKey || !secretKey) {
    return {};
  }
  
  return {
    'x-api-key-id': apiKey,
    'Authorization': `Bearer ${secretKey}`
  };
}

export function getRequiredHeaders(): Record<string, string> {
  const apiKey = process.env.COMPOSER_API_KEY;
  const secretKey = process.env.COMPOSER_SECRET_KEY;
  
  if (!apiKey || !secretKey) {
    throw new Error('COMPOSER_API_KEY and COMPOSER_SECRET_KEY must be set');
  }
  
  return {
    'x-api-key-id': apiKey,
    'Authorization': `Bearer ${secretKey}`
  };
} 