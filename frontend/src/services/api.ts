// FindersKeepers v2 - API Service Layer

import type { 
  AgentSession, 
  AgentAction, 
  Document, 
  VectorSearchResult,
  SearchQuery,
  ApiResponse,
  SystemHealth,
  GraphNode,
  GraphEdge
} from '@/types';

class ApiService {
  private baseUrl: string;
  private controller: AbortController;

  constructor(baseUrl?: string) {
    // Use environment variable or fallback based on environment
    this.baseUrl = baseUrl || this.getApiUrl();
    this.controller = new AbortController();
  }

  private getApiUrl(): string {
    // Check if we're in a browser environment
    if (typeof window !== 'undefined') {
      // Browser environment - use localhost for development
      return import.meta.env.VITE_API_URL || 'http://localhost:8000';
    } else {
      // Server-side or Node environment - use container service name
      return 'http://fastapi:80';
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: this.controller.signal,
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // Agent Session endpoints
  async getSessions(params?: {
    page?: number;
    limit?: number;
    agent_type?: string;
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<ApiResponse<AgentSession[]>> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.agent_type) searchParams.append('agent_type', params.agent_type);
    if (params?.status) searchParams.append('status', params.status);
    
    const response: any = await this.request(`/api/diary/sessions/list?${searchParams}`);
    
    // Return sessions data directly from the new endpoint
    if (response.success && response.data) {
      return response;
    }
    
    return {
      success: false,
      data: [],
      message: 'Failed to retrieve sessions',
      timestamp: new Date().toISOString(),
    };
  }

  async getSession(sessionId: string): Promise<ApiResponse<AgentSession>> {
    return this.request(`/api/diary/sessions/${sessionId}`);
  }

  async getSessionActions(sessionId: string): Promise<ApiResponse<AgentAction[]>> {
    return this.request(`/api/diary/sessions/${sessionId}/actions`);
  }

  async createSession(session: Partial<AgentSession>): Promise<ApiResponse<AgentSession>> {
    return this.request('/api/diary/sessions', {
      method: 'POST',
      body: JSON.stringify(session),
    });
  }

  async terminateSession(sessionId: string): Promise<ApiResponse<AgentSession>> {
    return this.request(`/api/diary/sessions/${sessionId}/end`, {
      method: 'PUT',
    });
  }

  // Document Management endpoints
  async getDocuments(params?: {
    page?: number;
    limit?: number;
    search?: string;
    format?: string;
    project?: string;
    tags?: string[];
    file_type?: string;
  }): Promise<ApiResponse<{ documents: Document[]; total_pages: number; stats: any }>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && key !== 'tags') {
          searchParams.append(key, value.toString());
        }
      });
      if (params.tags) {
        params.tags.forEach(tag => searchParams.append('tags', tag));
      }
    }
    
    // Temporarily use stats endpoint since /api/docs has conflicts
    return this.request(`/api/stats/documents`);
  }

  async getDocument(documentId: string): Promise<ApiResponse<Document>> {
    return this.request(`/api/docs/by-id/${documentId}`);
  }

  async uploadDocument(fileOrFormData: File | FormData, metadata?: Record<string, any>, signal?: AbortSignal): Promise<ApiResponse<Document>> {
    let formData: FormData;
    
    if (fileOrFormData instanceof FormData) {
      formData = fileOrFormData;
    } else {
      formData = new FormData();
      formData.append('file', fileOrFormData);
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }
    }

    return fetch(`${this.baseUrl}/api/v1/ingestion/single`, {
      method: 'POST',
      body: formData,
      signal: signal || this.controller.signal,
    }).then(async response => {
      const data = await response.json();
      
      // The ingestion API returns a different format than expected
      // Transform the response to match our ApiResponse interface
      if (response.ok && data.status === 'queued') {
        return {
          success: true,
          data: data,
          message: data.message || 'File uploaded successfully',
          timestamp: new Date().toISOString()
        };
      } else if (response.ok) {
        // Handle other successful statuses
        return {
          success: true,
          data: data,
          message: data.message || 'Upload completed',
          timestamp: new Date().toISOString()
        };
      } else {
        // Handle HTTP errors
        return {
          success: false,
          error: data.error || 'Upload failed',
          message: data.message || `HTTP ${response.status}: ${response.statusText}`,
          timestamp: new Date().toISOString()
        };
      }
    });
  }

  async deleteDocument(documentId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/docs/${documentId}`, {
      method: 'DELETE',
    });
  }

  async searchDocuments(params: {
    query: string;
    limit?: number;
    project?: string;
  }): Promise<ApiResponse<Document[]>> {
    const searchParams = new URLSearchParams();
    searchParams.append('search', params.query);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.project) searchParams.append('project', params.project);
    
    return this.request(`/api/stats/documents?${searchParams}`);
  }

  // Vector Search endpoints
  async vectorSearch(query: SearchQuery): Promise<ApiResponse<VectorSearchResult[]>> {
    return this.request('/api/search/vector', {
      method: 'POST',
      body: JSON.stringify(query),
    });
  }

  async semanticSearch(query: string, limit = 10): Promise<ApiResponse<VectorSearchResult[]>> {
    return this.request('/api/search/semantic', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  // Knowledge Graph endpoints
  async getGraphNodes(params?: {
    type?: string;
    limit?: number;
  }): Promise<ApiResponse<GraphNode[]>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/knowledge/nodes?${searchParams}`);
  }

  async getGraphEdges(nodeId?: string): Promise<ApiResponse<GraphEdge[]>> {
    const endpoint = nodeId 
      ? `/api/knowledge/edges?node_id=${nodeId}`
      : '/api/knowledge/edges';
    
    return this.request(endpoint);
  }

  async queryKnowledgeGraph(query: string): Promise<ApiResponse<{ nodes: GraphNode[]; edges: GraphEdge[] }>> {
    return this.request('/api/knowledge/query', {
      method: 'POST',
      body: JSON.stringify({ question: query }),
    });
  }

  // System Health endpoints
  async getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
    try {
      // Load only health endpoint for faster response
      const healthResponse = await this.request('/health');
      
      if (healthResponse) {
        // Transform the data to match our SystemHealth interface
        const containerDetails = null; // Skip stats for faster loading
        
        const transformedHealth: SystemHealth = {
          status: healthResponse.status || 'unknown',
          services: {
            fastapi: {
              status: healthResponse.services?.api || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_fastapi', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_fastapi', containerDetails) : undefined
            },
            postgres: {
              status: healthResponse.services?.postgres || 'unknown', 
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_postgres', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_postgres', containerDetails) : undefined
            },
            neo4j: {
              status: healthResponse.services?.neo4j || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_neo4j', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_neo4j', containerDetails) : undefined
            },
            qdrant: {
              status: healthResponse.services?.qdrant || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_qdrant', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_qdrant', containerDetails) : undefined
            },
            redis: {
              status: healthResponse.services?.redis || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_redis', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_redis', containerDetails) : undefined
            },
            ollama: {
              status: healthResponse.services?.ollama || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_ollama', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_ollama', containerDetails) : undefined
            },
            n8n: {
              status: healthResponse.services?.n8n || 'unknown',
              response_time_ms: containerDetails ? this.getServiceResponseTime('fk2_n8n', containerDetails) : undefined,
              uptime_percentage: containerDetails ? this.calculateUptime('fk2_n8n', containerDetails) : undefined
            }
          },
          local_llm: healthResponse.local_llm,
          last_check: healthResponse.timestamp || new Date().toISOString()
        };

        return {
          success: true,
          data: transformedHealth,
          timestamp: new Date().toISOString()
        };
      }
      
      return healthResponse;
    } catch (error) {
      console.error('Failed to get system health:', error);
      throw error;
    }
  }

  private getServiceResponseTime(serviceName: string, containers?: any[]): number | undefined {
    if (!containers) return undefined;
    const container = containers.find(c => c.name === serviceName);
    // Simulate response time based on CPU usage (this is a placeholder)
    return container ? Math.round(50 + (container.cpu_percent * 10)) : undefined;
  }

  private calculateUptime(serviceName: string, containers?: any[]): number | undefined {
    if (!containers) return undefined;
    const container = containers.find(c => c.name === serviceName);
    // Assume good uptime if container is running (this is a placeholder)
    return container?.status === 'running' ? 99.5 + Math.random() * 0.5 : 0;
  }

  private getContainerStatus(serviceName: string, containers?: any[]): string | undefined {
    if (!containers) return undefined;
    const container = containers.find(c => c.name === serviceName);
    return container?.status === 'running' ? 'up' : 'down';
  }

  async getServiceHealth(service: string): Promise<ApiResponse<any>> {
    return this.request(`/health/${service}`);
  }

  // Statistics endpoints
  async getSessionStats(timeframe?: '1h' | '24h' | '7d' | '30d'): Promise<ApiResponse<any>> {
    const params = timeframe ? `?timeframe=${timeframe}` : '';
    return this.request(`/api/stats/sessions${params}`);
  }

  async getDocumentStats(): Promise<ApiResponse<any>> {
    return this.request('/api/stats/documents');
  }

  async getPerformanceMetrics(): Promise<ApiResponse<any>> {
    return this.request('/api/stats/performance');
  }

  // Utility methods
  abort(): void {
    this.controller.abort();
    this.controller = new AbortController();
  }

  // Streaming endpoints
  async *streamSessions(): AsyncGenerator<AgentSession, void, unknown> {
    const response = await fetch(`${this.baseUrl}/api/diary/sessions/stream`, {
      signal: this.controller.signal,
    });

    if (!response.body) {
      throw new Error('Stream not supported');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data;
            } catch (e) {
              console.warn('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;