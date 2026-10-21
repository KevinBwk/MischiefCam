"""Local zone editor: draw protected zones on a camera snapshot and save them as ROI JSON.

    uv run mcam-roi --video data/clips/sofa_01.mp4 --at 3.0 --out config/rois/living_room.json
    uv run mcam-roi --image data/raw/snapshot.jpg

Serves on 127.0.0.1 only (stdlib http.server, no extra dependencies) and writes the same
normalized-polygon format that the pipeline reads (core.roi.load_rois).
"""

from __future__ import annotations

import argparse
import json
import re
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

from .branding import load_branding
from .config import bind_free_port, resolve
from .roi import load_rois

STATIC = Path(__file__).resolve().parent / "static" / "roi_editor.html"
ID_RE = re.compile(r"[^a-z0-9_]+")


def grab_frame(video: Path | str, at_s: float) -> np.ndarray:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video}")
    cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, at_s) * 1000.0)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise ValueError(f"No frame at {at_s:.2f}s in {video}")
    return frame


def video_duration(video: Path | str) -> float:
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    cap.release()
    return n / fps if fps else 0.0


def slug(name: str, taken: set[str]) -> str:
    base = ID_RE.sub("_", name.strip().lower()).strip("_") or "zone"
    sid, i = base, 2
    while sid in taken:
        sid, i = f"{base}_{i}", i + 1
    taken.add(sid)
    return sid


def normalize_payload(payload: dict) -> dict:
    """Validate editor output and convert it to the on-disk ROI format."""
    zones = payload.get("rois")
    if not isinstance(zones, list):
        raise ValueError("payload.rois must be a list")
    taken: set[str] = set()
    rois = []
    for z in zones:
        name = str(z.get("name", "")).strip() or "zone"
        policy = z.get("policy", "forbidden")
        if policy not in ("forbidden", "allowed"):
            raise ValueError(f"zone {name!r}: policy must be forbidden or allowed")
        pts = z.get("polygon") or []
        if len(pts) < 3:
            raise ValueError(f"zone {name!r}: needs at least 3 points")
        poly = []
        for p in pts:
            x, y = float(p[0]), float(p[1])
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                raise ValueError(f"zone {name!r}: point {p} outside [0,1]")
            poly.append([round(x, 4), round(y, 4)])
        rois.append({"id": slug(name, taken), "name": name, "policy": policy, "polygon": poly})
    return {
        "version": 1,
        "coordinate_space": "normalized",
        "note": "Drawn with the zone editor. policy: forbidden | allowed.",
        "snapshot": payload.get("snapshot", {}),
        "rois": rois,
    }


class EditorState:
    def __init__(self, frame: np.ndarray, out_path: Path, source_label: str,
                 video: Path | None = None, at_s: float = 0.0):
        self.frame = frame
        self.out_path = out_path
        self.source_label = source_label
        self.video = video
        self.at_s = at_s
        self.duration = video_duration(video) if video else 0.0

    def jpeg(self) -> bytes:
        ok, buf = cv2.imencode(".jpg", self.frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            raise RuntimeError("JPEG encoding failed")
        return buf.tobytes()

    def existing(self) -> dict:
        if not self.out_path.exists():
            return {"rois": []}
        data = json.loads(self.out_path.read_text(encoding="utf-8"))
        load_rois(self.out_path)  # validates
        return data

    def save(self, payload: dict) -> dict:
        data = normalize_payload(payload)
        h, w = self.frame.shape[:2]
        data["snapshot"] = {"source": self.source_label, "at_s": self.at_s, "width": w, "height": h}
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.out_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.out_path)
        load_rois(self.out_path)  # round-trip check with the pipeline's loader
        return data


def make_handler(state: EditorState, page: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the terminal quiet
            pass

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, obj) -> None:
            self._send(status, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(HTTPStatus.OK, page.encode(), "text/html; charset=utf-8")
            elif path == "/snapshot.jpg":
                self._send(HTTPStatus.OK, state.jpeg(), "image/jpeg")
            elif path == "/api/info":
                h, w = state.frame.shape[:2]
                self._json(HTTPStatus.OK, {
                    "source": state.source_label, "width": w, "height": h,
                    "at_s": state.at_s, "duration_s": round(state.duration, 2), "is_video": state.video is not None,
                    "out_path": str(state.out_path),
                })
            elif path == "/api/rois":
                try:
                    self._json(HTTPStatus.OK, state.existing())
                except Exception as exc:
                    self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
            else:
                self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid JSON"})
            try:
                if path == "/api/rois":
                    data = state.save(payload)
                    self._json(HTTPStatus.OK, {"saved": str(state.out_path), "count": len(data["rois"]), "rois": data["rois"]})
                elif path == "/api/seek" and state.video is not None:
                    at = float(payload.get("at_s", 0.0))
                    state.frame = grab_frame(state.video, at)
                    state.at_s = at
                    self._json(HTTPStatus.OK, {"at_s": at})
                else:
                    self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            except (ValueError, KeyError, TypeError) as exc:
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})

    return Handler


def build_page() -> str:
    b = load_branding()
    return (STATIC.read_text(encoding="utf-8")
            .replace("{{PRODUCT}}", b.product_name)
            .replace("{{MASCOT}}", b.mascot_name))


def make_server(state: EditorState, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(state, build_page()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Draw protected zones on a camera snapshot.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="Video file to take the snapshot from")
    src.add_argument("--image", help="Snapshot image")
    ap.add_argument("--at", type=float, default=1.0, help="Snapshot time in seconds (video only)")
    ap.add_argument("--out", default="config/rois.json", help="ROI JSON to load/save")
    ap.add_argument("--port", type=int, default=8765, help="Local port (avoid 5000/7000: macOS AirPlay)")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    if args.video:
        video = resolve(args.video) if not Path(args.video).exists() else Path(args.video)
        state = EditorState(grab_frame(video, args.at), resolve(args.out), str(args.video), video, args.at)
    else:
        frame = cv2.imread(args.image)
        if frame is None:
            raise SystemExit(f"Cannot read image: {args.image}")
        state = EditorState(frame, resolve(args.out), str(args.image))

    server, port = bind_free_port(lambda p: make_server(state, p), args.port)
    url = f"http://127.0.0.1:{port}/"
    print(f"Zone editor: {url}  (saving to {state.out_path}; Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
