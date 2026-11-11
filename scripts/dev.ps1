<#
.SYNOPSIS
    One-stop developer workflow for Media Manager (backend + frontend + MongoDB).

.DESCRIPTION
    Run from anywhere:  .\scripts\dev.ps1 <command> [options]
    Run with no arguments (or "help") to see all commands.
    Bash equivalent: ./scripts/dev.sh
#>
param(
    [Parameter(Position = 0)][string]$Command = "help",
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Rest = @()
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

function Info($m) { Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m) { Write-Host "[ OK ] $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; exit 1 }
function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Magenta }

# Run a native command and abort the script if it exits non-zero.
function Run([string]$Dir, [scriptblock]$Cmd) {
    Push-Location $Dir
    # Native tools (pnpm, uv, pytest) write progress to stderr; don't treat that as a script error.
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & $Cmd; if ($LASTEXITCODE -ne 0) { Fail "Command failed (exit $LASTEXITCODE): $Cmd" } }
    finally { $ErrorActionPreference = $prev; Pop-Location }
}

function Has($name) { [bool](Get-Command $name -ErrorAction SilentlyContinue) }

function Show-Help {
    @"
Media Manager dev script

Usage: .\scripts\dev.ps1 <command> [options]

Workflows
  all                 setup -> build -> test (full "is my environment good?" run)
  setup [-recompile]  check tools, create .env, install backend + frontend deps
                      (-recompile re-resolves requirements*.in via uv pip compile)
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

Examples
  .\scripts\dev.ps1 all
  .\scripts\dev.ps1 test backend tests/unit -x
  .\scripts\dev.ps1 run
"@ | Write-Host
}

# ---------------------------------------------------------------- prerequisites
function Test-Prereqs([switch]$Quiet) {
    $missing = @()
    foreach ($t in "uv", "node", "pnpm", "docker") {
        if (Has $t) { if (-not $Quiet) { Ok "$t found" } }
        else { $missing += $t; Warn "$t not found" }
    }
    if ($missing.Count -gt 0) {
        $hints = @{
            uv     = "winget install astral-sh.uv   (or https://docs.astral.sh/uv/)"
            node   = "mise install   (mise.toml pins node) or https://nodejs.org"
            pnpm   = "corepack enable pnpm   (or npm i -g pnpm)"
            docker = "https://www.docker.com/products/docker-desktop (needed for MongoDB)"
        }
        foreach ($m in $missing) { Write-Host "  install $m : $($hints[$m])" }
        return $false
    }
    return $true
}

function Cmd-Doctor {
    Step "Checking prerequisites"
    if (-not (Test-Prereqs)) { Fail "Install the missing tools above, then re-run." }
    if (Has docker) {
        docker info *> $null
        if ($LASTEXITCODE -ne 0) { Warn "Docker is installed but the daemon is not running (needed for MongoDB)" }
    }
    Ok "Prerequisites look good"
}

# ---------------------------------------------------------------------- config
function Ensure-Env {
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) {
        Copy-Item (Join-Path $Root ".env.example") $envFile
        Warn "Created .env from .env.example - add your TMDB_API_KEY"
    }
    elseif (-not (Select-String -Path $envFile -Pattern '^TMDB_API_KEY=(?!your_tmdb_api_key_here\s*$)\S+' -Quiet)) {
        Warn "TMDB_API_KEY looks unset in .env (movie metadata lookups will degrade)"
    }
    # The backend reads .env from its own working directory.
    # Host-run backend/tests must reach MongoDB via localhost (root .env may hold the Docker value 'mongodb').
    (Get-Content $envFile) -replace '^MONGO_HOST=.*$', 'MONGO_HOST=localhost' | Set-Content (Join-Path $Backend ".env")
    Ok "Synced .env -> backend/.env (MONGO_HOST forced to localhost)"
}

# ----------------------------------------------------------------------- setup
function Cmd-Setup {
    $recompile = $Rest -contains "-recompile" -or $Rest -contains "--recompile"
    Step "Prerequisites"
    if (-not (Test-Prereqs)) { Fail "Install the missing tools above, then re-run." }

    Step "Configuration"
    Ensure-Env

    Step "Backend dependencies"
    if (-not (Test-Path $VenvPython)) { Info "Creating virtual environment"; Run $Backend { uv venv } }
    if ($recompile) {
        Info "Recompiling requirements"
        Run $Backend { uv pip compile requirements.in -o requirements.txt --python .venv\Scripts\python.exe }
        Run $Backend { uv pip compile requirements-dev.in -o requirements-dev.txt --python .venv\Scripts\python.exe }
    }
    Run $Backend { uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt }

    Step "Frontend dependencies"
    Run $Root { pnpm install }
    Ok "Setup complete"
}

# ----------------------------------------------------------------------- build
function Require-Venv { if (-not (Test-Path $VenvPython)) { Fail "Backend venv missing. Run: .\scripts\dev.ps1 setup" } }

function Cmd-Build {
    Require-Venv
    Step "Backend: verify app imports"
    Run $Backend { & $VenvPython -c "import app.main; print('backend imports OK')" }
    Step "Frontend: production build"
    Run $Root { pnpm --filter frontend build }
    Ok "Build complete"
}

# ------------------------------------------------------------------------ db
function Wait-Mongo {
    Info "Waiting for MongoDB on localhost:27017"
    for ($i = 0; $i -lt 30; $i++) {
        $c = New-Object Net.Sockets.TcpClient
        try { $c.Connect("localhost", 27017); $c.Close(); Ok "MongoDB is up"; return }
        catch { Start-Sleep -Seconds 1 }
    }
    Fail "MongoDB did not become reachable. Check: .\scripts\dev.ps1 db logs"
}

function Cmd-Db {
    $action = if ($Rest.Count -gt 0) { $Rest[0] } else { "up" }
    switch ($action) {
        "up" { Run $Root { docker compose up -d mongodb mongo-express }; Wait-Mongo; Info "mongo-express: http://localhost:8081" }
        "down" { Run $Root { docker compose stop mongodb mongo-express } }
        "logs" { Run $Root { docker compose logs -f mongodb } }
        default { Fail "Unknown db action '$action' (use up|down|logs)" }
    }
}

function Ensure-Mongo {
    if (-not (Has docker)) { Warn "docker not found - assuming MongoDB is already running"; return }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { Fail "Docker daemon is not running. Start Docker Desktop, or run MongoDB yourself on localhost:27017." }
    Cmd-Db
}

# ------------------------------------------------------------------------ test
function Cmd-Test {
    $target = "all"
    $args2 = @($Rest)
    if ($args2.Count -gt 0 -and $args2[0] -in "all", "backend", "frontend") { $target = $args2[0]; $args2 = $args2[1..($args2.Count)] | Where-Object { $_ } }

    if ($target -in "all", "backend") {
        Require-Venv
        Step "Backend tests (pytest)"
        $Rest = @(); Ensure-Mongo
        Run $Backend { & $VenvPython -m pytest @args2 }
    }
    if ($target -in "all", "frontend") {
        Step "Frontend checks"
        $pkg = Get-Content (Join-Path $Frontend "package.json") -Raw | ConvertFrom-Json
        if ($pkg.scripts.PSObject.Properties.Name -contains "test") { Run $Root { pnpm --filter frontend test } }
        else { Info "No frontend test script defined; running svelte-check instead"; Run $Root { pnpm --filter frontend check } }
    }
    Ok "Tests complete"
}

# -------------------------------------------------------------------- lint/fmt
function Cmd-Lint {
    Require-Venv
    Step "Backend lint"
    Run $Backend { & $VenvPython -m flake8 app/ }
    Run $Backend { & $VenvPython -m black --check app/ }
    Step "Frontend check"
    Run $Root { pnpm --filter frontend check }
    Ok "Lint clean"
}

function Cmd-Format { Require-Venv; Run $Backend { & $VenvPython -m black app/ }; Ok "Formatted" }

# ------------------------------------------------------------------------- run
function Cmd-Run {
    $target = if ($Rest.Count -gt 0) { $Rest[0] } else { "all" }
    switch ($target) {
        "docker" { Run $Root { docker compose up --build } }
        "backend" { Require-Venv; Ensure-Env; Ensure-Mongo; Run $Backend { & $VenvPython -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 } }
        "frontend" { Run $Root { pnpm --filter frontend dev } }
        "all" {
            Require-Venv; Ensure-Env; Ensure-Mongo
            Info "Backend  http://localhost:8000  (docs: /docs)"
            Info "Frontend http://localhost:3000"
            Info "Press Ctrl+C to stop both"
            $pnpm = (Get-Command pnpm).Source   # may be pnpm.exe, pnpm.cmd or a shim depending on install
            $be = $null; $fe = $null
            try {
                $be = Start-Process -FilePath $VenvPython -WorkingDirectory $Backend -NoNewWindow -PassThru `
                    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"
                $fe = Start-Process -FilePath $pnpm -WorkingDirectory $Root -NoNewWindow -PassThru `
                    -ArgumentList "--filter", "frontend", "dev"
                Wait-Process -Id $be.Id, $fe.Id   # wait for BOTH, so `stop frontend` leaves the backend running
            }
            finally {
                foreach ($p in $be, $fe) { if ($p -and -not $p.HasExited) { taskkill /PID $p.Id /T /F *> $null } }
            }
        }
        default { Fail "Unknown run target '$target' (use all|backend|frontend|docker)" }
    }
}

# ------------------------------------------------------------------------ stop
# Kill a dev server: whatever listens on $Port, plus any process whose command line matches
# $Pattern (catches the uvicorn --reload parent, which can outlive the listener).
function Stop-DevServer([string]$Name, [int]$Port, [string]$Pattern) {
    $ids = @()
    $ids += Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | ForEach-Object { $_.OwningProcess }
    $ids += Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -match $Pattern } | ForEach-Object { $_.ProcessId }
    $ids = $ids | Where-Object { $_ -and $_ -ne 0 } | Select-Object -Unique
    if (-not $ids) { Info "$Name is not running"; return }
    foreach ($id in $ids) {
        $proc = Get-Process -Id $id -ErrorAction SilentlyContinue
        if ($proc) { Info "Stopping $Name (pid $id, $($proc.ProcessName))"; taskkill /PID $id /T /F *> $null }
    }
    Start-Sleep -Milliseconds 500
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { Warn "${Name}: port $Port is still in use" }
    else { Ok "$Name stopped (port $Port free)" }
}

function Cmd-Stop {
    $target = if ($Rest.Count -gt 0) { $Rest[0] } else { "all" }
    $root = [regex]::Escape($Root)
    switch ($target) {
        "backend" { Stop-DevServer "backend" 8000 'uvicorn app\.main:app' }
        "frontend" { Stop-DevServer "frontend" 3000 "$root.*(vite|svelte-kit)|(vite|svelte-kit).*$root" }
        "db" { Cmd-Db-Stop }
        "all" {
            Stop-DevServer "backend" 8000 'uvicorn app\.main:app'
            Stop-DevServer "frontend" 3000 "$root.*(vite|svelte-kit)|(vite|svelte-kit).*$root"
            Cmd-Db-Stop
        }
        default { Fail "Unknown stop target '$target' (use all|backend|frontend|db)" }
    }
}

function Cmd-Db-Stop {
    if (-not (Has docker)) { return }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { Info "Docker is not running; nothing to stop for db"; return }
    Run $Root { docker compose stop mongodb mongo-express }
}

# ------------------------------------------------------------- clients / clean
function Cmd-Clients {
    try { Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3 | Out-Null }
    catch { Fail "Backend is not running on :8000. Start it with: .\scripts\dev.ps1 run backend" }
    if (-not (Has bash)) { Fail "bash (Git Bash/WSL) is required for scripts/generate-clients.sh" }
    Run $Root { bash ./scripts/generate-clients.sh all }
}

function Cmd-Clean {
    foreach ($p in "backend\htmlcov", "backend\.pytest_cache", "backend\.coverage", "backend\dist", "frontend\.svelte-kit", "frontend\build", "frontend\dist") {
        $full = Join-Path $Root $p
        if (Test-Path $full) { Remove-Item $full -Recurse -Force; Info "removed $p" }
    }
    Ok "Clean (run 'setup' if you also want to reinstall dependencies)"
}

function Cmd-All { Cmd-Setup; $script:Rest = @(); Cmd-Build; Cmd-Test; Ok "Environment is ready. Start developing with: .\scripts\dev.ps1 run" }

switch ($Command.ToLower()) {
    "all" { Cmd-All }
    "setup" { Cmd-Setup }
    "build" { Cmd-Build }
    "test" { Cmd-Test }
    "run" { Cmd-Run }
    "db" { Cmd-Db }
    "stop" { Cmd-Stop }
    "lint" { Cmd-Lint }
    "format" { Cmd-Format }
    "clients" { Cmd-Clients }
    "clean" { Cmd-Clean }
    "doctor" { Cmd-Doctor }
    { $_ -in "help", "-h", "--help" } { Show-Help }
    default { Write-Host "Unknown command: $Command`n" -ForegroundColor Red; Show-Help; exit 1 }
}
