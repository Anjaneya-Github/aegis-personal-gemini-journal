# -------------------------------------------------------------
# Stage 1: Build React Vite Frontend SPA
# -------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# Copy package manifests and install dependencies
COPY package.json ./
RUN npm install --no-audit --no-fund

# Copy frontend source files, config, and assets
COPY index.html vite.config.js firebase-applet-config.json ./
COPY src ./src
COPY assets ./assets

# Build production static assets into /build/dist
RUN npm run build

# -------------------------------------------------------------
# Stage 2: Production Python Runtime
# -------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=3000

# Install Python backend dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI backend application code
COPY backend/app ./app

# Copy compiled frontend dist from Stage 1 into /app/dist
COPY --from=frontend-builder /build/dist ./dist

# Non-root security user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 3000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3000}"]
