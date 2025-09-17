# System Patterns

## Architecture Overview

```mermaid
graph TB
    subgraph Frontend [Frontend - Svelte + Skeleton]
        UI[UI Components]
        State[State Management]
        API_Client[API Client]
    end

    subgraph Backend [Backend - FastAPI]
        API[REST API]
        Auth[Session Auth]
        TMDB[TMDB Service]
        DB_Logic[Database Logic]
        Tests[Test Suites]
        StorageTree[Storage Tree Logic]
        Services[Service Layer]
    end

    subgraph Database [MongoDB]
        Movies[(Movies Collection)]
        Storage[(Storage Collection)]
        Users[(Users Collection)]
        Sessions[(Sessions Collection)]
        TestDB[(Test Database)]
    end

    UI --> State
    State --> API_Client
    API_Client --> API
    API --> Auth
    API --> Services
    Services --> TMDB
    API --> DB_Logic
    API --> StorageTree
    DB_Logic --> Movies
    DB_Logic --> Storage
    Auth --> Users
    Auth --> Sessions
    Tests --> API
    Tests --> DB_Logic
    Tests --> TestDB
```

## Design Patterns

### Backend Patterns

#### Repository Pattern
- Abstracts database operations
- Separates data access from business logic
- Implemented per collection (Movies, Storage, Users)

#### Service Layer Pattern
- Encapsulates business logic
- Coordinates between repositories
- Handles complex operations
- TMDB service with singleton pattern
- Dependency injection via FastAPI

#### Tree Structure Pattern
```mermaid
graph TD
    A[Storage Service] --> B[Tree Operations]
    B --> C[Create Node]
    B --> D[Move Node]
    B --> E[Delete Node]
    B --> F[Query Tree]
    
    C --> G[Validate Parent]
    C --> H[Update Path]
    
    D --> I[Update Children]
    D --> J[Rewrite Paths]
    
    F --> K[Get Ancestors]
    F --> L[Get Descendants]
    F --> M[Get Siblings]
```

#### Dependency Injection
- FastAPI's built-in DI system
- Database connections
- Configuration settings

#### CRUD Operations
- Standardized REST endpoints
- Consistent response formats
- Error handling patterns

#### External Service Integration
- TMDB API service with professional architecture
- Singleton pattern for service management
- HTTP client lifecycle management
- Graceful degradation on service failures
- Automatic image URL generation
- Rate limiting and timeout handling

### Testing Patterns

1. Test Database Management
   ```mermaid
   graph TD
       A[Test Setup] --> B[Create Test DB]
       B --> C[Apply Migrations]
       C --> D[Run Tests]
       D --> E[Cleanup]
       E --> F[Drop Test DB]
   ```

2. Test Categories
   ```mermaid
   graph TD
       A[Test Suite] --> B[Unit Tests]
       A --> C[Integration Tests]
       A --> D[Functional Tests]
       A --> E[Performance Tests]
       
       B --> F[Repository Tests]
       B --> G[Service Tests]
       B --> H[Utility Tests]
       
       C --> I[Database Tests]
       C --> J[TMDB Tests]
       C --> K[Auth Tests]
       
       D --> L[API Flow Tests]
       D --> M[Error Tests]
       D --> N[Security Tests]
       
       E --> O[Response Time]
       E --> P[Query Performance]
       E --> Q[Connection Pool]
   ```

3. Test Fixtures
   - Database fixtures
   - Authentication fixtures
   - Mock TMDB responses
   - Utility fixtures

4. Mocking Strategy
   - External API mocks
   - Database mocks when needed
   - Service layer mocks
   - Authentication mocks

### Frontend Patterns (Phase 2B)

1. Component Architecture
   - Reusable UI components
   - Skeleton UI integration
   - Consistent styling

2. State Management
   - Local component state
   - Shared application state
   - Form handling

3. API Integration
   - Centralized API client
   - Request/response handling
   - Error management

## Data Models

### Movie Schema
```javascript
{
  _id: ObjectId,
  title: String,
  year: Number,
  storage_id: ObjectId,  // Reference to any storage type
  format: Enum['DVD', 'Blu-ray', 'Digital'],
  tmdb_id: Number,
  genre: Array<String>,
  runtime: Number,
  cover_image: String
}
```

### Storage Schema
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
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

### User Schema
```javascript
{
  _id: ObjectId,
  username: String,
  password_hash: String,
  email: String
}
```

## Critical Implementation Paths

1. Authentication Flow
```mermaid
sequenceDiagram
    Client->>+Server: Login Request
    Server->>+Database: Validate Credentials
    Database-->>-Server: User Data
    Server->>Server: Create Session
    Server-->>-Client: Session Cookie
```

2. Storage Tree Operations
```mermaid
sequenceDiagram
    Client->>+Server: Create Storage Request
    Server->>+Database: Validate Parent
    Database-->>-Server: Parent Data
    Server->>Server: Generate Path
    Server->>+Database: Store Node
    Database-->>-Server: Confirmation
    Server-->>-Client: Success Response
```

3. Movie Management with TMDB Integration
```mermaid
sequenceDiagram
    Client->>+Server: Add Movie Request
    Server->>+Database: Validate Storage
    Database-->>-Server: Storage Data
    Server->>+Database: Store Movie
    Database-->>-Server: Confirmation
    Server-->>-Client: Success Response
    
    Note over Client,Server: Movie Enrichment Flow
    Client->>+Server: Enrich Movie Request
    Server->>+TMDB: Search/Get Movie Data
    TMDB-->>-Server: Enhanced Movie Details
    Server->>+Database: Update Movie with TMDB Data
    Database-->>-Server: Confirmation
    Server-->>-Client: Enriched Movie Response
```

4. TMDB Service Architecture
```mermaid
sequenceDiagram
    App->>+TMDBServiceManager: Initialize Service
    TMDBServiceManager->>+TMDBService: Create Instance
    TMDBService->>+HTTPClient: Create Persistent Client
    HTTPClient-->>-TMDBService: Client Ready
    TMDBService-->>-TMDBServiceManager: Service Ready
    TMDBServiceManager-->>-App: Service Initialized
    
    Note over App,HTTPClient: API Request Flow
    API->>+TMDBService: Search Movies
    TMDBService->>+HTTPClient: HTTP Request to TMDB
    HTTPClient-->>-TMDBService: TMDB Response
    TMDBService->>TMDBService: Process & Enhance Data
    TMDBService-->>-API: Enhanced Results
    
    Note over App,HTTPClient: Cleanup Flow
    App->>+TMDBServiceManager: Cleanup
    TMDBServiceManager->>+TMDBService: Close Service
    TMDBService->>+HTTPClient: Close Client
    HTTPClient-->>-TMDBService: Client Closed
    TMDBService-->>-TMDBServiceManager: Service Closed
    TMDBServiceManager-->>-App: Cleanup Complete
```

5. Testing Flow
```mermaid
sequenceDiagram
    Test->>+TestDB: Setup Test Database
    Test->>+API: Execute Test Cases
    API->>+TestDB: Perform Operations
    TestDB-->>-API: Return Results
    API-->>-Test: Assert Results
    Test->>-TestDB: Cleanup
```

## Integration Points

1. TMDB Integration
   - Professional service architecture with singleton pattern
   - Persistent HTTP client with connection pooling
   - Comprehensive error handling and graceful degradation
   - Automatic image URL generation (poster and backdrop)
   - Movie search functionality
   - Movie details retrieval with enhanced metadata
   - Movie enrichment with automatic metadata enhancement
   - Rate limiting compliance and timeout handling
   - Service lifecycle management (startup/shutdown)
   - FastAPI dependency injection integration

2. MongoDB Integration
   - Connection pooling
   - Async operations
   - Schema validation
   - Index optimization
   - Tree structure queries
   - ObjectId/String ID conversion patterns
   - Response formatting for MongoDB documents
   - Explicit field mapping for consistent API

3. Frontend-Backend Integration
   - REST API
   - CORS configuration
   - Authentication headers
   - Error handling

## Security Patterns

1. Authentication
   - Session-based
   - Secure cookie handling
   - CSRF protection

2. Data Validation
   - Input validation
   - Schema validation
   - Type checking
   - Tree structure validation

3. Error Handling
   - Standardized error responses
   - Logging
   - User-friendly messages

## MongoDB ID Handling Pattern

```mermaid
sequenceDiagram
    Client->>+API: Request with string IDs
    API->>API: Convert string IDs to ObjectId
    API->>+MongoDB: Query with ObjectId
    MongoDB-->>-API: Return documents with ObjectId
    API->>API: Convert ObjectId to string IDs
    API-->>-Client: Response with string IDs
```

1. API Input Processing
   - Accept string IDs in API requests
   - Convert string IDs to ObjectId before MongoDB operations
   - Handle conversion errors with appropriate HTTP responses

2. MongoDB Operations
   - Always use ObjectId for MongoDB queries
   - Store ObjectId in MongoDB collections
   - Use proper schema validation for ObjectId fields

3. API Response Formatting
   - Convert ObjectId to string before sending responses
   - Create explicit response dictionaries with proper field names
   - Ensure consistent field naming between requests and responses

4. Error Handling
   - Catch and handle ObjectId conversion errors
   - Provide clear error messages for invalid ID formats
   - Return appropriate HTTP status codes

## Testing Strategy

1. Test Environment
   - Isolated test database
   - Mocked external services
   - Controlled test data
   - Reproducible test conditions

2. Test Coverage
   - Repository layer coverage
   - Service layer coverage
   - API endpoint coverage
   - Error handling coverage
   - Tree operations coverage

3. Performance Testing
   - Response time benchmarks
   - Database query analysis
   - Resource utilization metrics
   - Load testing parameters
   - Tree traversal performance
