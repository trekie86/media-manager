# Technical Context

## Development Environment

### Backend (Python/FastAPI)
- Using uv for dependency management
- Virtual environment setup with development scripts
- Requirements managed through .in files and pip-compile
- Hot reload enabled for development

### Frontend (Svelte)
- Skeleton UI for components
- Development server on port 3000
- Hot module replacement enabled

### Database (MongoDB)
- MongoDB with Mongo Express
- Collections defined in mongo-init.js
- Schemas include: movies, storage, users, sessions
- Schema validation for all collections
- ObjectId handling for IDs and references
- Materialized path pattern for tree structures

### Docker Setup
- Multi-container architecture
- Development-focused configuration
- Volume mounts for hot reload
- Network configuration for service communication

## Project Structure

```
media-manager/
├── docker/
│   ├── development/
│   │   ├── frontend.dockerfile
│   │   ├── backend.dockerfile
│   │   └── mongo-init.js
│   └── production/
│       └── secrets/
├── frontend/
│   └── [Pending Svelte setup]
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── movies.py (CRUD + TMDB integration)
│   │   │   ├── auth.py
│   │   │   └── storage.py
│   │   ├── core/
│   │   │   └── config.py
│   │   ├── db/
│   │   ├── models/
│   │   └── services/
│   │       └── tmdb.py (TMDB service implementation)
│   ├── scripts/
│   │   ├── setup_dev.sh
│   │   └── setup_dev.ps1
│   ├── requirements.in
│   └── requirements-dev.in
├── docs/
│   ├── adr/
│   │   └── 001-technology-stack.md
│   └── implementation-plan.md
└── docker-compose.yml
```

## Configuration Files

### Environment Variables (.env.example)
- Frontend configuration
- Backend settings
- MongoDB credentials
- TMDB API configuration

### Docker Compose
- Frontend service (port 3000)
- Backend service (port 8000)
- MongoDB (port 27017)
- Mongo Express (port 8081)

## Development Workflow
1. Local development uses virtual environments
2. Dependencies managed through uv
3. Docker for full stack testing
4. Hot reload enabled for both frontend and backend
5. Test-driven development with pytest
6. Comprehensive test suite with unit, integration, and API tests
7. Service-oriented architecture with dependency injection
8. External service integration with proper lifecycle management

## Testing Framework
- pytest for test execution
- pytest-cov for coverage reporting
- pytest-asyncio for async tests
- Custom fixtures for database testing
- Test database isolation
- Comprehensive API test helpers

## External Integrations

### TMDB (The Movie Database) API
- Professional service implementation with singleton pattern
- Persistent HTTP client with connection pooling
- Movie search, details retrieval, and metadata enrichment
- Image URL generation for posters and backdrops
- Comprehensive error handling and logging
- Rate limiting and API key management
- Service lifecycle management with proper cleanup

### Future Integrations
- OAuth integration for social login
- Additional metadata providers
- Streaming service availability APIs

## Security Considerations
- Session-based authentication
- Secure password hashing
- Environment variable management
- Docker secrets for production
