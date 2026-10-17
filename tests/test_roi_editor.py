import json
import threading
import urllib.error
import urllib.request

import numpy as np
import pytest

from core.roi import load_rois
from core.roi_editor import EditorState, make_server, normalize_payload

SQUARE = [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]]


def test_normalize_assigns_unique_ids():
    out = normalize_payload({"rois": [
        {"name": "Sofa", "policy": "forbidden", "polygon": SQUARE},
        {"name": "Sofa", "policy": "allowed", "polygon": SQUARE},
    ]})
    assert [r["id"] for r in out["rois"]] == ["sofa", "sofa_2"]


@pytest.mark.parametrize("zone", [
    {"name": "a", "policy": "forbidden", "polygon": SQUARE[:2]},
    {"name": "a", "policy": "maybe", "polygon": SQUARE},
    {"name": "a", "policy": "forbidden", "polygon": [[0, 0], [1.2, 0], [1, 1]]},
])
def test_normalize_rejects_bad_zones(zone):
    with pytest.raises(ValueError):
        normalize_payload({"rois": [zone]})


@pytest.fixture
def server(tmp_path):
    frame = np.full((90, 160, 3), 127, dtype=np.uint8)
    state = EditorState(frame, tmp_path / "rois.json", "test.jpg")
    srv = make_server(state, 0)  # ephemeral port
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", state
    srv.shutdown()
    srv.server_close()


def _post(url, payload):
    req = urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return urllib.request.urlopen(req)


def test_server_binds_localhost_only(server):
    base, _ = server
    assert base.startswith("http://127.0.0.1:")


def test_page_snapshot_and_save_roundtrip(server):
    base, state = server
    page = urllib.request.urlopen(base + "/").read().decode()
    assert "Michelle" in page and "{{" not in page
    assert urllib.request.urlopen(base + "/snapshot.jpg").read()[:2] == b"\xff\xd8"  # JPEG
    resp = json.loads(_post(base + "/api/rois", {"rois": [{"name": "sofa", "policy": "forbidden", "polygon": SQUARE}]}).read())
    assert resp["count"] == 1
    rois = load_rois(state.out_path)  # the pipeline can read what the editor wrote
    assert rois[0].id == "sofa" and rois[0].policy == "forbidden"
    saved = json.loads(state.out_path.read_text())
    assert saved["snapshot"]["width"] == 160 and saved["snapshot"]["height"] == 90
    again = json.loads(urllib.request.urlopen(base + "/api/rois").read())
    assert again["rois"][0]["polygon"] == SQUARE


def test_invalid_save_returns_422_and_keeps_file(server):
    base, state = server
    with pytest.raises(urllib.error.HTTPError) as err:
        _post(base + "/api/rois", {"rois": [{"name": "x", "policy": "forbidden", "polygon": SQUARE[:2]}]})
    assert err.value.code == 422
    assert not state.out_path.exists()
