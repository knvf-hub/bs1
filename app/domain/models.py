from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class WorkflowResult(BaseModel):
    status: str  # "success" | "error"
    output: dict


class ExecutionRecord(BaseModel):
    id: str
    workflow: str
    payload: dict

    # status แยกให้ชัด
    state: str  # "running" | "success" | "error"
    result: WorkflowResult | None = None

    created_at: datetime
    finished_at: datetime | None = None