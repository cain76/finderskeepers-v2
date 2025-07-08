// FindersKeepers v2 - Core Types

// Agent Session Types
export interface AgentSession {
  id: string;
  agent_type: 'claude' | 'gpt' | 'local' | 'custom';
  session_start: string;
  session_end?: string;
  status: 'active' | 'completed' | 'terminated' | 'error';
  context: Record<string, any>;
  total_actions: number;
  total_files_modified: number;
  performance_metrics: {
    avg_response_time: number;
    total_tokens_used?: number;
    error_count: number;
  };
  metadata: {
    project_name?: string;
    session_type: string;
    tags: string[];
  };
}

// Agent Action Types
export interface AgentAction {
  id: string;
  session_id: string;
  action_type: 'file_read' | 'file_write' | 'command_execute' | 'api_call' | 'search';
  timestamp: string;
  duration_ms: number;
  success: boolean;
  details: Record<string, any>;
  files_affected: string[];
  error_message?: string;
}

// Knowledge Base Types
export interface Document {
  id: string;
  title: string;
  content?: string;
  format: string;
  project: string;
  tags: string[];
  file_path: string;
  file_size: number;
  metadata: DocumentMetadata;
  chunk_count?: number;
  vector_stored?: boolean;
  created_at: string;
  updated_at: string;
}

export interface DocumentMetadata {
  source_file?: string;
  file_type?: string;
  file_size?: number;
  page_count?: number;
  author?: string;
  created_date?: string;
  project?: string;
  tags?: string[];
  version?: string;
  type?: string;
  pdf_metadata?: Record<string, any>;
}

// Vector Search Types
export interface VectorSearchResult {
  document_id: string;
  chunk_id: string;
  content: string;
  similarity_score: number;
  metadata: DocumentMetadata;
  highlight?: string;
}

export interface SearchQuery {
  query: string;
  limit?: number;
  threshold?: number;
  filters?: Record<string, any>;
}

// Knowledge Graph Types
export interface GraphNode {
  id: string;
  label?: string;
  name?: string;
  title?: string;
  type: 'document' | 'entity' | 'concept' | 'session' | 'project';
  properties: Record<string, any>;
  connections?: number;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'references' | 'contains' | 'relates_to' | 'created_by';
  relationship: string;
  weight?: number;
  properties?: Record<string, any>;
}

// Real-time Events
export interface RealtimeEvent {
  type: 'session_start' | 'session_end' | 'action_completed' | 'document_ingested' | 'system_alert';
  timestamp: string;
  data: Record<string, any>;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    current_page: number;
    per_page: number;
    total_items: number;
    total_pages: number;
  };
}

// System Health Types
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: {
    fastapi: ServiceStatus;
    postgres: ServiceStatus;
    neo4j: ServiceStatus;
    qdrant: ServiceStatus;
    redis: ServiceStatus;
    ollama: ServiceStatus;
    n8n: ServiceStatus;
  };
  local_llm?: {
    enabled: boolean;
    healthy: boolean;
    embedding_model: string;
    chat_model: string;
  };
  last_check: string;
}

export interface ServiceStatus {
  status: 'up' | 'down' | 'degraded';
  response_time_ms?: number;
  last_error?: string;
  uptime_percentage?: number;
}

// Configuration Types
export interface AppConfig {
  apiBaseUrl: string;
  wsUrl: string;
  refreshInterval: number;
  features: {
    realTimeUpdates: boolean;
    vectorSearch: boolean;
    knowledgeGraph: boolean;
    sessionMonitoring: boolean;
  };
}

// UI State Types
export interface DashboardState {
  activeView: 'overview' | 'sessions' | 'documents' | 'monitoring';
  filters: {
    dateRange: [string, string] | null;
    agentTypes: string[];
    status: string[];
  };
  realTimeEnabled: boolean;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}