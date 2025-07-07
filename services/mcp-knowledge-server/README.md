# FindersKeepers v2 MCP Knowledge Server

An MCP (Model Context Protocol) server that provides AI agents with natural language access to the FindersKeepers knowledge base.

## Features

- 🔍 **Semantic Search**: Natural language document search using vector embeddings
- 🧠 **Knowledge Graph**: Query entity relationships and connections
- 📋 **Session Context**: Retrieve agent session history and activity
- 🔗 **Similarity Analysis**: Find related documents based on content
- 📊 **Project Overview**: Comprehensive project statistics and insights

## Installation

```bash
cd services/mcp-knowledge-server
pip install -e .
```

## Configuration

The server uses environment variables or defaults:

```bash
# PostgreSQL connection
POSTGRES_URL=postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2

# Neo4j connection  
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fk2025neo4j

# Qdrant connection
QDRANT_URL=http://localhost:6333

# Redis connection
REDIS_URL=redis://localhost:6379

# FastAPI embeddings service
FASTAPI_URL=http://localhost:8000
```

## Running the Server

```bash
# From the project root
python -m src.knowledge_server

# Or directly
cd services/mcp-knowledge-server
python src/knowledge_server.py
```

## Available Tools

### search_documents
Search documents using semantic similarity:
```
search_documents(
  query="Docker GPU configuration",
  project="finderskeepers",
  tags=["configuration"],
  limit=10,
  min_score=0.5
)
```

### query_knowledge_graph
Query the Neo4j knowledge graph:
```
query_knowledge_graph(
  question="What entities relate to authentication?",
  entity_types=["procedure", "component"],
  max_depth=2,
  limit=20
)
```

### get_session_context
Retrieve agent session history:
```
get_session_context(
  agent_type="claude",
  project="finderskeepers",
  recent_actions=10,
  include_files=true
)
```

### analyze_document_similarity
Find similar documents:
```
analyze_document_similarity(
  document_id="doc_12345",
  similarity_threshold=0.7,
  limit=8,
  include_content=false
)
```

### get_project_overview
Get comprehensive project statistics:
```
get_project_overview(
  project="finderskeepers",
  include_recent_activity=true,
  activity_days=7
)
```

## Available Resources

- **schema://database** - PostgreSQL database schema documentation
- **stats://knowledge-base** - Comprehensive knowledge base statistics
- **guide://knowledge-search** - Search strategy guide and tips

## Integration with Claude Code

Add to your `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "finderskeepers-knowledge": {
      "command": "python",
      "args": ["/path/to/services/mcp-knowledge-server/src/knowledge_server.py"]
    }
  }
}
```

Then in Claude Code:
```
"Search our knowledge base for Docker GPU setup"
"What do we know about FastAPI authentication?"
"Show me recent agent activity for this project"
```

## Architecture

The MCP server acts as a bridge between AI agents and the FindersKeepers v2 data layer:

```
AI Agent (Claude) <-> MCP Protocol <-> Knowledge Server
                                             |
                    +------------------------+------------------------+
                    |            |                       |            |
              PostgreSQL      Neo4j                 Qdrant        Redis
            (metadata)    (graph)              (vectors)      (cache)
```

## Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/
isort src/
```

## License

Part of FindersKeepers v2 - Personal AI Agent Knowledge Hub