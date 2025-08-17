# Code Style and Conventions

## Python (FastAPI Backend)
- **Version**: Python 3.12+
- **Package Manager**: uv (preferred) or pip
- **Formatting**: Black with 88 character line length
- **Import Sorting**: isort with black profile
- **Type Hints**: Required (target version py311)
- **Async**: Use async/await patterns throughout FastAPI
- **Logging**: Use structlog for structured logging
- **Pydantic**: Use for data validation and settings management

### Key Patterns
- Use `pyproject.toml` for dependency management
- Async database operations with asyncpg, neo4j, qdrant-client
- Environment variables via pydantic-settings
- JWT authentication with python-jose
- File operations with aiofiles

## Frontend (React TypeScript)
- **Version**: React 18 with TypeScript 5.7+
- **Build Tool**: Vite
- **Styling**: TailwindCSS + Material-UI components
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Real-time**: Socket.io-client
- **Linting**: ESLint with TypeScript rules
- **Icons**: Lucide React + Material Icons

### Project Structure
- Components use functional components with hooks
- Type-safe API interactions
- Responsive design with Material-UI + Tailwind
- Real-time updates via WebSocket

## Docker Conventions
- Multi-stage builds for production optimization
- Named volumes for persistent data
- Health checks for critical services
- NVIDIA GPU support configuration
- Shared network: `shared-network`

## Database Naming
- PostgreSQL: snake_case tables and columns
- Neo4j: CamelCase nodes and relationships
- Use JSONB for flexible schema in PostgreSQL
- Vector embeddings stored in pgvector format