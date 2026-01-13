# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Media Manager is a web application for managing physical media collections (movies, DVDs, Blu-rays) with hierarchical storage tracking. Built with FastAPI (Python), Svelte frontend, and MongoDB database.

**Core Problem Being Solved**: Physical media collectors lose track of where movies are stored across multiple bins, shelves, and cabinets. This app enables instant lookup of movie locations and bin contents, preventing duplicate purchases and eliminating the frustration of manual searching.

**Target Users**: Collectors with 100+ DVDs/Blu-rays using multiple storage containers, and their family members who need simple search access.

## Memory Bank (Cline Project Context)

This project was previously developed using [Cline](https://docs.cline.bot) and includes a **memory-bank/** directory containing project context files. These files provide historical context and architectural decisions:

### Memory Bank Structure

```
memory-bank/
├── projectbrief.md       # Core requirements and project goals
├── productContext.md     # Why this project exists, user experience goals
├── systemPatterns.md     # Architectural patterns and design decisions
├── techContext.md        # Technology stack and development environment
├── activeContext.md      # Current working memory and recent changes
└── progress.md           # Completed tasks and what's in progress
```

**When to reference these files:**
- **Starting new work**: Read `activeContext.md` and `progress.md` to understand current state
- **Architectural decisions**: Check `systemPatterns.md` for established patterns
- **Understanding requirements**: Review `projectbrief.md` and `productContext.md`
- **Technical setup questions**: Consult `techContext.md`

### Current Project State (from activeContext.md)

**Completed Phases:**
- ✅ Phase 1: Foundation (Docker, MongoDB, FastAPI setup)
- ✅ Phase 2A: Testing framework and authentication system (JWT-based, 89 tests passing)
- ✅ Phase 2B: OpenAPI documentation and client generation planning
- ✅ Phase 2C: OpenAPI client generation implementation (TypeScript + Python clients)

**Current Priority: Phase 3A - Frontend Development Setup**
- Set up Svelte application with generated TypeScript client
- Implement type-safe authentication UI
- Create movie catalog interface with TMDB integration
- Build storage management UI with generated API client

**Key Recent Implementations:**
- Complete movie management API with CRUD operations and TMDB integration
- Professional TMDB service with singleton pattern and dependency injection
- Generated TypeScript client (`@trekie86/media-manager-client`) for frontend
- Generated Python client for testing
- Prism CLI mock server for frontend development without backend dependency

### Future Vision (from productContext.md)

**Phase 1 (Current)**: Core functionality - movie/storage CRUD, TMDB integration, basic search, web interface

**Phase 2 (Next)**: Enhanced experience - mobile-responsive design, advanced filtering, collection statistics, bulk import/export

**Phase 3 (Future)**: Smart features - recommendation engine, loan tracking, wishlist integration, collection value tracking

**Success Metrics:**
- Find Rate: Users can locate any movie in under 30 seconds
- Accuracy: Storage locations are 95%+ accurate
- Coverage: 90%+ of movies have complete TMDB metadata
- Adoption: All family members actively use the system

## Technology Stack

- **Backend**: FastAPI (Python 3.11+), MongoDB, Pydantic
- **Frontend**: Svelte with Skeleton UI (separate frontend/ directory)
- **Infrastructure**: Docker, docker-compose
- **Testing**: pytest with comprehensive test suites
- **API**: OpenAPI/Swagger with automated client generation
- **External**: TMDB API for movie metadata

## Development Commands

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Initial setup (creates virtual environment and installs dependencies)
# Unix/macOS:
./scripts/setup_dev.sh
# Windows:
.\scripts\setup_dev.ps1

# Activate virtual environment
# Unix/macOS:
source .venv/bin/activate
# Windows:
.\.venv\Scripts\Activate.ps1

# Start backend server (requires MongoDB running)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Format code
python -m black app/

# Lint code
python -m flake8 app/
python -m black --check app/
```

### Frontend Development

```bash
cd frontend

# Install dependencies
pnpm install

# Start dev server
pnpm dev
```

### OpenAPI Client Generation

The project uses OpenAPI Generator for type-safe API clients. Backend must be running on http://localhost:8000.

```bash
# Generate all clients (TypeScript, Python, OpenAPI spec)
npm run generate:clients

# Generate specific clients
npm run generate:typescript    # TypeScript client for frontend
npm run generate:python       # Python client for testing

# Validate generated clients
npm run validate:clients
npm run validate:typescript
npm run validate:python

# Start mock server (for frontend development without backend)
npm run mock:server           # Downloads spec from running backend
npm run mock:server:file      # Uses local generated/openapi.json

# Watch backend files and auto-regenerate on changes
npm run watch:openapi
```

Generated clients are created in `generated/` directory (excluded from git).

### Full Stack Development

```bash
# Start all services in Docker
docker compose up -d

# Start only MongoDB (for local backend development)
docker compose up -d mongodb mongo-express

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# All tests from root
npm test
```

## Architecture

### Backend Structure

The backend follows a layered architecture with clear separation of concerns:

```
backend/app/
├── api/            # API route handlers (auth, movies, storage)
├── core/           # Core config, health checks
├── db/             # Database connection and base operations
├── models/         # Pydantic models (movie, storage, user, responses)
└── services/       # Business logic layer (TMDB service)
```

**Key Patterns**:
- **Repository Pattern**: Database operations abstracted in models
- **Service Layer**: Business logic in services/ (e.g., TMDB integration)
- **Dependency Injection**: FastAPI's built-in DI for database connections, config
- **Singleton Pattern**: TMDB service managed as singleton with lifecycle hooks

### Storage Hierarchy (Materialized Path Pattern)

The storage system uses a **materialized path pattern** for hierarchical organization:

**Schema**:
```javascript
{
  _id: ObjectId,
  name: String,
  type: Enum['cabinet', 'shelf', 'bin', 'drawer'],
  parent_id: Optional[ObjectId],
  path: Array<ObjectId>,  // Materialized path for efficient queries
  metadata: {
    capacity: Optional[Number],
    dimensions: Optional[String],
    location: Optional[String]
  }
}
```

**Key Operations**:
- Fast descendant queries: `db.storage.find({ path: parentId })`
- Immediate children: `db.storage.find({ parent_id: parentId })`
- Moving nodes requires cascading path updates to all descendants
- Service layer handles path generation, cycle detection, and validation

**Important**: Tree structure validation happens at both model level (basic checks) and service level (full cycle detection, parent existence).

### MongoDB ID Handling

**Critical Pattern**: Always convert between string IDs (API) and ObjectId (MongoDB):

1. **API Input**: Accept string IDs, convert to ObjectId before MongoDB operations
2. **MongoDB Operations**: Use ObjectId for all queries and storage
3. **API Response**: Convert ObjectId to string before returning responses
4. **Error Handling**: Catch ObjectId conversion errors, return appropriate HTTP codes

Example:
```python
# API receives string ID
storage_id = "507f1f77bcf86cd799439011"

# Convert to ObjectId for MongoDB query
from bson import ObjectId
storage_obj = ObjectId(storage_id)
db.storage.find_one({"_id": storage_obj})

# Convert back to string for response
response = {"id": str(doc["_id"]), ...}
```

### TMDB Integration

Professional service architecture with:
- Singleton pattern via FastAPI dependency injection
- Persistent HTTP client with connection pooling
- Automatic image URL generation (poster, backdrop)
- Graceful degradation on service failures
- Rate limiting and timeout handling
- Service lifecycle management (startup/shutdown)

Location: `backend/app/services/tmdb.py`

### Testing Strategy

**Test Organization**:
```
backend/tests/
├── unit/           # Models, services, utilities
├── integration/    # Database, TMDB, API integration
├── functional/     # Auth flow, movie management, storage operations
└── performance/    # Query performance, API response time
```

**Key Testing Patterns**:
- Isolated test database per session with automatic cleanup
- FastAPI test client fixtures
- Mocked TMDB responses
- Tree operation validation tests
- MongoDB ObjectId conversion tests

Run specific test categories:
```bash
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests
pytest -k "storage"         # Tests matching "storage"
pytest tests/unit/test_storage.py::test_create_storage  # Specific test
```

## Environment Configuration

Required environment variables (copy `.env.example` to `.env`):

```bash
# TMDB API
TMDB_API_KEY=your_tmdb_api_key

# MongoDB
MONGO_HOST=localhost        # Use 'localhost' for local dev, 'mongodb' for Docker
MONGO_PORT=27017
MONGO_USER=mediamanager
MONGO_PASSWORD=your_password
MONGO_DB=mediamanager
```

**Important**: When running backend locally, use `MONGO_HOST=localhost`. When running in Docker, use `MONGO_HOST=mongodb`.

## Documentation

The project uses Architecture Decision Records (ADRs) in `docs/adr/`:

- **ADR-001**: Technology stack decisions (Svelte, FastAPI, MongoDB, Docker)
- **ADR-002**: Testing strategy implementation (pytest, multi-layered testing)
- **ADR-003**: Storage tree implementation (materialized path pattern)
- **ADR-004**: OpenAPI client generation architecture (TypeScript/Python clients)

**When to create an ADR** (follow `docs/adr/template.md`):
- Major dependency changes
- Architectural pattern changes
- New integration patterns
- Database schema changes

### Maintaining the Memory Bank (for Cline users)

If continuing development with Cline, update the memory bank files after significant changes:

1. **activeContext.md**: Update after completing features, changing focus, or making architectural decisions
2. **progress.md**: Mark tasks complete, add new tasks, update phase status
3. **systemPatterns.md**: Document new patterns, architectural decisions, or integration approaches
4. **techContext.md**: Update when adding dependencies, changing dev workflow, or adding integrations

Reference: [Cline Memory Bank Documentation](https://docs.cline.bot/prompting/cline-memory-bank)

## API Documentation

When backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI spec: http://localhost:8000/openapi.json

## Common Development Workflows

### Adding a New API Endpoint

1. Define Pydantic models in `backend/app/models/`
2. Create API route handler in `backend/app/api/`
3. Add route to `backend/app/main.py`
4. Write tests in `backend/tests/`
5. Regenerate API clients: `npm run generate:clients`

### Modifying Storage Tree Structure

1. Update models in `backend/app/models/storage.py`
2. Update service layer validation and path management
3. Update tests for tree operations
4. Consider impact on existing data (migration if needed)

### Integrating External Services

Follow TMDB service pattern:
- Create service class in `backend/app/services/`
- Use singleton pattern with startup/shutdown lifecycle
- Implement graceful degradation
- Add comprehensive error handling
- Mock in tests

### Working with MongoDB

- Use `backend/app/db/connection.py` for database connection
- All MongoDB operations should use ObjectId internally
- Convert to/from strings at API boundaries
- Use proper indexing for path arrays in storage collection

## Code Style

- **Backend**: Follow black formatting, flake8 linting
- **Frontend**: Follow project's ESLint/Prettier config
- **Prefer composition over inheritance**
- **Use type hints in Python code**
- **OpenAPI Generator**: Generated code goes in `generated/`, always regenerate after API changes

## Key Project Insights (from Memory Bank)

### Development Philosophy

1. **Test-Driven Development**: The project follows TDD with comprehensive test coverage (89 tests, 62% coverage). Always write tests for new features.

2. **Service-Oriented Architecture**: Business logic lives in the service layer (`backend/app/services/`), not in route handlers. The TMDB service exemplifies this pattern with singleton management and lifecycle hooks.

3. **Type Safety End-to-End**: The OpenAPI client generation ensures type safety from Python Pydantic models through to TypeScript frontend, eliminating integration bugs.

4. **User Experience First**: Architecture decisions prioritize the core user problem: "Where did I put The Matrix?" The entire system is optimized for fast movie location lookup (sub-second response times).

### Technical Lessons Learned

From `activeContext.md` and development sessions:

- **MongoDB Schema Validation**: Requires careful None/null value handling in Pydantic models
- **Exception Handling Order**: Critical for proper HTTP status codes; specific exceptions must be caught before generic ones
- **ObjectId Conversion**: Always convert at API boundaries; MongoDB uses ObjectId internally, API uses strings
- **Path Array Indexing**: Essential for performance in storage tree queries; index the `path` array field
- **TMDB Integration**: Graceful degradation is critical; the app must work even if TMDB API is down

### Common Patterns to Follow

1. **Repository Pattern**: Database operations abstracted in models, not scattered in routes
2. **Dependency Injection**: Use FastAPI's `Depends()` for database connections, services, auth
3. **Singleton Services**: External services (TMDB) use singleton pattern with app lifecycle management
4. **Materialized Path**: Storage hierarchy uses path arrays for efficient tree queries
5. **Comprehensive Testing**: Every new feature needs unit tests, integration tests, and API tests

### User Experience Goals

From `productContext.md`:

- **Speed**: Movie lookup must be sub-second
- **Accuracy**: Storage locations must be 95%+ accurate
- **Simplicity**: One-click movie lookup, minimal data entry
- **Visual Organization**: Storage hierarchy mirrors physical layout
- **Family-Friendly**: Simple enough for all household members

## Important Notes

- The `generated/` directory is excluded from git; always regenerate after pulling API changes
- Storage tree operations require careful path management to maintain consistency
- TMDB service is initialized at app startup; don't create separate instances
- Test database is isolated and automatically cleaned between test runs
- MongoDB connection uses connection pooling; don't create additional connections
- Always activate virtual environment before backend development
- Client generation requires backend server running on port 8000
- **Memory Bank**: If using Cline, keep `activeContext.md` and `progress.md` updated as the source of truth
