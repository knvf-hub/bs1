from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.application.workflows import (
    list_workflows,
    run_workflow_async,
    list_execution_history,
    read_execution,
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


class RunWorkflowRequest(BaseModel):
    name: str
    payload: dict = {}


@router.get("")
def get_workflows():
    return {"items": list_workflows()}


@router.post("/run")
async def post_run_workflow(req: RunWorkflowRequest, request: Request):
    executor = request.app.state.executor
    record = await run_workflow_async(name=req.name, payload=req.payload, executor=executor)
    return {"ok": True, "execution": record.model_dump(mode="json")}


@router.get("/executions")
def get_executions():
    items = list_execution_history()
    return {"items": [x.model_dump(mode="json") for x in items]}


@router.get("/executions/{exec_id}")
def get_execution(exec_id: str):
    rec = read_execution(exec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="execution not found")
    return rec.model_dump(mode="json")