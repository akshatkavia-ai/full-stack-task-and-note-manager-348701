"""Unit tests for in-process task business-service behavior."""

from __future__ import annotations

import pytest

from app.models import TaskCreate, TaskStatus
from app.service import TaskNotFoundError, TaskService


def test_list_tasks_returns_tasks_in_identifier_order() -> None:
    """The service exposes the stable array form expected by the frontend."""
    service = TaskService()
    first = service.create_task(TaskCreate(title="First"))
    second = service.create_task(TaskCreate(title="Second"))

    assert [task.id for task in service.list_tasks()] == [first.id, second.id]


def test_update_retains_identifier_and_creation_timestamp() -> None:
    """Replacing a task preserves immutable identity and creation metadata."""
    service = TaskService()
    created = service.create_task(TaskCreate(title="Original"))

    updated = service.update_task(
        created.id,
        TaskCreate(title="Updated", description="New text", status=TaskStatus.DONE),
    )

    assert updated.id == created.id
    assert updated.created_at == created.created_at
    assert updated.updated_at >= created.updated_at
    assert updated.title == "Updated"
    assert updated.status == TaskStatus.DONE


def test_missing_task_operations_raise_public_domain_error() -> None:
    """Read, update, and delete consistently report missing task identifiers."""
    service = TaskService()

    with pytest.raises(TaskNotFoundError, match="Task 5 was not found"):
        service.get_task(5)
    with pytest.raises(TaskNotFoundError, match="Task 5 was not found"):
        service.update_task(5, TaskCreate(title="Missing"))
    with pytest.raises(TaskNotFoundError, match="Task 5 was not found"):
        service.delete_task(5)
