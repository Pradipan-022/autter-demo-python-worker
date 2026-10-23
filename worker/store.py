import threading
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    org_id: str
    kind: str
    payload: dict
    status: str = "queued"
    attempts: int = 0
    error: str | None = None
    visible_at: float = 0
    idempotency_key: str | None = None


jobs: list[Job] = []
_jobs_lock = threading.Lock()


def submit_job(org_id, kind, payload, idempotency_key=None):
    with _jobs_lock:
        if idempotency_key:
            for job in jobs:
                if job.org_id != org_id or job.idempotency_key != idempotency_key:
                    continue
                if job.kind != kind or job.payload != payload:
                    raise ValueError(
                        "idempotency key already used with different parameters"
                    )
                return job

        job = Job(
            id=str(uuid.uuid4()),
            org_id=org_id,
            kind=kind,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        jobs.append(job)
        return job


def next_job(org_id):
    with _jobs_lock:
        now = time.time()
        for job in jobs:
            if job.status in ("queued", "processing") and job.visible_at <= now:
                job.status = "processing"
                job.visible_at = now + 1
                return job
        return None
