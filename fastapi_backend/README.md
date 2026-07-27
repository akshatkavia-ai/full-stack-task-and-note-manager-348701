# Task Manager FastAPI Backend

The Task Manager backend exposes the public task REST API on port `3001`. It validates browser requests, enables CORS for the React frontend, and keeps task data in thread-safe in-process memory.

## Prerequisites

- Python 3.11 or newer
- No database service or database container is required

## Install and run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3001
```

Interactive OpenAPI documentation is available at `http://localhost:3001/docs`.

## Full-stack integration

Run the two application services:

1. Start this backend on port `3001`.
2. Start `react_frontend` on port `3000`.

The React client calls this API through `VITE_API_BASE_URL` (default `http://localhost:3001`). The backend stores tasks in memory, so all data is cleared whenever the backend process restarts.

Use this health check before a manual CRUD smoke test:

```bash
curl http://localhost:3001/health
```

Create, list, replace, and delete a task through the frontend. A blank or malformed payload returns `422`, and an unknown task returns `404`.

## Configuration

The application uses environment variables, with safe local defaults:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated browser origins allowed to call this API. |

Request deployment-specific values through the environment rather than hard-coding them in source files.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Verify backend readiness and report the in-memory task count. |
| `GET` | `/tasks` | List all tasks as a JSON array. |
| `GET` | `/tasks/{id}` | Get a task. |
| `POST` | `/tasks` | Create a task. |
| `PUT` | `/tasks/{id}` | Replace a task. |
| `DELETE` | `/tasks/{id}` | Delete a task. |

Task create and update bodies accept:

```json
{
  "title": "Prepare release",
  "description": "Review final API coverage.",
  "status": "todo"
}
```

Titles are required, trimmed, and limited to 120 characters. Descriptions are optional and limited to 500 characters. Valid statuses are `todo`, `in_progress`, and `done`.

## Test and coverage

Run all backend tests and create the SonarQube-compatible `coverage.xml` report with:

```bash
pytest
```

The command enforces at least 85% branch coverage. SonarQube reads `coverage.xml` through `sonar-project.properties`.

The React project independently runs `npm test`, writes `coverage/lcov.info`, and provides its own SonarQube properties file. Run the commands in each project directory so their artifacts remain in the paths referenced by their respective Sonar configurations.
