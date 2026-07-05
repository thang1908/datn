"""FastAPI application — CS Agent QA Pipeline."""

import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from src.api.routes import connections, conversations, health, pipeline
from src.core import setup_logging
from src.core.config import settings
from src.db import close_db

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
}


def _frontend_url(path: str, query: str) -> str:
    origin = os.getenv("NEXT_INTERNAL_ORIGIN", "http://127.0.0.1:3000").rstrip("/")
    url = f"{origin}/{path}" if path else f"{origin}/"
    return f"{url}?{query}" if query else url


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup/shutdown."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CS Agent QA — LangGraph pipeline agent. Submit a call or ticket and receive analysis results synchronously.",
    lifespan=lifespan,
)

# CORS — cho phép frontend Next.js gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(health.router)
app.include_router(connections.router)
app.include_router(pipeline.router)
app.include_router(conversations.router)


@app.api_route("/{path:path}", methods=["GET", "HEAD"])
async def serve_frontend(path: str, request: Request):
    """Serve the Next.js UI when this FastAPI app is the public Render entrypoint."""
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS and key.lower() != "host"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
            upstream = await client.request(
                request.method,
                _frontend_url(path, request.url.query),
                headers=headers,
            )
    except httpx.HTTPError:
        return Response("Frontend is starting. Please refresh shortly.", status_code=503)

    response_headers = {
        key: value
        for key, value in upstream.headers.items()
        if key.lower() not in _HOP_BY_HOP_HEADERS
    }

    return Response(
        content=b"" if request.method == "HEAD" else upstream.content,
        status_code=upstream.status_code,
        headers=response_headers,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )
