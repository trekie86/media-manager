# Media Manager

A web application to manage your physical media collection and track storage locations.

## Features

- Track movie collections with metadata from TMDB
- Manage storage locations (bins)
- Search and filter your collection
- Secure authentication system

## Technology Stack

- Frontend: Svelte with Skeleton UI
- Backend: FastAPI (Python)
- Database: MongoDB
- Infrastructure: Docker

## Development Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.11 or higher
- Node.js 20 or higher
- uv (Python package installer)

### Quick Start

1. Clone the repository
2. Copy environment file: `cp .env.example .env`
3. Update environment variables in `.env`
4. Start required services:
   - **Full Docker Setup**: Run `docker compose up -d` (runs everything in containers)
   - **Local Development**: Run `docker compose up -d mongodb mongo-express` (provides required MongoDB instance)

Note: Local development requires MongoDB. The easiest way to provide this is by running the MongoDB container from the docker-compose configuration. If you prefer to use your own MongoDB instance, update the connection details in `.env`.

### Backend Setup

#### Using Virtual Environment (Local Development)

Prerequisites:
- Ensure MongoDB is running (either through Docker or your own instance)
- If using Docker: `docker compose up -d mongodb mongo-express`

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Run setup script:
   - Unix/macOS:
     ```bash
     ./scripts/setup_dev.sh
     ```
   - Windows:
     ```powershell
     .\scripts\setup_dev.ps1
     ```

   The setup scripts will:
   - Install uv if not present
   - Create and activate a virtual environment
   - Generate requirements.txt from requirements.in
   - Install all development dependencies

3. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. Access the API:
   - API Endpoints: http://localhost:8000
   - Interactive API Documentation (Swagger UI): http://localhost:8000/docs
   - Alternative API Documentation (ReDoc): http://localhost:8000/redoc

Notes:
- To activate the virtual environment in new terminals:
  - Unix/macOS: `source .venv/bin/activate`
  - Windows: `.\.venv\Scripts\Activate.ps1`
- The `--reload` flag enables hot-reload during development
- The server will restart automatically when you make changes

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

3. Start development server:
   ```bash
   pnpm dev
   ```

4. Access the frontend:
   - Open http://localhost:3000 in your browser
   - Changes will hot-reload automatically

### Docker Setup (Full Stack)

1. Start all services:
   ```bash
   # Build and start containers
   docker compose up -d

   # View logs (optional)
   docker compose logs -f
   ```

2. Access services:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MongoDB Express: http://localhost:8081

3. Stop services:
   ```bash
   # Stop containers
   docker compose down

   # Stop and remove volumes (if needed)
   docker compose down -v
   ```

Notes:
- First startup may take a few minutes to build containers
- MongoDB data persists between restarts unless you use `-v`
- Use `docker compose ps` to check container status

## Available Services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- MongoDB Express: http://localhost:8081

## Development Workflow

1. Activate virtual environment (for backend development)
2. Make your changes
3. Run tests: `pytest` (in backend directory)
4. Format code: `black .` (in backend directory)
5. Submit pull request

## Environment Variables

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Required variables:
- `TMDB_API_KEY`: Your TMDB API key
- `MONGO_USER`: MongoDB username
- `MONGO_PASSWORD`: MongoDB password

## License

[License details here]
