// API configuration
export const API_URL = 
  typeof window !== 'undefined' 
    ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1')
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

export const getApiUrl = (path: string): string => {
  const baseUrl = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;
  const apiPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${apiPath}`;
};

