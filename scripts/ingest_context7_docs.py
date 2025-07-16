#!/usr/bin/env python3
"""
Direct Context7 Documentation Ingestion Script

This script takes the documentation we gathered from Context7 and ingests it
directly into FindersKeepers v2 knowledge base using the FastAPI ingestion endpoint.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Dict

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectDocumentIngester:
    """Directly ingest documentation into FindersKeepers v2."""
    
    def __init__(self, fastapi_url: str = "http://localhost:8000"):
        self.fastapi_url = fastapi_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.success_count = 0
        self.failure_count = 0
    
    async def ingest_document(self, title: str, content: str, tags: List[str], 
                            project: str = "finderskeepers-v2") -> bool:
        """Ingest a document into the knowledge base via FastAPI."""
        try:
            payload = {
                "filename": f"{title.lower().replace(' ', '_').replace('/', '_')}.md",
                "content": content,
                "project": project,
                "tags": tags,
                "metadata": {
                    "doc_type": "technology_documentation",
                    "source": "context7_manual_ingestion",
                    "ingestion_date": datetime.utcnow().isoformat(),
                    "technology": title
                }
            }
            
            response = await self.client.post(
                f"{self.fastapi_url}/api/docs/ingest",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Successfully ingested: {title}")
                self.success_count += 1
                return True
            else:
                logger.error(f"❌ Failed to ingest {title}: {response.status_code} - {response.text}")
                self.failure_count += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception ingesting {title}: {e}")
            self.failure_count += 1
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

# Context7 Documentation Data
DOCUMENTATION_ENTRIES = [
    {
        "title": "FastAPI Core Framework",
        "content": """# FastAPI Core Framework for FindersKeepers v2

## Overview
FastAPI is the core backend framework for FindersKeepers v2, providing high-performance API endpoints for agent session tracking, knowledge queries, and document management.

## Key Features in Our Implementation

### Dependency Injection
- Used extensively for database connections, authentication, and shared services
- Example: Database session injection for consistent connection management

### Async Support
- All endpoints use async/await for non-blocking I/O operations
- Critical for concurrent document processing and vector operations

### Automatic API Documentation
- OpenAPI specification automatically generated
- Interactive docs available at `/docs` endpoint

## Core Usage Patterns

### Path Operations
```python
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/api/docs/search")
async def search_documents(query: str, limit: int = 10):
    # Vector search implementation
    return results
```

### Dependency Injection
```python
from fastapi import Depends

async def get_db_session():
    # Database connection logic
    yield session

@app.post("/api/diary/sessions")
async def create_session(session_data: dict, db = Depends(get_db_session)):
    # Use injected database session
    return result
```

### Background Tasks
```python
from fastapi import BackgroundTasks

@app.post("/api/docs/ingest")
async def ingest_document(doc: dict, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_embeddings, doc)
    return {"status": "processing"}
```

## Integration Points
- **Database**: AsyncPG for PostgreSQL, Neo4j Python Driver
- **Vector Operations**: Qdrant client for similarity search
- **Authentication**: OAuth2 with JWT tokens
- **Real-time**: WebSocket support for live updates

## Performance Optimizations
- Connection pooling for database operations
- Async processing for I/O-bound operations
- Background tasks for heavy computations
- Response caching for frequent queries

## Error Handling
- Custom exception handlers for graceful error responses
- Structured logging for debugging and monitoring
- Health check endpoints for service monitoring
""",
        "tags": ["fastapi", "backend", "api", "python", "async", "dependency-injection"]
    },
    
    {
        "title": "Neo4j Graph Database Integration",
        "content": """# Neo4j Graph Database Integration for FindersKeepers v2

## Overview
Neo4j serves as the knowledge graph backbone for FindersKeepers v2, storing entity relationships, document connections, and semantic links between AI agent sessions.

## Core Implementation

### Python Driver Setup
```python
from neo4j import GraphDatabase

class Neo4jService:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    async def create_document_relationships(self, doc_id, entities):
        async with self.driver.session() as session:
            await session.run("""
                MATCH (d:Document {id: $doc_id})
                UNWIND $entities AS entity
                MERGE (e:Entity {name: entity.name, type: entity.type})
                MERGE (d)-[:MENTIONS]->(e)
            """, doc_id=doc_id, entities=entities)
```

### Knowledge Graph Structure
- **Document Nodes**: Represent ingested documents with metadata
- **Entity Nodes**: Extracted concepts, people, technologies
- **Session Nodes**: AI agent interaction sessions
- **Project Nodes**: Group related documents and sessions

### Key Relationships
- `BELONGS_TO`: Documents → Projects
- `MENTIONS`: Documents → Entities
- `CREATED_IN`: Sessions → Projects
- `REFERENCES`: Sessions → Documents
- `DERIVED_FROM`: Entities → Documents

## Cypher Queries for Knowledge Retrieval

### Find Related Documents
```cypher
MATCH (d1:Document)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(d2:Document)
WHERE d1.id = $document_id AND d1 <> d2
RETURN d2, count(e) as shared_entities
ORDER BY shared_entities DESC
```

### Session Context Discovery
```cypher
MATCH (s:Session)-[:REFERENCES]->(d:Document)-[:MENTIONS]->(e:Entity)
WHERE s.id = $session_id
RETURN e.name, e.type, count(d) as frequency
ORDER BY frequency DESC
```

### Knowledge Graph Analytics
```cypher
MATCH (d:Document)-[:MENTIONS]->(e:Entity)
RETURN e.type, count(d) as document_count
ORDER BY document_count DESC
```

## Integration with FastAPI
- Async session management for concurrent operations
- Connection pooling for optimal performance
- Error handling with graceful fallbacks
- Health checks for service monitoring

## Performance Considerations
- Index on frequently queried properties
- Batch operations for bulk updates
- Connection pooling for multiple concurrent requests
- Query optimization using PROFILE and EXPLAIN

## Monitoring and Maintenance
- Regular index maintenance
- Query performance monitoring
- Connection health checks
- Backup and recovery procedures
""",
        "tags": ["neo4j", "graph-database", "cypher", "knowledge-graph", "relationships"]
    },
    
    {
        "title": "Qdrant Vector Database Operations",
        "content": """# Qdrant Vector Database Operations for FindersKeepers v2

## Overview
Qdrant provides high-performance vector similarity search for FindersKeepers v2, enabling semantic document retrieval and intelligent knowledge discovery.

## Core Setup and Configuration

### Python Client Initialization
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Initialize client
client = QdrantClient("http://localhost:6333")

# Create collection
client.create_collection(
    collection_name="fk2_documents",
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)
```

### Document Ingestion Pipeline
```python
async def store_document_embeddings(doc_id: str, chunks: List[dict]):
    points = []
    for i, chunk in enumerate(chunks):
        point = PointStruct(
            id=f"{doc_id}_{i}",
            vector=chunk["embedding"],
            payload={
                "document_id": doc_id,
                "chunk_index": i,
                "content": chunk["text"][:500],
                "project": "finderskeepers-v2"
            }
        )
        points.append(point)
    
    await client.upsert(collection_name="fk2_documents", points=points)
```

## Similarity Search Operations

### Basic Vector Search
```python
async def search_similar_content(query_vector: List[float], limit: int = 10):
    search_result = await client.search(
        collection_name="fk2_documents",
        query_vector=query_vector,
        limit=limit,
        score_threshold=0.7
    )
    return search_result
```

### Filtered Search
```python
async def search_with_filters(query_vector: List[float], project: str = None):
    filter_conditions = []
    if project:
        filter_conditions.append({
            "key": "project",
            "match": {"value": project}
        })
    
    results = await client.search(
        collection_name="fk2_documents",
        query_vector=query_vector,
        query_filter={"must": filter_conditions} if filter_conditions else None,
        limit=20
    )
    return results
```

## Integration with FindersKeepers v2

### Embedding Generation
- OpenAI text-embedding-3-small for document chunks
- Consistent embedding dimensions (1536)
- Batch processing for efficiency

### Search Endpoints
- `/api/docs/search` - Semantic document search
- `/api/knowledge/query` - Natural language queries
- `/api/docs/similar` - Find similar documents

### Performance Optimization
- Chunk size optimization (200-500 tokens)
- Batch upsert operations
- Connection pooling
- Index optimization

## Collection Management

### Health Monitoring
```python
async def check_collection_health():
    info = await client.get_collection("fk2_documents")
    return {
        "status": info.status,
        "vectors_count": info.vectors_count,
        "segments_count": info.segments_count
    }
```

### Backup and Recovery
```python
# Create snapshot
await client.create_snapshot("fk2_documents")

# List snapshots
snapshots = await client.list_snapshots("fk2_documents")
```

## Best Practices
- Regular index optimization
- Monitoring query performance
- Embedding consistency checks
- Graceful error handling
- Connection health verification
""",
        "tags": ["qdrant", "vector-database", "similarity-search", "embeddings", "semantic-search"]
    },
    
    {
        "title": "React Frontend Architecture",
        "content": """# React Frontend Architecture for FindersKeepers v2

## Overview
React powers the FindersKeepers v2 user interface, providing an interactive dashboard for managing AI agent sessions, browsing knowledge, and monitoring system performance.

## Core Architecture Patterns

### Component Structure
```jsx
// Main application component
import { useState, useEffect } from 'react';
import { ThemeProvider } from '@mui/material/styles';

function App() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  
  useEffect(() => {
    // Load initial data
    loadUserSessions();
  }, []);
  
  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Header user={user} />
        <Routes>
          <Route path="/sessions" element={<SessionDashboard />} />
          <Route path="/knowledge" element={<KnowledgeExplorer />} />
          <Route path="/monitoring" element={<SystemMonitoring />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
```

### State Management with Hooks
```jsx
// Custom hook for session management
import { useState, useCallback } from 'react';

export function useSessionManager() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const createSession = useCallback(async (sessionData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/diary/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      });
      const newSession = await response.json();
      setSessions(prev => [...prev, newSession]);
    } finally {
      setLoading(false);
    }
  }, []);
  
  return { sessions, createSession, loading };
}
```

## Key Components

### Session Dashboard
- Real-time session monitoring
- Interactive session timeline
- Performance metrics visualization
- Action logging and filtering

### Knowledge Explorer
- Document search interface
- Graph visualization of relationships
- Similar document recommendations
- Tag-based filtering

### System Monitoring
- Service health indicators
- Database performance metrics
- API response times
- Error rate tracking

## Integration Patterns

### API Communication
```jsx
// API client with error handling
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }
  
  async request(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });
      
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
}
```

### WebSocket Integration
```jsx
// Real-time updates
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

export function useRealTimeUpdates() {
  const [socket, setSocket] = useState(null);
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    const newSocket = io('http://localhost:8000');
    setSocket(newSocket);
    
    newSocket.on('session_update', (data) => {
      setNotifications(prev => [...prev, data]);
    });
    
    return () => newSocket.close();
  }, []);
  
  return { notifications, socket };
}
```

## Performance Optimization

### Code Splitting
```jsx
import { lazy, Suspense } from 'react';

const SessionDashboard = lazy(() => import('./SessionDashboard'));
const KnowledgeExplorer = lazy(() => import('./KnowledgeExplorer'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/sessions" element={<SessionDashboard />} />
        <Route path="/knowledge" element={<KnowledgeExplorer />} />
      </Routes>
    </Suspense>
  );
}
```

### Memoization
```jsx
import { useMemo, useCallback } from 'react';

function DocumentList({ documents, filter }) {
  const filteredDocs = useMemo(() => {
    return documents.filter(doc => 
      doc.title.toLowerCase().includes(filter.toLowerCase())
    );
  }, [documents, filter]);
  
  const handleDocumentClick = useCallback((docId) => {
    // Navigate to document details
  }, []);
  
  return (
    <div>
      {filteredDocs.map(doc => (
        <DocumentCard 
          key={doc.id} 
          document={doc} 
          onClick={handleDocumentClick}
        />
      ))}
    </div>
  );
}
```

## Testing Strategy
- Component unit tests with Testing Library
- Integration tests for API communication
- E2E tests for critical user workflows
- Visual regression testing for UI consistency

## Build and Deployment
- Vite for fast development and building
- TypeScript for type safety
- ESLint and Prettier for code quality
- Docker containerization for deployment
""",
        "tags": ["react", "frontend", "javascript", "hooks", "components", "ui"]
    },
    
    {
        "title": "Material-UI Component System",
        "content": """# Material-UI Component System for FindersKeepers v2

## Overview
Material-UI (MUI) provides the component foundation for FindersKeepers v2's user interface, ensuring consistent design, accessibility, and responsive behavior across all screens.

## Theme Configuration

### Custom Theme Setup
```jsx
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    body1: {
      fontSize: '1rem',
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {/* Your app components */}
    </ThemeProvider>
  );
}
```

## Core Components Usage

### Layout Components
```jsx
import { 
  AppBar, 
  Toolbar, 
  Drawer, 
  Container, 
  Grid, 
  Paper 
} from '@mui/material';

function DashboardLayout() {
  return (
    <>
      <AppBar position="fixed">
        <Toolbar>
          <Typography variant="h6">FindersKeepers v2</Typography>
        </Toolbar>
      </AppBar>
      
      <Drawer variant="permanent" sx={{ width: 240 }}>
        <NavigationMenu />
      </Drawer>
      
      <Container maxWidth="lg" sx={{ mt: 8, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <MainContent />
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2 }}>
              <Sidebar />
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </>
  );
}
```

### Data Display Components
```jsx
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip,
  Avatar
} from '@mui/material';

function SessionTable({ sessions }) {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Session ID</TableCell>
            <TableCell>Agent Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Created</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id}>
              <TableCell>{session.id}</TableCell>
              <TableCell>
                <Chip 
                  avatar={<Avatar>{session.agent_type[0]}</Avatar>}
                  label={session.agent_type}
                  size="small"
                />
              </TableCell>
              <TableCell>
                <Chip 
                  label={session.status}
                  color={session.status === 'active' ? 'success' : 'default'}
                />
              </TableCell>
              <TableCell>{session.created_at}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
```

### Form Components
```jsx
import { 
  TextField, 
  Button, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  Box
} from '@mui/material';

function DocumentUploadForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    title: '',
    project: '',
    tags: ''
  });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };
  
  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      <TextField
        fullWidth
        label="Document Title"
        value={formData.title}
        onChange={(e) => setFormData({...formData, title: e.target.value})}
        margin="normal"
        required
      />
      
      <FormControl fullWidth margin="normal">
        <InputLabel>Project</InputLabel>
        <Select
          value={formData.project}
          onChange={(e) => setFormData({...formData, project: e.target.value})}
        >
          <MenuItem value="finderskeepers-v2">FindersKeepers v2</MenuItem>
          <MenuItem value="research">Research</MenuItem>
        </Select>
      </FormControl>
      
      <TextField
        fullWidth
        label="Tags (comma-separated)"
        value={formData.tags}
        onChange={(e) => setFormData({...formData, tags: e.target.value})}
        margin="normal"
        helperText="Enter tags separated by commas"
      />
      
      <Button 
        type="submit" 
        variant="contained" 
        sx={{ mt: 2 }}
        fullWidth
      >
        Upload Document
      </Button>
    </Box>
  );
}
```

## Advanced Components

### Data Visualization Integration
```jsx
import { Card, CardContent, CardHeader } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

function MetricsCard({ title, data }) {
  return (
    <Card>
      <CardHeader title={title} />
      <CardContent>
        <BarChart width={400} height={300} data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#1976d2" />
        </BarChart>
      </CardContent>
    </Card>
  );
}
```

### Custom Styled Components
```jsx
import { styled } from '@mui/material/styles';
import { Paper, Typography } from '@mui/material';

const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  '&:hover': {
    boxShadow: theme.shadows[4],
  },
}));

const HighlightText = styled(Typography)(({ theme }) => ({
  color: theme.palette.primary.main,
  fontWeight: 'bold',
}));

function DocumentCard({ document }) {
  return (
    <StyledPaper>
      <HighlightText variant="h6">
        {document.title}
      </HighlightText>
      <Typography variant="body2" color="text.secondary">
        {document.summary}
      </Typography>
    </StyledPaper>
  );
}
```

## Responsive Design

### Breakpoint Usage
```jsx
import { useTheme, useMediaQuery } from '@mui/material';

function ResponsiveComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  return (
    <Grid container spacing={isMobile ? 1 : 3}>
      <Grid item xs={12} md={isMobile ? 12 : 8}>
        <MainContent />
      </Grid>
      {!isMobile && (
        <Grid item md={4}>
          <Sidebar />
        </Grid>
      )}
    </Grid>
  );
}
```

## Performance Considerations
- Use `sx` prop for performance-optimized styling
- Implement proper tree shaking for bundle size optimization
- Leverage theme caching for better performance
- Use MUI's built-in accessibility features

## Integration Best Practices
- Consistent theme application across all components
- Proper TypeScript integration for type safety
- Accessibility compliance with ARIA standards
- Mobile-first responsive design approach
""",
        "tags": ["material-ui", "mui", "components", "styling", "theme", "ui-library"]
    }
]

async def main():
    """Main execution function."""
    ingester = DirectDocumentIngester()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  📚 Direct Context7 Documentation Ingestion                     ║
║                                                                  ║
║  Ingesting curated technology documentation into                 ║
║  FindersKeepers v2 knowledge base...                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Check FastAPI health
        try:
            response = await ingester.client.get(f"{ingester.fastapi_url}/health")
            if response.status_code != 200:
                logger.error("❌ FastAPI service not accessible. Please start the service first.")
                return
        except:
            logger.error("❌ Cannot connect to FastAPI service. Please ensure it's running on localhost:8000")
            return
        
        logger.info(f"🚀 Starting ingestion of {len(DOCUMENTATION_ENTRIES)} documentation entries...")
        
        # Ingest each document
        for entry in DOCUMENTATION_ENTRIES:
            await ingester.ingest_document(
                title=entry["title"],
                content=entry["content"],
                tags=entry["tags"]
            )
            
            # Small delay to avoid overwhelming the system
            await asyncio.sleep(0.5)
        
        # Summary report
        total = len(DOCUMENTATION_ENTRIES)
        logger.info("\n" + "="*50)
        logger.info("📊 INGESTION SUMMARY")
        logger.info("="*50)
        logger.info(f"✅ Successfully ingested: {ingester.success_count}")
        logger.info(f"❌ Failed: {ingester.failure_count}")
        logger.info(f"📈 Success rate: {(ingester.success_count/total*100):.1f}%")
        logger.info("="*50)
        
        if ingester.success_count > 0:
            logger.info("🎉 Documentation ingestion completed!")
            logger.info("💡 Your FindersKeepers v2 knowledge base now contains core tech stack documentation")
            logger.info("🔍 Use the search endpoints to query this knowledge")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await ingester.close()

if __name__ == "__main__":
    asyncio.run(main())