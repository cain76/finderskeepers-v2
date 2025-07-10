import { QdrantClient } from '@qdrant/js-client-rest';

export interface QdrantSearchResult {
  id: string | number;
  score: number;
  payload: Record<string, any>;
  vector?: number[];
}

export interface QdrantCollection {
  name: string;
  status: string;
  vectorsCount: number;
  indexedVectorsCount: number;
  pointsCount: number;
  segmentsCount: number;
}

export interface QdrantSearchQuery {
  query: string;
  collection: string;
  limit: number;
  threshold: number;
}

export interface QdrantPoint {
  id: string | number;
  payload: Record<string, any>;
  vector: number[];
}

class QdrantService {
  private client: QdrantClient;
  private readonly baseUrl: string;

  constructor() {
    // Use environment variables or defaults for Qdrant connection
    this.baseUrl = import.meta.env.VITE_QDRANT_URL || 'http://localhost:6333';
    this.client = new QdrantClient({ url: this.baseUrl });
  }

  // Get all collections
  async getCollections(): Promise<QdrantCollection[]> {
    try {
      const response = await this.client.getCollections();
      
      if (response.collections) {
        return response.collections.map(collection => ({
          name: collection.name,
          status: collection.status || 'unknown',
          vectorsCount: collection.vectors_count || 0,
          indexedVectorsCount: collection.indexed_vectors_count || 0,
          pointsCount: collection.points_count || 0,
          segmentsCount: collection.segments_count || 0
        }));
      }
      
      return [];
    } catch (error) {
      console.error('Failed to fetch collections:', error);
      throw new Error('Failed to fetch collections from Qdrant');
    }
  }

  // Get collection info
  async getCollectionInfo(collectionName: string): Promise<QdrantCollection | null> {
    try {
      const response = await this.client.getCollection(collectionName);
      
      if (response.result) {
        const collection = response.result;
        return {
          name: collectionName,
          status: collection.status || 'unknown',
          vectorsCount: collection.vectors_count || 0,
          indexedVectorsCount: collection.indexed_vectors_count || 0,
          pointsCount: collection.points_count || 0,
          segmentsCount: collection.segments_count || 0
        };
      }
      
      return null;
    } catch (error) {
      console.error(`Failed to fetch collection ${collectionName}:`, error);
      return null;
    }
  }

  // Search vectors by text query (requires embedding generation)
  async searchByText(query: string, collectionName: string, limit: number = 10): Promise<QdrantSearchResult[]> {
    try {
      // Note: This would typically require generating embeddings from the text first
      // For now, we'll return a placeholder that indicates this needs backend support
      console.warn('Text search requires embedding generation on the backend');
      return [];
    } catch (error) {
      console.error('Failed to search by text:', error);
      throw new Error('Failed to search vectors by text');
    }
  }

  // Search vectors by vector (direct vector search)
  async searchByVector(vector: number[], collectionName: string, limit: number = 10, threshold: number = 0.7): Promise<QdrantSearchResult[]> {
    try {
      const searchResult = await this.client.search(collectionName, {
        vector,
        limit,
        score_threshold: threshold,
        with_payload: true,
        with_vector: false
      });

      if (searchResult.length > 0) {
        return searchResult.map(result => ({
          id: result.id,
          score: result.score || 0,
          payload: result.payload || {},
          vector: result.vector
        }));
      }
      
      return [];
    } catch (error) {
      console.error('Failed to search by vector:', error);
      throw new Error('Failed to search vectors in Qdrant');
    }
  }

  // Get all points from a collection (for browsing)
  async getPoints(collectionName: string, limit: number = 100, offset?: string): Promise<QdrantPoint[]> {
    try {
      const response = await this.client.scroll(collectionName, {
        limit,
        offset,
        with_payload: true,
        with_vector: false
      });

      if (response.points) {
        return response.points.map(point => ({
          id: point.id,
          payload: point.payload || {},
          vector: point.vector || []
        }));
      }
      
      return [];
    } catch (error) {
      console.error('Failed to get points:', error);
      throw new Error('Failed to get points from Qdrant');
    }
  }

  // Get point by ID
  async getPointById(collectionName: string, pointId: string | number): Promise<QdrantPoint | null> {
    try {
      const response = await this.client.getPoint(collectionName, pointId);
      
      if (response.result) {
        const point = response.result;
        return {
          id: point.id,
          payload: point.payload || {},
          vector: point.vector || []
        };
      }
      
      return null;
    } catch (error) {
      console.error(`Failed to get point ${pointId}:`, error);
      return null;
    }
  }

  // Get collection statistics
  async getCollectionStats(): Promise<{
    totalCollections: number;
    totalPoints: number;
    collections: Array<{
      name: string;
      pointsCount: number;
      vectorsCount: number;
    }>;
  }> {
    try {
      const collections = await this.getCollections();
      
      const totalPoints = collections.reduce((sum, col) => sum + col.pointsCount, 0);
      const totalVectors = collections.reduce((sum, col) => sum + col.vectorsCount, 0);
      
      return {
        totalCollections: collections.length,
        totalPoints,
        collections: collections.map(col => ({
          name: col.name,
          pointsCount: col.pointsCount,
          vectorsCount: col.vectorsCount
        }))
      };
    } catch (error) {
      console.error('Failed to get collection stats:', error);
      throw new Error('Failed to get collection statistics');
    }
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Qdrant health check failed:', error);
      return false;
    }
  }

  // Get cluster info
  async getClusterInfo(): Promise<Record<string, any>> {
    try {
      const response = await fetch(`${this.baseUrl}/cluster`);
      if (response.ok) {
        return await response.json();
      }
      return {};
    } catch (error) {
      console.error('Failed to get cluster info:', error);
      return {};
    }
  }
}

// Export a singleton instance
export const qdrantService = new QdrantService();
export default qdrantService;