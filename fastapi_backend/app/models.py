"""Pydantic models for task API requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(str, Enum):
    """Allowed workflow states for task records."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Validated fields accepted to create or replace a task."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Required non-blank title, up to 120 characters.",
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Optional description, up to 500 characters.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Workflow status of the task.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        """Normalize titles and reject values containing only whitespace."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("title must not be blank")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        """Trim optional descriptions for a consistent API contract."""
        return value.strip()


class Task(TaskCreate):
    """Persisted task representation returned by the public API."""

    id: int = Field(..., description="Positive deterministic task identifier.")
    created_at: datetime = Field(..., description="UTC task creation timestamp.")
    updated_at: datetime = Field(..., description="UTC task update timestamp.")


class TaskListResponse(BaseModel):
    """Database service's wrapped task-list response."""

    items: list[Task] = Field(..., description="Tasks returned by the storage service.")
    count: int = Field(..., description="Number of returned tasks.")


class DeleteResponse(BaseModel):
    """Confirmation returned after a successful task deletion."""

    message: str = Field(..., description="Human-readable deletion confirmation.")
    id: int = Field(..., description="Identifier of the deleted task.")


class HealthResponse(BaseModel):
    """Operational health response for backend readiness checks."""

    status: str = Field(..., description="Backend health status.")
    task_count: int = Field(..., description="Number of tasks in storage.")
