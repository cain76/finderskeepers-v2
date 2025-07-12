// API Response Types for Dashboard Real-Time Data

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  completed_sessions: number;
  average_duration: number;
  actions_per_session: number;
  timeline: Array<{
    hour: string;
    count: number;
  }>;
  by_agent_type: Record<string, number>;
}

export interface DocumentStats {
  total_documents: number;
  total_chunks: number;
  vectors_stored: number;
  storage_used_mb: number;
  by_document_type: Record<string, number>;
  by_project: Record<string, number>;
  ingestion_timeline: Array<{
    date: string;
    count: number;
  }>;
}

export interface PerformanceStats {
  response_times: {
    average: number;
    p95: number;
    p99: number;
  };
  error_rate: number;
  database_connections: {
    active: number;
    total: number;
  };
  system_resources: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
  ollama_stats?: {
    models_loaded: number;
    requests_per_minute: number;
  };
}

export interface SystemStats {
  containers: Array<{
    name: string;
    status: string;
    cpu_percent: number;
    memory_usage: number;
    memory_limit: number;
    memory_percent: number;
    disk_usage: number;
    network_io: {
      bytes_recv: number;
      bytes_sent: number;
    };
  }>;
  host_system: {
    cpu_percent: number;
    memory: {
      total: number;
      available: number;
      percent: number;
    };
    disk: {
      total: number;
      used: number;
      free: number;
      percent: number;
    };
  };
}

export interface HealthStatus {
  status: string;
  uptime: string;
  timestamp: string;
  services: {
    postgres: {
      status: string;
      connection_time: number;
    };
    neo4j: {
      status: string;
      connection_time: number;
    };
    redis: {
      status: string;
      connection_time: number;
    };
    qdrant: {
      status: string;
      connection_time: number;
    };
  };
}

export interface DashboardData {
  sessions: SessionStats;
  documents: DocumentStats;
  performance: PerformanceStats;
  system: SystemStats;
  health: HealthStatus;
}

export interface LoadingStates {
  initial: boolean;
  sessions: boolean;
  documents: boolean;
  performance: boolean;
  system: boolean;
  health: boolean;
}

export interface ErrorStates {
  sessions: string | null;
  documents: string | null;
  performance: string | null;
  system: string | null;
  health: string | null;
}