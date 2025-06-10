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

### Backend Setup

#### Using Virtual Environment (Local Development)

Unix/macOS:
```bash
# Navigate to backend directory
cd backend

# Run setup script
./scripts/setup_dev.sh
```

Windows:
```powershell
# Navigate to backend directory
cd backend

# Run setup script
.\scripts\setup_dev.ps1
```

The setup scripts will:
1. Install uv if not present
2. Create and activate a virtual environment
3. Generate requirements.txt from requirements.in
4. Install all development dependencies

To activate the virtual environment in new terminals:
- Unix/macOS: `source .venv/bin/activate`
- Windows: `.\.venv\Scripts\Activate.ps1`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Docker Setup (Full Stack)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

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
