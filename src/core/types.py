"""Shared data contracts between pipeline stages.

These are the seams that let the Stage I prototype grow into the full product
without rewrites: new sources, detectors and VLM backends only need to produce
or consume these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import numpy as np

Decision = Literal["normal", "suspect", "insufficient"]
Policy = Literal["forbidden", "allowed"]


@dataclass(frozen=True)
class Frame:
    image: np.ndarray  # BGR, HxWx3 (OpenCV convention)
    pts_s: float       # media timestamp in seconds
    index: int


@dataclass(frozen=True)
class Detection:
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels
    score: float
    class_name: str
    track_id: int | None = None
    mask: np.ndarray | None = None  # reserved for segmentation backends


@dataclass(frozen=True)
class ROI:
    id: str
    name: str
    policy: Policy
    polygon: tuple[tuple[float, float], ...]  # normalized [0, 1] coordinates


@dataclass(frozen=True)
class VLMRequest:
    images: tuple  # PIL.Image.Image, RGB; a tuple so multi-frame / video backends fit later
    prompt: str
    max_new_tokens: int = 48


@dataclass(frozen=True)
class VLMResult:
    decision: Decision
    raw_text: str
    elapsed_ms: float
    reason: str = ""
    source: str = ""  # "vlm" | "probe" | "": which judge produced the decision


class EpisodeState(str, Enum):
    CANDIDATE = "candidate"
    OBSERVING = "observing"
    REVIEWING = "reviewing"
    COOLDOWN = "cooldown"


@dataclass
class ReviewRequest:
    """Emitted by the state machine when an episode needs a VLM verdict."""

    episode_id: str
    track_id: int
    roi_id: str
    pts_s: float


@dataclass
class Event:
    kind: Literal["alert", "insufficient", "review", "confirming", "episode_closed", "error", "dropped"]
    episode_id: str
    track_id: int
    roi_id: str
    roi_name: str
    policy: Policy
    pts_s: float
    decision: Decision | None = None
    reason: str = ""
    extra: dict = field(default_factory=dict)
