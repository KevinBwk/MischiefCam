"""Episode state machine, keyed by (track_id, roi_id) from day one.

Stage I only needs one dog and one zone, but keying by (track, zone) now means
multi-dog / multi-zone later is a configuration change, not a rewrite.

All times are media time (pts seconds), so replays of recorded video behave the
same as live streams.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .types import Decision, EpisodeState, ReviewRequest

Key = tuple[int, str]  # (track_id, roi_id)


@dataclass
class StateConfig:
    dwell_s: float = 2.0
    leave_grace_s: float = 1.5
    reobserve_s: float = 6.0
    cooldown_s: float = 60.0


@dataclass
class Episode:
    episode_id: str
    track_id: int
    roi_id: str
    state: EpisodeState
    first_seen: float
    last_seen: float
    last_review_pts: float = -math.inf
    reviews: int = 0
    verdicts: list[Decision] = field(default_factory=list)


@dataclass
class Transition:
    """Result of feeding one frame (or one verdict) into the state machine."""

    reviews: list[ReviewRequest] = field(default_factory=list)
    closed: list[Episode] = field(default_factory=list)


class EpisodeTracker:
    def __init__(self, cfg: StateConfig):
        self.cfg = cfg
        self.episodes: dict[Key, Episode] = {}
        self.by_id: dict[str, Episode] = {}
        # Zone-level cooldown survives track-id changes (dog leaves and comes back).
        self.roi_cooldown_until: dict[str, float] = {}

    # -- frame updates -----------------------------------------------------
    def update(self, pts: float, present: set[Key]) -> Transition:
        out = Transition()
        for key in present:
            ep = self.episodes.get(key)
            if ep is None:
                ep = self._open(key, pts)
            ep.last_seen = pts
            self._advance(ep, pts, out)

        for key, ep in list(self.episodes.items()):
            if key not in present and pts - ep.last_seen > self.cfg.leave_grace_s:
                if ep.state is not EpisodeState.REVIEWING:  # keep it until the verdict lands
                    out.closed.append(self._close(key))
        return out

    def _open(self, key: Key, pts: float) -> Episode:
        track_id, roi_id = key
        ep = Episode(
            episode_id=f"{roi_id}-t{track_id}-{int(pts * 1000)}",
            track_id=track_id,
            roi_id=roi_id,
            state=EpisodeState.CANDIDATE,
            first_seen=pts,
            last_seen=pts,
        )
        self.episodes[key] = ep
        self.by_id[ep.episode_id] = ep
        return ep

    def _close(self, key: Key) -> Episode:
        ep = self.episodes.pop(key)
        self.by_id.pop(ep.episode_id, None)
        return ep

    def _advance(self, ep: Episode, pts: float, out: Transition) -> None:
        if ep.state is EpisodeState.CANDIDATE and pts - ep.first_seen >= self.cfg.dwell_s:
            ep.state = EpisodeState.OBSERVING
        if ep.state is EpisodeState.COOLDOWN and pts >= self.roi_cooldown_until.get(ep.roi_id, -math.inf):
            ep.state = EpisodeState.OBSERVING
            ep.last_review_pts = -math.inf
        if ep.state is EpisodeState.OBSERVING:
            if pts < self.roi_cooldown_until.get(ep.roi_id, -math.inf):
                ep.state = EpisodeState.COOLDOWN
            elif pts - ep.last_review_pts >= self.cfg.reobserve_s:
                ep.state = EpisodeState.REVIEWING
                ep.reviews += 1
                out.reviews.append(ReviewRequest(ep.episode_id, ep.track_id, ep.roi_id, pts))

    # -- verdicts ----------------------------------------------------------
    def on_verdict(self, episode_id: str, roi_id: str, decision: Decision | None, pts: float) -> bool:
        """Apply a VLM verdict (None = backend error/dropped). Returns True if an alert should fire."""
        ep = self.by_id.get(episode_id)
        if decision == "suspect":
            self.roi_cooldown_until[roi_id] = pts + self.cfg.cooldown_s
        if ep is None:
            return decision == "suspect"
        if decision is not None:
            ep.verdicts.append(decision)
        if decision == "suspect":
            ep.state = EpisodeState.COOLDOWN
            return True
        # normal / insufficient / error: keep watching, ask again after reobserve_s
        ep.state = EpisodeState.OBSERVING
        ep.last_review_pts = pts
        return False
