"""Business-service layer and in-process storage for task operations."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from app.models import DeleteResponse, Task, TaskCreate


class TaskNotFoundError(Exception):
    """Raised when an operation targets a task that does not exist."""


class TaskService:
    """Provide thread-safe, in-process CRUD operations for task records.

    Storage is intentionally ephemeral: tasks remain available for the lifetime of
    the FastAPI process and are reset when that process restarts.
    """

    # PUBLIC_INTERFACE
    def __init__(self) -> None:
        """Initialize an empty task collection and its synchronization lock."""
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        self._lock = RLock()

    # PUBLIC_INTERFACE
    def health(self) -> int:
        """Return the number of tasks currently held in process memory."""
        with self._lock:
            return len(self._tasks)

    # PUBLIC_INTERFACE
    def list_tasks(self) -> list[Task]:
        """Return all tasks in stable ascending identifier order."""
        with self._lock:
            return [self._tasks[task_id] for task_id in sorted(self._tasks)]

    # PUBLIC_INTERFACE
    def get_task(self, task_id: int) -> Task:
        """Return one task or raise a public missing-task error."""
        with self._lock:
            try:
                return self._tasks[task_id]
            except KeyError as exc:
                raise TaskNotFoundError(f"Task {task_id} was not found.") from exc

    # PUBLIC_INTERFACE
    def create_task(self, payload: TaskCreate) -> Task:
        """Create and return a task from validated request fields."""
        with self._lock:
            timestamp = datetime.now(timezone.utc)
            task = Task(
                id=self._next_id,
                created_at=timestamp,
                updated_at=timestamp,
                **payload.model_dump(),
            )
            self._tasks[task.id] = task
            self._next_id += 1
            return task

    # PUBLIC_INTERFACE
    def update_task(self, task_id: int, payload: TaskCreate) -> Task:
        """Replace editable fields on an existing task while retaining its creation time."""
        with self._lock:
            try:
                existing = self._tasks[task_id]
            except KeyError as exc:
                raise TaskNotFoundError(f"Task {task_id} was not found.") from exc

            task = Task(
                id=existing.id,
                created_at=existing.created_at,
                updated_at=datetime.now(timezone.utc),
                **payload.model_dump(),
            )
            self._tasks[task_id] = task
            return task

    # PUBLIC_INTERFACE
    def delete_task(self, task_id: int) -> DeleteResponse:
        """Delete an existing task and return the established API confirmation."""
        with self._lock:
            if task_id not in self._tasks:
                raise TaskNotFoundError(f"Task {task_id} was not found.")

            del self._tasks[task_id]
            return DeleteResponse(message="Task deleted.", id=task_id)
