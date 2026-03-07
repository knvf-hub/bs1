from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class WorkflowResult(BaseModel):
    status: str  # "success" | "error" | "cancelled"
    output: dict


class ExecutionRecord(BaseModel):
    id: str
    workflow: str
    payload: dict

    state: str     # "running" | "success" | "error" | "cancelled"
    result: WorkflowResult | None = None

    created_at: datetime
    finished_at: datetime | None = None