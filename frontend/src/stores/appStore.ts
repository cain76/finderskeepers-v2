// FindersKeepers v2 - Main Application Store

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import type { 
  DashboardState, 
  AppConfig, 
  SystemHealth, 
  AgentSession,
  AppError
} from '@/types';

export type ThemeMode = 'light' | 'dark' | 'system';

interface AppState {
  // Configuration
  config: AppConfig;
  
  // Theme Management
  theme: ThemeMode;
  resolvedTheme: 'light' | 'dark';
  
  // UI State
  dashboard: DashboardState;
  
  // System Health
  systemHealth: SystemHealth | null;
  
  // Loading States
  isLoading: {
    sessions: boolean;
    documents: boolean;
    health: boolean;
    search: boolean;
  };
  
  // Error Handling
  errors: AppError[];
  
  // Connection Status
  connectionStatus: {
    api: 'connected' | 'disconnected' | 'error';
    websocket: 'connected' | 'disconnected' | 'error';
    lastCheck: string | null;
  };

  // Real-time Data
  activeSessions: AgentSession[];
  recentActivity: any[];
  
  // Actions
  setConfig: (config: Partial<AppConfig>) => void;
  setTheme: (theme: ThemeMode) => void;
  toggleTheme: () => void;
  updateDashboard: (updates: Partial<DashboardState>) => void;
  setSystemHealth: (health: SystemHealth) => void;
  setLoading: (key: keyof AppState['isLoading'], value: boolean) => void;
  addError: (error: AppError) => void;
  removeError: (errorId: string) => void;
  clearErrors: () => void;
  setConnectionStatus: (service: 'api' | 'websocket', status: 'connected' | 'disconnected' | 'error') => void;
  setActiveSessions: (sessions: AgentSession[]) => void;
  addRecentActivity: (activity: any) => void;
  reset: () => void;
}

// System preference detection helper
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
};

// Resolve theme helper
const resolveTheme = (theme: ThemeMode): 'light' | 'dark' => 
  theme === 'system' ? getSystemTheme() : theme;

const initialState = {
  config: {
    apiBaseUrl: '/api',
    wsUrl: 'ws://localhost:8000',
    refreshInterval: 30000, // 30 seconds
    features: {
      realTimeUpdates: true,
      vectorSearch: true,
      knowledgeGraph: true,
      sessionMonitoring: true,
    },
  },
  
  theme: 'light' as ThemeMode,
  resolvedTheme: 'light' as const,
  
  dashboard: {
    activeView: 'overview' as const,
    filters: {
      dateRange: null,
      agentTypes: [],
      status: [],
    },
    realTimeEnabled: true,
  },
  
  systemHealth: null,
  
  isLoading: {
    sessions: false,
    documents: false,
    health: false,
    search: false,
  },
  
  errors: [],
  
  connectionStatus: {
    api: 'disconnected' as const,
    websocket: 'disconnected' as const,
    lastCheck: null,
  },
  
  activeSessions: [],
  recentActivity: [],
};

export const useAppStore = create<AppState>()(
  devtools(
    subscribeWithSelector((set) => ({
      ...initialState,
      
      setConfig: (config) =>
        set((state) => ({
          config: { ...state.config, ...config },
        }), false, 'setConfig'),
      
      setTheme: (theme) =>
        set((state) => ({
          theme,
          resolvedTheme: resolveTheme(theme),
        }), false, 'setTheme'),
      
      toggleTheme: () =>
        set((state) => {
          const newTheme = state.resolvedTheme === 'dark' ? 'light' : 'dark';
          return {
            theme: newTheme,
            resolvedTheme: newTheme,
          };
        }, false, 'toggleTheme'),
      
      updateDashboard: (updates) =>
        set((state) => ({
          dashboard: { ...state.dashboard, ...updates },
        }), false, 'updateDashboard'),
      
      setSystemHealth: (health) =>
        set({ systemHealth: health }, false, 'setSystemHealth'),
      
      setLoading: (key, value) =>
        set((state) => ({
          isLoading: { ...state.isLoading, [key]: value },
        }), false, 'setLoading'),
      
      addError: (error) =>
        set((state: AppState) => ({
          errors: [error, ...state.errors].slice(0, 10), // Keep last 10 errors
        }), false, 'addError'),
      
      removeError: (errorId) =>
        set((state) => ({
          errors: state.errors.filter(error => error.code !== errorId),
        }), false, 'removeError'),
      
      clearErrors: () =>
        set({ errors: [] }, false, 'clearErrors'),
      
      setConnectionStatus: (service, status) =>
        set((state) => ({
          connectionStatus: {
            ...state.connectionStatus,
            [service]: status,
            lastCheck: new Date().toISOString(),
          },
        }), false, 'setConnectionStatus'),
      
      setActiveSessions: (sessions) =>
        set({ activeSessions: sessions }, false, 'setActiveSessions'),
      
      addRecentActivity: (activity) =>
        set((state) => ({
          recentActivity: [
            { ...activity, timestamp: new Date().toISOString() },
            ...state.recentActivity
          ].slice(0, 50), // Keep last 50 activities
        }), false, 'addRecentActivity'),
      
      reset: () =>
        set(initialState, false, 'reset'),
    })),
    {
      name: 'finderskeepers-app-store',
      partialize: (state: AppState) => ({
        config: state.config,
        theme: state.theme,
        dashboard: state.dashboard,
      }),
    }
  )
);

// Selector hooks for specific parts of the store
export const useConfig = () => useAppStore((state) => state.config);
export const useTheme = () => useAppStore((state) => ({ 
  theme: state.theme, 
  resolvedTheme: state.resolvedTheme,
  setTheme: state.setTheme,
  toggleTheme: state.toggleTheme,
  isDark: state.resolvedTheme === 'dark',
  isLight: state.resolvedTheme === 'light',
  isSystem: state.theme === 'system'
}));
export const useDashboard = () => useAppStore((state) => state.dashboard);
export const useSystemHealth = () => useAppStore((state) => state.systemHealth);
export const useLoading = () => useAppStore((state) => state.isLoading);
export const useErrors = () => useAppStore((state) => state.errors);
export const useConnectionStatus = () => useAppStore((state) => state.connectionStatus);
export const useActiveSessions = () => useAppStore((state) => state.activeSessions);
export const useRecentActivity = () => useAppStore((state) => state.recentActivity);

// Computed selectors
export const useIsHealthy = () => 
  useAppStore((state) => 
    state.systemHealth?.status === 'healthy' && 
    state.connectionStatus.api === 'connected'
  );

export const useActiveSessionsCount = () =>
  useAppStore((state) => 
    state.activeSessions.filter(session => session.status === 'active').length
  );

export const useCriticalErrors = () =>
  useAppStore((state) => 
    state.errors.filter(error => error.severity === 'critical')
  );

export default useAppStore;