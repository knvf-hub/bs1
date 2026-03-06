from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from app.domain.models import WorkflowResult
from app.infrastructure.storage import update_execution

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

    async def _worker_loop(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                fn = self._registry.get(job.workflow)
                if not fn:
                    res = WorkflowResult(status="error", output={"error": f"unknown workflow: {job.workflow}"})
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