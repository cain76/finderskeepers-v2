# FindersKeepers v2 - Automatic Document Processing

## Overview

This automatic document processing pipeline ensures that all documents in FindersKeepers v2 are:
- Automatically processed through entity extraction
- Indexed with embeddings for vector search
- Connected in the Neo4j knowledge graph
- Searchable via Qdrant vector database

## Portability Features ✅

This solution is **fully portable** across different computers and operating systems because:

1. **Docker Integration**: All processing logic is built into the Docker container
2. **Automatic Initialization**: The pipeline initializes on container startup
3. **Database Triggers**: PostgreSQL triggers ensure no document is missed
4. **Self-Contained**: No manual intervention required after deployment

## How It Works

### Automatic Initialization

When you run `docker-compose up`, the following happens automatically:

1. **Container Startup**: The FastAPI container starts with the custom entrypoint script
2. **Service Health Checks**: Waits for all dependencies (PostgreSQL, Neo4j, Qdrant, Ollama)
3. **Pipeline Initialization**: Creates database triggers and processes unprocessed documents
4. **Continuous Monitoring**: Listens for new documents and processes them automatically

### Processing Pipeline

Each document goes through these stages:

```mermaid
graph LR
    A[Document Created] --> B[Entity Extraction]
    B --> C[Embedding Generation]
    C --> D[Knowledge Graph]
    D --> E[Vector Storage]
    E --> F[Searchable Document]
```

## File Structure

```
services/diary-api/
├── app/
│   └── core/
│       ├── __init__.py                    # Core module exports
│       └── automatic_processing.py        # Processing pipeline (singleton)
├── docker-entrypoint.sh                   # Container initialization script
├── Dockerfile                              # Updated with entrypoint
└── main.py                                # FastAPI app with pipeline integration
```

## Deployment Instructions

### Fresh Installation

1. **Clone the repository** on any computer:
```bash
git clone https://github.com/yourusername/finderskeepers-v2.git
cd finderskeepers-v2
```

2. **Start the services**:
```bash
docker-compose up -d
```

That's it! The automatic processing pipeline will:
- Initialize on first startup
- Create necessary database triggers
- Process any existing documents
- Monitor for new documents

### Verification

Check that automatic processing is working:

```bash
# View container logs
docker logs fk2_fastapi

# You should see:
# ✅ Automatic document processing pipeline initialized!
# ✅ Database trigger created for automatic processing
# 📄 Processed X unprocessed documents on startup
```

### Testing

Test with a new document:

```bash
# Inside the container
docker exec -it fk2_fastapi python test_automatic_processing.py

# Or via API
curl -X POST http://localhost:8000/api/docs/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Document",
    "content": "This document mentions Docker, Python, and FastAPI.",
    "project": "test-project",
    "doc_type": "technical",
    "tags": ["test"]
  }'
```

## Environment Variables

All configuration is in `docker-compose.yml` (no changes needed):

```yaml
POSTGRES_URL: postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2
OLLAMA_URL: http://ollama:11434
EMBEDDING_MODEL: mxbai-embed-large  # DO NOT CHANGE - 1024 dimensions
CHAT_MODEL: llama3:8b
NEO4J_URI: bolt://neo4j:7687
QDRANT_URL: http://qdrant:6333
```

## Cross-Platform Compatibility

### Linux ✅
- Native Docker support
- GPU acceleration available
- Tested on Ubuntu, Debian, Fedora

### macOS ✅
- Docker Desktop required
- GPU acceleration via Metal (if available)
- Tested on M1/M2 and Intel Macs

### Windows ✅
- Docker Desktop with WSL2 backend
- GPU acceleration via WSL2
- Tested on Windows 10/11

## Monitoring

### Check Processing Status

```sql
-- Connect to PostgreSQL
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2

-- View processing status
SELECT 
    id, 
    title,
    metadata->>'entities_extracted' as entities,
    metadata->>'embeddings_generated' as embeddings,
    metadata->>'entity_count' as entity_count
FROM documents
ORDER BY created_at DESC
LIMIT 10;
```

### View Knowledge Graph

Access Neo4j Browser at `http://localhost:7474`:
- Username: `neo4j`
- Password: `fk2025neo4j`

Query examples:
```cypher
// Count entities by type
MATCH (e:Entity) 
RETURN e.type, COUNT(e) as count 
ORDER BY count DESC;

// View document relationships
MATCH (d:Document)-[r:MENTIONS]->(e:Entity)
RETURN d, r, e
LIMIT 50;
```

### Search Vector Database

```bash
# Check Qdrant collection
curl http://localhost:6333/collections/fk2_documents
```

## Troubleshooting

### Pipeline Not Processing

1. **Check logs**:
```bash
docker logs fk2_fastapi | grep -i "automatic"
```

2. **Verify trigger exists**:
```sql
SELECT * FROM pg_trigger WHERE tgname = 'document_insert_trigger';
```

3. **Manually trigger processing**:
```bash
docker exec -it fk2_fastapi python -c "
import asyncio
from app.core import processing_pipeline
asyncio.run(processing_pipeline.process_unprocessed_documents())
"
```

### Ollama Connection Issues

```bash
# Test Ollama
curl http://localhost:11434/api/version

# Restart if needed
docker restart fk2_ollama
```

### Neo4j Connection Issues

```bash
# Test Neo4j
curl http://localhost:7474

# Check logs
docker logs fk2_neo4j
```

## Performance Tuning

### Processing Limits

Edit `app/core/automatic_processing.py`:

```python
# Adjust batch size (default: 10)
await processing_pipeline.process_unprocessed_documents(limit=20)

# Adjust entity limit (default: 30)
return list(unique.values())[:50]  # Increase to 50 entities

# Adjust embedding content size (default: 8000)
"input": content[:12000]  # Increase to 12000 chars
```

### Database Optimization

```sql
-- Add indexes for faster queries
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX idx_documents_embeddings ON documents (embeddings);
```

## Backup and Migration

### Export Data

```bash
# Backup PostgreSQL
docker exec fk2_postgres pg_dump -U finderskeepers finderskeepers_v2 > backup.sql

# Export Neo4j
docker exec fk2_neo4j neo4j-admin database dump neo4j --to=/data/neo4j-backup.dump

# Export Qdrant
curl http://localhost:6333/collections/fk2_documents/snapshots -X POST
```

### Import Data

```bash
# Restore PostgreSQL
docker exec -i fk2_postgres psql -U finderskeepers finderskeepers_v2 < backup.sql

# Import Neo4j
docker exec fk2_neo4j neo4j-admin database load neo4j --from=/data/neo4j-backup.dump

# Restore Qdrant snapshot
# Use Qdrant API to restore from snapshot
```

## Development

### Adding New Entity Types

Edit `app/core/automatic_processing.py`:

```python
# Add to extraction prompt
"Identify: PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, YOUR_NEW_TYPE"

# Add to regex fallback
your_keywords = ['Keyword1', 'Keyword2']
```

### Custom Processing Steps

Add to the `process_document` method:

```python
async def process_document(self, doc: Dict[str, Any]):
    # ... existing steps ...
    
    # Add your custom processing
    await self.custom_processing_step(doc)
    
    # Update metadata
    metadata_updates["custom_processed"] = True
```

## Support

For issues:
1. Check container logs: `docker logs fk2_fastapi`
2. Verify service health: `http://localhost:8000/health`
3. Review this documentation
4. Check PostgreSQL triggers and Neo4j connections

## License

Part of FindersKeepers v2 - Personal AI Agent Knowledge Hub
