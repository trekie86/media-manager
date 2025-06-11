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
2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```
   Note: The setup script will automatically copy this .env file to the backend directory.
   If you update the .env file later, either:
   - Copy it manually to the backend folder
   - Or run the setup script again

3. Start required services:
   - **Full Docker Setup**: Run `docker compose up -d` (runs everything in containers)
   - **Local Development**: Run `docker compose up -d mongodb mongo-express` (provides required MongoDB instance)

Note: Local development requires MongoDB. The easiest way to provide this is by running the MongoDB container from the docker-compose configuration. When running the backend locally, you need to use different MongoDB connection settings:

For local backend development:
```bash
# In .env
MONGO_HOST=localhost  # Use localhost when running backend locally
```

For Docker development:
```bash
# In .env
MONGO_HOST=mongodb   # Use container name when running in Docker
```

If you prefer to use your own MongoDB instance, update all the connection details in `.env` accordingly.

### Backend Setup

#### Using Virtual Environment (Local Development)

Prerequisites:
- Ensure MongoDB is running (either through Docker or your own instance)
- If using Docker: `docker compose up -d mongodb mongo-express`
- Ensure you have configured .env file in the root directory

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Run setup script to create virtual environment and install dependencies:
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
   - Create virtual environment
   - Generate requirements.txt from requirements.in
   - Install all development dependencies

3. Activate the virtual environment:
   ```bash
   # On Unix/macOS:
   source .venv/bin/activate
   
   # On Windows:
   .\.venv\Scripts\Activate.ps1
   ```
   
   You should see your prompt change to indicate the virtual environment is active.

4. Start the development server:
   ```bash
   # Make sure your virtual environment is activated first
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Access the API:
   - API Endpoints: http://localhost:8000
   - Interactive API Documentation (Swagger UI): http://localhost:8000/docs
   - Alternative API Documentation (ReDoc): http://localhost:8000/redoc

Notes:
- The virtual environment must be activated in each new terminal window you open
- The `--reload` flag enables hot-reload during development
- The server will restart automatically when you make changes
- To deactivate the virtual environment when done:
  ```bash
  deactivate
  ```

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
