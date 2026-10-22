from core.state import EpisodeTracker, StateConfig
from core.types import EpisodeState

CFG = StateConfig(dwell_s=2.0, leave_grace_s=1.0, reobserve_s=5.0, reobserve_insufficient_s=1.5, cooldown_s=30.0)
KEY = (1, "sofa")


def feed(tracker, start, end, step=0.5, present=True):
    reviews, closed = [], []
    t = start
    while t <= end + 1e-9:
        tr = tracker.update(t, {KEY} if present else set())
        reviews += tr.reviews
        closed += tr.closed
        t += step
    return reviews, closed


def test_no_review_before_dwell():
    tr = EpisodeTracker(CFG)
    reviews, _ = feed(tr, 0.0, 1.5)
    assert reviews == []


def test_review_after_dwell_and_only_once_while_pending():
    tr = EpisodeTracker(CFG)
    reviews, _ = feed(tr, 0.0, 10.0)
    assert len(reviews) == 1
    assert reviews[0].pts_s == 2.0


def test_normal_verdict_reobserves_after_interval():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", "normal", 2.0) is False
    reviews, _ = feed(tr, 2.5, 6.5)
    assert reviews == []
    reviews, _ = feed(tr, 7.0, 7.0)
    assert len(reviews) == 1


def test_suspect_alerts_then_cooldown_suppresses():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", "suspect", 2.0) is True
    assert tr.episodes[KEY].state is EpisodeState.COOLDOWN
    reviews, _ = feed(tr, 2.5, 31.5)
    assert reviews == []
    reviews, _ = feed(tr, 32.0, 32.0)
    assert len(reviews) == 1  # cooldown over, still present -> review again


def test_zone_cooldown_survives_new_track_id():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    tr.on_verdict(req.episode_id, "sofa", "suspect", 2.0)
    feed(tr, 2.5, 5.0, present=False)  # dog leaves, episode closes
    reviews = []
    for t in [6.0 + 0.5 * i for i in range(20)]:
        reviews += tr.update(t, {(2, "sofa")}).reviews  # comes back with a new track id
    assert reviews == []


def test_episode_closes_after_grace():
    tr = EpisodeTracker(CFG)
    feed(tr, 0.0, 1.0)
    _, closed = feed(tr, 1.5, 3.0, present=False)
    assert len(closed) == 1 and KEY not in tr.episodes


def test_reviewing_episode_not_closed_until_verdict():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    _, closed = feed(tr, 2.5, 6.0, present=False)
    assert closed == []
    tr.on_verdict(req.episode_id, "sofa", "normal", 6.0)
    _, closed = feed(tr, 6.5, 6.5, present=False)
    assert len(closed) == 1


def test_error_verdict_keeps_watching():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", None, 2.0) is False
    assert tr.episodes[KEY].state is EpisodeState.OBSERVING


def test_insufficient_reobserves_sooner_than_normal():
    tr = EpisodeTracker(CFG)
    (req,), _ = feed(tr, 0.0, 2.0)
    tr.on_verdict(req.episode_id, "sofa", "insufficient", 2.0)
    reviews, _ = feed(tr, 2.5, 3.0)
    assert reviews == []
    reviews, _ = feed(tr, 3.5, 3.5)  # 1.5 s later
    assert len(reviews) == 1


def test_vlm_needs_two_suspects_in_a_row():
    cfg = StateConfig(dwell_s=2.0, leave_grace_s=1.0, reobserve_s=5.0, reobserve_insufficient_s=1.5,
                      cooldown_s=30.0, vlm_confirmations=2, confirm_gap_s=1.0)
    tr = EpisodeTracker(cfg)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", "suspect", 2.0, required=2) is False
    reviews, _ = feed(tr, 2.5, 2.5)
    assert reviews == []                      # waits confirm_gap_s
    (req2,), _ = feed(tr, 3.0, 3.0)
    assert tr.on_verdict(req2.episode_id, "sofa", "suspect", 3.0, required=2) is True


def test_normal_between_suspects_resets_confirmation():
    cfg = StateConfig(dwell_s=2.0, leave_grace_s=1.0, reobserve_s=1.0, reobserve_insufficient_s=1.0,
                      cooldown_s=30.0, vlm_confirmations=2, confirm_gap_s=1.0)
    tr = EpisodeTracker(cfg)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", "suspect", 2.0, required=2) is False
    (r2,), _ = feed(tr, 3.0, 3.0)
    assert tr.on_verdict(r2.episode_id, "sofa", "normal", 3.0, required=2) is False
    (r3,), _ = feed(tr, 4.0, 4.0)
    assert tr.on_verdict(r3.episode_id, "sofa", "suspect", 4.0, required=2) is False


def test_classifier_suspect_alerts_immediately():
    cfg = StateConfig(dwell_s=2.0, leave_grace_s=1.0, vlm_confirmations=2)
    tr = EpisodeTracker(cfg)
    (req,), _ = feed(tr, 0.0, 2.0)
    assert tr.on_verdict(req.episode_id, "sofa", "suspect", 2.0, required=1) is True
