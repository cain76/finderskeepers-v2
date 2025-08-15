import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Create axios instance with default configuration
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API endpoint functions
export const apiService = {
  // Health check
  health: () => api.get('/health'),
  
  // MCP endpoints
  mcp: {
    health: () => api.get('/api/mcp/health'),
    sessions: {
      recent: () => api.get('/api/mcp/sessions/recent'),
      create: (data: any) => api.post('/api/mcp/session/start', data),
      end: (sessionId: string, data: any) => api.post(`/api/mcp/session/end/${sessionId}`, data),
    },
    actions: (data: any) => api.post('/api/mcp/action', data),
  },
  
  // Diary API endpoints
  diary: {
    sessions: () => api.get('/api/diary/sessions'),
    actions: () => api.get('/api/diary/actions'),
    search: (query: string) => api.get(`/api/diary/search?q=${encodeURIComponent(query)}`),
  },
  
  // Document endpoints
  documents: {
    list: () => api.get('/api/docs'),
    ingest: (data: FormData) => api.post('/api/docs/ingest', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    context: (project?: string) => api.get(`/api/docs/context${project ? `?project=${project}` : ''}`),
  },
  
  // Knowledge endpoints
  knowledge: {
    query: (data: any) => api.post('/api/knowledge/query', data),
  },
  
  // Admin endpoints
  admin: {
    stats: () => api.get('/api/admin/processing-stats'),
    bulkEmbedding: () => api.post('/api/admin/bulk-embedding'),
    queueMaintenance: () => api.post('/api/admin/queue-maintenance'),
  },
};

// WebSocket connection helper
export const createWebSocketConnection = (clientId: string) => {
  const wsUrl = `${WS_URL.replace(/^http/, 'ws').replace(/^https/, 'wss')}/ws/${clientId}`;
  return new WebSocket(wsUrl);
};

export default apiService;