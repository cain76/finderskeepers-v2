# Proper AsyncPG Vector Fix for FindersKeepers v2

**Date**: 2025-07-07  
**Research Source**: pgvector-python official documentation  
**Issue**: PostgreSQL vector storage failing with "expected str, got list"

## Root Cause Analysis

The error `invalid input for query argument $8: [0.0043400563, 0.021738416, 0.0038776777... (expected str, got list)` occurs because:

1. **Missing pgvector package**: Not installed in requirements.txt
2. **No vector type registration**: asyncpg doesn't know how to handle vector types
3. **Incorrect approach**: Trying to fix with JSON serialization instead of proper type registration

## Correct Solution (Keep AsyncPG)

### 1. Update requirements.txt
```txt
# Add this line to existing requirements.txt:
pgvector>=0.2.0          # pgvector support for PostgreSQL  
```

### 2. Fix storage.py - Vector Type Registration
```python
# In storage.py imports:
from pgvector.asyncpg import register_vector

# In StorageService.__init__():
async def _ensure_pg_pool(self):
    """Ensure PostgreSQL connection pool exists with vector support"""
    if self._pg_pool is None:
        async def init_connection(conn):
            # Register pgvector types for each connection
            await register_vector(conn)
            
        self._pg_pool = await asyncpg.create_pool(
            self.pg_dsn, 
            min_size=1, 
            max_size=10,
            init=init_connection  # Initialize each connection with vector support
        )
```

### 3. Fix vector insertion (Remove JSON conversion)
```python
# In _store_in_postgres method:
await conn.execute("""
    INSERT INTO documents (
        id, title, content, project, doc_type,
        tags, metadata, embeddings
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
""",
    document_id,
    metadata.title,
    combined_content,
    request.project,
    request.metadata.get('doc_type', 'ingested'),
    request.tags,
    json.dumps({...}),  # Keep JSON for metadata
    chunks[0].embeddings  # Pass vector directly, NO json.dumps()
)

# And for chunks:
await conn.execute("""
    INSERT INTO document_chunks (
        id, document_id, chunk_index, content,
        embedding, metadata
    ) VALUES ($1, $2, $3, $4, $5, $6)
""",
    chunk.chunk_id,
    document_id,
    chunk.metadata.chunk_index,
    chunk.content,
    chunk.embeddings,  # Pass vector directly, NO json.dumps()
    json.dumps({...})  # Keep JSON for metadata
)
```

## Why This Works

1. **pgvector.asyncpg.register_vector()** teaches asyncpg how to handle PostgreSQL vector types
2. **Connection pool initialization** ensures every connection knows about vectors
3. **Direct vector passing** lets the registered type converter handle the serialization
4. **No JSON conversion needed** because pgvector handles list→vector conversion

## Implementation Steps

1. **Add pgvector to requirements.txt**
2. **Update storage.py imports and pool initialization**  
3. **Remove json.dumps() from vector fields**
4. **Rebuild container with new dependencies**

## Expected Result

After this fix:
- Vectors will be stored properly in PostgreSQL
- Qdrant will receive valid vectors
- Vector search will work correctly
- No more "expected str, got list" errors

## Alternative: Switch to Psycopg3

If we wanted to switch to psycopg3 (as shown in pgvector docs), the pattern would be:
```python
from pgvector.psycopg import register_vector

def configure_connection(conn):
    register_vector(conn)
    
pool = psycopg_pool.AsyncConnectionPool(
    dsn, 
    configure=configure_connection
)
```

But keeping asyncpg is simpler since it's already working for everything else.