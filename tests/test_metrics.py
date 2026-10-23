import json
import sys
from pathlib import Path

from core import metrics
from core.metrics import write_timings
from core.pipeline import RunStats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_latency_report_pools_runs_and_drops_warmup(tmp_path):
    import latency_report

    metrics._judges_seen.clear()  # fresh "process"
    for i in range(2):
        st = RunStats(detector_ms=[500.0] + [10.0 + i] * 9)  # first frames are slow warm-up
        st.add_timings({"clip": 300.0})                       # first judge call = warm-up
        st.add_timings({"clip": 20.0})
        run = tmp_path / f"clip{i}"
        run.mkdir()
        write_timings(st, run / "timings.json", "batch")
    (tmp_path / "batch_summary.json").write_text(json.dumps([{"alert_delay_s": 2.5}, {"alert_delay_s": None}]))
    pooled, dropped, modes = latency_report.collect([tmp_path])
    assert modes == {"batch"}
    assert len(pooled["detector"]) == 2 * (10 - 5) and max(pooled["detector"]) < 100
    assert pooled["clip"] == [20.0, 300.0, 20.0] and dropped["clip"] == 1  # only the process's first call
    assert pooled["alert_delay_s"] == [2.5]
    assert latency_report.pct([1, 2, 3, 4, 100], 50) == 3


def test_first_positive_start():
    import batch_run

    entry = {"segments": [{"start_s": 0.0, "end_s": 2.0, "label": "negative"},
                          {"start_s": 3.4, "end_s": -1, "label": "positive"},
                          {"start_s": 2.1, "end_s": 3.0, "label": "positive"}]}
    assert batch_run.first_positive_start(entry) == 2.1
    assert batch_run.first_positive_start({"segments": [{"start_s": 0, "end_s": -1, "label": "negative"}]}) is None
