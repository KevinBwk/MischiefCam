"""Raw timing records for latency reports (P50 / P95 across many clips).

Every run writes timings.json next to its events: all raw milliseconds, not summaries, so
scripts/latency_report.py can pool clips. Warm-up samples are flagged and excluded by the report:
the first frames of every run for the detector (measured 2026-10-24: ~100 ms vs ~20 ms after, the
tracker restarts per clip), but only the first call per process for a judge (later clips' first
calls were as fast as the rest; a per-clip rule would drop every one-per-clip explanation).
"""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path

WARMUP_DETECTOR_FRAMES = 5  # first frames of a run
WARMUP_JUDGE_CALLS = 1      # first call of each judge in this process
_judges_seen: set[str] = set()


def write_timings(stats, path: Path, mode: str) -> None:
    """mode: "batch" (as fast as possible) or "realtime" (paced playback / camera)."""
    judge_warmup = {}
    for name, values in stats.judge_ms.items():
        judge_warmup[name] = 0 if name in _judges_seen else min(WARMUP_JUDGE_CALLS, len(values))
        if values:
            _judges_seen.add(name)
    data = {
        "mode": mode,
        "warmup": {"detector_frames": WARMUP_DETECTOR_FRAMES, "judge_calls": judge_warmup},
        "detector_ms": [round(v, 2) for v in stats.detector_ms],
        "judge_ms": stats.judge_ms,
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def machine_info() -> dict:
    """Model, chip and RAM of this machine (macOS via sysctl; best effort elsewhere)."""
    info = {"platform": platform.platform(), "machine": platform.machine()}

    def sysctl(key: str) -> str | None:
        try:
            return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, timeout=5).stdout.strip() or None
        except (OSError, subprocess.SubprocessError):
            return None
    model, chip, mem = sysctl("hw.model"), sysctl("machdep.cpu.brand_string"), sysctl("hw.memsize")
    if model:
        info["model"] = model
    if chip:
        info["chip"] = chip
    if mem and mem.isdigit():
        info["ram_gb"] = round(int(mem) / 2**30)
    return info
