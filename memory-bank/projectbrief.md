# Media Manager Project Brief

## Project Overview
A web application to manage physical media collections (movies) and track their storage locations (bins). The application allows users to search for movies and find their storage locations, as well as look up bins to see their contents.

## Core Requirements
1. Movie Management
   - Track movie collections with metadata from TMDB
   - Store movie details (title, year, format, etc.)
   - Link movies to storage bins
   - Display cover images

2. Storage Management
   - Custom-labeled storage bins
   - Track what's stored in each bin
   - Search by bin to see contents

3. Search & Filter
   - Search for movies
   - Find storage locations
   - Filter by various criteria

4. User System
   - Secure authentication
   - Session-based user management

## Technical Requirements
1. Frontend
   - Svelte framework
   - Skeleton UI toolkit
   - Single-page application (SPA)

2. Backend
   - FastAPI (Python)
   - RESTful API design
   - OpenAPI/Swagger documentation
   - TMDB API integration

3. Database
   - MongoDB
   - Mongo Express for management

4. Infrastructure
   - Docker containerization
   - Development and production configurations
   - Local development with virtual environments
