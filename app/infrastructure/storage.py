from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from app.domain.models import ExecutionRecord, WorkflowResult


def _default_data_path() -> Path:
    return Path(".data") / "executions.json"


def _ensure_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def save_execution(
    *,
    exec_id: str,
    workflow: str,
    payload: dict[str, Any],
    state: str,
    result: WorkflowResult | None = None,
    path: Path | None = None,
) -> ExecutionRecord:
    p = path or _default_data_path()
    _ensure_file(p)

    record = ExecutionRecord(
        id=exec_id,
        workflow=workflow,
        payload=payload,
        state=state,
        result=result,
        created_at=datetime.now(timezone.utc),
        finished_at=None,
    )

    items = json.loads(p.read_text(encoding="utf-8"))
    items.insert(0, record.model_dump(mode="json"))
    p.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def update_execution(
    exec_id: str,
    *,
    state: str,
    result: WorkflowResult | None = None,
    path: Path | None = None,
) -> ExecutionRecord | None:
    p = path or _default_data_path()
    _ensure_file(p)

    items = json.loads(p.read_text(encoding="utf-8"))
    for i, item in enumerate(items):
        if item.get("id") == exec_id:
            item["state"] = state
            item["result"] = result.model_dump(mode="json") if result else item.get("result")
            item["finished_at"] = datetime.now(timezone.utc).isoformat()
            items[i] = item
            p.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
            return ExecutionRecord.model_validate(item)

    return None


def list_executions(path: Path | None = None) -> list[ExecutionRecord]:
    p = path or _default_data_path()
    _ensure_file(p)
    items = json.loads(p.read_text(encoding="utf-8"))
    return [ExecutionRecord.model_validate(x) for x in items]


def get_execution(exec_id: str, path: Path | None = None) -> ExecutionRecord | None:
    for rec in list_executions(path=path):
        if rec.id == exec_id:
            return rec
    return None