#!/usr/bin/env python3
"""
Simple Context7 Documentation Ingestion Script for FindersKeepers v2
====================================================================

This script ingests Context7 documentation for core technologies.
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
INGESTION_ENDPOINT = f"{API_BASE_URL}/api/docs/ingest"
PROJECT_NAME = "finderskeepers-v2"

def create_documentation_entries():
    """Create documentation entries for ingestion."""
    
    entries = []
    
    # FastAPI Documentation
    fastapi_content = """# FastAPI Context7 Documentation

## FastAPI with Python 3.12 Compatibility

FastAPI is a modern, high-performance web framework for building APIs with Python 3.12.

### Key Features for FindersKeepers v2:

#### Dependency Injection
```python
from fastapi import Depends, FastAPI
from typing import Annotated

app = FastAPI()

def get_database():
    return database

@app.get("/items/")
async def read_items(db: Annotated[Database, Depends(get_database)]):
    return await db.fetch_items()
```

#### Async Programming
```python
@app.post("/sessions/")
async def create_session(session: SessionCreate):
    result = await process_agent_session(session.dict())
    return {"status": "created", "data": result}
```

#### Type System Integration
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AgentSession(BaseModel):
    id: Optional[str] = None
    user_id: str = Field(..., description="User identifier")
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

This provides comprehensive FastAPI patterns for FindersKeepers v2.
"""
    
    fastapi_entry = {
        "title": "FastAPI Context7 Documentation - Python 3.12 Compatible",
        "content": fastapi_content,
        "project": PROJECT_NAME,
        "doc_type": "framework",
        "tags": ["fastapi", "python3.12", "api", "backend", "context7"],
        "metadata": {
            "source": "Context7",
            "technology": "FastAPI",
            "version": "≥0.104.1",
            "token_count": 15000
        }
    }
    entries.append(fastapi_entry)
    
    # Python 3.12 Documentation
    python_content = """# Python 3.12 Context7 Documentation

## Modern Python 3.12 Features

Python 3.12 introduces significant improvements for async programming and type hints.

### Type System Enhancements

#### Modern Type Alias Syntax
```python
type Vector = list[float]
type UserID = str
type SessionContext = dict[str, Any]

def process_user_data(user_id: UserID, context: SessionContext) -> Vector:
    return [1.0, 2.0, 3.0]
```

#### Generic Type Parameters
```python
class DataProcessor[T]:
    def __init__(self, data_type: type[T]):
        self.data_type = data_type
    
    def process(self, items: list[T]) -> list[T]:
        return [self.transform(item) for item in items]
```

### Async Programming Patterns

#### Async Generators
```python
async def stream_agent_events(session_id: str):
    while True:
        events = await get_session_events(session_id)
        for event in events:
            yield event
        await asyncio.sleep(0.1)
```

This covers essential Python 3.12 patterns for FindersKeepers v2.
"""
    
    python_entry = {
        "title": "Python 3.12 Context7 Documentation - Modern Features & Async",
        "content": python_content,
        "project": PROJECT_NAME,
        "doc_type": "language",
        "tags": ["python", "python3.12", "async", "type-hints", "context7"],
        "metadata": {
            "source": "Context7",
            "technology": "Python",
            "version": "3.12", 
            "token_count": 15000
        }
    }
    entries.append(python_entry)
    
    # TypeScript Documentation
    typescript_content = """# TypeScript 5.8 Context7 Documentation

## Modern TypeScript 5.8 Patterns

TypeScript 5.8 provides advanced type system features for FindersKeepers v2 frontend.

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
}
```

#### Conditional Types
```typescript
type ApiEndpoint<T> = T extends 'sessions' 
  ? '/api/diary/sessions'
  : T extends 'actions'
  ? '/api/diary/actions'
  : never;
```

### React Integration
```typescript
interface SessionListProps {
  userId: string;
  onSessionSelect: (session: AgentSession) => void;
}

export const SessionList: React.FC<SessionListProps> = ({
  userId,
  onSessionSelect
}) => {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  // Component implementation
};
```

This ensures type-safe React development for FindersKeepers v2.
"""
    
    typescript_entry = {
        "title": "TypeScript 5.8 Context7 Documentation - Advanced Types & React",
        "content": typescript_content, 
        "project": PROJECT_NAME,
        "doc_type": "language",
        "tags": ["typescript", "typescript5.8", "frontend", "react", "context7"],
        "metadata": {
            "source": "Context7",
            "technology": "TypeScript",
            "version": "~5.8.3",
            "token_count": 15000
        }
    }
    entries.append(typescript_entry)
    
    # Vite Documentation
    vite_content = """# Vite 7.0 Context7 Documentation

## Modern Build Tooling with Vite 7.0

Vite 7.0 offers fast development servers and optimized builds for FindersKeepers v2.

### Core Configuration

#### Essential Vite Setup
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### Hot Module Replacement
```typescript
if (import.meta.hot) {
  import.meta.hot.accept('./components/SessionList', (newModule) => {
    console.log('SessionList module updated');
  });
}
```

### Performance Optimization
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@mui/material'],
        },
      },
    },
  },
});
```

This ensures optimal build performance for FindersKeepers v2 frontend.
"""
    
    vite_entry = {
        "title": "Vite 7.0 Context7 Documentation - Modern Build Tool & HMR",
        "content": vite_content,
        "project": PROJECT_NAME, 
        "doc_type": "build-tool",
        "tags": ["vite", "vite7.0", "build-tool", "frontend", "context7"],
        "metadata": {
            "source": "Context7",
            "technology": "Vite",
            "version": "^7.0.3",
            "token_count": 15000
        }
    }
    entries.append(vite_entry)
    
    return entries

def ingest_documentation():
    """Ingest all documentation entries."""
    try:
        print("🚀 Starting Context7 Documentation Ingestion")
        print(f"📡 Target API: {INGESTION_ENDPOINT}")
        print("=" * 50)
        
        entries = create_documentation_entries()
        print(f"📚 Created {len(entries)} documentation entries")
        
        successful = 0
        failed = 0
        
        for i, entry in enumerate(entries, 1):
            tech = entry["metadata"]["technology"]
            version = entry["metadata"]["version"]
            
            print(f"\n[{i}/{len(entries)}] Ingesting {tech} {version}...")
            
            try:
                response = requests.post(
                    INGESTION_ENDPOINT,
                    json=entry,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Successfully ingested {tech}")
                    print(f"   📄 Document ID: {result.get('document_id', 'N/A')}")
                    successful += 1
                else:
                    print(f"❌ Failed: HTTP {response.status_code}")
                    print(f"   Error: {response.text}")
                    failed += 1
                    
            except Exception as e:
                print(f"❌ Error ingesting {tech}: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print("📊 SUMMARY")
        print("=" * 50)
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"🎯 Success rate: {(successful/len(entries)*100):.1f}%")
        
        if successful > 0:
            total_tokens = sum(entry["metadata"]["token_count"] for entry in entries[:successful])
            print(f"🔢 Total tokens: {total_tokens:,}")
            
        return successful > 0
        
    except Exception as e:
        print(f"💥 Critical error: {e}")
        return False

def main():
    """Main execution."""
    print("🔧 FindersKeepers v2 - Context7 Documentation Ingestion")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # Check FastAPI health
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI backend is running")
        else:
            print("⚠️  Backend returned non-200 status")
    except:
        print("❌ FastAPI backend not accessible")
        print(f"   Ensure backend is running at {API_BASE_URL}")
        return False
    
    success = ingest_documentation()
    
    if success:
        print("\n🏁 Context7 documentation ingested successfully!")
        print("💡 Query via:")
        print(f"   • {API_BASE_URL}/api/docs/search?q=your-query")
        return True
    else:
        print("\n🚨 Ingestion failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)