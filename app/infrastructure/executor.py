from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.domain.models import WorkflowResult
from app.infrastructure.storage import update_execution, get_execution, cancel_execution

logger = logging.getLogger(__name__)

WorkflowFunc = Callable[[dict[str, Any]], Awaitable[WorkflowResult]]


@dataclass
class Job:
    exec_id: str
    workflow: str
    payload: dict[str, Any]


class InMemoryExecutor:
    """
    MVP executor: queue in memory + background worker loop.

    - เหมาะกับ dev/MVP
    - restart แล้ว queue หาย (โอเคสำหรับตอนนี้)
    """

    def __init__(self, registry: dict[str, WorkflowFunc]) -> None:
        self._registry = registry
        self._queue: asyncio.Queue[Job] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._cancelled_ids: set[str] = set()

    def start(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Executor started")

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Executor stopped")

    async def enqueue(self, job: Job) -> None:
        await self._queue.put(job)
        logger.info("Enqueued job %s (%s)", job.exec_id, job.workflow)

    def cancel(self, exec_id: str) -> bool:
        rec = get_execution(exec_id)
        if rec is None:
            return False

        if rec.state != "running":
            return False

        self._cancelled_ids.add(exec_id)
        cancel_execution(exec_id)
        logger.info("Cancelled job %s", exec_id)
        return True

    async def _worker_loop(self) -> None:
        while True:
            job = await self._queue.get()

            try:
                if job.exec_id in self._cancelled_ids:
                    self._cancelled_ids.discard(job.exec_id)
                    logger.info("Skipped cancelled job %s", job.exec_id)
                    continue

                rec = get_execution(job.exec_id)
                if rec and rec.state == "cancelled":
                    logger.info("Job %s already cancelled before execution", job.exec_id)
                    continue

                fn = self._registry.get(job.workflow)
                if not fn:
                    res = WorkflowResult(
                        status="error",
                        output={"error": f"unknown workflow: {job.workflow}"},
                    )
                    update_execution(job.exec_id, state="error", result=res)
                    continue

                res = await fn(job.payload)
                new_state = "success" if res.status == "success" else "error"
                update_execution(job.exec_id, state=new_state, result=res)

            except Exception as e:
                logger.exception("Job failed %s: %s", job.exec_id, e)
                res = WorkflowResult(status="error", output={"error": str(e)})
                update_execution(job.exec_id, state="error", result=res)

            finally:
                self._queue.task_done()