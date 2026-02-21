# Use Node.js LTS (Long Term Support) as base image
FROM node:20-slim

# Set working directory to workspace root (needed for pnpm workspace)
WORKDIR /workspace

# Install pnpm globally
RUN npm install -g pnpm

# Copy workspace and lock files first for layer caching
COPY pnpm-workspace.yaml ./
COPY pnpm-lock.yaml ./

# Copy frontend package manifest
COPY frontend/package.json ./frontend/

# Install only frontend dependencies
RUN pnpm install --filter frontend --frozen-lockfile

# Copy the frontend source
COPY frontend/ ./frontend/

# Run dev server from within the frontend package
WORKDIR /workspace/frontend

# Expose port 3000
EXPOSE 3000

# Re-run pnpm install on each container start so node_modules stays in sync
# with the lockfile even when Docker anonymous volumes are reused across rebuilds.
CMD ["sh", "-c", "cd /workspace && pnpm install --filter frontend --frozen-lockfile && pnpm --filter frontend dev --host"]
