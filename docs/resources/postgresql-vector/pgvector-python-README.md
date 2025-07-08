# pgvector-python

pgvector support for Python
Supports Django, SQLAlchemy, SQLModel, Psycopg 3, Psycopg 2, asyncpg, pg8000, and Peewee

## Installation

Run:
```
pip install pgvector
```

## Critical Findings for FindersKeepers v2

### Key Issue: asyncpg vs psycopg3 for Vector Storage

**IMPORTANT**: The pgvector-python documentation shows that **both asyncpg and psycopg3 are supported**, but they have different approaches for vector insertion:

#### Psycopg 3 (Recommended for vectors)
```python
from pgvector.psycopg import register_vector

# Register vector type with connection
register_vector(conn)

# Insert vector directly as numpy array or list
embedding = np.array([1, 2, 3])
conn.execute('INSERT INTO items (embedding) VALUES (%s)', (embedding,))
```

#### asyncpg (Current implementation)
```python
from pgvector.asyncpg import register_vector

# Register vector type with connection
await register_vector(conn)

# Insert vector directly as numpy array
embedding = np.array([1, 2, 3])
await conn.execute('INSERT INTO items (embedding) VALUES ($1)', embedding)
```

### Connection Pool Configuration

For **asyncpg** (what we're currently using):
```python
async def init(conn):
    await register_vector(conn)
pool = await asyncpg.create_pool(..., init=init)
```

For **psycopg3** (if we switch):
```python
def configure(conn):
    register_vector(conn)
pool = ConnectionPool(..., configure=configure)
```

### Current Error Analysis

Our error: `invalid input for query argument $8: [0.0043400563, 0.021738416, 0.0038776777... (expected str, got list)`

This suggests we're not properly registering the vector type with asyncpg, so PostgreSQL sees the vector as a raw list instead of a proper vector type.

### Required Dependencies

Current requirements.txt shows:
```
asyncpg>=0.29.0          # PostgreSQL async driver
```

Should also include:
```
pgvector>=0.2.0          # pgvector support for PostgreSQL
```

### Proper asyncpg Implementation

1. Install pgvector: `pip install pgvector`
2. Register vector type with pool initialization:
```python
from pgvector.asyncpg import register_vector

async def init_connection(conn):
    await register_vector(conn)
    
# In connection pool creation:
self._pg_pool = await asyncpg.create_pool(
    self.pg_dsn, 
    min_size=1, 
    max_size=10,
    init=init_connection
)
```

3. Insert vectors directly without json.dumps:
```python
await conn.execute("""
    INSERT INTO documents (id, title, content, project, doc_type, tags, metadata, embeddings) 
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
""", document_id, title, content, project, doc_type, tags, metadata_json, embeddings_list)
```

**Conclusion**: We can keep using asyncpg but need to properly register the vector type and install pgvector package.