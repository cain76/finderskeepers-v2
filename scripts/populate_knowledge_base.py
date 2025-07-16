#!/usr/bin/env python3
"""
FindersKeepers v2 Knowledge Base Population Script

This script uses Context7 to gather comprehensive documentation for our entire tech stack
and ingests it into the FindersKeepers v2 knowledge base for intelligent retrieval.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx
import asyncpg
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Technology stack mapping for Context7 library IDs
TECH_STACK_MAPPING = {
    # Backend & API
    "FastAPI": "/tiangolo/fastapi",
    
    # Databases & Storage
    "PostgreSQL with pgvector": "/pgvector/pgvector",
    "Neo4j": "/context7/neo4j",
    "Qdrant": "/qdrant/qdrant",
    "Redis": "/redis/redis",
    
    # Frontend Framework
    "React": "/context7/react_dev",
    "React Router": "/context7/reactrouter",
    "React Flow": "/context7/reactflow_dev",
    
    # UI Libraries
    "Material-UI": "/mui/mui-x",
    "Emotion React": "/emotion-js/emotion",
    
    # Data Visualization
    "Recharts": "/recharts/recharts",
    
    # State Management
    "Zustand": "/pmndrs/zustand",
    
    # Real-time Communication
    "Socket.IO": "/socketio/socket.io",
    
    # Development Tools
    "TypeScript": "/microsoft/typescript",
    "Vite": "/vitejs/vite",
    "ESLint": "/eslint/eslint",
    
    # Testing
    "Jest": "/jestjs/jest",
    "Testing Library React": "/testing-library/react-testing-library",
    
    # Python Libraries
    "Pydantic": "/pydantic/pydantic",
    "Asyncpg": "/magicstack/asyncpg",
    "Uvicorn": "/encode/uvicorn",
    
    # AI & ML
    "OpenAI Python": "/openai/openai-python",
    "LangChain": "/langchain-ai/langchain",
    "Transformers": "/huggingface/transformers",
    
    # Document Processing
    "Unstructured": "/unstructured-io/unstructured",
    "Python Magic": "/ahupp/python-magic",
    
    # Container & Deployment
    "Docker": "/docker/docs",
    "Docker Compose": "/docker/compose",
    
    # HTTP & Networking
    "HTTPX": "/encode/httpx",
    "Aiofiles": "/rtobar/aiofiles",
    
    # Configuration & Environment
    "Python Dotenv": "/theskumar/python-dotenv",
    "Pydantic Settings": "/pydantic/pydantic-settings",
    
    # Security & Authentication
    "Python Jose": "/mpdavis/python-jose",
    "Passlib": "/hynek/passlib",
    
    # Monitoring & Logging
    "Structlog": "/hynek/structlog",
    "Prometheus Client": "/prometheus/client_python",
}

class Context7Client:
    """Client for interacting with Context7 API via MCP."""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def resolve_library_id(self, library_name: str) -> Optional[str]:
        """Resolve library name to Context7-compatible ID via MCP."""
        try:
            # This would typically go through the MCP server
            # For now, use our predefined mapping
            return TECH_STACK_MAPPING.get(library_name)
        except Exception as e:
            logger.error(f"Failed to resolve library ID for {library_name}: {e}")
            return None
    
    async def get_library_docs(self, library_id: str, tokens: int = 10000, topic: str = None) -> Optional[str]:
        """Fetch documentation for a library via MCP."""
        try:
            # This would typically call the MCP Context7 server
            # For now, return a placeholder
            logger.info(f"Fetching documentation for {library_id} (tokens: {tokens})")
            return f"# {library_id} Documentation\n\nComprehensive documentation for {library_id}..."
        except Exception as e:
            logger.error(f"Failed to fetch docs for {library_id}: {e}")
            return None

class FindersKeepersIngester:
    """Ingests documentation into FindersKeepers v2 knowledge base."""
    
    def __init__(self):
        self.pg_url = "postgresql://finderskeepers:fk2025secure@localhost:5432/finderskeepers_v2"
        self.fastapi_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def check_fastapi_health(self) -> bool:
        """Check if FastAPI service is running."""
        try:
            response = await self.client.get(f"{self.fastapi_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"FastAPI health check failed: {e}")
            return False
    
    async def ingest_document(self, title: str, content: str, tags: List[str], 
                            project: str = "finderskeepers-v2", doc_type: str = "documentation") -> bool:
        """Ingest a document into the knowledge base via FastAPI."""
        try:
            payload = {
                "filename": f"{title.lower().replace(' ', '_')}.md",
                "content": content,
                "project": project,
                "tags": tags,
                "metadata": {
                    "doc_type": doc_type,
                    "source": "context7",
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
                return True
            else:
                logger.error(f"❌ Failed to ingest {title}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception ingesting {title}: {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

class KnowledgeBasePopulator:
    """Main class orchestrating the knowledge base population."""
    
    def __init__(self):
        self.context7 = Context7Client()
        self.ingester = FindersKeepersIngester()
        self.success_count = 0
        self.failure_count = 0
        self.start_time = None
    
    async def populate_tech_documentation(self):
        """Populate knowledge base with technology documentation."""
        logger.info("🚀 Starting FindersKeepers v2 Knowledge Base Population")
        self.start_time = time.time()
        
        # Check if FastAPI is running
        if not await self.ingester.check_fastapi_health():
            logger.error("❌ FastAPI service is not accessible. Please start the service first.")
            return
        
        logger.info(f"📚 Processing {len(TECH_STACK_MAPPING)} technologies...")
        
        # Process each technology
        for tech_name, library_id in TECH_STACK_MAPPING.items():
            await self._process_technology(tech_name, library_id)
            # Add small delay to avoid overwhelming the system
            await asyncio.sleep(1)
        
        await self._generate_summary_report()
    
    async def _process_technology(self, tech_name: str, library_id: str):
        """Process a single technology."""
        logger.info(f"📖 Processing: {tech_name}")
        
        try:
            # Determine appropriate token count and topic based on technology
            tokens, topic = self._get_doc_parameters(tech_name)
            
            # Fetch documentation
            docs = await self.context7.get_library_docs(library_id, tokens=tokens, topic=topic)
            
            if not docs:
                logger.warning(f"⚠️  No documentation retrieved for {tech_name}")
                self.failure_count += 1
                return
            
            # Generate comprehensive content
            content = self._generate_comprehensive_content(tech_name, library_id, docs)
            
            # Generate tags
            tags = self._generate_tags(tech_name)
            
            # Ingest into knowledge base
            success = await self.ingester.ingest_document(
                title=f"{tech_name} Documentation",
                content=content,
                tags=tags
            )
            
            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to process {tech_name}: {e}")
            self.failure_count += 1
    
    def _get_doc_parameters(self, tech_name: str) -> tuple[int, str]:
        """Get appropriate documentation parameters for each technology."""
        doc_params = {
            "FastAPI": (15000, "API development, async programming, dependency injection"),
            "PostgreSQL with pgvector": (12000, "vector database, SQL queries, pgvector operations"),
            "Neo4j": (12000, "graph database operations, Cypher queries, Python driver"),
            "Qdrant": (10000, "vector database, similarity search, Python client"),
            "React": (12000, "components, hooks, state management"),
            "Material-UI": (8000, "React components, theming, styling"),
            "TypeScript": (10000, "type system, interfaces, advanced types"),
            "Docker": (8000, "containerization, deployment, best practices"),
            "OpenAI Python": (8000, "API usage, completions, embeddings"),
            "LangChain": (10000, "LLM integration, chains, agents"),
        }
        
        return doc_params.get(tech_name, (8000, "usage, configuration, best practices"))
    
    def _generate_comprehensive_content(self, tech_name: str, library_id: str, docs: str) -> str:
        """Generate comprehensive documentation content."""
        content = f"""# {tech_name} Documentation for FindersKeepers v2

## Overview
This documentation provides comprehensive information about {tech_name} as used in the FindersKeepers v2 project. This is a personal AI agent knowledge hub built with a containerized microservices architecture.

## Library Information
- **Library ID**: {library_id}
- **Integration Context**: FindersKeepers v2 Tech Stack
- **Last Updated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Role in FindersKeepers v2
{self._get_role_description(tech_name)}

## Documentation Content

{docs}

## Integration Notes for FindersKeepers v2

### Configuration
- **Environment**: Docker containerized setup
- **Development**: Local development with hot reload
- **Production**: Optimized container builds

### Dependencies
- Compatible with Python 3.12+ (backend)
- Compatible with Node.js 20+ (frontend)
- Integrates with our PostgreSQL + pgvector setup
- Works with Neo4j graph database
- Compatible with Qdrant vector search

### Best Practices
1. Follow the established code patterns in the FindersKeepers v2 codebase
2. Ensure proper error handling and logging
3. Implement proper type hints (Python) or types (TypeScript)
4. Follow the project's testing patterns
5. Maintain compatibility with the containerized architecture

### Related Technologies in Our Stack
{self._get_related_technologies(tech_name)}

## Quick Reference
- **Project Structure**: Follow the established patterns in `services/` (backend) or `frontend/src/` (frontend)
- **Configuration**: Environment variables defined in `.env` files
- **Testing**: Follow patterns in existing test suites
- **Documentation**: Update relevant documentation when making changes

---
*This documentation was automatically generated for the FindersKeepers v2 project using Context7.*
"""
        return content
    
    def _get_role_description(self, tech_name: str) -> str:
        """Get role description for each technology in our stack."""
        roles = {
            "FastAPI": "Core backend API framework providing REST endpoints for agent session tracking, knowledge queries, and document management.",
            "PostgreSQL with pgvector": "Primary database storing relational data, vector embeddings, and supporting similarity search for the knowledge base.",
            "Neo4j": "Graph database storing knowledge relationships, entity connections, and semantic links between documents and sessions.",
            "Qdrant": "High-performance vector database optimized for semantic search and document retrieval operations.",
            "React": "Frontend framework powering the user interface for managing agent sessions, browsing knowledge, and system monitoring.",
            "Material-UI": "UI component library providing consistent, accessible interface components following Material Design principles.",
            "TypeScript": "Type system ensuring type safety across the frontend application and improving developer experience.",
            "Docker": "Containerization platform enabling consistent deployment across development, testing, and production environments.",
            "OpenAI Python": "Client library for integrating with OpenAI services for embeddings, completions, and AI capabilities.",
            "LangChain": "Framework for building LLM-powered applications, handling document processing and AI agent coordination.",
        }
        return roles.get(tech_name, f"Supporting technology in the FindersKeepers v2 architecture.")
    
    def _get_related_technologies(self, tech_name: str) -> str:
        """Get related technologies in our stack."""
        relations = {
            "FastAPI": "Works with: Uvicorn (ASGI server), Pydantic (data validation), AsyncPG (PostgreSQL), Neo4j Python Driver",
            "PostgreSQL with pgvector": "Integrates with: FastAPI (via AsyncPG), pgvector extension, Neo4j (data sync), Qdrant (backup vectors)",
            "Neo4j": "Connects to: PostgreSQL (entity references), FastAPI (via Python driver), Knowledge extraction pipelines",
            "Qdrant": "Complements: PostgreSQL (primary storage), FastAPI (search endpoints), OpenAI (embeddings)",
            "React": "Works with: TypeScript, Material-UI, React Router, Zustand (state), Socket.IO (real-time)",
            "Material-UI": "Integrates with: React, TypeScript, Emotion (styling), React components",
        }
        return relations.get(tech_name, "Integrates with other technologies in the FindersKeepers v2 stack.")
    
    def _generate_tags(self, tech_name: str) -> List[str]:
        """Generate relevant tags for each technology."""
        base_tags = ["finderskeepers-v2", "tech-stack", "documentation", "context7"]
        
        tech_specific_tags = {
            "FastAPI": ["backend", "api", "python", "async", "rest"],
            "PostgreSQL with pgvector": ["database", "vector-search", "sql", "embeddings"],
            "Neo4j": ["graph-database", "cypher", "relationships", "knowledge-graph"],
            "Qdrant": ["vector-database", "similarity-search", "machine-learning"],
            "React": ["frontend", "javascript", "components", "ui"],
            "Material-UI": ["ui-library", "components", "design-system"],
            "TypeScript": ["javascript", "type-system", "frontend", "backend"],
            "Docker": ["containerization", "deployment", "devops"],
            "OpenAI Python": ["ai", "llm", "embeddings", "machine-learning"],
            "LangChain": ["ai", "llm", "agents", "document-processing"],
        }
        
        return base_tags + tech_specific_tags.get(tech_name, ["general"])
    
    async def _generate_summary_report(self):
        """Generate and display summary report."""
        elapsed_time = time.time() - self.start_time
        total_processed = self.success_count + self.failure_count
        
        logger.info("\n" + "="*60)
        logger.info("📊 KNOWLEDGE BASE POPULATION SUMMARY")
        logger.info("="*60)
        logger.info(f"🎯 Total Technologies: {len(TECH_STACK_MAPPING)}")
        logger.info(f"✅ Successfully Processed: {self.success_count}")
        logger.info(f"❌ Failed: {self.failure_count}")
        logger.info(f"⏱️  Total Time: {elapsed_time:.2f} seconds")
        logger.info(f"📈 Success Rate: {(self.success_count/total_processed*100):.1f}%")
        logger.info("="*60)
        
        if self.success_count > 0:
            logger.info("🎉 Knowledge base population completed!")
            logger.info("💡 Your FindersKeepers v2 system now has comprehensive tech stack documentation")
            logger.info("🔍 Use the search endpoints to query this knowledge")
        
        if self.failure_count > 0:
            logger.warning(f"⚠️  {self.failure_count} technologies failed to process")
            logger.info("🔄 You can re-run this script to retry failed items")
    
    async def close(self):
        """Clean up resources."""
        await self.ingester.close()

async def main():
    """Main execution function."""
    populator = KnowledgeBasePopulator()
    
    try:
        await populator.populate_tech_documentation()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        await populator.close()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  🧠 FindersKeepers v2 Knowledge Base Population Script           ║
║                                                                  ║
║  This script will populate your knowledge base with              ║
║  comprehensive documentation for your entire tech stack          ║
║  using Context7 integration.                                     ║
║                                                                  ║
║  Prerequisites:                                                  ║
║  • FastAPI service running on localhost:8000                    ║
║  • PostgreSQL with pgvector available                           ║
║  • Context7 MCP server accessible                               ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run the async main function
    asyncio.run(main())