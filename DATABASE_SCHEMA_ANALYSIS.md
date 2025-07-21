# Database Schema Analysis - Session Continuity Fixes

## Critical Issues Identified

### 1. Vector Dimension Mismatch (HIGHEST PRIORITY)

**Problem**: The PostgreSQL schema expects 1536-dimensional embeddings but the application uses 1024-dimensional embeddings.

**Database Schema** (`/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`):
- Line 81: `embedding vector(1536)` - OpenAI text-embedding-3-small dimension
- Line 196: `query_embedding vector(1536)` in search function
- Comment says "OpenAI text-embedding-3-small dimension"

**Application Code** (uses mxbai-embed-large model with 1024 dimensions):
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py:48`: `self.embedding_dimension = 1024`
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py:116-117`: Mock embeddings use 1024 dimensions

**Inconsistencies Found**:
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py:225`: Uses `[0.0] * 1536` for dummy vector
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/services/redis_vector_cache.py:36`: `self.max_vector_dimension = 1536`

### 2. Database Schema vs Application Model Inconsistencies

**Current Schema Tables**:
- `agent_sessions` - ✅ Matches application usage
- `agent_actions` - ✅ Matches application usage  
- `conversation_messages` - ✅ Properly implemented in schema
- `documents` - ⚠️ Column name inconsistencies
- `document_chunks` - ⚠️ Wrong vector dimension
- `config_changes` - ✅ Matches application usage
- `knowledge_entities` - ⚠️ Not fully utilized
- `entity_references` - ⚠️ Not fully utilized

**Application Queries Analysis**:

From `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/queries.py`:
- `StatsQueries` - Uses correct table/column names
- `SessionQueries` - Uses correct table/column names
- `DocumentQueries` - Uses correct table/column names
- `ConversationQueries` - Uses correct table/column names (well implemented)

From `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py`:
- Document insertion uses: `title`, `content`, `content_hash`, `project`, `doc_type`, `tags`, `metadata`, `embeddings`
- Chunk insertion uses: `id`, `document_id`, `chunk_index`, `content`, `embedding`, `metadata`

**Schema vs Application Mismatches**:
1. **documents.embeddings**: Schema doesn't have this column but application tries to insert it
2. **Vector dimensions**: Schema uses 1536, application uses 1024
3. **Storage service**: Uses different connection patterns than database queries

### 3. Database Connection Inconsistencies

**Multiple Connection Patterns**:
1. **diary-api**: Uses `DatabaseManager` class with pooling (`/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/connection.py`)
2. **mcp-knowledge-server**: Uses individual client classes per database
3. **ingestion/storage.py**: Creates its own connection pools

**Connection Config Differences**:
- diary-api uses Docker service names: `fk2_postgres`, `fk2_neo4j`, `fk2_redis`, `fk2_qdrant`
- ingestion/storage.py uses different names: `postgres`, `neo4j`, `redis`, `qdrant`

### 4. Missing Database Columns

**documents table missing**:
- `embeddings` column (referenced in storage.py line 193)
- Possibly other columns expected by application

**document_chunks table issues**:
- Vector dimension mismatch (1536 vs 1024)

## Files That Need Updates

### 1. Database Schema (CRITICAL)
- `/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`
  - Change `embedding vector(1536)` to `embedding vector(1024)` (line 81)
  - Change `query_embedding vector(1536)` to `query_embedding vector(1024)` (line 196)
  - Add missing `embeddings` column to documents table if needed

### 2. Application Code (HIGH PRIORITY)
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py`
  - Line 225: Change `[0.0] * 1536` to `[0.0] * 1024`
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/services/redis_vector_cache.py`
  - Line 36: Change `self.max_vector_dimension = 1536` to `1024`

### 3. Connection Standardization (MEDIUM PRIORITY)
- Standardize database connection patterns across all services
- Use consistent Docker service names
- Implement proper connection pooling everywhere

## Session Continuity Components Status

### ✅ Working Components
- **conversation_messages table**: Properly implemented in schema
- **ConversationQueries class**: Complete implementation for message logging/retrieval
- **SessionQueries class**: Complete implementation for session management
- **Basic MCP session tools**: `resume_session`, `endsession`, `initialize_claude_session`

### ⚠️ Partially Working Components
- **Vector search**: Works but with wrong dimensions
- **Document storage**: Works but column mismatches
- **Activity logger**: Works but needs better fallback mechanisms

### ❌ Broken Components
- **Vector embeddings**: Dimension mismatch breaks vector operations
- **Document embedding storage**: Missing columns in schema
- **Knowledge graph integration**: Incomplete implementation

## Recommended Fix Order

1. **Fix vector dimensions** (database schema + application code)
2. **Add missing database columns** (documents.embeddings if needed)
3. **Standardize database connections** across all services
4. **Test session continuity end-to-end**
5. **Implement proper error handling and fallbacks**

## Key Code Locations

- **Main schema**: `/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`
- **Database queries**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/queries.py`
- **Storage service**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py`
- **Database connection**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/connection.py`
- **MCP server**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py`
- **Qdrant client**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py`

## Current Todo List Status

- [IN PROGRESS] Fix database schema inconsistencies between PostgreSQL init.sql and application models
- [PENDING] Implement proper session lifecycle management in MCP Knowledge Server
- [PENDING] Fix vector dimension mismatch (1536 vs 1024) across all components
- [PENDING] Implement conversation message storage and retrieval for session continuity
- [PENDING] Implement graceful session termination with data persistence verification

## Next Steps

1. **IMMEDIATE**: Fix the vector dimension mismatch in database schema
2. **IMMEDIATE**: Fix the vector dimension mismatch in application code
3. **AFTER SCHEMA FIX**: Restart PostgreSQL container to apply schema changes
4. **TEST**: Verify vector operations work correctly
5. **CONTINUE**: Move to next high-priority item in todo list

## Important Notes

- **Schema changes require database restart**: PostgreSQL container needs restart after schema changes
- **Vector operations will fail**: Until dimension mismatch is fixed, vector search won't work
- **Session continuity partially works**: Basic session management works, but vector-based features are broken
- **MCP server restart needed**: After schema changes, MCP Knowledge Server needs restart to pick up changes

## Database Service Names

**Docker Compose Services**:
- `fk2_postgres` (PostgreSQL)
- `fk2_neo4j` (Neo4j)
- `fk2_redis` (Redis)
- `fk2_qdrant` (Qdrant)

**Connection Patterns**:
- Some services use `localhost` for local development
- Some use Docker service names for container-to-container communication
- Inconsistent patterns need standardization