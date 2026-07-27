"""FastAPI entrypoint for the task management backend."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import Settings
from app.models import (
    DeleteResponse,
    HealthResponse,
    Task,
    TaskCreate,
)
from app.service import TaskNotFoundError, TaskService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("task_backend")

settings = Settings()
app = FastAPI(
    title="Task Manager Backend API",
    description=(
        "Public REST API for task management. The backend validates requests and "
        "stores tasks in process memory for the lifetime of the application."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "Operations", "description": "Health and service availability checks."},
        {"name": "Tasks", "description": "Create, read, update, and delete tasks."},
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)
app.state.task_service = TaskService()


@app.middleware("http")
# PUBLIC_INTERFACE
async def log_requests(request: Request, call_next: Callable) -> Response:
    """Attach a request ID and log completed HTTP requests without exposing payloads."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request failure request_id=%s method=%s path=%s",
            request_id,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected server error occurred.",
                "request_id": request_id,
            },
        )

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(TaskNotFoundError)
# PUBLIC_INTERFACE
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    """Translate absent in-memory records into a consistent public 404 response."""
    logger.warning("Task not found request_id=%s detail=%s", request.headers.get("X-Request-ID"), exc)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


# PUBLIC_INTERFACE
def get_task_service(request: Request) -> TaskService:
    """Return the request application's configured in-process task service."""
    return request.app.state.task_service


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Operations"],
    summary="Check backend health",
    description="Returns backend readiness and the current in-process task count.",
)
# PUBLIC_INTERFACE
def health(request: Request) -> HealthResponse:
    """Report backend health and the number of tasks held in process memory."""
    task_count = get_task_service(request).health()
    return HealthResponse(status="ok", task_count=task_count)


@app.get(
    "/tasks",
    response_model=list[Task],
    tags=["Tasks"],
    summary="List tasks",
    description="Returns all tasks ordered by their deterministic numeric identifier.",
)
# PUBLIC_INTERFACE
def list_tasks(request: Request) -> list[Task]:
    """List all tasks available through the in-process task store."""
    return get_task_service(request).list_tasks()


@app.get(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Get a task",
    description="Returns one task identified by a positive numeric task ID.",
)
# PUBLIC_INTERFACE
def get_task(task_id: int, request: Request) -> Task:
    """Return the task for ``task_id`` or a documented 404 response."""
    return get_task_service(request).get_task(task_id)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    summary="Create a task",
    description="Validates and creates a task in the backend's in-process store.",
)
# PUBLIC_INTERFACE
def create_task(payload: TaskCreate, request: Request) -> Task:
    """Create a task from validated request fields and return its stored form."""
    return get_task_service(request).create_task(payload)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    tags=["Tasks"],
    summary="Replace a task",
    description="Validates and fully replaces the editable fields of an existing task.",
)
# PUBLIC_INTERFACE
def update_task(task_id: int, payload: TaskCreate, request: Request) -> Task:
    """Replace the task identified by ``task_id`` with validated request fields."""
    return get_task_service(request).update_task(task_id, payload)


@app.delete(
    "/tasks/{task_id}",
    response_model=DeleteResponse,
    tags=["Tasks"],
    summary="Delete a task",
    description="Deletes an existing task and returns a predictable confirmation object.",
)
# PUBLIC_INTERFACE
def delete_task(task_id: int, request: Request) -> DeleteResponse:
    """Delete the identified task or return a documented 404 response."""
    return get_task_service(request).delete_task(task_id)
