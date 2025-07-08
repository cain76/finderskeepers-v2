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

  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl;
    this.controller = new AbortController();
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
    
    return this.request(`/api/docs?${searchParams}`);
  }

  async getDocument(documentId: string): Promise<ApiResponse<Document>> {
    return this.request(`/api/docs/${documentId}`);
  }

  async uploadDocument(fileOrFormData: File | FormData, metadata?: Record<string, any>): Promise<ApiResponse<Document>> {
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
      signal: this.controller.signal,
    }).then(response => response.json());
  }

  async deleteDocument(documentId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/docs/${documentId}`, {
      method: 'DELETE',
    });
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
      body: JSON.stringify({ query }),
    });
  }

  // System Health endpoints
  async getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.request('/health');
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