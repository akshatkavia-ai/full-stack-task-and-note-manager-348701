"""Integration-style tests for public FastAPI task routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.service import TaskService


@pytest.fixture()
def client() -> TestClient:
    """Return a test client with isolated in-process task state."""
    app.state.task_service = TaskService()
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_empty_task_list(client: TestClient) -> None:
    """Health and list routes expose expected initial states."""
    assert client.get("/health").json() == {"status": "ok", "task_count": 0}
    assert client.get("/tasks").json() == []


def test_complete_task_crud_flow(client: TestClient) -> None:
    """Routes create, read, update, list, and delete a task successfully."""
    created = client.post("/tasks", json={"title": "Draft API tests"}).json()
    assert created["id"] == 1
    assert created["status"] == "todo"

    assert client.get("/tasks/1").json()["title"] == "Draft API tests"
    updated = client.put(
        "/tasks/1",
        json={"title": "Complete API tests", "description": "Include errors.", "status": "done"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    assert len(client.get("/tasks").json()) == 1
    assert client.delete("/tasks/1").json() == {"message": "Task deleted.", "id": 1}
    assert client.get("/tasks").json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "   "},
        {"title": "x" * 121},
        {"title": "Valid", "status": "unknown"},
        {"title": "Valid", "unexpected": True},
    ],
)
def test_create_rejects_invalid_payloads(client: TestClient, payload: dict[str, object]) -> None:
    """Server-side validation rejects malformed and out-of-contract task payloads."""
    response = client.post("/tasks", json=payload)
    assert response.status_code == 422


def test_unknown_task_returns_clear_404(client: TestClient) -> None:
    """Read, update, and delete routes return a consistent missing-task response."""
    assert client.get("/tasks/999").status_code == 404
    assert client.put("/tasks/999", json={"title": "Missing"}).status_code == 404
    assert client.delete("/tasks/999").status_code == 404
