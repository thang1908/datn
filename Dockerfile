# ── Stage 1: Backend dependencies ─────────────────────────────
FROM python:3.12-slim AS backend-builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Frontend dependencies ────────────────────────────
FROM node:22-slim AS frontend-deps

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm ci

# ── Stage 3: Frontend build ───────────────────────────────────
FROM frontend-deps AS frontend-builder

WORKDIR /app/frontend

ENV NEXT_PUBLIC_API_URL="" \
    INTERNAL_API_ORIGIN="http://127.0.0.1:8000"

COPY frontend/ ./

RUN npm run build

# ── Stage 4: Runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    NEXT_HOST=127.0.0.1 \
    NEXT_PORT=3000 \
    PORT=8000

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=backend-builder /install /usr/local

# Copy Node runtime for the standalone Next.js server
COPY --from=frontend-deps /usr/local/bin/node /usr/local/bin/node

# Copy application source
COPY src/ ./src/
COPY scripts/start-render.sh ./scripts/start-render.sh

# Copy standalone Next.js application
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/
COPY --from=frontend-builder /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /app/frontend/public ./frontend/public

# Create non-root user
RUN useradd --no-create-home --shell /bin/false appuser \
    && chmod +x /app/scripts/start-render.sh \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT', '8000')}/\")"

CMD ["./scripts/start-render.sh"]
