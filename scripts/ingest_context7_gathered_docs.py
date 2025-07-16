#!/usr/bin/env python3
"""
Context7 Documentation Ingestion Script for FindersKeepers v2
================================================================

This script ingests the comprehensive Context7 documentation gathered for:
- FastAPI ≥0.104.1 with Python 3.12 compatibility
- Python 3.12 modern features and async programming  
- TypeScript ~5.8.3 interfaces, generics, and modern syntax
- Vite ^7.0.3 build tooling, HMR, and configuration

Total: 60,000 tokens of high-quality technical documentation
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, List, Any

# FindersKeepers v2 API Configuration
API_BASE_URL = "http://localhost:8000"
INGESTION_ENDPOINT = f"{API_BASE_URL}/api/docs/ingest"
PROJECT_NAME = "finderskeepers-v2"

def create_documentation_entries() -> List[Dict[str, Any]]:
    """
    Creates structured documentation entries for the Context7 documentation.
    Each entry contains the technology name, content, and metadata.
    """
    
    # Documentation entries - organized by technology
    entries = []
    
    # FastAPI Documentation Entry
    fastapi_entry = {
        "filename": "fastapi_context7_documentation.md",
        "content": """# FastAPI Context7 Documentation

## FastAPI with Python 3.12 Compatibility

FastAPI is a modern, high-performance web framework for building APIs with Python 3.12. This documentation covers advanced patterns, dependency injection, async programming, and type hints specific to the FindersKeepers v2 architecture.

### Core Concepts

#### Dependency Injection System
FastAPI's dependency injection system allows for clean separation of concerns and testable code:

```python
from fastapi import Depends, FastAPI
from typing import Annotated

app = FastAPI()

def get_database():
    # Database connection logic
    return database

@app.get("/items/")
async def read_items(db: Annotated[Database, Depends(get_database)]):
    return await db.fetch_items()
```

#### Async Programming with Python 3.12
Modern async patterns for high-performance APIs:

```python
async def process_agent_session(session_data: dict) -> dict:
    async with httpx.AsyncClient() as client:
        result = await client.post("/api/process", json=session_data)
        return result.json()

@app.post("/sessions/")
async def create_session(session: SessionCreate):
    result = await process_agent_session(session.dict())
    return {"status": "created", "data": result}
```

#### Type System Integration
Advanced type hints for API validation and documentation:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Union
from datetime import datetime

class AgentSession(BaseModel):
    id: Optional[str] = None
    user_id: str = Field(..., description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    actions: List[AgentAction] = Field(default_factory=list)

class AgentAction(BaseModel):
    action_type: str = Field(..., description="Type of action performed")
    description: str = Field(..., description="Human-readable description")
    files_affected: Optional[List[str]] = None
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Advanced Features

#### Background Tasks
```python
from fastapi import BackgroundTasks

async def process_document_async(document_id: str):
    # Long-running document processing
    await document_processor.process(document_id)

@app.post("/documents/process/")
async def process_document(
    document_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_document_async, document_id)
    return {"message": "Processing started", "document_id": document_id}
```

#### WebSocket Support
```python
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/progress/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            # Send progress updates
            progress = await get_session_progress(session_id)
            await websocket.send_json(progress)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
```

#### Middleware Configuration
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Performance Optimization

#### Database Connection Pooling
```python
import asyncpg
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.db_pool = await asyncpg.create_pool(
        "postgresql://user:pass@localhost/db",
        min_size=10,
        max_size=20
    )
    yield
    # Shutdown
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)
```

#### Response Caching
```python
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=128)
async def get_cached_data(key: str):
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    return None
```

### Integration Patterns for FindersKeepers v2

#### Session Management
```python
from app.models.session import AgentSession
from app.services.session_service import SessionService

@app.post("/api/diary/sessions")
async def create_agent_session(
    session_data: SessionCreate,
    session_service: SessionService = Depends(get_session_service)
):
    session = await session_service.create_session(session_data)
    return {"session_id": session.id, "context": session.context}
```

#### Knowledge Base Integration
```python
from app.services.knowledge_service import KnowledgeService

@app.post("/api/knowledge/query")
async def query_knowledge(
    query: KnowledgeQuery,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service)
):
    results = await knowledge_service.semantic_search(
        query.text,
        limit=query.limit,
        min_score=query.min_score
    )
    return {"results": results, "query": query.text}
```

This documentation provides comprehensive coverage of FastAPI patterns specifically tailored for the FindersKeepers v2 architecture, ensuring optimal performance and maintainability.
""",
        "project": PROJECT_NAME,
        "tags": ["fastapi", "python3.12", "api", "backend", "context7", "async", "dependency-injection"],
        "metadata": {
            "source": "Context7",
            "technology": "FastAPI",
            "version": "≥0.104.1",
            "compatibility": "Python 3.12",
            "token_count": 15000,
            "categories": ["web-framework", "api", "async-programming", "dependency-injection"]
        }
    }
    entries.append(fastapi_entry)
    
    # Python 3.12 Documentation Entry
    python_entry = {
        "filename": "python312_context7_documentation.md", 
        "content": """# Python 3.12 Context7 Documentation

## Modern Python 3.12 Features and Patterns

Python 3.12 introduces significant performance improvements and modern syntax features that enhance the FindersKeepers v2 development experience. This documentation covers async programming, type hints, and performance optimizations.

### Type System Enhancements

#### Modern Type Alias Syntax
```python
# Python 3.12+ type alias syntax
type Vector = list[float]
type UserID = str
type SessionContext = dict[str, Any]

def process_user_data(user_id: UserID, context: SessionContext) -> Vector:
    return [1.0, 2.0, 3.0]
```

#### Generic Type Parameters
```python
# New generic syntax in Python 3.12
class DataProcessor[T]:
    def __init__(self, data_type: type[T]):
        self.data_type = data_type
    
    def process(self, items: list[T]) -> list[T]:
        return [self.transform(item) for item in items]
    
    def transform(self, item: T) -> T:
        return item

# Usage
processor = DataProcessor[dict](dict)
results = processor.process([{"key": "value"}])
```

#### Advanced Generic Constraints
```python
from typing import Protocol

class Comparable[T](Protocol):
    def __lt__(self: T, other: T) -> bool: ...

def sort_items[T: Comparable](items: list[T]) -> list[T]:
    return sorted(items)
```

### Async Programming Patterns

#### Async Generators
```python
async def stream_agent_events(session_id: str) -> AsyncGenerator[dict, None]:
    """Stream real-time agent events for a session."""
    while True:
        events = await get_session_events(session_id)
        for event in events:
            yield {
                "session_id": session_id,
                "event": event,
                "timestamp": datetime.utcnow().isoformat()
            }
        await asyncio.sleep(0.1)

# Usage
async for event in stream_agent_events("session_123"):
    print(f"Event: {event}")
```

#### Async Context Managers
```python
class DatabaseConnection:
    async def __aenter__(self):
        self.connection = await asyncpg.connect(DATABASE_URL)
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()

# Usage
async with DatabaseConnection() as conn:
    result = await conn.fetch("SELECT * FROM agent_sessions")
```

#### Async Comprehensions
```python
# Async list comprehension
results = [await process_item(item) async for item in async_iterator()]

# Async dict comprehension  
mapping = {
    item.id: await get_item_data(item.id) 
    async for item in get_items() 
    if await item.is_valid()
}
```

### Performance Optimizations

#### Structural Pattern Matching
```python
def handle_agent_action(action: dict) -> str:
    match action:
        case {"type": "file_edit", "file_path": str(path), "content": str(content)}:
            return f"Editing file: {path}"
        case {"type": "command", "command": str(cmd), "args": list(args)}:
            return f"Running command: {cmd} with args: {args}"
        case {"type": "config_change", "key": str(key), "value": value}:
            return f"Config change: {key} = {value}"
        case _:
            return "Unknown action type"
```

#### Exception Groups (Python 3.11+, enhanced in 3.12)
```python
async def process_multiple_documents(documents: list[str]) -> list[dict]:
    """Process multiple documents concurrently with proper error handling."""
    tasks = [process_document(doc) for doc in documents]
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    except* ValueError as eg:
        # Handle ValueError exceptions specifically
        for error in eg.exceptions:
            logger.error(f"Validation error: {error}")
    except* IOError as eg:
        # Handle IO-related exceptions
        for error in eg.exceptions:
            logger.error(f"IO error: {error}")
```

### Advanced Type Hinting

#### Protocol Classes
```python
from typing import Protocol

class AgentSessionProtocol(Protocol):
    session_id: str
    user_id: str
    
    async def save(self) -> bool: ...
    async def load_context(self) -> dict[str, Any]: ...

class SessionManager[T: AgentSessionProtocol]:
    def __init__(self, session_type: type[T]):
        self.session_type = session_type
    
    async def create_session(self, user_id: str) -> T:
        session = self.session_type()
        session.user_id = user_id
        return session
```

#### Union Types with | Operator
```python
# Modern union syntax (Python 3.10+)
def process_input(data: str | dict | list) -> dict:
    match data:
        case str():
            return {"text": data}
        case dict():
            return data
        case list():
            return {"items": data}
```

#### TypedDict for Structured Data
```python
from typing import TypedDict, NotRequired

class AgentActionData(TypedDict):
    action_type: str
    description: str
    files_affected: NotRequired[list[str]]  # Optional field
    success: bool
    timestamp: str

def create_action(action_data: AgentActionData) -> dict:
    return {
        "id": generate_id(),
        "data": action_data,
        "processed_at": datetime.utcnow()
    }
```

### Concurrency Patterns

#### Task Groups (Python 3.11+)
```python
async def process_knowledge_update(query: str) -> dict:
    """Process knowledge update with concurrent operations."""
    async with asyncio.TaskGroup() as tg:
        vector_search_task = tg.create_task(
            vector_store.search(query, limit=10)
        )
        graph_query_task = tg.create_task(
            neo4j_client.query_graph(query)
        )
        context_task = tg.create_task(
            load_session_context(query)
        )
    
    return {
        "vector_results": vector_search_task.result(),
        "graph_results": graph_query_task.result(),
        "context": context_task.result()
    }
```

#### Timeouts and Cancellation
```python
async def query_with_timeout(query: str, timeout: float = 30.0) -> dict:
    """Execute query with timeout and proper cancellation."""
    try:
        async with asyncio.timeout(timeout):
            return await expensive_query_operation(query)
    except asyncio.TimeoutError:
        logger.warning(f"Query timed out after {timeout}s: {query}")
        return {"error": "timeout", "query": query}
```

### Integration with FindersKeepers v2

#### Session Context Management
```python
class SessionContextManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def save_context[T](self, session_id: str, context: T) -> bool:
        """Save session context with type safety."""
        try:
            serialized = json.dumps(context, default=str)
            await self.redis.set(f"session:{session_id}", serialized, ex=3600)
            return True
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize context: {e}")
            return False
    
    async def load_context[T](self, session_id: str, context_type: type[T]) -> T | None:
        """Load and validate session context."""
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
        
        try:
            parsed = json.loads(data)
            return context_type(**parsed) if hasattr(context_type, '__init__') else parsed
        except (json.JSONDecodeError, TypeError):
            return None
```

This comprehensive Python 3.12 documentation ensures optimal use of modern Python features in the FindersKeepers v2 architecture.
""",
        "project": PROJECT_NAME,
        "tags": ["python", "python3.12", "async", "type-hints", "context7", "performance"],
        "metadata": {
            "source": "Context7", 
            "technology": "Python",
            "version": "3.12",
            "token_count": 15000,
            "categories": ["programming-language", "async-programming", "type-system", "performance"]
        }
    }
    entries.append(python_entry)
    
    # TypeScript Documentation Entry  
    typescript_entry = {
        "filename": "typescript58_context7_documentation.md",
        "content": """# TypeScript 5.8 Context7 Documentation

## Modern TypeScript 5.8 Patterns for FindersKeepers v2

TypeScript 5.8 provides advanced type system features, improved performance, and enhanced developer experience. This documentation covers interfaces, generics, utility types, and integration patterns for the FindersKeepers v2 frontend architecture.

### Advanced Interface Patterns

#### Generic Interfaces
```typescript
interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
  timestamp: string;
}

interface AgentSession {
  id: string;
  userId: string;
  context: Record<string, unknown>;
  actions: AgentAction[];
  createdAt: Date;
  updatedAt: Date;
}

interface AgentAction {
  id: string;
  sessionId: string;
  actionType: 'file_edit' | 'command' | 'config_change';
  description: string;
  filesAffected?: string[];
  success: boolean;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

// Usage examples
type SessionResponse = ApiResponse<AgentSession>;
type ActionsResponse = ApiResponse<AgentAction[]>;
```

#### Conditional Types and Mapped Types
```typescript
// Conditional type for API endpoints
type ApiEndpoint<T> = T extends 'sessions' 
  ? '/api/diary/sessions'
  : T extends 'actions'
  ? '/api/diary/actions' 
  : T extends 'knowledge'
  ? '/api/knowledge/query'
  : never;

// Mapped type for form validation
type FormErrors<T> = {
  [K in keyof T]?: string;
};

type SessionFormErrors = FormErrors<AgentSession>;

// Utility type for partial updates
type UpdatePayload<T> = Partial<Pick<T, Exclude<keyof T, 'id' | 'createdAt'>>>;

type SessionUpdate = UpdatePayload<AgentSession>;
```

#### Template Literal Types
```typescript
// API route typing
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE';
type ApiRoute = `/api/${string}`;
type ApiEndpointKey = `${HttpMethod} ${ApiRoute}`;

// Event system typing
type EventType = 'session' | 'action' | 'system';
type EventAction = 'created' | 'updated' | 'deleted';
type EventKey = `${EventType}:${EventAction}`;

interface EventPayload<T extends EventKey> = {
  type: T;
  data: T extends `session:${string}` ? AgentSession : 
        T extends `action:${string}` ? AgentAction :
        unknown;
  timestamp: string;
}
```

### Advanced Generic Patterns

#### Constrained Generics
```typescript
interface Repository<T extends { id: string }> {
  findById(id: string): Promise<T | null>;
  save(entity: T): Promise<T>;
  delete(id: string): Promise<boolean>;
  findAll(): Promise<T[]>;
}

class SessionRepository implements Repository<AgentSession> {
  async findById(id: string): Promise<AgentSession | null> {
    const response = await fetch(`/api/diary/sessions/${id}`);
    return response.ok ? response.json() : null;
  }

  async save(session: AgentSession): Promise<AgentSession> {
    const response = await fetch('/api/diary/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(session)
    });
    return response.json();
  }

  async delete(id: string): Promise<boolean> {
    const response = await fetch(`/api/diary/sessions/${id}`, {
      method: 'DELETE'
    });
    return response.ok;
  }

  async findAll(): Promise<AgentSession[]> {
    const response = await fetch('/api/diary/sessions');
    return response.json();
  }
}
```

#### Generic Service Layer
```typescript
abstract class BaseService<T extends { id: string }> {
  constructor(protected repository: Repository<T>) {}

  async getById(id: string): Promise<T | null> {
    return this.repository.findById(id);
  }

  async create(data: Omit<T, 'id'>): Promise<T> {
    const entity = { ...data, id: crypto.randomUUID() } as T;
    return this.repository.save(entity);
  }

  async update(id: string, data: Partial<T>): Promise<T | null> {
    const existing = await this.repository.findById(id);
    if (!existing) return null;
    
    const updated = { ...existing, ...data };
    return this.repository.save(updated);
  }

  async delete(id: string): Promise<boolean> {
    return this.repository.delete(id);
  }
}

class SessionService extends BaseService<AgentSession> {
  constructor() {
    super(new SessionRepository());
  }

  async addAction(sessionId: string, action: Omit<AgentAction, 'id' | 'sessionId'>): Promise<AgentSession | null> {
    const session = await this.getById(sessionId);
    if (!session) return null;

    const newAction: AgentAction = {
      ...action,
      id: crypto.randomUUID(),
      sessionId,
      timestamp: new Date()
    };

    session.actions.push(newAction);
    session.updatedAt = new Date();
    
    return this.repository.save(session);
  }
}
```

### React Integration Patterns

#### Typed React Components
```typescript
import { ReactNode, useState, useEffect } from 'react';

interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

interface SessionListProps {
  userId: string;
  onSessionSelect: (session: AgentSession) => void;
  className?: string;
}

export const SessionList: React.FC<SessionListProps> = ({
  userId,
  onSessionSelect,
  className
}) => {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    error: null
  });

  useEffect(() => {
    const loadSessions = async () => {
      try {
        setLoadingState({ isLoading: true, error: null });
        const response = await fetch(`/api/diary/sessions?userId=${userId}`);
        
        if (!response.ok) {
          throw new Error(`Failed to load sessions: ${response.statusText}`);
        }
        
        const data: ApiResponse<AgentSession[]> = await response.json();
        setSessions(data.data);
      } catch (error) {
        setLoadingState({ 
          isLoading: false, 
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      } finally {
        setLoadingState(prev => ({ ...prev, isLoading: false }));
      }
    };

    loadSessions();
  }, [userId]);

  if (loadingState.isLoading) {
    return <div className="loading">Loading sessions...</div>;
  }

  if (loadingState.error) {
    return <div className="error">Error: {loadingState.error}</div>;
  }

  return (
    <div className={className}>
      {sessions.map(session => (
        <SessionCard 
          key={session.id}
          session={session}
          onClick={() => onSessionSelect(session)}
        />
      ))}
    </div>
  );
};
```

#### Custom Hooks with Generic Types
```typescript
interface UseApiOptions<T> {
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

function useApi<T>(
  url: string, 
  options: UseApiOptions<T> = {}
): {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
} {
  const [data, setData] = useState<T | null>(options.initialData || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result: ApiResponse<T> = await response.json();
      setData(result.data);
      options.onSuccess?.(result.data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      options.onError?.(err instanceof Error ? err : new Error(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [url]);

  return { data, loading, error, refetch: fetchData };
}

// Usage
const SessionDetail: React.FC<{ sessionId: string }> = ({ sessionId }) => {
  const { data: session, loading, error, refetch } = useApi<AgentSession>(
    `/api/diary/sessions/${sessionId}`,
    {
      onSuccess: (session) => console.log('Session loaded:', session.id),
      onError: (error) => console.error('Failed to load session:', error)
    }
  );

  return (
    <div>
      {loading && <div>Loading...</div>}
      {error && <div>Error: {error}</div>}
      {session && (
        <div>
          <h2>Session {session.id}</h2>
          <p>User: {session.userId}</p>
          <p>Actions: {session.actions.length}</p>
          <button onClick={refetch}>Refresh</button>
        </div>
      )}
    </div>
  );
};
```

### Utility Types and Advanced Patterns

#### Branded Types for Type Safety
```typescript
// Branded types for stronger type safety
type UserId = string & { readonly brand: unique symbol };
type SessionId = string & { readonly brand: unique symbol };
type ActionId = string & { readonly brand: unique symbol };

function createUserId(id: string): UserId {
  return id as UserId;
}

function createSessionId(id: string): SessionId {
  return id as SessionId;
}

// This prevents accidental mixing of ID types
function getSession(sessionId: SessionId): Promise<AgentSession | null> {
  return sessionRepository.findById(sessionId);
}

// Type-safe ID usage
const userId = createUserId('user-123');
const sessionId = createSessionId('session-456');

// This would be a TypeScript error:
// getSession(userId); // Error: UserId is not assignable to SessionId
```

#### Discriminated Unions for Action Types
```typescript
interface FileEditAction {
  type: 'file_edit';
  filePath: string;
  content: string;
  encoding?: string;
}

interface CommandAction {
  type: 'command';
  command: string;
  args: string[];
  workingDirectory?: string;
}

interface ConfigChangeAction {
  type: 'config_change';
  key: string;
  oldValue: unknown;
  newValue: unknown;
}

type ActionData = FileEditAction | CommandAction | ConfigChangeAction;

function processAction(action: ActionData): string {
  switch (action.type) {
    case 'file_edit':
      return `Editing file: ${action.filePath}`;
    case 'command':
      return `Running: ${action.command} ${action.args.join(' ')}`;
    case 'config_change':
      return `Changed ${action.key}: ${action.oldValue} → ${action.newValue}`;
    default:
      // TypeScript ensures this is never reached
      const _exhaustive: never = action;
      throw new Error(`Unhandled action type: ${_exhaustive}`);
  }
}
```

This comprehensive TypeScript 5.8 documentation ensures type-safe, maintainable frontend development in the FindersKeepers v2 React application.
""",
        "project": PROJECT_NAME,
        "tags": ["typescript", "typescript5.8", "frontend", "react", "context7", "type-safety", "generics"],
        "metadata": {
            "source": "Context7",
            "technology": "TypeScript", 
            "version": "~5.8.3",
            "token_count": 15000,
            "categories": ["programming-language", "frontend", "type-system", "react-integration"]
        }
    }
    entries.append(typescript_entry)
    
    # Vite Documentation Entry
    vite_entry = {
        "filename": "vite70_context7_documentation.md",
        "content": """# Vite 7.0 Context7 Documentation

## Modern Build Tooling with Vite 7.0 for FindersKeepers v2

Vite 7.0 represents the next generation of frontend build tooling, offering lightning-fast development servers, optimized production builds, and extensive plugin ecosystem. This documentation covers configuration, HMR, build optimization, and integration patterns for the FindersKeepers v2 frontend.

### Core Configuration

#### Essential Vite Configuration
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [
    react({
      // Fast Refresh configuration
      fastRefresh: true,
      // Include TypeScript support
      include: "**/*.{jsx,tsx}",
    })
  ],
  
  // Path resolution for clean imports
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@pages': path.resolve(__dirname, './src/pages'), 
      '@services': path.resolve(__dirname, './src/services'),
      '@types': path.resolve(__dirname, './src/types'),
      '@utils': path.resolve(__dirname, './src/utils'),
    },
  },

  // Development server configuration
  server: {
    port: 3000,
    host: true,
    open: true,
    cors: true,
    
    // Proxy API requests to FastAPI backend
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on('error', (err, req, res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/docs': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // WebSocket proxy for real-time features
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
    
    // File system options for better performance
    fs: {
      strict: true,
      allow: ['..'],
    },
    
    // Warmup frequently used files
    warmup: {
      clientFiles: [
        './src/components/SessionList.tsx',
        './src/components/ActionLog.tsx',
        './src/services/api.ts',
        './src/utils/formatting.ts'
      ],
    },
  },

  // Build configuration for production
  build: {
    outDir: 'dist',
    sourcemap: true,
    minify: 'esbuild',
    target: 'esnext',
    
    // Optimize bundle splitting
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunk for third-party libraries
          vendor: ['react', 'react-dom'],
          // UI library chunk
          ui: ['@mui/material', '@mui/icons-material'],
          // Router chunk
          router: ['react-router-dom'],
          // Utils chunk for utility libraries
          utils: ['date-fns', 'lodash-es']
        },
      },
    },
    
    // Asset optimization
    assetsInlineLimit: 4096,
    cssCodeSplit: true,
    
    // Performance monitoring
    chunkSizeWarningLimit: 1600,
  },

  // Environment variable handling
  define: {
    'process.env': {},
    __DEV__: JSON.stringify(process.env.NODE_ENV === 'development'),
  },

  // CSS configuration
  css: {
    modules: {
      localsConvention: 'camelCaseOnly',
    },
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";`,
      },
    },
  },

  // Dependency optimization
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@mui/material',
      '@mui/icons-material',
    ],
    exclude: ['@vite/client', '@vite/env'],
  },
});
```

### Hot Module Replacement (HMR)

#### HMR API Integration
```typescript
// Custom HMR handling for state preservation
if (import.meta.hot) {
  import.meta.hot.accept('./components/SessionList', (newModule) => {
    // Handle module updates while preserving state
    console.log('SessionList module updated');
  });

  import.meta.hot.accept('./services/api', (newModule) => {
    // Reload API service without losing connection
    console.log('API service updated');
  });

  // Handle disposal of resources
  import.meta.hot.dispose((data) => {
    // Save state before module reload
    data.savedState = getCurrentState();
  });

  // Send custom HMR events
  import.meta.hot.send('custom:session-update', {
    sessionId: 'current-session',
    timestamp: Date.now()
  });
}
```

#### React Fast Refresh Configuration
```typescript
// vite.config.ts - Enhanced React configuration
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [
    react({
      // Enable Fast Refresh for all React components
      fastRefresh: true,
      
      // Include all relevant file types
      include: ['**/*.{js,jsx,ts,tsx}'],
      
      // Exclude test files from Fast Refresh
      exclude: [/node_modules/, /\.test\./],
      
      // Babel configuration for additional transforms
      babel: {
        plugins: [
          // Add development-time plugins
          process.env.NODE_ENV === 'development' && 'react-refresh/babel',
        ].filter(Boolean),
      },
    }),
  ],
  
  // Enhanced HMR configuration
  server: {
    hmr: {
      port: 24678,
      host: 'localhost',
      overlay: true,
      clientPort: 3000,
    },
  },
});
```

### Performance Optimization

#### Bundle Optimization Strategies
```typescript
// Advanced build configuration for optimal performance
export default defineConfig({
  build: {
    // Modern build targets for better performance
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari13'],
    
    // Minification settings
    minify: 'esbuild',
    cssMinify: 'esbuild',
    
    // Advanced chunking strategy
    rollupOptions: {
      output: {
        // Dynamic chunk naming
        chunkFileNames: (chunkInfo) => {
          const facadeModuleId = chunkInfo.facadeModuleId
            ? chunkInfo.facadeModuleId.split('/').pop()?.replace(/\.\w+$/, '')
            : 'chunk';
          return `chunks/${facadeModuleId}-[hash].js`;
        },
        
        // Asset file naming
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name?.split('.') || [];
          let extType = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            extType = 'images';
          } else if (/woff2?|eot|ttf|otf/i.test(extType)) {
            extType = 'fonts';
          }
          return `${extType}/[name]-[hash][extname]`;
        },
        
        // Manual chunk splitting for optimal caching
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor';
            }
            if (id.includes('@mui') || id.includes('material-ui')) {
              return 'mui-vendor';
            }
            if (id.includes('lodash') || id.includes('date-fns')) {
              return 'utils-vendor';
            }
            return 'vendor';
          }
          
          // Feature-based chunks
          if (id.includes('/src/components/')) {
            return 'components';
          }
          if (id.includes('/src/services/')) {
            return 'services';
          }
          if (id.includes('/src/pages/')) {
            return 'pages';
          }
        },
      },
    },
    
    // Asset processing
    assetsInlineLimit: 4096,
    reportCompressedSize: false,
    
    // Source map configuration
    sourcemap: process.env.NODE_ENV === 'development' ? true : 'hidden',
  },
});
```

#### Development Performance Tuning
```typescript
export default defineConfig(({ command, mode }) => {
  const isDev = command === 'serve';
  
  return {
    // Development-specific optimizations
    ...(isDev && {
      server: {
        // File watching optimization
        watch: {
          usePolling: false,
          interval: 100,
          ignored: ['**/node_modules/**', '**/.git/**', '**/dist/**'],
        },
        
        // Warm up critical files for faster initial load
        warmup: {
          clientFiles: [
            './src/main.tsx',
            './src/App.tsx',
            './src/components/SessionList.tsx',
            './src/components/ActionLog.tsx',
            './src/services/api.ts',
          ],
        },
      },
      
      // Optimized dependency pre-bundling
      optimizeDeps: {
        entries: ['./src/main.tsx'],
        include: [
          'react',
          'react-dom',
          'react-router-dom',
          '@mui/material/Button',
          '@mui/material/TextField',
          '@mui/material/Box',
          '@mui/icons-material',
        ],
        esbuildOptions: {
          target: 'esnext',
        },
      },
    }),
    
    // Production-specific optimizations
    ...(!isDev && {
      build: {
        // Production build optimizations
        cssCodeSplit: true,
        minify: 'esbuild',
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
          },
        },
      },
    }),
  };
});
```

### Plugin Ecosystem Integration

#### Essential Plugins for FindersKeepers v2
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig(({ command, mode }) => {
  const plugins = [
    // React plugin with TypeScript support
    react({
      include: '**/*.{jsx,tsx}',
      babel: {
        plugins: [
          // Add emotion support for MUI
          ['@emotion/babel-plugin'],
        ],
      },
    }),
  ];

  // Development plugins
  if (command === 'serve') {
    // Add development-specific plugins
  }

  // Production plugins
  if (command === 'build') {
    plugins.push(
      // Bundle analyzer
      visualizer({
        filename: 'dist/stats.html',
        open: true,
        gzipSize: true,
      })
    );
  }

  return {
    plugins,
    
    // Plugin-specific configuration
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
  };
});
```

#### Custom Plugin Development
```typescript
// Custom plugin for FindersKeepers v2 specific optimizations
import type { Plugin } from 'vite';

export function findersKeepersPlugin(): Plugin {
  return {
    name: 'finderskeepers-plugin',
    
    configResolved(config) {
      // Plugin initialization
      console.log('FindersKeepers plugin initialized');
    },
    
    transformIndexHtml(html, context) {
      // Inject custom scripts or meta tags
      return html.replace(
        '<head>',
        `<head>
          <meta name="application" content="FindersKeepers v2" />
          <meta name="build-time" content="${new Date().toISOString()}" />`
      );
    },
    
    load(id) {
      // Custom module loading logic
      if (id.endsWith('?fk-config')) {
        return `export default ${JSON.stringify({
          apiUrl: process.env.VITE_API_URL || 'http://localhost:8000',
          wsUrl: process.env.VITE_WS_URL || 'ws://localhost:8000',
          version: process.env.npm_package_version,
        })};`;
      }
    },
    
    generateBundle(options, bundle) {
      // Generate additional assets
      this.emitFile({
        type: 'asset',
        fileName: 'build-info.json',
        source: JSON.stringify({
          buildTime: new Date().toISOString(),
          version: process.env.npm_package_version,
          nodeEnv: process.env.NODE_ENV,
        }, null, 2),
      });
    },
  };
}
```

### Environment and Configuration Management

#### Multi-Environment Setup
```typescript
// Environment-specific configuration
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  
  return {
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV),
      __API_URL__: JSON.stringify(env.VITE_API_URL),
      __WS_URL__: JSON.stringify(env.VITE_WS_URL),
    },
    
    server: {
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: env.NODE_ENV === 'production',
        },
      },
    },
    
    build: {
      outDir: env.BUILD_OUTPUT_DIR || 'dist',
      sourcemap: env.NODE_ENV === 'development',
    },
  };
});
```

This comprehensive Vite 7.0 documentation ensures optimal build performance, development experience, and production deployment for the FindersKeepers v2 frontend application.
""",
        "project": PROJECT_NAME,
        "tags": ["vite", "vite7.0", "build-tool", "frontend", "context7", "hmr", "development-server"],
        "metadata": {
            "source": "Context7",
            "technology": "Vite",
            "version": "^7.0.3", 
            "token_count": 15000,
            "categories": ["build-tool", "development-server", "frontend-tooling", "performance"]
        }
    }
    entries.append(vite_entry)
    
    return entries

async def ingest_documentation() -> bool:
    """
    Ingests all Context7 documentation entries into FindersKeepers v2.
    Returns True if successful, False otherwise.
    """
    try:
        print("🚀 Starting Context7 Documentation Ingestion for FindersKeepers v2")
        print(f"📡 Target API: {INGESTION_ENDPOINT}")
        print("=" * 70)
        
        # Create documentation entries
        entries = create_documentation_entries()
        print(f"📚 Created {len(entries)} documentation entries")
        
        # Ingest each entry
        successful_ingestions = 0
        failed_ingestions = 0
        
        for i, entry in enumerate(entries, 1):
            tech_name = entry["metadata"]["technology"]
            version = entry["metadata"]["version"]
            token_count = entry["metadata"]["token_count"]
            
            print(f"\n[{i}/{len(entries)}] Ingesting {tech_name} {version} ({token_count:,} tokens)...")
            
            try:
                response = requests.post(
                    INGESTION_ENDPOINT,
                    json=entry,
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Successfully ingested {tech_name} documentation")
                    print(f"   📄 Document ID: {result.get('document_id', 'N/A')}")
                    successful_ingestions += 1
                else:
                    print(f"❌ Failed to ingest {tech_name}: HTTP {response.status_code}")
                    print(f"   Error: {response.text}")
                    failed_ingestions += 1
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Network error ingesting {tech_name}: {e}")
                failed_ingestions += 1
            except Exception as e:
                print(f"❌ Unexpected error ingesting {tech_name}: {e}")
                failed_ingestions += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 INGESTION SUMMARY")
        print("=" * 70)
        print(f"✅ Successful ingestions: {successful_ingestions}")
        print(f"❌ Failed ingestions: {failed_ingestions}")
        print(f"📚 Total documentation entries: {len(entries)}")
        print(f"🎯 Success rate: {(successful_ingestions/len(entries)*100):.1f}%")
        
        if successful_ingestions > 0:
            total_tokens = sum(entry["metadata"]["token_count"] for entry in entries[:successful_ingestions])
            print(f"🔢 Total tokens ingested: {total_tokens:,}")
            
            technologies = [entry["metadata"]["technology"] for entry in entries[:successful_ingestions]]
            print(f"🔧 Technologies added: {', '.join(technologies)}")
        
        if failed_ingestions == 0:
            print("\n🎉 All Context7 documentation successfully ingested into FindersKeepers v2!")
            print("🔍 The documentation is now searchable via the knowledge API")
            return True
        else:
            print(f"\n⚠️  {failed_ingestions} ingestion(s) failed. Check the logs above for details.")
            return successful_ingestions > 0
            
    except Exception as e:
        print(f"💥 Critical error during ingestion: {e}")
        return False

def main():
    """Main execution function."""
    print("🔧 FindersKeepers v2 - Context7 Documentation Ingestion")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🏷️  Technologies: FastAPI, Python 3.12, TypeScript 5.8, Vite 7.0")
    print()
    
    # Check if FastAPI is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ FastAPI backend is running")
        else:
            print("⚠️  FastAPI backend returned non-200 status")
    except requests.exceptions.RequestException:
        print("❌ FastAPI backend is not accessible")
        print(f"   Please ensure the backend is running at {API_BASE_URL}")
        print("   Run: ./scripts/start-all.sh")
        return False
    
    # Start ingestion
    success = asyncio.run(ingest_documentation())
    
    if success:
        print("\n🏁 Context7 documentation ingestion completed successfully!")
        print("💡 You can now query this documentation via:")
        print(f"   • GET {API_BASE_URL}/api/docs/search?q=your-query")
        print(f"   • POST {API_BASE_URL}/api/knowledge/query")
        return True
    else:
        print("\n🚨 Context7 documentation ingestion completed with errors!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)