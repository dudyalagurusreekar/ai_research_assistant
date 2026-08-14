"""IntegrationScheduler for background cron and interval job scheduling."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
import time
import asyncio

from infrastructure.logging.logger import StructuredLogger


@dataclass
class ScheduledJob:
    """Represents a scheduled integration job."""
    job_id: str
    service_name: str
    action: str
    interval_seconds: float = 60.0
    priority: int = 1  # 1 = Normal, 2 = High, 3 = Urgent
    params: Dict[str, Any] = field(default_factory=dict)
    last_run_timestamp: float = 0.0
    next_run_timestamp: float = field(default_factory=time.time)
    is_active: bool = True
    execution_count: int = 0


@dataclass
class JobExecutionRecord:
    """Historical record of job execution."""
    job_id: str
    status: str  # 'success', 'failed'
    execution_time_ms: float
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class IntegrationScheduler:
    """Background scheduler managing job queues, priorities, and concurrent execution."""

    def __init__(self) -> None:
        self._logger = StructuredLogger("IntegrationScheduler")
        self._jobs: Dict[str, ScheduledJob] = {}
        self._execution_history: List[JobExecutionRecord] = []
        self._is_running = False
        self._max_concurrent_jobs = 5

    def add_job(
        self,
        job_id: str,
        service_name: str,
        action: str,
        interval_seconds: float = 60.0,
        priority: int = 1,
        params: Optional[Dict[str, Any]] = None,
    ) -> ScheduledJob:
        """Register scheduled job."""
        job = ScheduledJob(
            job_id=job_id,
            service_name=service_name,
            action=action,
            interval_seconds=interval_seconds,
            priority=priority,
            params=params or {},
            next_run_timestamp=time.time() + interval_seconds,
        )
        self._jobs[job_id] = job
        self._logger.info(f"Added scheduled job '{job_id}' for service '{service_name}' (interval={interval_seconds}s)")
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove job by ID."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    def list_jobs(self) -> List[ScheduledJob]:
        """List registered jobs sorted by priority and next run time."""
        jobs = list(self._jobs.values())
        return sorted(jobs, key=lambda j: (-j.priority, j.next_run_timestamp))

    async def run_pending_jobs(self, executor_func: Callable[[ScheduledJob], Any]) -> List[JobExecutionRecord]:
        """Run pending jobs whose next_run_timestamp has passed."""
        now = time.time()
        pending = [j for j in self.list_jobs() if j.is_active and now >= j.next_run_timestamp]
        records: List[JobExecutionRecord] = []

        for job in pending[: self._max_concurrent_jobs]:
            start = time.time()
            try:
                if asyncio.iscoroutinefunction(executor_func):
                    await executor_func(job)
                else:
                    executor_func(job)
                elapsed = (time.time() - start) * 1000.0
                rec = JobExecutionRecord(job_id=job.job_id, status="success", execution_time_ms=elapsed)
                job.last_run_timestamp = start
                job.next_run_timestamp = start + job.interval_seconds
                job.execution_count += 1
            except Exception as e:
                elapsed = (time.time() - start) * 1000.0
                rec = JobExecutionRecord(job_id=job.job_id, status="failed", execution_time_ms=elapsed, error_message=str(e))
                self._logger.error(f"Error executing scheduled job '{job.job_id}': {e}")

            records.append(rec)
            self._execution_history.append(rec)

        return records

    def get_execution_history(self, limit: int = 50) -> List[JobExecutionRecord]:
        """Return history records."""
        return self._execution_history[-limit:]
