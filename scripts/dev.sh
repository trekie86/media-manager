#!/usr/bin/env bash
# One-stop developer workflow for Media Manager (backend + frontend + MongoDB).
# Usage: ./scripts/dev.sh <command> [options]   (no args or "help" lists commands)
# PowerShell equivalent: .\scripts\dev.ps1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
if [ -x "$BACKEND/.venv/bin/python" ]; then VENV_PY="$BACKEND/.venv/bin/python"; else VENV_PY="$BACKEND/.venv/Scripts/python.exe"; fi

info() { printf '\033[0;36m[INFO]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m[ OK ]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
fail() { printf '\033[0;31m[FAIL]\033[0m %s\n' "$*"; exit 1; }
step() { printf '\n\033[0;35m=== %s ===\033[0m\n' "$*"; }
has()  { command -v "$1" >/dev/null 2>&1; }

show_help() {
  cat <<'EOF'
Media Manager dev script

Usage: ./scripts/dev.sh <command> [options]

Workflows
  all                 setup -> build -> test (full "is my environment good?" run)
  setup [--recompile] check tools, create .env, install backend + frontend deps
                      (--recompile re-resolves requirements*.in via uv pip compile)
  build               backend import check + frontend production build
  test [target] [args]  target: all (default) | backend | frontend
                      extra args go to pytest, e.g. test backend -k storage
                      (starts MongoDB in Docker automatically if needed)

Run
  run [target]        target: all (default: db + backend + frontend) | backend |
                      frontend | docker (full stack in docker compose)
  stop [target]       target: all (default: backend + frontend + db) | backend |
                      frontend | db   (kills the process trees, frees :8000 / :3000)
  db [up|down|logs]   manage the MongoDB + mongo-express containers (default: up)

Quality / tooling
  lint                flake8 + black --check (backend), frontend svelte-check
  format              black (backend)
  clients             regenerate OpenAPI clients (needs backend running on :8000)
  clean               remove build output and caches (keeps .venv / node_modules)
  doctor              check prerequisites only
EOF
}

check_prereqs() {
  local missing=0 t
  for t in uv node pnpm docker; do
    if has "$t"; then ok "$t found"; else warn "$t not found"; missing=1; fi
  done
  if [ "$missing" -eq 1 ]; then
    echo "  uv: https://docs.astral.sh/uv/   node: mise install (see mise.toml)"
    echo "  pnpm: corepack enable pnpm       docker: https://www.docker.com (needed for MongoDB)"
    return 1
  fi
}

cmd_doctor() {
  step "Checking prerequisites"
  check_prereqs || fail "Install the missing tools above, then re-run."
  if has docker && ! docker info >/dev/null 2>&1; then warn "Docker is installed but the daemon is not running (needed for MongoDB)"; fi
  ok "Prerequisites look good"
}

ensure_env() {
  if [ ! -f "$ROOT/.env" ]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
    warn "Created .env from .env.example - add your TMDB_API_KEY"
  elif ! grep -Eq '^TMDB_API_KEY=[^[:space:]]+' "$ROOT/.env" || grep -q '^TMDB_API_KEY=your_tmdb_api_key_here' "$ROOT/.env"; then
    warn "TMDB_API_KEY looks unset in .env (movie metadata lookups will degrade)"
  fi
  # The backend reads .env from its own working directory.
  # Host-run backend/tests must reach MongoDB via localhost (root .env may hold the Docker value 'mongodb').
  sed 's/^MONGO_HOST=.*/MONGO_HOST=localhost/' "$ROOT/.env" > "$BACKEND/.env"
  ok "Synced .env -> backend/.env (MONGO_HOST forced to localhost)"
}

require_venv() { [ -x "$VENV_PY" ] || [ -f "$VENV_PY" ] || fail "Backend venv missing. Run: ./scripts/dev.sh setup"; }

cmd_setup() {
  local recompile=0 a
  for a in "$@"; do [ "$a" = "--recompile" ] && recompile=1; done
  step "Prerequisites"; check_prereqs || fail "Install the missing tools above, then re-run."
  step "Configuration"; ensure_env
  step "Backend dependencies"
  cd "$BACKEND"
  [ -d .venv ] || { info "Creating virtual environment"; uv venv; }
  if [ "$recompile" -eq 1 ]; then
    info "Recompiling requirements"
    uv pip compile requirements.in -o requirements.txt --python "$VENV_PY"
    uv pip compile requirements-dev.in -o requirements-dev.txt --python "$VENV_PY"
  fi
  [ -x "$BACKEND/.venv/bin/python" ] && VENV_PY="$BACKEND/.venv/bin/python" || VENV_PY="$BACKEND/.venv/Scripts/python.exe"
  uv pip install --python "$VENV_PY" -r requirements-dev.txt
  step "Frontend dependencies"
  cd "$ROOT" && pnpm install
  ok "Setup complete"
}

cmd_build() {
  require_venv
  step "Backend: verify app imports"
  (cd "$BACKEND" && "$VENV_PY" -c "import app.main; print('backend imports OK')")
  step "Frontend: production build"
  (cd "$ROOT" && pnpm --filter frontend build)
  ok "Build complete"
}

wait_mongo() {
  info "Waiting for MongoDB on localhost:27017"
  for _ in $(seq 1 30); do
    if (exec 3<>/dev/tcp/localhost/27017) 2>/dev/null; then ok "MongoDB is up"; return 0; fi
    sleep 1
  done
  fail "MongoDB did not become reachable. Check: ./scripts/dev.sh db logs"
}

cmd_db() {
  case "${1:-up}" in
    up)   (cd "$ROOT" && docker compose up -d mongodb mongo-express); wait_mongo; info "mongo-express: http://localhost:8081" ;;
    down) (cd "$ROOT" && docker compose stop mongodb mongo-express) ;;
    logs) (cd "$ROOT" && docker compose logs -f mongodb) ;;
    *)    fail "Unknown db action '$1' (use up|down|logs)" ;;
  esac
}

ensure_mongo() {
  if ! has docker; then warn "docker not found - assuming MongoDB is already running"; return; fi
  docker info >/dev/null 2>&1 || fail "Docker daemon is not running. Start Docker, or run MongoDB yourself on localhost:27017."
  cmd_db up
}

cmd_test() {
  local target=all
  case "${1:-}" in all|backend|frontend) target="$1"; shift ;; esac
  if [ "$target" = all ] || [ "$target" = backend ]; then
    require_venv
    step "Backend tests (pytest)"
    ensure_mongo
    (cd "$BACKEND" && "$VENV_PY" -m pytest "$@")
  fi
  if [ "$target" = all ] || [ "$target" = frontend ]; then
    step "Frontend checks"
    if grep -q '"test"' "$FRONTEND/package.json"; then (cd "$ROOT" && pnpm --filter frontend test)
    else info "No frontend test script defined; running svelte-check instead"; (cd "$ROOT" && pnpm --filter frontend check); fi
  fi
  ok "Tests complete"
}

cmd_lint() {
  require_venv
  step "Backend lint"; (cd "$BACKEND" && "$VENV_PY" -m flake8 app/ && "$VENV_PY" -m black --check app/)
  step "Frontend check"; (cd "$ROOT" && pnpm --filter frontend check)
  ok "Lint clean"
}

cmd_format() { require_venv; (cd "$BACKEND" && "$VENV_PY" -m black app/); ok "Formatted"; }

cmd_run() {
  case "${1:-all}" in
    docker)   (cd "$ROOT" && docker compose up --build) ;;
    backend)  require_venv; ensure_env; ensure_mongo; cd "$BACKEND" && exec "$VENV_PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 ;;
    frontend) cd "$ROOT" && exec pnpm --filter frontend dev ;;
    all)
      require_venv; ensure_env; ensure_mongo
      info "Backend  http://localhost:8000  (docs: /docs)"
      info "Frontend http://localhost:3000"
      info "Press Ctrl+C to stop both"
      trap 'kill 0 2>/dev/null || true' INT TERM EXIT
      (cd "$BACKEND" && "$VENV_PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
      (cd "$ROOT" && pnpm --filter frontend dev) &
      wait   # wait for BOTH, so `stop frontend` leaves the backend running
      ;;
    *) fail "Unknown run target '$1' (use all|backend|frontend|docker)" ;;
  esac
}

# Kill a dev server: whatever listens on $2 (port), plus processes whose command line matches $3.
stop_server() {
  local name="$1" port="$2" pattern="$3" pids=""
  if has lsof; then pids="$(lsof -ti "tcp:$port" -sTCP:LISTEN 2>/dev/null || true)"
  elif has fuser; then pids="$(fuser "$port/tcp" 2>/dev/null || true)"; fi
  pids="$pids $(pgrep -f "$pattern" 2>/dev/null || true)"
  pids="$(printf '%s\n' $pids | grep -E '^[0-9]+$' | grep -vx "$$" | sort -u | tr '\n' ' ')"
  if [ -z "${pids// /}" ]; then info "$name is not running"; return; fi
  info "Stopping $name (pid ${pids% })"
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true; sleep 1
  # shellcheck disable=SC2086
  kill -9 $pids 2>/dev/null || true
  ok "$name stopped"
}

stop_db() {
  has docker && docker info >/dev/null 2>&1 || { info "Docker is not running; nothing to stop for db"; return 0; }
  (cd "$ROOT" && docker compose stop mongodb mongo-express)
}

cmd_stop() {
  case "${1:-all}" in
    backend)  stop_server backend 8000 'uvicorn app.main:app' ;;
    frontend) stop_server frontend 3000 "$ROOT.*(vite|svelte-kit)" ;;
    db)       stop_db ;;
    all)      stop_server backend 8000 'uvicorn app.main:app'; stop_server frontend 3000 "$ROOT.*(vite|svelte-kit)"; stop_db ;;
    *)        fail "Unknown stop target '$1' (use all|backend|frontend|db)" ;;
  esac
}

cmd_clients() {
  curl -fsS http://localhost:8000/health >/dev/null 2>&1 || fail "Backend is not running on :8000. Start it with: ./scripts/dev.sh run backend"
  (cd "$ROOT" && bash ./scripts/generate-clients.sh all)
}

cmd_clean() {
  local p
  for p in backend/htmlcov backend/.pytest_cache backend/.coverage backend/dist frontend/.svelte-kit frontend/build frontend/dist; do
    if [ -e "$ROOT/$p" ]; then rm -rf "$ROOT/$p"; info "removed $p"; fi
  done
  ok "Clean (run 'setup' if you also want to reinstall dependencies)"
}

cmd="${1:-help}"; [ $# -gt 0 ] && shift
case "$cmd" in
  all)     cmd_setup; cmd_build; cmd_test; ok "Environment is ready. Start developing with: ./scripts/dev.sh run" ;;
  setup)   cmd_setup "$@" ;;
  build)   cmd_build ;;
  test)    cmd_test "$@" ;;
  run)     cmd_run "$@" ;;
  db)      cmd_db "$@" ;;
  stop)    cmd_stop "$@" ;;
  lint)    cmd_lint ;;
  format)  cmd_format ;;
  clients) cmd_clients ;;
  clean)   cmd_clean ;;
  doctor)  cmd_doctor ;;
  help|-h|--help) show_help ;;
  *) echo "Unknown command: $cmd"; echo; show_help; exit 1 ;;
esac
