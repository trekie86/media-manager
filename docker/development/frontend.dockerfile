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

# Start development server with hot reload
CMD ["pnpm", "dev", "--host"]
