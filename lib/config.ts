// Configuration for the application
export const config = {
  // Backend API URL - change this to match your backend server
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Default settings
  DEFAULT_CHUNK_SIZE: 1000,
  DEFAULT_CHUNK_OVERLAP: 500,
  DEFAULT_SEARCH_K: 5,
} as const;

// Helper function to get the full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${config.API_BASE_URL}${endpoint}`;
};
