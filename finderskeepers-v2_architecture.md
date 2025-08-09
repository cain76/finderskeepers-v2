# FindersKeepers v2 System Architecture

## AI GOD MODE Personal Knowledge Management System
### For bitcain.net - RTX 2080 Ti GPU Accelerated Platform
### Date: August 9, 2025

---

## Executive Summary

FindersKeepers v2 is a sophisticated personal AI knowledge management system that implements an "AI GOD MODE" architecture with persistent memory capabilities across sessions. The system uses a modern microservices architecture with direct FastAPI integration, bypassing traditional workflow automation tools for enhanced reliability and performance. It leverages local GPU acceleration (RTX 2080 Ti) for embedding generation and LLM inference, creating a completely self-contained AI knowledge hub.

The core innovation is the MCP (Model Context Protocol) server that maintains persistent AI memory across Claude Desktop sessions, eliminating traditional context window limitations through intelligent session management and comprehensive conversation capture.

---

## 1. System Architecture Overview

### Core Design Principles

The FindersKeepers v2 system is built on several key architectural principles:

1. **Direct Integration Pattern**: All communication flows directly through FastAPI endpoints, eliminating the n8n workflow automation layer that previously caused silent failures and broken conversation logging

2. **Persistent AI Memory**: The AI GOD MODE system maintains comprehensive session memory that persists across conversations, enabling true continuity and context awareness

3. **GPU-Accelerated Processing**: Local RTX 2080 Ti GPU acceleration for all AI operations including embeddings, entity extraction, and LLM inference

4. **Automatic Background Processing**: Self-healing document processing pipeline that automatically processes new documents every 5 minutes without manual intervention

5. **Multi-Modal Storage**: Hybrid storage approach combining PostgreSQL with pgvector, Qdrant vector database, Neo4j knowledge graph, and Redis caching

### High-Level Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Desktop + MCP Client                 │
│                    (AI GOD MODE Session Interface)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Session Server                         │
│                   (fk2-mcp - FastMCP 2.10.6)                   │
│     • Session Management    • Conversation Capture              │
│     • Tool Execution        • Context Persistence               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Direct HTTP/JSON-RPC
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                          │
│                    (Diary API - Port 8000)                      │
│     • MCP Endpoints         • Document Processing               │
│     • Chat Interface        • Background Tasks                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │PostgreSQL│      │  Qdrant  │      │  Neo4j   │
    │ pgvector │      │  Vector  │      │Knowledge │
    │    DB    │      │    DB    │      │  Graph   │
    └──────────┘      └──────────┘      └──────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                             ▼
                    ┌──────────────┐
                    │   Ollama     │
                    │ Local LLM    │
                    │  (RTX 2080)  │
                    └──────────────┘
```

---

## 2. Core Components Deep Dive

### 2.1 MCP Session Server (fk2-mcp)

The MCP server is the heart of the AI GOD MODE system, built with FastMCP 2.10.6 framework. It provides:

**Key Features:**
- **Persistent Session Management**: Maintains session state across Claude Desktop interactions with unique session IDs
- **Automatic Conversation Capture**: Uses FastMCP middleware to intercept all JSON-RPC 2.0 protocol messages
- **Accomplishment Tracking**: Automatically detects and logs successes and failures for AI learning
- **Tool Integration**: Provides tools for vector search, database queries, knowledge graph exploration, and document search

**Session Lifecycle:**
1. `start_session()`: Initializes AI GOD MODE with persistent session ID
2. Continuous conversation capture via middleware interception
3. Real-time accomplishment and failure detection
4. `end_session()`: Generates comprehensive session summary with AI insights
5. `resume_session()`: Loads previous context for seamless continuation

**Direct FastAPI Integration:**
```python
# Critical endpoints for AI GOD MODE
SESSION_START_ENDPOINT = "http://localhost:8000/api/mcp/session/start"
SESSION_END_ENDPOINT = "http://localhost:8000/api/mcp/session/end"  
ACTION_ENDPOINT = "http://localhost:8000/api/mcp/action"
CONVERSATION_ENDPOINT = "http://localhost:8000/api/mcp/action"
```

### 2.2 FastAPI Backend (Diary API)

The FastAPI backend serves as the central processing hub for all data operations:

**Core Responsibilities:**
- **MCP Integration**: Direct endpoints for session management and conversation logging
- **Document Processing**: Automatic background processing every 5 minutes
- **Embedding Generation**: Local Ollama integration for zero-cost embeddings
- **Entity Extraction**: Automated knowledge graph population from conversations
- **WebSocket Support**: Real-time chat interface with URL detection

**Automatic Background Processing:**
```python
# Environment variables for automatic processing
FK2_ENABLE_BACKGROUND_PROCESSING=true       
FK2_PROCESSING_INTERVAL_MINUTES=5           
FK2_PROCESSING_BATCH_SIZE=10                
FK2_PROCESSING_MAX_RETRIES=3                
FK2_PROCESSING_START_DELAY_SECONDS=30       
```

### 2.3 Database Architecture

#### PostgreSQL with pgvector
Primary relational database with vector extension for hybrid search:

**Core Tables:**
- `ai_sessions`: MCP session tracking
- `ai_session_memory`: AI GOD MODE persistent memory storage
- `agent_sessions`: Legacy session compatibility
- `documents`: Document metadata and content
- `document_chunks`: Chunked document segments with embeddings
- `knowledge_entities`: Extracted entities from conversations
- `entity_references`: Entity relationship mappings
- `processing_queue`: Document processing pipeline state

**AI GOD MODE Schema Highlights:**
```sql
CREATE TABLE ai_session_memory (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project TEXT NOT NULL,
    session_summary TEXT,
    accomplishments JSONB DEFAULT '[]'::jsonb,
    failures JSONB DEFAULT '[]'::jsonb,
    context_snapshot JSONB DEFAULT '{}'::jsonb,
    conversation_count INTEGER DEFAULT 0,
    tools_used JSONB DEFAULT '[]'::jsonb,
    files_touched JSONB DEFAULT '[]'::jsonb,
    ai_insights TEXT,
    resume_context TEXT
);
```

#### Qdrant Vector Database
High-performance vector similarity search engine:
- **Purpose**: Semantic search across document embeddings
- **Dimension**: 1024 (mxbai-embed-large model)
- **Collections**: `fk2_documents`, `fk2_conversations`
- **GPU Acceleration**: Enabled for faster similarity computations

#### Neo4j Knowledge Graph
Graph database for entity relationships and knowledge networks:
- **Node Types**: Person, Organization, Project, Technology, Concept
- **Relationship Types**: MENTIONS, RELATES_TO, WORKS_ON, USES
- **APOC & GDS**: Graph algorithms for advanced analytics
- **Auto-Population**: From conversation entity extraction

#### Redis Cache
High-speed caching layer:
- **Session State**: Temporary session data
- **Processing Locks**: Prevent duplicate processing
- **Rate Limiting**: API throttling
- **WebSocket State**: Active connection management

### 2.4 Ollama Local LLM Service

GPU-accelerated local language model inference:

**Configuration:**
```yaml
Models:
  - Chat Model: llama3:8b (8B parameters)
  - Embedding Model: mxbai-embed-large (1024 dimensions)
  
GPU Settings:
  - OLLAMA_GPU_LAYERS: 999 (full GPU utilization)
  - OLLAMA_FLASH_ATTENTION: 1 (optimized attention)
  - OLLAMA_GPU_MEMORY_FRACTION: 0.95 (11GB VRAM usage)
  - OLLAMA_PARALLEL_CONTEXT: 2048
  - OLLAMA_BATCH_SIZE: 512
```

---

## 3. Data Flow and Processing Pipelines

### 3.1 Conversation Capture Pipeline

The conversation capture pipeline ensures every interaction is preserved for AI memory:

```
User Message → Claude Desktop → MCP Server
                                    ↓
                            Middleware Intercept
                                    ↓
                            Capture & Enrich
                                    ↓
                        FastAPI /api/mcp/action
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            PostgreSQL Store               Generate Embeddings
                    ↓                               ↓
            Update Session                  Qdrant Vector Store
                    ↓                               ↓
            Track Accomplishments           Entity Extraction
                    ↓                               ↓
            Generate Insights               Neo4j Graph Update
```

### 3.2 Document Processing Pipeline

Automatic document processing occurs every 5 minutes:

```
Document Upload/Creation → PostgreSQL Queue
                              ↓
                    Background Processor (5 min)
                              ↓
                    Document Chunking (512 tokens)
                              ↓
                    Ollama Embedding Generation
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            Qdrant Vector Store    Entity Extraction
                    ↓                   ↓
            Similarity Index       Neo4j Graph Update
                    ↓                   ↓
                    └─────────┬─────────┘
                              ↓
                    Mark as Processed
```

### 3.3 Knowledge Query Pipeline

When querying the knowledge base:

```
Query Input → Generate Query Embedding
                    ↓
            Vector Similarity Search
                    ↓
            Qdrant + PostgreSQL Hybrid
                    ↓
            Knowledge Graph Traversal
                    ↓
            Context Aggregation
                    ↓
            LLM Response Generation
                    ↓
            Return Enhanced Answer
```

---

## 4. AI GOD MODE Features

### 4.1 Persistent Memory System

The AI GOD MODE implements true persistent memory that survives across sessions:

**Memory Components:**
- **Session Summary**: AI-generated summary of each session's activities
- **Accomplishments Tracker**: Automatic detection of completed tasks
- **Failure Tracker**: Learning from errors and issues
- **Context Snapshot**: Key information preserved for future sessions
- **Tool Usage History**: Which tools were used and how
- **File Touch History**: Documents and files modified

### 4.2 Intelligent Session Continuity

The system maintains context across sessions through:

1. **Resume Context Generation**: AI creates optimal context for session resumption
2. **Conversation History Loading**: Last N conversations loaded on resume
3. **Project State Tracking**: Current project status and progress
4. **Cross-Client Support**: Works with any MCP-compatible client

### 4.3 Automatic Learning and Adaptation

The AI GOD MODE continuously learns through:

- **Pattern Recognition**: Identifies recurring tasks and workflows
- **Success Pattern Analysis**: Learns from successful completions
- **Failure Analysis**: Understands common error patterns
- **Context Optimization**: Improves context selection over time

---

## 5. Integration Points and APIs

### 5.1 MCP Tool Registry

Available MCP tools for AI interaction:

```python
Tools = {
    "start_session": Initialize AI GOD MODE,
    "end_session": Close with comprehensive summary,
    "resume_session": Continue from previous context,
    "vector_search": Semantic search across knowledge,
    "database_query": Direct SQL execution,
    "knowledge_graph_search": Graph traversal queries,
    "document_search": Full-text document search,
    "capture_conversation": Manual conversation logging,
    "test_webhooks": Validate integration pipeline
}
```

### 5.2 FastAPI Endpoints

Core API endpoints for system interaction:

```
/api/mcp/session/start       - Initialize new session
/api/mcp/session/end         - End session with summary
/api/mcp/action              - Log actions and conversations
/api/v1/ingestion/           - Document ingestion
/api/v1/diary/               - Diary entries
/api/v1/entity-extraction/   - Entity processing
/api/admin/                  - System administration
/api/background/             - Background task control
```

### 5.3 WebSocket Interface

Real-time communication channel:

```
ws://localhost:8000/ws/{client_id}

Message Types:
- chat: Regular chat messages
- knowledge_query: Knowledge base queries
- url_scrape: Web scraping requests
- chat_response: AI responses
- knowledge_response: Knowledge query results
```

---

## 6. Deployment and Scaling

### 6.1 Container Architecture

The system uses Docker Compose for orchestration:

**Service Containers:**
- `fk2_fastapi`: Main API backend
- `fk2_postgres`: PostgreSQL with pgvector
- `fk2_qdrant`: Vector database
- `fk2_neo4j`: Knowledge graph
- `fk2_redis`: Cache layer
- `fk2_ollama`: Local LLM service
- `fk2_frontend`: React UI (port 3000)
- `fk2_n8n`: Legacy workflow automation (deprecated)

### 6.2 GPU Resource Management

Optimized for RTX 2080 Ti (11GB VRAM):

```yaml
Resource Allocation:
- Ollama: 95% VRAM (10.45GB)
- Batch Processing: 512 tokens
- Parallel Context: 2048 tokens
- Flash Attention: Enabled
- Multiple Models: 2 concurrent max
```

### 6.3 Network Architecture

All services communicate via `shared-network`:

```yaml
Network Aliases:
- fastapi: API backend
- postgres: Database
- qdrant: Vector search
- neo4j: Knowledge graph
- redis: Cache
- ollama: LLM service
```

---

## 7. Security and Privacy

### 7.1 Data Privacy

- **Local Processing**: All AI operations run locally on RTX 2080 Ti
- **No Cloud Dependencies**: Completely self-contained system
- **Encrypted Storage**: Database encryption at rest
- **Session Isolation**: Each user's data is segregated

### 7.2 Authentication

- **Basic Auth**: n8n interface (deprecated)
- **Session Tokens**: MCP session management
- **API Keys**: External service integration (optional)

---

## 8. Performance Optimizations

### 8.1 Caching Strategy

Multi-layer caching for optimal performance:

1. **Redis Cache**: Hot data and session state
2. **PostgreSQL Query Cache**: Prepared statements
3. **Vector Index Cache**: Qdrant in-memory indices
4. **LLM Context Cache**: Ollama model state

### 8.2 Processing Optimizations

- **Batch Processing**: 10 documents per cycle
- **Async Operations**: Non-blocking I/O throughout
- **Connection Pooling**: Database connection reuse
- **GPU Batching**: Vectorized operations on GPU

---

## 9. Monitoring and Maintenance

### 9.1 Health Checks

Automated health monitoring:

```python
Health Endpoints:
- /health: Overall system status
- /api/admin/stats: Detailed statistics
- /api/background/status: Processor status
```

### 9.2 Logging

Comprehensive logging strategy:

- **Application Logs**: FastAPI and MCP server
- **Database Logs**: Query performance tracking
- **Processing Logs**: Document pipeline status
- **Error Tracking**: Failure analysis and recovery

---

## 10. Future Enhancements

### Planned Improvements

1. **Multi-User Support**: Full user isolation and permissions
2. **Distributed Processing**: Horizontal scaling capabilities
3. **Advanced Analytics**: ML-based insight generation
4. **Plugin System**: Extensible tool framework
5. **Mobile Support**: Native mobile applications
6. **Federated Learning**: Privacy-preserving model updates

---

## Conclusion

FindersKeepers v2 represents a paradigm shift in personal AI knowledge management through its AI GOD MODE architecture. By combining persistent memory, local GPU acceleration, and direct integration patterns, the system achieves unprecedented reliability and performance for personal knowledge management.

The elimination of workflow automation dependencies in favor of direct FastAPI integration has resulted in 100% conversation capture rates and eliminated silent failures. The automatic background processing ensures the system is self-maintaining, while the comprehensive storage architecture provides multiple query modalities for knowledge retrieval.

This architecture positions FindersKeepers v2 as a robust, scalable, and intelligent personal AI assistant that truly remembers everything and learns from every interaction.

---

## Technical Contact

**System Owner**: bitcain (bitcain.net)  
**Platform**: Ubuntu Linux 24.04.2  
**GPU**: NVIDIA RTX 2080 Ti (CUDA Toolkit)  
**Docker Hub**: bitcainnet  

---

*Document Generated: August 9, 2025*  
*Architecture Version: 2.0 (AI GOD MODE)*  
*FindersKeepers v2 - Personal AI Knowledge Hub*
