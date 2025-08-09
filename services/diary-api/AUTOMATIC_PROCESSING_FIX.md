# FindersKeepers v2 - Automatic Document Processing Fix

## Problem Summary

The FindersKeepers v2 system wasn't automatically processing documents to:
1. Extract entities and create relationships
2. Generate embeddings for vector search
3. Populate the knowledge graph in Neo4j
4. Store vectors in Qdrant database

## Root Causes Identified

1. **Basic Entity Extraction**: The `_extract_entities` function in `storage.py` only uses simple regex patterns
2. **No Automatic Triggers**: Documents added to PostgreSQL don't trigger the processing pipeline
3. **Silent Failures**: When Ollama is unavailable, embeddings fail silently
4. **Sparse Knowledge Graph**: Only document-to-project relationships are created

## Solution Implementation

### Files Created

1. **`fix_automatic_processing.py`** - Complete automatic processing pipeline
2. **`test_automatic_processing.py`** - Test script to verify the fix works

### Key Features of the Fix

#### 1. Advanced Entity Extraction
- Uses Ollama LLM for Named Entity Recognition (NER)
- Extracts: PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, CONCEPT, FILE, URL, CODE_ELEMENT
- Fallback to regex if Ollama fails
- Creates entity metadata with context

#### 2. Automatic Processing Pipeline
- Finds unprocessed documents (missing embeddings or entities)
- Processes documents through all stages automatically
- PostgreSQL trigger for new document notifications
- Retry logic for embedding generation

#### 3. Rich Knowledge Graph
- Creates document nodes with full metadata
- Creates entity nodes with types
- Document-to-entity relationships (MENTIONS)
- Entity-to-entity relationships (RELATED_TO)
- Project nodes and relationships

#### 4. Vector Database Population
- Stores embeddings in Qdrant with rich metadata
- Includes entities and tags in payload
- Enables semantic search across documents

## How to Apply the Fix

### Step 1: Enter the FastAPI Container

```bash
docker exec -it fk2_fastapi bash
```

### Step 2: Run the Fix Script

```bash
cd /app
python fix_automatic_processing.py
```

This will:
- Create PostgreSQL triggers for automatic processing
- Process any existing unprocessed documents
- Set up the pipeline for future documents

### Step 3: Test the Fix

```bash
python test_automatic_processing.py
```

This will:
- Ingest a test document
- Verify entity extraction
- Check embedding generation
- Test vector search
- Validate knowledge graph creation

## Monitoring Processing

### Check Processing Status

```sql
-- Connect to PostgreSQL
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2

-- Check unprocessed documents
SELECT id, title, 
       metadata->>'entities_extracted' as entities,
       metadata->>'embeddings_generated' as embeddings,
       metadata->>'relationships_created' as relationships
FROM documents
WHERE metadata->>'entities_extracted' IS NULL
   OR metadata->>'embeddings_generated' IS NULL;
```

### Check Neo4j Knowledge Graph

```cypher
-- Connect to Neo4j Browser: http://localhost:7474
-- Username: neo4j, Password: fk2025neo4j

-- Count entities
MATCH (e:Entity) RETURN e.type, COUNT(e) as count ORDER BY count DESC;

-- View relationships
MATCH (d:Document)-[r:MENTIONS]->(e:Entity)
RETURN d.title, type(r), e.name, e.type LIMIT 20;

-- Entity co-occurrence
MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
RETURN e1.name, e1.type, r.count, e2.name, e2.type
ORDER BY r.count DESC LIMIT 20;
```

### Check Qdrant Vector Database

```bash
# Check collection status
curl http://localhost:6333/collections/fk2_documents

# Search for similar documents
curl -X POST http://localhost:6333/collections/fk2_documents/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # Use actual embeddings
    "limit": 5
  }'
```

## Configuration

### Environment Variables

The fix uses these environment variables (already set in docker-compose.yml):

```yaml
POSTGRES_URL: postgresql://finderskeepers:fk2025secure@postgres:5432/finderskeepers_v2
OLLAMA_URL: http://ollama:11434
EMBEDDING_MODEL: mxbai-embed-large
CHAT_MODEL: llama3:8b
NEO4J_URI: bolt://neo4j:7687
NEO4J_USER: neo4j
NEO4J_PASSWORD: fk2025neo4j
QDRANT_URL: http://qdrant:6333
```

## Automatic Processing Workflow

1. **Document Creation** → PostgreSQL trigger fires
2. **Entity Extraction** → Ollama NER + regex fallback
3. **Embedding Generation** → Ollama mxbai-embed-large model
4. **Knowledge Graph** → Neo4j relationships created
5. **Vector Storage** → Qdrant indexing with metadata
6. **Metadata Update** → PostgreSQL tracking of processing status

## Troubleshooting

### If Ollama Fails

```bash
# Check Ollama status
docker logs fk2_ollama

# Restart Ollama
docker restart fk2_ollama

# Test Ollama
curl http://localhost:11434/api/version
```

### If Neo4j Connection Fails

```bash
# Check Neo4j status
docker logs fk2_neo4j

# Test connection
docker exec -it fk2_neo4j cypher-shell -u neo4j -p fk2025neo4j
```

### If Processing Doesn't Trigger

```bash
# Check PostgreSQL triggers
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2 -c "\df notify_document_insert"

# Manually trigger processing
docker exec -it fk2_fastapi python -c "
import asyncio
from fix_automatic_processing import AutomaticProcessingPipeline
asyncio.run(AutomaticProcessingPipeline().process_unprocessed_documents())
"
```

## Performance Considerations

- **Entity Extraction**: Limited to 50 entities per document
- **Relationships**: Limited to 20 entity-to-entity relationships
- **Embeddings**: Content limited to 8000 characters
- **Batch Processing**: Processes 10 documents at a time

## Future Improvements

1. **Better NER**: Use spaCy or Hugging Face models for entity extraction
2. **Streaming Processing**: Use Kafka/RabbitMQ for queue management
3. **Incremental Updates**: Only process changed content
4. **Relationship Scoring**: Weight relationships by importance
5. **Custom Embeddings**: Fine-tune embedding model for your domain

## Support

For issues or questions:
- Check logs: `docker logs fk2_fastapi`
- Database status: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`

## Author

Created by Claude to fix the FindersKeepers v2 automatic processing pipeline.
Date: August 2025
