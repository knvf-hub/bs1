from __future__ import annotations

import asyncio
from typing import Any

from app.domain.models import WorkflowResult


async def wf_hello(payload: dict[str, Any]) -> WorkflowResult:
    await asyncio.sleep(0.5)  # จำลองงาน
    return WorkflowResult(status="success", output={"message": "hello from bs1", "payload": payload})


async def wf_ping(payload: dict[str, Any]) -> WorkflowResult:
    await asyncio.sleep(0.1)
    return WorkflowResult(status="success", output={"pong": True})


WORKFLOW_REGISTRY = {
    "hello": wf_hello,
    "ping": wf_ping,
}