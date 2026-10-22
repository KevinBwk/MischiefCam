"""Single background VLM worker with a bounded queue.

Capture and detection never wait for the VLM. When the queue is full the oldest
pending request is dropped; requests that waited longer than max_age_s are
dropped too. Every drop/error is reported, never silently turned into "normal".

Two job kinds share the queue: "judge" (a verdict for the state machine) and "explain"
(a visual assessment for an alert that already fired, sent straight to the VLM). Explanations
are best-effort: they never evict a judge job, and a full queue drops an explanation first.
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
    kind: str = "judge"  # "judge" | "explain"
    owner: object = None  # who submitted it (a Pipeline); a worker reused across clips can return a late job


@dataclass
class Outcome:
    job: Job
    result: VLMResult | None = None
    error: str | None = None  # "dropped:queue_full", "dropped:stale", or an exception message


class VLMWorker:
    def __init__(self, backend: VLMBackend, queue_size: int = 2, max_age_s: float = 10.0,
                 explainer: VLMBackend | None = None):
        self.backend = backend
        self.explainer = explainer  # the VLM itself (not the probe-first "either" judge); None = no explanations
        self.max_age_s = max_age_s
        self._pending: deque[Job] = deque()
        self._queue_size = queue_size
        self._cv = threading.Condition()
        self._busy = False
        self._stop = False
        self.outcomes: queue.Queue[Outcome] = queue.Queue()
        self._thread = threading.Thread(target=self._run, name="vlm-worker", daemon=True)
        self._thread.start()

    def submit(self, episode_id: str, pts_s: float, request: VLMRequest, kind: str = "judge",
               owner: object = None) -> None:
        job = Job(episode_id, pts_s, request, time.monotonic(), kind, owner)
        with self._cv:
            if any(j.episode_id == episode_id and j.kind == kind for j in self._pending):
                return  # same episode already waiting: merge
            if len(self._pending) >= self._queue_size:
                explains = [j for j in self._pending if j.kind == "explain"]
                if explains:
                    victim = explains[0]
                elif kind == "explain":
                    self.outcomes.put(Outcome(job, error="dropped:queue_full"))
                    return
                else:
                    victim = self._pending[0]
                self._pending.remove(victim)
                self.outcomes.put(Outcome(victim, error="dropped:queue_full"))
            self._pending.append(job)
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
                job = next((j for j in self._pending if j.kind == "judge"), self._pending[0])  # judges run first
                self._pending.remove(job)
                self._busy = True
            try:
                if time.monotonic() - job.submitted > self.max_age_s:
                    self.outcomes.put(Outcome(job, error="dropped:stale"))
                    continue
                backend = self.explainer if job.kind == "explain" else self.backend
                if backend is None:
                    raise RuntimeError("no explainer backend")
                self.outcomes.put(Outcome(job, result=backend.infer(job.request)))
            except Exception as exc:  # backend failure must surface as an error, not a verdict
                self.outcomes.put(Outcome(job, error=f"{type(exc).__name__}: {exc}"))
            finally:
                with self._cv:
                    self._busy = False
