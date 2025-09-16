# TMDB Integration Documentation

## Overview

The Media Manager API now includes full integration with The Movie Database (TMDB) API for movie metadata enrichment and search functionality.

## Features

### 1. TMDB Movie Search
- **Endpoint**: `GET /api/movies/tmdb/search`
- **Parameters**:
  - `q` (required): Search query for movie titles
  - `year` (optional): Filter by release year
  - `page` (optional): Page number for pagination (default: 1)
- **Returns**: TMDB search results with enhanced image URLs

### 2. TMDB Movie Details
- **Endpoint**: `GET /api/movies/tmdb/{tmdb_id}`
- **Parameters**:
  - `tmdb_id` (required): TMDB movie ID
- **Returns**: Detailed movie information including cast, crew, and metadata

### 3. Movie Enrichment
- **Endpoint**: `POST /api/movies/{movie_id}/enrich`
- **Parameters**:
  - `movie_id` (required): Local movie ID to enrich
- **Returns**: Updated movie with TMDB metadata
- **Behavior**: 
  - If movie has `tmdb_id`, fetches detailed information
  - If no `tmdb_id`, searches by title and provides suggestions
  - Preserves existing user data while adding TMDB metadata

### 4. Local Movie Search
- **Endpoint**: `GET /api/movies/search`
- **Parameters**:
  - `q` (required): Search query for local movie titles
  - Standard filtering parameters (storage_id, format, genre)
- **Returns**: Local movies matching search criteria
- **Features**:
  - MongoDB text search with relevance scoring
  - Automatic fallback to regex search if text indexes don't exist

## Configuration

### Environment Variables
```bash
# Required: Get your API key from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_actual_api_key_here

# Optional: TMDB API base URL (defaults to https://api.themoviedb.org/3)
TMDB_API_URL=https://api.themoviedb.org/3
```

### Getting a TMDB API Key
1. Create an account at [themoviedb.org](https://www.themoviedb.org/)
2. Go to Settings → API
3. Request an API key (free for non-commercial use)
4. Add the key to your `.env` file

## Architecture

### TMDBService Class
- **Purpose**: Handles all TMDB API interactions
- **Features**:
  - Persistent HTTP client for better performance
  - Automatic image URL generation
  - Comprehensive error handling
  - Rate limiting and timeout handling

### TMDBServiceManager
- **Purpose**: Singleton manager for TMDB service lifecycle
- **Features**:
  - Clean initialization and cleanup
  - Thread-safe singleton pattern
  - FastAPI dependency injection support

### Integration Points
- **Startup**: TMDB service initializes during app startup
- **Shutdown**: HTTP client properly closed during app shutdown
- **Dependencies**: Available via FastAPI's dependency injection system

## Usage Examples

### Search TMDB for Movies
```bash
curl -X GET "http://localhost:8000/api/movies/tmdb/search?q=The%20Matrix&year=1999"
```

### Get TMDB Movie Details
```bash
curl -X GET "http://localhost:8000/api/movies/tmdb/603"
```

### Enrich Local Movie with TMDB Data
```bash
curl -X POST "http://localhost:8000/api/movies/{movie_id}/enrich"
```

### Search Local Movies
```bash
curl -X GET "http://localhost:8000/api/movies/search?q=matrix"
```

## Error Handling

### TMDB API Errors
- **401 Unauthorized**: Invalid or missing API key
- **404 Not Found**: Movie not found in TMDB
- **429 Too Many Requests**: Rate limit exceeded
- **500+ Server Errors**: TMDB service unavailable

### Graceful Degradation
- When TMDB API key is missing, endpoints return empty results
- Network errors are logged but don't crash the application
- Local search functionality works independently of TMDB

## Data Enhancement

### Movie Enrichment Process
1. **Existing TMDB ID**: Fetches detailed information and updates movie
2. **No TMDB ID**: Searches by title and provides suggestions
3. **Data Preservation**: User data is never overwritten, only enhanced
4. **Selective Updates**: Only empty fields are populated from TMDB

### Enhanced Fields
- `tmdb_title`: Official TMDB title
- `tmdb_overview`: Movie plot summary
- `tmdb_release_date`: Official release date
- `tmdb_runtime`: Runtime in minutes
- `tmdb_rating`: Average user rating
- `tmdb_vote_count`: Number of votes
- `tmdb_poster_url`: High-quality poster image
- `tmdb_backdrop_url`: High-quality backdrop image
- `tmdb_genres`: List of genre names
- `tmdb_production_companies`: List of production companies

## Performance Considerations

### HTTP Client Management
- Single persistent HTTP client per service instance
- Connection pooling for better performance
- Proper cleanup during application shutdown

### Caching Strategy
- TMDB responses could be cached for better performance
- Consider implementing Redis cache for frequently accessed movies
- Rate limiting compliance to avoid API throttling

## Testing

### Unit Tests
- TMDB service methods with mocked HTTP responses
- Error handling scenarios
- Data transformation logic

### Integration Tests
- API endpoints with test TMDB responses
- Database integration with enriched data
- Error scenarios and graceful degradation

## Security

### API Key Management
- Store TMDB API key in environment variables
- Never commit API keys to version control
- Use different keys for development/production environments

### Rate Limiting
- TMDB API has rate limits (40 requests per 10 seconds)
- Consider implementing client-side rate limiting
- Monitor usage to avoid exceeding limits

## Future Enhancements

### Potential Features
- Automatic movie poster downloads
- Bulk movie enrichment
- TMDB watchlist integration
- Movie recommendations based on collection
- Cast and crew information display
- Movie trailers and videos

### Performance Improvements
- Response caching with Redis
- Background job processing for bulk operations
- Image optimization and CDN integration
- Database indexing for enhanced search performance
