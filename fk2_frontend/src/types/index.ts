// Core types for FindersKeepers v2 Frontend

export interface AgentSession {
  id: string;
  client_id: string;
  session_start: string;
  session_end?: string;
  context_summary?: string;
  total_actions: number;
  status: 'active' | 'ended' | 'error';
  metadata?: Record<string, any>;
}

export interface AgentAction {
  id: string;
  session_id: string;
  action_type: string;
  content: string;
  metadata?: Record<string, any>;
  timestamp: string;
  file_path?: string;
}

export interface DocumentIngest {
  id: string;
  title: string;
  file_path: string;
  project: string;
  format: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: string;
  updated_at: string;
  embedding_status?: string;
  chunk_count?: number;
}

export interface KnowledgeQuery {
  id: string;
  query_text: string;
  response?: string;
  context_used?: any[];
  confidence_score?: number;
  timestamp: string;
}

export interface ConnectionStatus {
  api: 'connected' | 'disconnected' | 'error';
  websocket: 'connected' | 'disconnected' | 'connecting' | 'error';
  database: 'connected' | 'disconnected' | 'error';
}

export interface SystemStats {
  total_sessions: number;
  active_sessions: number;
  total_documents: number;
  unprocessed_documents: number;
  total_actions: number;
  embedding_queue_size: number;
  processing_status: string;
}

export interface WebSocketMessage {
  type: 'chat' | 'knowledge_query' | 'chat_response' | 'knowledge_response' | 'typing' | 'online_status';
  message?: string;
  data?: any;
  timestamp: string;
  client_id: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Neo4jNode {
  id: string;
  labels: string[];
  properties: Record<string, any>;
}

export interface Neo4jRelationship {
  id: string;
  type: string;
  startNode: string;
  endNode: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Neo4jNode[];
  relationships: Neo4jRelationship[];
}

export interface VectorSearchResult {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
  document_id?: string;
  chunk_index?: number;
}

export interface ProcessingStats {
  documents_processed: number;
  documents_pending: number;
  documents_failed: number;
  embeddings_created: number;
  processing_rate: number;
  last_processing_time?: string;
}

// Component prop types
export interface DashboardCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'success';
  loading?: boolean;
}

export interface SessionTableProps {
  sessions: AgentSession[];
  onSessionSelect: (session: AgentSession) => void;
  loading?: boolean;
}

export interface DocumentUploadProps {
  onUpload: (files: FileList) => void;
  accept?: string;
  multiple?: boolean;
  project?: string;
}

export interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isConnected: boolean;
  isTyping?: boolean;
}

export interface KnowledgeGraphProps {
  data: GraphData;
  onNodeSelect: (node: Neo4jNode) => void;
  onRelationshipSelect: (relationship: Neo4jRelationship) => void;
  layout?: 'hierarchical' | 'force' | 'circular';
}

export interface VectorSearchProps {
  onSearch: (query: string) => void;
  results: VectorSearchResult[];
  loading?: boolean;
}

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_next: boolean;
  has_prev: boolean;
}