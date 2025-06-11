"""
Main FastAPI application module.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import connect_to_mongo, close_mongo_connection

# Create FastAPI app instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    Media Manager API enables managing physical media collections and their storage locations.
    
    ## Features
    * Movie Management - Track your movie collection with TMDB integration
    * Storage Management - Organize movies in custom-labeled storage bins
    * Search & Filter - Find movies and their storage locations easily
    * User System - Secure authentication and session management
    
    ## Authentication
    All endpoints except /health require authentication via session cookie.
    Use the /auth/login endpoint to obtain a session.
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and session management"
        },
        {
            "name": "movies",
            "description": "Movie collection management operations"
        },
        {
            "name": "bins",
            "description": "Storage bin management operations"
        },
        {
            "name": "users",
            "description": "User management operations"
        }
    ],
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection management
@app.on_event("startup")
async def startup_db_client():
    """
    Initialize database connection on startup.
    """
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    """
    Close database connection on shutdown.
    """
    await close_mongo_connection()

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {"status": "healthy", "version": "0.1.0"}
