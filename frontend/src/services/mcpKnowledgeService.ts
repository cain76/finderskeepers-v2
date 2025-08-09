// MCP Knowledge Service - Interface to FK Knowledge Server
// This service provides vector search functionality using the MCP knowledge server

export interface McpSearchResult {
  content: string;
  score: number;
  document_id: string;
  chunk_id: number | string;
  metadata: Record<string, any>;
  preview?: string;
}

export interface McpSearchResponse {
  query: string;
  total_results: number;
  results: McpSearchResult[];
  search_params: {
    project?: string | null;
    tags?: string[] | null;
    limit: number;
    min_score: number;
  };
  embeddings_used: boolean;
  timestamp: string;
}

export interface McpSearchQuery {
  query: string;
  limit?: number;
  project?: string;
  tags?: string[];
  min_score?: number;
}

class McpKnowledgeService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('MCP Knowledge Server health check failed:', error);
      return false;
    }
  }

  async search(query: McpSearchQuery): Promise<McpSearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/knowledge/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(query),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Knowledge search failed:', error);
      throw new Error('Failed to search knowledge base. Check that the FastAPI backend is running and the /api/knowledge/search endpoint exists.');
    }
  }

  async getRelatedDocuments(documentId: string): Promise<McpSearchResult[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/knowledge/related/${documentId}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get related documents:', error);
      throw new Error('TODO: Implement /api/knowledge/related/{documentId} endpoint in FastAPI backend');
    }
  }

  async getEntityRelationships(entityId: string): Promise<any> {
    try {
      const response = await fetch(`${this.baseUrl}/api/knowledge/entities/${entityId}/relationships`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to get entity relationships:', error);
      throw new Error('TODO: Implement /api/knowledge/entities/{entityId}/relationships endpoint in FastAPI backend');
    }
  }
}

// Export singleton instance
export const mcpKnowledgeService = new McpKnowledgeService();
export default mcpKnowledgeService;
