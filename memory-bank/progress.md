# Project Progress

## Completed Items

### Phase 1: Foundation ✅
- [x] Architecture Decision Records (ADRs 001-004)
- [x] Docker configuration (multi-container: frontend, backend, mongodb, mongo-express)
- [x] MongoDB initialization script with schema validators and indexes
- [x] FastAPI project initialization with core config, settings, DB connection
- [x] Environment variable templates

### Phase 2A: Testing Framework & Authentication ✅
- [x] pytest with custom markers, fixtures, test database isolation
- [x] JWT-based authentication (login, logout, register, refresh, /me)
- [x] 89 tests passing, 62% code coverage

### Phase 2B/2C: OpenAPI Client Generation ✅
- [x] TypeScript client generated (@trekie86/media-manager-client)
- [x] Python client generated (media_manager_client)
- [x] Prism CLI mock server (port 3001)
- [x] npm scripts for generate/validate/watch

### Movie Management API ✅
- [x] CRUD endpoints (POST, GET, PUT, DELETE /api/movies)
- [x] List with filtering (storage_id, format, genre) and pagination
- [x] Local search (/api/movies/search) with text + regex fallback
- [x] TMDB search (/api/movies/tmdb/search)
- [x] TMDB movie details (/api/movies/tmdb/{id})
- [x] Movie enrichment (/api/movies/{id}/enrich)

### Storage Management API ✅
- [x] CRUD endpoints (POST, GET, PUT, DELETE /api/storage)
- [x] Materialized path pattern for hierarchy (cabinet → shelf → bin → drawer)
- [x] Tree endpoint (/api/storage/{id}/tree) with ancestors + descendants
- [x] Cycle detection and path cascading on move

### Phase 3A: Frontend Development ✅
- [x] SvelteKit 2 + Svelte 5 + TypeScript project in `frontend/`
- [x] Tailwind CSS v4 via `@tailwindcss/vite` plugin
- [x] Skeleton UI v4 (cerberus theme) — relative path import workaround in `app.css`
- [x] `pnpm-workspace.yaml` at project root
- [x] Typed API client layer: `src/lib/api/{client,auth,movies,storage}.ts`
- [x] Auth store with localStorage persistence (`src/lib/stores/auth.ts`)
- [x] Login page `/login`
- [x] Register page `/register` (auto-login after registration)
- [x] Protected app layout `/(app)/+layout.svelte` — sidebar, search bar, user menu, logout
- [x] Movies catalog `/movies` — grid, filters, TMDB search-to-fill, enrich, edit, delete
- [x] Storage management `/storage` — tree panel + detail panel with movies list

### Phase 3A: Backend Bug Fixes ✅
- [x] `db/connection.py`: `if not db` → `if db is None` (pymongo forbids bool on Database objects)
- [x] `api/auth.py`: Replaced passlib `CryptContext` with direct `bcrypt` calls (passlib 1.7.4 incompatible with bcrypt 4.x)
- [x] `api/auth.py`: `model_dump(exclude_none=True)` on user insert to avoid null email failing MongoDB schema validator
- [x] `mongo-init.js`: email field updated to `bsonType: ['string', 'null']`
- [x] Live MongoDB `users` collection schema patched via `collMod`

### Phase 3B: Polish & Integration ✅
- [x] Removed `passlib` from `requirements.in`, regenerated `requirements.txt` via uv (bcrypt is now a direct dep)
- [x] Fixed FastAPI route ordering bug: `/search` and `/tmdb/*` routes moved before `/{movie_id}` in `api/movies.py`
- [x] Added MongoDB text index on `(title, genre)` in `create_indexes()` — `/api/movies/search` now works via text search with regex fallback
- [x] Global toast store (`src/lib/stores/toast.ts`) + Toast component (`src/lib/components/Toast.svelte`) mounted in root layout
- [x] Movie grid loading skeletons (12 animated placeholder cards) replacing plain spinner
- [x] Toast notifications wired to all CRUD actions on movies and storage pages

## In Progress / Next Priority: Phase 4 - Testing & CI

### Setup
- [ ] Add real TMDB API key to `.env` (currently placeholder `your_tmdb_api_key_here`)

### Testing
- [ ] End-to-end smoke test: register → create storage → add movie → search → verify location
- [ ] Performance tests for storage tree operations
- [ ] CI pipeline integration (GitHub Actions)

### Future Polish
- [ ] Mobile responsive layout review
- [ ] Empty state illustrations

### Future (Phase 4)
- [ ] Mobile-responsive design pass
- [ ] Advanced filtering (multi-genre, year range)
- [ ] Collection statistics dashboard
- [ ] Bulk import/export (CSV)
- [ ] Loan tracking
- [ ] Wishlist integration

## Current Challenges / Known Issues
- `passlib` still in requirements.txt (unused, should be removed)
- TMDB enrichment requires a valid API key in `.env`
- Movie text search requires MongoDB text index to be created manually (not auto-created on startup)
- The `/api/movies/search` route ordering in FastAPI may conflict with `/{movie_id}` — worth investigating if search returns unexpected results
