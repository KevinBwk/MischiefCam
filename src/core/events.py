"""In-process event bus and sinks. MQTT / push notifications become extra subscribers later."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from .branding import Branding
from .types import Event

Subscriber = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._subs: list[Subscriber] = []

    def subscribe(self, fn: Subscriber) -> None:
        self._subs.append(fn)

    def publish(self, event: Event) -> None:
        for fn in self._subs:
            fn(event)


class JsonlSink:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._fh = path.open("a", encoding="utf-8")

    def __call__(self, event: Event) -> None:
        self._fh.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def fmt_time(pts_s: float) -> str:
    m, s = divmod(int(pts_s), 60)
    return f"{m:02d}:{s:02d}"


class MascotNotifier:
    """Prints user-facing notifications in the mascot's voice (local only)."""

    def __init__(self, branding: Branding, printer: Callable[[str], None] = print, notify_insufficient: bool = False):
        self.branding = branding
        self.printer = printer
        # "insufficient" is logged in events.jsonl; pushing it to the owner is opt-in to avoid noise.
        self.notify_insufficient = notify_insufficient

    def __call__(self, event: Event) -> None:
        if event.kind == "alert":
            self.printer(self.branding.message("suspect", roi=event.roi_name, time=fmt_time(event.pts_s),
                                               decision=event.decision or "", reason=event.reason))
        elif event.kind == "insufficient" and self.notify_insufficient:
            self.printer(self.branding.message("insufficient", roi=event.roi_name, time=fmt_time(event.pts_s),
                                               decision=event.decision or "", reason=event.reason))
