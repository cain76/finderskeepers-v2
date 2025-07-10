# Qdrant JavaScript SDK Integration Guide
**Date**: 07-09-2025  
**Source**: https://github.com/qdrant/qdrant-js  
**Version**: 1.14.1  
**Project**: FindersKeepers v2 - Vector Database Integration  

## Overview

Official JavaScript/TypeScript SDK for Qdrant Vector Database. Essential for implementing vector search functionality in the FindersKeepers v2 frontend and backend integration.

## Available Packages

### 1. Main SDK Package
```bash
npm install @qdrant/qdrant-js
```
- Complete SDK with all features
- TypeScript support included
- Both REST and gRPC clients

### 2. REST Client (Lightweight)
```bash
npm install @qdrant/js-client-rest
```
- Lightweight REST-only client
- Ideal for frontend applications
- Supports Node.js, Deno, Browser, Cloudflare Workers

### 3. gRPC Client
```bash
npm install @qdrant/js-client-grpc
```
- High-performance gRPC client
- Best for backend applications
- Lower latency than REST

## Basic Client Setup

### REST Client Configuration
```typescript
import {QdrantClient} from '@qdrant/js-client-rest';

// Connect to local Qdrant instance
const client = new QdrantClient({
  url: 'http://fk2_qdrant:6333'  // Docker service name
});

// Or connect to Qdrant Cloud
const client = new QdrantClient({
  url: 'https://xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.us-east-0-1.aws.cloud.qdrant.io',
  apiKey: '<your-api-key>',
});
```

### Main SDK Configuration
```typescript
import {QdrantClient} from '@qdrant/qdrant-js';

const client = new QdrantClient({
  url: 'http://fk2_qdrant:6333',
  // Optional: configure connection pool
  maxConnections: 100,
  // Optional: set request timeout
  timeout: 30000
});
```

## Core Operations

### Collection Management
```typescript
// List all collections
const collections = await client.getCollections();
console.log('Collections:', collections.collections);

// Create a collection
await client.createCollection('documents', {
  vectors: {
    size: 384,  // Vector dimension
    distance: 'Cosine'  // Distance metric
  }
});

// Get collection info
const info = await client.getCollection('documents');
```

### Vector Operations
```typescript
// Insert vectors
await client.upsert('documents', {
  wait: true,
  points: [
    {
      id: 1,
      vector: [0.1, 0.2, 0.3, ...],  // 384-dimensional vector
      payload: {
        title: 'Document title',
        content: 'Document content',
        project: 'finderskeepers-v2',
        timestamp: new Date().toISOString()
      }
    }
  ]
});

// Search vectors
const searchResult = await client.search('documents', {
  vector: [0.1, 0.2, 0.3, ...],  // Query vector
  limit: 10,
  score_threshold: 0.5,
  with_payload: true,
  with_vectors: false
});
```

## FindersKeepers v2 Implementation

### 1. Environment Configuration
```typescript
// For Docker environment
const QDRANT_CONFIG = {
  url: process.env.QDRANT_URL || 'http://fk2_qdrant:6333',
  timeout: 30000,
  maxConnections: 50
};
```

### 2. Document Collection Schema
```typescript
interface DocumentPayload {
  title: string;
  content: string;
  project: string;
  doc_type: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  session_id?: string;
  agent_type?: string;
}

// Collection configuration
const DOCUMENT_COLLECTION = {
  name: 'fk2_documents',
  vectors: {
    size: 384,  // mxbai-embed-large dimensions
    distance: 'Cosine'
  }
};
```

### 3. Vector Search Service
```typescript
class VectorSearchService {
  private client: QdrantClient;

  constructor() {
    this.client = new QdrantClient(QDRANT_CONFIG);
  }

  async searchDocuments(
    queryVector: number[],
    filters?: Record<string, any>,
    limit: number = 10
  ) {
    const searchParams = {
      vector: queryVector,
      limit,
      score_threshold: 0.5,
      with_payload: true,
      with_vectors: false
    };

    if (filters) {
      searchParams.filter = {
        must: Object.entries(filters).map(([key, value]) => ({
          key,
          match: { value }
        }))
      };
    }

    return await this.client.search(DOCUMENT_COLLECTION.name, searchParams);
  }

  async addDocument(
    id: string,
    vector: number[],
    payload: DocumentPayload
  ) {
    return await this.client.upsert(DOCUMENT_COLLECTION.name, {
      wait: true,
      points: [{
        id,
        vector,
        payload
      }]
    });
  }
}
```

## React Frontend Integration

### 1. Frontend Service
```typescript
// services/vectorSearch.ts
import {QdrantClient} from '@qdrant/js-client-rest';

export class FrontendVectorService {
  private client: QdrantClient;

  constructor() {
    this.client = new QdrantClient({
      url: process.env.REACT_APP_QDRANT_URL || 'http://localhost:6333'
    });
  }

  async searchKnowledge(query: string, limit: number = 5) {
    // Get embeddings from backend
    const embeddingResponse = await fetch('/api/embeddings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: query })
    });
    
    const { embeddings } = await embeddingResponse.json();
    
    // Search vectors
    return await this.client.search('fk2_documents', {
      vector: embeddings,
      limit,
      with_payload: true
    });
  }
}
```

### 2. React Hook
```typescript
// hooks/useVectorSearch.ts
import { useState, useCallback } from 'react';
import { FrontendVectorService } from '../services/vectorSearch';

export const useVectorSearch = () => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const vectorService = new FrontendVectorService();
      const searchResults = await vectorService.searchKnowledge(query);
      setResults(searchResults);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
};
```

## Configuration for FindersKeepers v2

### Docker Compose Integration
```yaml
# Already configured in docker-compose.yml
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: fk2_qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
```

### Environment Variables
```env
QDRANT_URL=http://fk2_qdrant:6333
QDRANT_API_KEY=  # Optional for cloud deployment
```

## Best Practices

1. **Connection Pooling**: Use maxConnections for backend services
2. **Error Handling**: Always implement proper error handling
3. **Batch Operations**: Use batch inserts for better performance
4. **Filtering**: Use payload filters for efficient searches
5. **Monitoring**: Monitor vector search performance

## Performance Considerations

- **Vector Dimensions**: Use 384 for mxbai-embed-large model
- **Distance Metric**: Cosine distance for semantic similarity
- **Batch Size**: Insert vectors in batches of 100-1000
- **Index Settings**: Configure HNSW parameters for your use case

## Required Dependencies for FindersKeepers v2

```json
{
  "dependencies": {
    "@qdrant/js-client-rest": "^1.14.1"
  }
}
```

## Resources

- [Official Documentation](https://qdrant.tech/documentation/)
- [API Reference](https://qdrant.github.io/qdrant/redoc/index.html)
- [Examples](https://github.com/qdrant/qdrant-js/tree/master/examples)
- [Discord Community](https://qdrant.to/discord)

## Next Steps for FindersKeepers v2

1. Add @qdrant/js-client-rest to frontend package.json
2. Implement VectorSearchService in React components
3. Connect to existing Qdrant container (fk2_qdrant)
4. Integrate with Ollama embeddings pipeline
5. Add vector search to chat interface