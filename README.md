# Task Manager Full-Stack Application

This project is a two-service task manager application:

- `react_frontend` runs the browser UI on port `3000`.
- `fastapi_backend` provides the task REST API on port `3001`.

The FastAPI backend stores tasks in process memory. No database, database configuration, or separate in-memory-database service is required. Tasks are intentionally cleared when the backend process restarts.

See [`fastapi_backend/README.md`](fastapi_backend/README.md) for backend setup, API documentation, and test instructions.
