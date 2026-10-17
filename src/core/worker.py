"""Single background VLM worker with a bounded queue.

Capture and detection never wait for the VLM. When the queue is full the oldest
pending request is dropped; requests that waited longer than max_age_s are
dropped too. Every drop/error is reported, never silently turned into "normal".
"""

from __future__ import annotations

import queue
import threading
import time
from collections import deque
from dataclasses import dataclass

from .types import VLMRequest, VLMResult
from .vlm import VLMBackend


@dataclass
class Job:
    episode_id: str
    pts_s: float
    request: VLMRequest
    submitted: float  # wall-clock (time.monotonic)


@dataclass
class Outcome:
    job: Job
    result: VLMResult | None = None
    error: str | None = None  # "dropped:queue_full", "dropped:stale", or an exception message


class VLMWorker:
    def __init__(self, backend: VLMBackend, queue_size: int = 2, max_age_s: float = 10.0):
        self.backend = backend
        self.max_age_s = max_age_s
        self._pending: deque[Job] = deque()
        self._queue_size = queue_size
        self._cv = threading.Condition()
        self._busy = False
        self._stop = False
        self.outcomes: queue.Queue[Outcome] = queue.Queue()
        self._thread = threading.Thread(target=self._run, name="vlm-worker", daemon=True)
        self._thread.start()

    def submit(self, episode_id: str, pts_s: float, request: VLMRequest) -> None:
        with self._cv:
            if any(j.episode_id == episode_id for j in self._pending):
                return  # same episode already waiting: merge
            if len(self._pending) >= self._queue_size:
                self.outcomes.put(Outcome(self._pending.popleft(), error="dropped:queue_full"))
            self._pending.append(Job(episode_id, pts_s, request, time.monotonic()))
            self._cv.notify()

    def idle(self) -> bool:
        with self._cv:
            return not self._pending and not self._busy

    def wait_idle(self, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.idle():
                return True
            time.sleep(0.05)
        return self.idle()

    def close(self) -> None:
        with self._cv:
            self._stop = True
            self._cv.notify()
        self._thread.join(timeout=5)
        self.backend.close()

    def _run(self) -> None:
        while True:
            with self._cv:
                while not self._pending and not self._stop:
                    self._cv.wait()
                if self._stop:
                    return
                job = self._pending.popleft()
                self._busy = True
            try:
                if time.monotonic() - job.submitted > self.max_age_s:
                    self.outcomes.put(Outcome(job, error="dropped:stale"))
                    continue
                self.outcomes.put(Outcome(job, result=self.backend.infer(job.request)))
            except Exception as exc:  # backend failure must surface as an error, not a verdict
                self.outcomes.put(Outcome(job, error=f"{type(exc).__name__}: {exc}"))
            finally:
                with self._cv:
                    self._busy = False
