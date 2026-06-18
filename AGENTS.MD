# Agent Instructions

## Project Overview

This repository contains the CS Agent QA system for automated customer-service call quality analysis.

- Backend: FastAPI application in `src/`.
- AI pipeline: LangGraph workflow in `src/graph/` using Google Gemini through LangChain.
- Storage: MongoDB accessed asynchronously with Motor in `src/db/`.
- Frontend: Next.js application in `frontend/`.
- Tests: Pytest tests in `tests/`.

## Scope

These instructions apply to the whole repository. More specific instructions in nested files take precedence, especially `frontend/AGENTS.md` for frontend work.

## Repository Layout

- `src/main.py`: FastAPI entrypoint.
- `src/api/routes/`: HTTP API routes.
- `src/services/`: orchestration and service logic.
- `src/graph/`: LangGraph workflow, state, and processing nodes.
- `src/models/`: Pydantic request, response, CRM, and pipeline models.
- `src/core/`: configuration, logging, and LLM client setup.
- `src/db/`: MongoDB connection and persistence helpers.
- `src/utils/`: constants, prompts, and shared helpers.
- `frontend/`: Next.js dashboard.
- `docs/`: project documentation.
- `data/`: local or temporary data.

## Development Commands

Backend:

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
npm run build
```

Docker:

```bash
docker compose up --build
```

## Environment

Backend settings are loaded from `.env` through `src/core/config.py`. Required values include:

- `HOST`
- `PORT`
- `MAX_UPLOAD_BYTES`
- `PIPELINE_CONCURRENCY`
- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `MONGODB_COLLECTION_CALLS`
- `MONGODB_TIMEOUT_MS`
- `GEMINI_API_KEY`

Optional observability values:

- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST`

Do not commit real API keys, database credentials, uploaded audio files, generated caches, `.env`, `.venv`, `.next`, `node_modules`, or `__pycache__`.

## Backend Guidelines

- Keep API concerns in `src/api/routes/`, orchestration in `src/services/`, graph behavior in `src/graph/`, and data access in `src/db/`.
- Use Pydantic models for request and response contracts instead of untyped dictionaries at API boundaries.
- Preserve the internal snake_case pipeline state and the CRM-facing PascalCase output fields where already established.
- Keep LangGraph nodes focused and independently testable.
- Avoid blocking I/O in async FastAPI routes and services.
- Respect configured upload size, MongoDB timeout, and pipeline concurrency settings.
- When changing model fields, update all affected layers: Pydantic models, graph state, merge/output mapping, API responses, persistence, frontend consumers, and tests.

## Frontend Guidelines

- Follow `frontend/AGENTS.md` before editing files under `frontend/`.
- This project uses Next.js 16 and React 19. Check the local Next.js docs in `frontend/node_modules/next/dist/docs/` when touching framework-specific APIs.
- Keep UI changes consistent with the dashboard workflow: upload audio, stream progress, inspect results, manage history, and edit AI output.
- Prefer TypeScript types that match backend response models.

## Testing Expectations

- Run focused tests for the area changed.
- Run `pytest` for backend behavior when API routes, services, graph state, models, database code, or configuration changes.
- Run `npm run build` in `frontend/` when changing frontend pages, components, or TypeScript contracts.
- If tests cannot be run because required services or secrets are unavailable, state that clearly in the final response.

## Working Rules

- Keep changes scoped to the user request.
- Do not overwrite unrelated user changes in the working tree.
- Do not introduce broad refactors unless they are required to solve the task.
- Prefer existing project patterns over new abstractions.
- Use clear, concise comments only for non-obvious logic.
- Keep generated artifacts and dependency directories out of edits unless explicitly requested.
