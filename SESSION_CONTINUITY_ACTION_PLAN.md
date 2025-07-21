# Session Continuity Action Plan

## Current Status
- **Analysis Phase**: COMPLETE
- **Schema Fix Phase**: IN PROGRESS
- **Implementation Phase**: PENDING
- **Testing Phase**: PENDING

## Critical Path Items

### 1. Vector Dimension Fix (CRITICAL - MUST FIX FIRST)

**Problem**: Database schema expects 1536-dimensional vectors but application uses 1024-dimensional vectors from mxbai-embed-large model.

**Files to Fix**:
1. `/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`
   - Line 81: Change `embedding vector(1536)` to `embedding vector(1024)`
   - Line 196: Change `query_embedding vector(1536)` to `query_embedding vector(1024)`

2. `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py`
   - Line 225: Change `[0.0] * 1536` to `[0.0] * 1024`

3. `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/services/redis_vector_cache.py`
   - Line 36: Change `self.max_vector_dimension = 1536` to `1024`

**After Making Changes**:
1. Restart PostgreSQL container: `docker compose restart fk2_postgres`
2. Restart MCP Knowledge Server (requires exiting Claude Code)
3. Test vector operations

### 2. Missing Database Columns (HIGH PRIORITY)

**Investigation Needed**:
- Check if `documents.embeddings` column is actually needed
- Verify all columns match between schema and application queries

**Files to Check**:
- Schema: `/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`
- Application: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py`

### 3. Database Connection Standardization (MEDIUM PRIORITY)

**Current Issues**:
- Multiple connection patterns across services
- Inconsistent service names
- No shared connection pooling

**Files to Standardize**:
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/connection.py`
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py`
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/`

### 4. Session Lifecycle Management (HIGH PRIORITY)

**Components to Fix**:
- MCP Knowledge Server session management
- Graceful session termination
- Session timeout and cleanup
- Data persistence verification

**Files to Update**:
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py`
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/activity_logger.py`

### 5. Conversation Message Storage (HIGH PRIORITY)

**Status**: Schema is complete, application implementation exists
**Files to Verify**:
- `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/queries.py` (ConversationQueries)
- Test end-to-end conversation logging

## Current Todo List

1. [IN PROGRESS] Fix database schema inconsistencies between PostgreSQL init.sql and application models
2. [PENDING] Implement proper session lifecycle management in MCP Knowledge Server
3. [PENDING] Fix vector dimension mismatch (1536 vs 1024) across all components
4. [PENDING] Implement conversation message storage and retrieval for session continuity
5. [PENDING] Implement graceful session termination with data persistence verification

## Steps to Resume Work

### When Starting New Claude Code Session:

1. **Load Context**:
   - Read `/media/cain/linux_storage/projects/finderskeepers-v2/DATABASE_SCHEMA_ANALYSIS.md`
   - Read `/media/cain/linux_storage/projects/finderskeepers-v2/SESSION_CONTINUITY_ACTION_PLAN.md`

2. **Check Current Status**:
   - Review todo list to see what's in progress
   - Check if database schema fixes have been applied

3. **Resume Work**:
   - Continue with the current in-progress task
   - Apply fixes in the order specified in this plan

### Critical Dependencies

**Database Schema Changes**:
- MUST restart PostgreSQL container after schema changes
- MUST restart MCP Knowledge Server after schema changes
- Cannot test vector operations until dimension mismatch is fixed

**Service Restart Requirements**:
- PostgreSQL: `docker compose restart fk2_postgres`
- MCP Knowledge Server: Exit Claude Code, restart, re-enter Claude Code
- FastAPI: `docker compose restart fk2_fastapi` (if needed)

## Testing Plan

### Phase 1: Schema Validation
1. Apply vector dimension fixes
2. Restart services
3. Test basic database connections
4. Test vector operations

### Phase 2: Session Continuity
1. Test session creation
2. Test conversation logging
3. Test session termination
4. Test session resume

### Phase 3: End-to-End
1. Complete session lifecycle test
2. Multiple session test
3. Error handling test
4. Data persistence verification

## Key Commands

### Database Operations
```bash
# Restart PostgreSQL
docker compose restart fk2_postgres

# Check PostgreSQL logs
docker compose logs fk2_postgres

# Connect to PostgreSQL
docker exec -it fk2_postgres psql -U finderskeepers -d finderskeepers_v2
```

### Service Management
```bash
# Start all services
./scripts/start-all.sh

# Stop all services
./scripts/stop-all.sh

# Check service status
docker compose ps
```

### MCP Knowledge Server
```bash
# Start MCP server (after schema fixes)
cd services/mcp-knowledge-server
source .venv/bin/activate
python src/knowledge_server.py
```

## Critical Files for Quick Reference

1. **Database Schema**: `/media/cain/linux_storage/projects/finderskeepers-v2/config/pgvector/init.sql`
2. **Database Queries**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/database/queries.py`
3. **Storage Service**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/diary-api/app/api/v1/ingestion/storage.py`
4. **MCP Server**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/knowledge_server.py`
5. **Qdrant Client**: `/media/cain/linux_storage/projects/finderskeepers-v2/services/mcp-knowledge-server/src/database/qdrant_client.py`

## What Works vs What's Broken

### ✅ Currently Working
- Basic session creation and tracking
- Conversation message schema
- Database connection pooling (in diary-api)
- Session queries and statistics
- Activity logging to n8n

### ⚠️ Partially Working
- Vector search (wrong dimensions)
- Document storage (schema mismatches)
- MCP session management (needs improvements)

### ❌ Broken
- Vector embeddings (dimension mismatch)
- Document embedding storage
- Knowledge graph integration
- Proper session termination verification

## Next Claude Code Session Instructions

1. **First**: Read this document and the analysis document
2. **Check**: What's marked as "in_progress" in the todo list
3. **Apply**: Vector dimension fixes if not already done
4. **Test**: Database connections after any changes
5. **Continue**: With next high-priority item in todo list

Remember: You'll need to exit Claude Code and restart it after any PostgreSQL schema changes and MCP Knowledge Server changes.