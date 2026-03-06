from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.domain.models import ExecutionRecord
from app.infrastructure.storage import save_execution, list_executions, get_execution
from app.infrastructure.executor import Job, InMemoryExecutor


def list_workflows() -> list[dict[str, Any]]:
    return [{"name": k, "description": "workflow"} for k in ["hello", "ping"]]


async def run_workflow_async(
    *,
    name: str,
    payload: dict[str, Any],
    executor: InMemoryExecutor,
) -> ExecutionRecord:
    exec_id = uuid4().hex

    record = save_execution(
        exec_id=exec_id,
        workflow=name,
        payload=payload,
        state="running",
        result=None,
    )

    await executor.enqueue(Job(exec_id=exec_id, workflow=name, payload=payload))
    return record


def list_execution_history() -> list[ExecutionRecord]:
    return list_executions()


def read_execution(exec_id: str) -> ExecutionRecord | None:
    return get_execution(exec_id)