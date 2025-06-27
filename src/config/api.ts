// API configuration
const getApiUrl = () => {
  // In development, use empty string to leverage Vite proxy
  if (import.meta.env.DEV) {
    return '';
  }
  
  // In webcontainer, we need to use the current host
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
    const host = window.location.hostname;
    // Use port 8000 for backend
    return `${protocol}//${host}:8000`;
  }
  return import.meta.env.VITE_API_URL || 'http://localhost:8000';
};

const getWsUrl = () => {
  // In development, use empty string to leverage Vite proxy
  if (import.meta.env.DEV) {
    return '/ws';
  }
  
  // In webcontainer, we need to use the current host
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // Use port 8000 for backend WebSocket
    return `${protocol}//${host}:8000`;
  }
  return import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
};

export const API_URL = getApiUrl();
export const WS_URL = getWsUrl();