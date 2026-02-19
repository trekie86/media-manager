"""
Main FastAPI application module.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.core.config import settings
from app.db import connect_to_mongo, close_mongo_connection
from app.api import api_router
from app.services.tmdb import init_tmdb_service, cleanup_tmdb_service
from app.models.responses import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events for the FastAPI application.
    """
    # Startup: Initialize database connection and services
    await connect_to_mongo()
    await init_tmdb_service()
    yield
    # Shutdown: Close database connection and cleanup services
    await cleanup_tmdb_service()
    await close_mongo_connection()


# Create FastAPI app instance
app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    description="""
    # Media Manager API

    A comprehensive REST API for managing physical media collections
    and their storage locations.
    Perfect for collectors who want to organize and track their DVD,
    Blu-ray, and digital movie collections.

    ## 🎬 Features

    ### Movie Management
    - **CRUD Operations**: Create, read, update, and delete movies in your collection
    - **TMDB Integration**: Automatic metadata enrichment from The Movie Database
    - **Advanced Search**: Find movies by title, genre, format, or storage location
    - **Metadata Support**: Track genres, runtime, cover images, and more

    ### Storage Management
    - **Hierarchical Organization**: Organize with cabinets → shelves → bins → drawers
    - **Custom Labels**: Use your own naming system for storage containers
    - **Location Tracking**: Always know exactly where each movie is stored
    - **Flexible Structure**: Adapt to any physical organization system

    ### Search & Discovery
    - **Fast Search**: Sub-second response times across your entire collection
    - **Multiple Filters**: Filter by storage location, format, genre, and more
    - **TMDB Search**: Discover new movies to add to your collection
    - **Pagination Support**: Handle large collections efficiently

    ### User System
    - **Secure Authentication**: JWT-based session management
    - **Multi-user Support**: Share collections with family members
    - **Session Management**: Secure login, logout, and token refresh

    ## 🔐 Authentication

    Most endpoints require authentication via session cookie or JWT token.

    **Getting Started:**
    1. Register a new account: `POST /api/auth/register`
    2. Login to get session: `POST /api/auth/login`
    3. Use authenticated endpoints with session cookie
    4. Refresh tokens as needed: `POST /api/auth/refresh`

    ## 📚 API Usage

    ### Response Format
    All API responses follow a consistent format:

    **Success Response:**
    ```json
    {
      "success": true,
      "data": { ... },
      "message": "Optional success message"
    }
    ```

    **Error Response:**
    ```json
    {
      "success": false,
      "error": "error_type",
      "message": "Human-readable error message",
      "details": [...]
    }
    ```

    **Paginated Response:**
    ```json
    {
      "success": true,
      "data": [...],
      "pagination": {
        "page": 1,
        "per_page": 20,
        "total_items": 150,
        "total_pages": 8,
        "has_next": true,
        "has_prev": false
      }
    }
    ```

    ### Rate Limiting
    - TMDB API calls are rate-limited to comply with their terms of service
    - Authentication endpoints have additional rate limiting for security

    ### Error Handling
    - All errors include detailed information for debugging
    - Validation errors specify which fields are problematic
    - HTTP status codes follow REST conventions

    ## 🚀 Getting Started

    1. **Health Check**: `GET /health` - Verify API is running
    2. **Register**: `POST /api/auth/register` - Create your account
    3. **Login**: `POST /api/auth/login` - Get authenticated session
    4. **Add Storage**: `POST /api/storage` - Create your first storage bin
    5. **Add Movies**: `POST /api/movies` - Start building your collection

    ## 📖 External Resources

    - **TMDB API**: Movie metadata provided by
      [The Movie Database](https://www.themoviedb.org/)
    - **Documentation**: Full API documentation available at `/docs` and `/redoc`
    - **OpenAPI Spec**: Machine-readable specification at `/openapi.json`
    """,
    version=settings.VERSION,
    contact={
        "name": "Media Manager API Support",
        "email": "support@example.com",
        "url": "https://github.com/trekie86/media-manager",
    },
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.mediamanager.local", "description": "Production server"},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Health check and system status endpoints"},
        {
            "name": "auth",
            "description": "Authentication and session management operations",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.mediamanager.local/auth",
            },
        },
        {
            "name": "movies",
            "description": (
                "Movie collection management operations"
                " including CRUD, search, and TMDB integration"
            ),
            "externalDocs": {
                "description": "Movie Management Guide",
                "url": "https://docs.mediamanager.local/movies",
            },
        },
        {
            "name": "storage",
            "description": (
                "Storage container management operations"
                " for organizing your physical media"
            ),
            "externalDocs": {
                "description": "Storage Organization Guide",
                "url": "https://docs.mediamanager.local/storage",
            },
        },
    ],
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "none",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "tryItOutEnabled": True,
    },
    openapi_url="/openapi.json",
    generate_unique_id_function=lambda route: (
        f"{route.tags[0]}-{route.name}" if route.tags else route.name
    ),
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add after CORS middleware
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["localhost", "*.yourdomain.com"]
)
# For production only:
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Include API routes
app.include_router(api_router)


# Health check endpoint
@app.get(
    "/health",
    tags=["health"],
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
    response_model=HealthResponse,
    responses={
        200: {
            "description": "API is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        503: {
            "description": "API is unhealthy - service unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "version": "1.0.0",
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
    },
)
async def health_check():
    """
    Health check endpoint to verify API is running and operational.

    This endpoint provides a quick way to verify that the API is:
    - Running and accepting requests
    - Connected to required services
    - Operating within normal parameters

    **Use Cases:**
    - Load balancer health checks
    - Monitoring system verification
    - Deployment validation
    - Service discovery confirmation

    **Response includes:**
    - Service health status
    - API version information
    - Response timestamp

    **No authentication required** - This endpoint is publicly accessible
    for monitoring and health check purposes.
    """
    from datetime import datetime, timezone
    from app.core.health import (
        check_database_health,
        check_tmdb_health,
        get_memory_usage,
    )

    # Perform health checks
    checks = {
        "database": await check_database_health(),
        "tmdb_service": await check_tmdb_health(),
        "memory": get_memory_usage(),
    }

    # Determine overall status
    database_healthy = checks["database"]
    tmdb_healthy = checks["tmdb_service"]
    memory_healthy = checks["memory"].get("healthy", False)

    all_healthy = all([database_healthy, tmdb_healthy, memory_healthy])
    overall_status = "healthy" if all_healthy else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        env=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc).isoformat(),
        checks=checks,
    )
