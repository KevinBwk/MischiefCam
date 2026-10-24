"""Demo view for screen recording: live overlay + Michelle's notifications, served on 127.0.0.1.

    uv run mcam-demo --playlist demo/playlist.json            # several clips with captions
    uv run mcam-demo --video data/Videos/v4.mp4                # one clip
    uv run mcam-demo --camera 0                                # live camera (index or rtsp/http URL)

The page opens paused so you can start the screen recording first; press Start (or Space).
Recorded clips are played in real time ("pre-recorded video, live inference").
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import webbrowser
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np

from .branding import load_branding
from .config import bind_free_port, load_config, resolve
from .events import EventBus, JsonlSink, fmt_time
from .pipeline import Pipeline, PipelineConfig
from .roi import load_rois
from .sources import CameraSource, VideoFileSource
from .state import StateConfig
from .types import ROI, Event
from .metrics import write_timings
from .vlm import make_backend, probe_crop
from .worker import VLMWorker

STATIC = Path(__file__).resolve().parent / "static" / "demo.html"
AUTO_SOFA = ROI("sofa", "sofa", "forbidden", (), auto="couch")  # zone = detected couch boxes (config/rois.auto.json)

# BGR colours for the overlay
# BGR. The zone is violet so it never reads as the red "chewing -> alert" state.
C_ZONE, C_DOG, C_WATCH, C_JUDGE, C_ALERT, C_TEXT = (230, 110, 170), (90, 200, 90), (40, 190, 250), (240, 160, 60), (40, 40, 235), (255, 255, 255)
STATE_COLOR = {"candidate": C_WATCH, "observing": C_WATCH, "reviewing": C_JUDGE, "cooldown": C_ALERT}


# --------------------------------------------------------------------------- playlist
def load_items(args) -> list[dict]:
    if args.playlist:
        data = json.loads(resolve(args.playlist).read_text(encoding="utf-8"))
        items = data["items"] if isinstance(data, dict) else data
    elif args.camera is not None:
        items = [{"camera": args.camera, "caption": args.caption or "Live camera", "synthetic": False}]
    else:
        items = [{"video": v, "caption": args.caption or Path(v).name} for v in args.video]
    for it in items:
        it.setdefault("synthetic", "camera" not in it)
        it.setdefault("caption", "")
        if args.rois and "rois" not in it:
            it["rois"] = args.rois
    return items


def item_rois(item: dict) -> list[ROI]:
    if item.get("rois"):
        return load_rois(resolve(item["rois"]))
    if "camera" in item and resolve("config/rois.json").exists():
        return load_rois(resolve("config/rois.json"))  # a fixed home camera: the zone the owner drew
    return [AUTO_SOFA]


class PacedSource:
    """Plays a recorded clip at real-time speed so the demo looks like a live camera."""

    def __init__(self, inner: VideoFileSource, should_stop):
        self.inner = inner
        self.should_stop = should_stop

    @property
    def size(self):
        return self.inner.size

    def frames(self):
        start = time.monotonic()
        for f in self.inner.frames():
            if self.should_stop():
                return
            wait = f.pts_s - (time.monotonic() - start)
            if wait > 0:
                time.sleep(wait)
            yield f


# --------------------------------------------------------------------------- shared state
class DemoState:
    def __init__(self, branding, backend_name: str):
        self.lock = threading.Lock()
        self.branding = branding
        self.backend_name = backend_name
        self.status = "loading"          # loading | ready | running | finished | error
        self.message = "Loading models…"
        self.item = {}
        self.item_index = -1
        self.total = 0
        self.jpeg = b""
        self.frame_seq = 0
        self.events: list[dict] = []
        self.snaps: dict[int, bytes] = {}
        self.det_ms: list[float] = []
        self.judge_ms: list[float] = []
        self.started = threading.Event()
        self.stop_requested = False

    def snapshot(self) -> dict:
        with self.lock:
            p = lambda xs: round(float(np.median(xs[-50:])), 1) if xs else None
            return {"status": self.status, "message": self.message, "item": self.item, "index": self.item_index,
                    "total": self.total, "events": self.events[-60:], "backend": self.backend_name,
                    "det_ms": p(self.det_ms), "judge_ms": p(self.judge_ms), "product": self.branding.product_name,
                    "mascot": self.branding.mascot_name, "frame_seq": self.frame_seq}

    def add_event(self, ev: dict, snap: bytes | None = None) -> None:
        with self.lock:
            ev["id"] = len(self.events)
            ev["wall"] = time.strftime("%H:%M:%S")
            if snap:
                self.snaps[ev["id"]] = snap
                ev["snap"] = f"/snap/{ev['id']}.jpg"
            self.events.append(ev)


# --------------------------------------------------------------------------- overlay
def draw_overlay(image: np.ndarray, rois: list[ROI], dets, info: dict, pts: float, item: dict) -> np.ndarray:
    h, w = image.shape[:2]
    out = image.copy()
    layer = out.copy()
    auto = info.get("auto_zones", {})
    shapes = []  # (polygon px, label) for drawn zones and for each detected box of an auto zone
    for roi in rois:
        if roi.auto:
            for x1, y1, x2, y2 in auto.get(roi.id, []):
                poly = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.int32)
                shapes.append((poly, f"{roi.name} (protected, auto)"))
        else:
            poly = np.array([[int(x * w), int(y * h)] for x, y in roi.polygon], dtype=np.int32)
            shapes.append((poly, f"{roi.name} (protected)"))
    for poly, _ in shapes:
        cv2.fillPoly(layer, [poly], C_ZONE)
    out = cv2.addWeighted(layer, 0.12, out, 0.88, 0)
    for poly, label in shapes:
        cv2.polylines(out, [poly], True, C_ZONE, 2, cv2.LINE_AA)
        _label(out, label, (int(poly[0][0]), max(24, int(poly[0][1]))), C_ZONE)
    dogs = info.get("dogs", {})
    s = max(1.0, w / 1280)
    for det in dets:
        tid = det.track_id if det.track_id is not None else -1
        d = dogs.get(tid, {})
        state = d.get("state", "")
        v = d.get("verdict") or {}
        color = C_ALERT if state == "cooldown" else STATE_COLOR.get(state, C_DOG)
        x1, y1, x2, y2 = map(int, det.bbox)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, int(3 * s), cv2.LINE_AA)
        text = f"dog #{tid}"
        if state:
            text += {"candidate": " - in zone", "observing": " - watching", "reviewing": " - checking...",
                     "cooldown": " - alert sent"}.get(state, f" - {state}")
        _label(out, text, (x1, max(int(24 * s), y1)), color)
        if v and state:
            why = v.get("reason") or _judge_name(v.get("raw", ""))
            _label(out, f"{v['decision']}" + (f" - {why[:38]}" if why else ""), (x1, min(h - 4, y2 + int(26 * s))), color)
    _label(out, f"t={pts:5.1f}s", (int(12 * s), int(34 * s)), (40, 40, 40))
    badge = "ON-DEVICE  |  NO CLOUD"
    (tw, _), _ = cv2.getTextSize(badge, cv2.FONT_HERSHEY_SIMPLEX, 0.7 * s, 2)
    _label(out, badge, (w - tw - int(26 * s), int(34 * s)), (60, 120, 40))
    if item.get("synthetic"):
        _label(out, "SYNTHETIC CLIP - pre-recorded video, live inference", (int(12 * s), h - int(14 * s)), (60, 60, 60))
    elif "camera" in item:
        _label(out, "LIVE CAMERA", (int(12 * s), h - int(14 * s)), (40, 40, 200))
    return out


def _label(img, text, org, color):
    s = max(1.0, img.shape[1] / 1280)
    font, scale, th = cv2.FONT_HERSHEY_SIMPLEX, 0.62 * s, max(1, int(2 * s))
    (tw, tht), base = cv2.getTextSize(text, font, scale, th)
    x, y = int(org[0]), int(org[1])
    cv2.rectangle(img, (x - 4, y - tht - 8), (x + tw + 6, y + base), color, -1)
    cv2.putText(img, text, (x + 1, y - 3), font, scale, C_TEXT, th, cv2.LINE_AA)


def encode(img: np.ndarray, width: int = 1280, quality: int = 82) -> bytes:
    if img.shape[1] > width:
        img = cv2.resize(img, (width, int(img.shape[0] * width / img.shape[1])), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else b""


# --------------------------------------------------------------------------- runner
class Runner(threading.Thread):
    def __init__(self, state: DemoState, items: list[dict], cfg: dict, loop: bool):
        super().__init__(daemon=True, name="demo-runner")
        self.state, self.items, self.cfg, self.loop = state, items, cfg, loop
        self.camera: CameraSource | None = None
        self.plays = 0  # playback counter: card keys stay unique when the playlist loops

    def run(self) -> None:
        st = self.state
        try:
            from .detector import UltralyticsDetector

            dc, vc = self.cfg["detector"], self.cfg["vlm"]
            detector = UltralyticsDetector(str(resolve(dc["model"])), dc["device"], dc["target_classes"],
                                           dc["min_score"], dc["tracker"], dc.get("context_classes", []))
            backend = make_backend(vc)
            # "either": the VLM inside it also writes the visual assessment for classifier alerts
            worker = VLMWorker(backend, vc["queue_size"], vc["max_age_s"], explainer=getattr(backend, "vlm", None))
        except Exception as exc:  # show the problem on the page instead of a silent dead server
            with st.lock:
                st.status, st.message = "error", f"Could not load models: {exc}"
            return
        with st.lock:
            st.status, st.message, st.total = "ready", "Ready — press Start", len(self.items)
        st.started.wait()
        out_root = resolve(self.cfg["output"]["dir"]) / time.strftime("demo_%Y%m%d_%H%M%S")
        try:
            while True:
                for i, item in enumerate(self.items):
                    if st.stop_requested:
                        break
                    self.plays += 1
                    self.play(i, item, detector, worker, out_root / f"{self.plays:03d}_{i:02d}")
                if not self.loop or st.stop_requested:
                    break
        except Exception as exc:
            with st.lock:
                st.status, st.message = "error", f"{type(exc).__name__}: {exc}"
            return
        finally:
            worker.close()
        with st.lock:
            st.status, st.message = "finished", "Demo finished"

    def play(self, index: int, item: dict, detector, worker, out_dir: Path) -> None:
        st, cfg = self.state, self.cfg
        rois = item_rois(item)
        if "camera" in item:
            self.camera = CameraSource(item["camera"], cfg["source"].get("demo_fps", 10.0))
            source = self.camera
        else:
            source = PacedSource(VideoFileSource(resolve(item["video"]) if not Path(item["video"]).exists() else item["video"],
                                                 cfg["source"].get("demo_fps", 10.0)), lambda: st.stop_requested)
        detector.reset_tracks()
        with st.lock:
            st.item, st.item_index, st.status, st.message = item, index, "running", item.get("caption", "")
        alerts_before = sum(1 for e in st.events if e["kind"] == "alert")
        play = self.plays
        recent: deque = deque(maxlen=120)  # (pts, overlay frame): the alert snapshot is the frame that was judged
        bus = EventBus()
        out_dir.mkdir(parents=True, exist_ok=True)
        sink = JsonlSink(out_dir / "events.jsonl")
        bus.subscribe(sink)

        def on_event(ev: Event) -> None:
            if ev.kind not in ("alert", "explained", "insufficient", "review", "confirming"):
                return
            v = ev.extra or {}
            if ev.kind == "explained":  # updates the alert card in place (no new notification)
                tone, text = assessment_line(v.get("explanation"))
                st.add_event({"kind": "explained", "alert_key": f"{play}:{v.get('alert_key')}", "tone": tone, "text": text,
                              "ms": v.get("vlm_ms")})
                return
            card = {"kind": ev.kind, "clip": item.get("caption", ""), "t": fmt_time(ev.pts_s), "pts": ev.pts_s,
                    "zone": ev.roi_name, "dog": ev.track_id, "decision": ev.decision, "reason": ev.reason,
                    "judge": _judge_name(v.get("raw", "")), "ms": v.get("vlm_ms")}
            snap = None
            if ev.kind == "alert":
                card["message"] = st.branding.message("suspect", roi=ev.roi_name, time=fmt_time(ev.pts_s),
                                                      decision=ev.decision or "", reason=ev.reason)
                card["alert_key"] = f"{play}:{v.get('alert_key')}"  # track ids restart per clip: scope by playback
                if v.get("explaining"):
                    card["tone"], card["text"] = "pending", f"{st.branding.mascot_name} is taking a closer look"
                elif v.get("judge_source") == "vlm":  # the VLM itself raised the alert: its reason is the assessment
                    card["tone"], card["text"] = "ok", f"Visual check: {ev.reason}" if ev.reason else "Visual check: chewing seen"
                judged = min(recent, key=lambda f: abs(f[0] - ev.pts_s), default=None)  # the reviewed frame
                snap = encode(judged[1], width=640) if judged is not None else None
            if ev.kind in ("alert", "insufficient") and v.get("vlm_ms"):
                with st.lock:
                    st.judge_ms.append(float(v["vlm_ms"]))
            st.add_event(card, snap)

        bus.subscribe(on_event)

        def on_frame(frame, dets, info) -> None:
            img = draw_overlay(frame.image, rois, dets, info, frame.pts_s, item)
            recent.append((frame.pts_s, cv2.resize(img, (640, int(img.shape[0] * 640 / img.shape[1])))))
            jpeg = encode(img)
            with st.lock:
                st.jpeg, st.frame_seq = jpeg, st.frame_seq + 1
                if pipe.stats.detector_ms:
                    st.det_ms.append(pipe.stats.detector_ms[-1])

        vc = cfg["vlm"]
        pipe = Pipeline(source, detector, rois, worker, bus, StateConfig(**cfg["state"]),
                        PipelineConfig(bbox_expand=cfg["roi"]["bbox_expand"], min_overlap=cfg["roi"]["min_overlap"],
                                       vlm_input_size=vc["input_size"], crop_mode=vc.get("crop", "animal"), probe_crop_mode=probe_crop(vc),
                                       context_classes=tuple(self.cfg["detector"].get("context_classes", [])),
                                       max_new_tokens=vc["max_new_tokens"], frames=vc.get("frames", 1),
                                       frame_gap_s=vc.get("frame_gap_s", 0.5), save_crops=False, output_dir=out_dir),
                        on_frame=on_frame)
        try:
            pipe.run(drain_timeout_s=15.0)
        finally:
            sink.close()
            write_timings(pipe.stats, out_dir / "timings.json", "realtime")  # paced playback: R4 latency
            self.camera = None
        if sum(1 for e in st.events if e["kind"] == "alert") == alerts_before:
            st.add_event({"kind": "quiet", "clip": item.get("caption", ""),
                          "message": f"{st.branding.mascot_name} stayed quiet — no chewing on a protected zone."})
        time.sleep(float(cfg["source"].get("demo_pause_s", 1.5)))


def assessment_line(expl: dict | None) -> tuple[str, str]:
    """(tone, text) for the VLM's visual assessment under an alert. Tiered so a true alert does not read as the
    product doubting itself, but contradicting evidence stays visible and "can't tell" never reads as a yes.
    tone: "ok" supports the alert, "warn" contradicts it, "muted" cannot tell / unavailable."""
    if not expl or not expl.get("ok"):
        return "muted", "Visual assessment unavailable"
    obs = expl.get("observation", "")
    # support needs consistent visible evidence: a yes, on the sofa, mouth actually seen, and an observation
    if (expl["assessment"] == "suspect" and expl["contact"] == "sofa" and obs
            and expl["mouth_visibility"] in ("clear", "partial")):
        return "ok", f"Visual check: {obs}"
    if expl["assessment"] == "normal" or expl["contact"] in ("toy", "other", "none"):
        toy = ", looks like a toy" if expl["contact"] == "toy" else ""
        return "warn", f"Visual check found no clear chewing on the sofa{toy} — check the snapshot"
    if expl["mouth_visibility"] == "hidden" or expl["limitation"] == "occlusion":
        return "muted", "Mouth hidden from camera — check the snapshot"
    # no "mouth at the sofa" tier: on 2026-10-22 the VLM said contact=sofa for a toy-chewing false alert too
    return "muted", "Limited view of the mouth — check the snapshot"


def _judge_name(raw: str) -> str:
    if raw.startswith("probe:") and "vlm:" in raw:
        return "classifier + VLM"
    if raw.startswith("probe:") or raw.startswith("p="):
        return "classifier"
    return "VLM" if raw else ""


# --------------------------------------------------------------------------- web
def make_handler(state: DemoState, page: str, runner: Runner):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, body: bytes, ctype: str):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                return self._send(HTTPStatus.OK, page.encode(), "text/html; charset=utf-8")
            if path == "/api/state":
                return self._send(HTTPStatus.OK, json.dumps(state.snapshot(), ensure_ascii=False).encode(),
                                  "application/json; charset=utf-8")
            if path == "/frame.jpg":
                with state.lock:
                    body = state.jpeg
                return self._send(HTTPStatus.OK if body else HTTPStatus.NO_CONTENT, body, "image/jpeg")
            if path.startswith("/snap/"):
                try:
                    body = state.snaps[int(path.split("/")[-1].split(".")[0])]
                except (KeyError, ValueError):
                    return self._send(HTTPStatus.NOT_FOUND, b"", "text/plain")
                return self._send(HTTPStatus.OK, body, "image/jpeg")
            if path == "/stream.mjpg":
                return self._mjpeg()
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

        def _mjpeg(self):
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            seen = -1
            try:
                while True:
                    with state.lock:
                        seq, body = state.frame_seq, state.jpeg
                    if body and seq != seen:
                        seen = seq
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                                         + str(len(body)).encode() + b"\r\n\r\n" + body + b"\r\n")
                    time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError):
                return

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/start":
                state.started.set()
            elif path == "/api/stop":
                state.stop_requested = True
                state.started.set()
                if runner.camera is not None:
                    runner.camera.stop()
            else:
                return self._send(HTTPStatus.NOT_FOUND, b"", "text/plain")
            self._send(HTTPStatus.OK, b"{}", "application/json")

    return Handler


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Demo view for screen recording (localhost only).")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--playlist", help="JSON: {\"items\": [{\"video\"|\"camera\", \"caption\", \"rois\", \"synthetic\"}]}")
    src.add_argument("--video", action="append", help="clip to play (repeatable)")
    src.add_argument("--camera", help="live camera: device index or rtsp/http URL")
    ap.add_argument("--caption", help="caption for --video/--camera")
    ap.add_argument("--rois", help="zone file for items without their own (default: whole frame = sofa)")
    ap.add_argument("--vlm", default="either", choices=["mlx", "probe", "either", "fake"])
    ap.add_argument("--config")
    ap.add_argument("--fps", type=float, default=10.0, help="processing / display rate")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--autostart", action="store_true", help="start without waiting for the Start button")
    ap.add_argument("--port", type=int, default=8768)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    cfg["vlm"]["backend"] = args.vlm
    cfg["source"]["demo_fps"] = args.fps
    branding = load_branding()
    items = load_items(args)
    state = DemoState(branding, {"either": "classifier + VLM", "probe": "classifier", "mlx": "VLM", "fake": "fake"}[args.vlm])
    runner = Runner(state, items, cfg, args.loop)
    page = STATIC.read_text(encoding="utf-8").replace("{{PRODUCT}}", branding.product_name).replace("{{MASCOT}}", branding.mascot_name)
    server, port = bind_free_port(lambda p: ThreadingHTTPServer(("127.0.0.1", p), make_handler(state, page, runner)), args.port)
    runner.start()
    if args.autostart:
        state.started.set()
    url = f"http://127.0.0.1:{port}/"
    print(f"Demo: {url}  ({len(items)} item(s), judge: {state.backend_name}; Ctrl+C to stop)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        state.stop_requested = True
        if runner.camera is not None:
            runner.camera.stop()
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
