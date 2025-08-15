import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type {
  AgentSession,
  AgentAction,
  DocumentIngest,
  ConnectionStatus,
  SystemStats,
  ChatMessage,
  WebSocketMessage,
  ProcessingStats
} from '@/types';

interface AppState {
  // Connection status
  connectionStatus: ConnectionStatus;
  setConnectionStatus: (status: Partial<ConnectionStatus>) => void;

  // Sessions
  sessions: AgentSession[];
  currentSession: AgentSession | null;
  setSessions: (sessions: AgentSession[]) => void;
  setCurrentSession: (session: AgentSession | null) => void;
  addSession: (session: AgentSession) => void;
  updateSession: (id: string, updates: Partial<AgentSession>) => void;

  // Actions
  actions: AgentAction[];
  setActions: (actions: AgentAction[]) => void;
  addAction: (action: AgentAction) => void;

  // Documents
  documents: DocumentIngest[];
  setDocuments: (documents: DocumentIngest[]) => void;
  addDocument: (document: DocumentIngest) => void;
  updateDocument: (id: string, updates: Partial<DocumentIngest>) => void;

  // System stats
  stats: SystemStats | null;
  setStats: (stats: SystemStats) => void;

  // Processing stats
  processingStats: ProcessingStats | null;
  setProcessingStats: (stats: ProcessingStats) => void;

  // Chat
  chatMessages: ChatMessage[];
  addChatMessage: (message: ChatMessage) => void;
  clearChatMessages: () => void;

  // WebSocket
  wsConnection: WebSocket | null;
  setWsConnection: (ws: WebSocket | null) => void;
  isTyping: boolean;
  setIsTyping: (typing: boolean) => void;

  // UI state
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  
  // Loading states
  loading: {
    sessions: boolean;
    documents: boolean;
    stats: boolean;
    chat: boolean;
  };
  setLoading: (key: keyof AppState['loading'], loading: boolean) => void;

  // Error handling
  errors: Array<{ id: string; message: string; timestamp: string }>;
  addError: (message: string) => void;
  removeError: (id: string) => void;
  clearErrors: () => void;
}

export const useAppStore = create<AppState>()(
  subscribeWithSelector((set, get) => ({
    // Initial state
    connectionStatus: {
      api: 'disconnected',
      websocket: 'disconnected',
      database: 'disconnected',
    },
    sessions: [],
    currentSession: null,
    actions: [],
    documents: [],
    stats: null,
    processingStats: null,
    chatMessages: [],
    wsConnection: null,
    isTyping: false,
    sidebarOpen: true,
    currentPage: 'dashboard',
    loading: {
      sessions: false,
      documents: false,
      stats: false,
      chat: false,
    },
    errors: [],

    // Actions
    setConnectionStatus: (status) =>
      set((state) => ({
        connectionStatus: { ...state.connectionStatus, ...status },
      })),

    setSessions: (sessions) => set({ sessions }),
    setCurrentSession: (session) => set({ currentSession: session }),
    addSession: (session) =>
      set((state) => ({ sessions: [session, ...state.sessions] })),
    updateSession: (id, updates) =>
      set((state) => ({
        sessions: state.sessions.map((session) =>
          session.id === id ? { ...session, ...updates } : session
        ),
        currentSession:
          state.currentSession?.id === id
            ? { ...state.currentSession, ...updates }
            : state.currentSession,
      })),

    setActions: (actions) => set({ actions }),
    addAction: (action) =>
      set((state) => ({ actions: [action, ...state.actions] })),

    setDocuments: (documents) => set({ documents }),
    addDocument: (document) =>
      set((state) => ({ documents: [document, ...state.documents] })),
    updateDocument: (id, updates) =>
      set((state) => ({
        documents: state.documents.map((doc) =>
          doc.id === id ? { ...doc, ...updates } : doc
        ),
      })),

    setStats: (stats) => set({ stats }),
    setProcessingStats: (processingStats) => set({ processingStats }),

    addChatMessage: (message) =>
      set((state) => ({ chatMessages: [...state.chatMessages, message] })),
    clearChatMessages: () => set({ chatMessages: [] }),

    setWsConnection: (ws) => set({ wsConnection: ws }),
    setIsTyping: (typing) => set({ isTyping: typing }),

    setSidebarOpen: (open) => set({ sidebarOpen: open }),
    setCurrentPage: (page) => set({ currentPage: page }),

    setLoading: (key, loading) =>
      set((state) => ({
        loading: { ...state.loading, [key]: loading },
      })),

    addError: (message) =>
      set((state) => ({
        errors: [
          ...state.errors,
          {
            id: Date.now().toString(),
            message,
            timestamp: new Date().toISOString(),
          },
        ],
      })),
    removeError: (id) =>
      set((state) => ({
        errors: state.errors.filter((error) => error.id !== id),
      })),
    clearErrors: () => set({ errors: [] }),
  }))
);

// Selectors
export const useConnectionStatus = () => useAppStore((state) => state.connectionStatus);
export const useSessions = () => useAppStore((state) => state.sessions);
export const useCurrentSession = () => useAppStore((state) => state.currentSession);
export const useDocuments = () => useAppStore((state) => state.documents);
export const useStats = () => useAppStore((state) => state.stats);
export const useProcessingStats = () => useAppStore((state) => state.processingStats);
export const useChatMessages = () => useAppStore((state) => state.chatMessages);
export const useIsTyping = () => useAppStore((state) => state.isTyping);
export const useErrors = () => useAppStore((state) => state.errors);
export const useLoading = () => useAppStore((state) => state.loading);

export default useAppStore;