# Active Context

## Current Focus

### COMPLETED: Phase 2A - Testing Framework & Authentication System ✅
- ✅ Built complete CRUD operations for movies
- ✅ Integrated with existing storage system
- ✅ Implemented comprehensive validation and error handling
- ✅ Created full test suite with 21 integration tests for movies
- ✅ Achieved 82% test coverage for movies API
- ✅ Full TMDB API integration with professional service architecture
- ✅ Advanced movie search with text search and regex fallback
- ✅ Movie metadata enrichment from TMDB database
- ✅ Clean service architecture with singleton pattern and dependency injection
- ✅ TMDB search endpoints for external movie discovery
- ✅ Movie enrichment endpoint with automatic metadata enhancement
- ✅ Comprehensive TMDB integration documentation
- ✅ **Authentication middleware and session management implementation**
- ✅ **Comprehensive authentication test suite (14 tests)**
- ✅ **All 89 tests passing with 62% code coverage**
- ✅ **JWT-based stateless session management**
- ✅ **Complete authentication system (login, logout, register, refresh, /me)**

### COMPLETED: Phase 2B - OpenAPI Documentation & Client Generation Planning ✅
- ✅ Comprehensive OpenAPI integration documentation
- ✅ ADR-004 for OpenAPI client generation architecture
- ✅ TypeScript client generation strategy for Svelte frontend
- ✅ Mock server generation plan for frontend development
- ✅ Multi-language client support (TypeScript + Python)

### COMPLETED: Phase 2C - OpenAPI Client Generation Implementation ✅
- ✅ Generated TypeScript client (@trekie86/media-manager-client)
- ✅ Generated Python client (media_manager_client)
- ✅ Prism CLI mock server for frontend development
- ✅ Comprehensive automation scripts for client generation and validation

### COMPLETED: Phase 3A - Frontend Development Setup ✅
- ✅ SvelteKit 2 + Svelte 5 + TypeScript project initialized in `frontend/`
- ✅ Vite configured to run on port 3000
- ✅ Tailwind CSS v4 via `@tailwindcss/vite` plugin configured
- ✅ Skeleton UI v4 integrated (cerberus theme, relative CSS import path workaround)
- ✅ `pnpm-workspace.yaml` created at project root
- ✅ Typed API client layer (`src/lib/api/client.ts`, `auth.ts`, `movies.ts`, `storage.ts`)
- ✅ Auth store (`src/lib/stores/auth.ts`) with localStorage persistence + auto token injection
- ✅ Login page (`/login`) with error handling and redirect
- ✅ Register page (`/register`) with auto-login after registration
- ✅ Protected app layout (`/(app)/+layout.svelte`) with sidebar nav, search bar, user menu
- ✅ Movies catalog (`/movies`) — grid view, format/storage/genre filters, TMDB search-to-fill modal, enrich button, delete confirm
- ✅ Storage management (`/storage`) — tree view panel, detail panel with movies per location, full CRUD

### COMPLETED: Phase 3A - Backend Bug Fixes ✅
- ✅ **pymongo bool check bug**: `if not db` / `if client` → `if db is None` / `if client is not None` in `db/connection.py`
- ✅ **passlib + bcrypt 4.x incompatibility**: Replaced `CryptContext` with direct `bcrypt.hashpw` / `bcrypt.checkpw` calls in `api/auth.py`
- ✅ **MongoDB null email validation**: Added `exclude_none=True` to `model_dump()` on user insert; patched live collection schema to allow `["string", "null"]` for email; updated `mongo-init.js` to match

### COMPLETED: Phase 3B - Frontend Polish & Integration ✅
- ✅ Removed `passlib` from `requirements.in`, added `bcrypt>=4.0.0` directly; regenerated `requirements.txt` via uv
- ✅ Added MongoDB text index on `(title, genre)` to `create_indexes()` in `db/connection.py`
- ✅ Fixed FastAPI route ordering in `api/movies.py`: `/search`, `/tmdb/search`, `/tmdb/{tmdb_id}` now defined before `/{movie_id}` (was being shadowed)
- ✅ Global toast notification system: `src/lib/stores/toast.ts` + `src/lib/components/Toast.svelte`, mounted in root layout
- ✅ Loading skeleton grid on movies page (12 animated placeholder cards matching movie card proportions)
- ✅ Wired toast success/error to all movie CRUD actions and enrich, and storage CRUD actions

### CURRENT PRIORITY: Phase 4 - Testing & CI
- End-to-end smoke test: register → create storage → add movie → search → verify location
- TMDB API key configuration (currently placeholder in `.env`)
- Mobile responsive layout review
- Performance tests for storage tree operations
- CI pipeline integration

## Recent Changes

### Phase 3A Frontend (Just Completed)
- **SvelteKit project**: `frontend/` created with sv CLI, TypeScript, Svelte 5 runes syntax
- **Skeleton UI setup**: Tailwind v4 `@import` with bare package specifiers fails in `@tailwindcss/vite` bundler for wildcard exports. Fix: use relative paths `../node_modules/@skeletonlabs/skeleton/src/...` directly in `app.css`
- **Theme activation**: `data-theme="cerberus"` added to `<body>` in `app.html` (Skeleton v4 scopes theme under this attribute)
- **API client**: `setTokenGetter()` pattern wires auth store into every API request automatically
- **Route protection**: `/(app)/+layout.ts` sets `ssr = false`; auth check in `onMount` in layout component
- **Storage tree**: `buildTree()` in `storage.ts` converts flat list → nested `StorageNode[]` client-side

### Backend Bug Fixes (Just Completed)
- `backend/app/db/connection.py` — two `is None` fixes
- `backend/app/api/auth.py` — passlib removed, bcrypt used directly
- MongoDB `users` collection schema patched live via `mongosh collMod`
- `docker/development/mongo-init.js` — email field updated to `["string", "null"]`

## Key Technical Decisions Made

### Skeleton UI v4 CSS Import Workaround
The `@tailwindcss/vite` CSS bundler does not resolve wildcard subpath package exports
(`"./themes/*": "./src/themes/*.css"`). Solution: import via relative filesystem path in `app.css`:
```css
@import "../node_modules/@skeletonlabs/skeleton/src/themes/cerberus.css";
@import "../node_modules/@skeletonlabs/skeleton/src/index.css";
```
This also ensures `@utility` directives in Skeleton CSS are processed by Tailwind in the same bundle.

### Direct bcrypt Usage
`passlib 1.7.4` is incompatible with `bcrypt 4.x` — the `detect_wrap_bug()` test sends a >72 byte
password which bcrypt 4.x rejects with `ValueError`. Fix: use `bcrypt` directly, no passlib needed.

### pnpm Workspaces
`pnpm-workspace.yaml` created at project root (pnpm ignores the `"workspaces"` field in `package.json`).

## Active Decisions
- Using FastAPI with async/await pattern for all API endpoints
- MongoDB with proper schema validation and ObjectId handling
- Comprehensive test coverage for all API endpoints
- RESTful API design with proper HTTP status codes
- Pydantic models for consistent request/response validation
- SvelteKit with Svelte 5 runes (`$state`, `$props`, `$effect`, `$derived`)
- Client-side only auth (SSR disabled for protected routes)

## Next Immediate Steps

1. **TMDB API Key** — Add real key to `.env` (currently placeholder), required for movie enrichment
2. **MongoDB text index** — Run `db.movies.createIndex({ title: "text" })` so `/api/movies/search` works
3. **passlib cleanup** — Remove from `requirements.in`, regenerate `requirements.txt`
4. **Frontend UX polish** — Loading states, error boundaries, mobile layout review
5. **End-to-end smoke test** — Register → create storage hierarchy → add movie → search → verify location
