"""Clip annotations: time segments with a label, shared by the labeling tool, training and batch runs.

File format (JSON):
{
  "version": 1,
  "clips": {
    "<path relative to the video folder>": {
      "segments": [{"start_s": 1.0, "end_s": 6.5, "label": "positive", "behavior": "chewing_furniture",
                    "target": "sofa armrest", "visibility": "clear"}],
      "simulated": true, "source_note": "...", "damage_confirmed": "unknown", "split": "", "updated": "..."
    }
  }
}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

LABELS = ("positive", "negative", "uncertain")
VISIBILITY = ("clear", "partial", "unobservable")
BEHAVIORS = (
    "chewing_furniture", "chewing_toy", "sniffing", "licking_object", "licking_self", "resting", "sitting",
    "walking", "carrying", "playing", "scratching_self", "rolling", "person_present", "unobservable", "other",
)


def empty() -> dict:
    return {"version": 1, "clips": {}}


def load(path: Path | str) -> dict:
    p = Path(path)
    if not p.exists():
        return empty()
    data = json.loads(p.read_text(encoding="utf-8"))
    if "clips" not in data:  # legacy {filename: label} map
        return {"version": 1, "clips": {k: {"segments": [{"start_s": 0.0, "end_s": -1.0, "label": v}]}
                                        for k, v in data.items()}}
    return data


def validate_clip(entry: dict) -> dict:
    segs = []
    for s in entry.get("segments", []):
        label = s.get("label")
        if label not in LABELS:
            raise ValueError(f"segment label must be one of {LABELS}, got {label!r}")
        start, end = float(s.get("start_s", 0.0)), float(s.get("end_s", -1.0))
        if end >= 0 and end <= start:
            raise ValueError(f"segment end ({end}) must be after start ({start})")
        vis = s.get("visibility", "clear")
        if vis not in VISIBILITY:
            raise ValueError(f"visibility must be one of {VISIBILITY}")
        behavior = s.get("behavior", "other") or "other"
        segs.append({"start_s": round(start, 3), "end_s": round(end, 3), "label": label, "behavior": behavior,
                     "target": str(s.get("target", "")), "visibility": vis})
    segs.sort(key=lambda s: s["start_s"])
    return {
        "segments": segs,
        "simulated": bool(entry.get("simulated", False)),
        "source_note": str(entry.get("source_note", "")),
        "damage_confirmed": entry.get("damage_confirmed", "unknown"),
        "split": str(entry.get("split", "")),
        "ai_assisted": bool(entry.get("ai_assisted", False)),  # segments started from an AI pre-label
        "updated": datetime.now().isoformat(timespec="seconds"),
    }


def save(path: Path | str, data: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(p)


def clip_label(entry: dict) -> str | None:
    """Clip-level label: positive if any positive segment, else negative, else uncertain; None if unlabeled."""
    labels = {s["label"] for s in entry.get("segments", [])}
    for lab in ("positive", "negative", "uncertain"):
        if lab in labels:
            return lab
    return None


def label_at(entry: dict, t: float, duration: float) -> str | None:
    """Label covering time t (end_s < 0 means 'until the end of the clip').

    Overlapping segments (several dogs: one chews the sofa, another a toy) resolve positive > uncertain >
    negative: any dog chewing the protected object makes that moment positive.
    """
    covering = set()
    for s in entry.get("segments", []):
        end = duration if s["end_s"] < 0 else s["end_s"]
        if s["start_s"] <= t <= end:
            covering.add(s["label"])
    for lab in ("positive", "uncertain", "negative"):
        if lab in covering:
            return lab
    return None
