"""Local labeling tool: watch clips, mark time segments and labels, save to a labels JSON.

    uv run mcam-label --folder data/raw --labels data/labels.json

Serves on 127.0.0.1 only. If a clip's file name starts with a prompt id (e.g. V012_...), the
expected label from prompts/training_video_prompts.json is shown as a hint — the label you save
should describe what is actually visible.
"""

from __future__ import annotations

import argparse
import json
import re
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import labels as L
from .branding import load_branding
from .config import resolve

STATIC = Path(__file__).resolve().parent / "static" / "label_tool.html"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm"}
PROMPT_ID = re.compile(r"^(V\d{3})[_\-]")


def find_clips(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_EXT and not p.name.startswith("."))


def load_hints(prompts_path: Path) -> dict[str, dict]:
    if not prompts_path.exists():
        return {}
    data = json.loads(prompts_path.read_text(encoding="utf-8"))
    return {p["id"]: {"label": p["label"], "behavior": p["behavior"], "target": p.get("target", ""),
                      "prompt": p["prompt"]} for p in data.get("prompts", [])}


def guess_hint(name: str, hints: dict[str, dict]) -> dict | None:
    m = PROMPT_ID.match(name)
    if m and m.group(1) in hints:
        return {"source": "prompt " + m.group(1), **hints[m.group(1)]}
    low = name.lower()
    if "sleep" in low or low.startswith("neg_"):
        return {"source": "file name", "label": "negative", "behavior": "", "target": "", "prompt": ""}
    if "chew" in low and "toy" not in low:
        return {"source": "file name", "label": "positive", "behavior": "chewing_furniture", "target": "", "prompt": ""}
    return None


class LabelState:
    def __init__(self, folder: Path, labels_path: Path, prompts_path: Path):
        self.folder = folder
        self.labels_path = labels_path
        self.clips = find_clips(folder)
        self.hints = load_hints(prompts_path)
        self.data = L.load(labels_path)

    def rel(self, p: Path) -> str:
        return p.relative_to(self.folder).as_posix()

    def listing(self) -> list[dict]:
        out = []
        for i, p in enumerate(self.clips):
            rel = self.rel(p)
            entry = self.data["clips"].get(rel) or self.data["clips"].get(p.name)  # legacy: keyed by file name
            out.append({
                "index": i, "path": rel,
                "label": L.clip_label(entry) if entry else None,
                "segments": entry["segments"] if entry else [],
                "simulated": entry.get("simulated") if entry else None,
                "source_note": entry.get("source_note", "") if entry else "",
                "damage_confirmed": entry.get("damage_confirmed", "unknown") if entry else "unknown",
                "hint": guess_hint(p.name, self.hints),
            })
        return out

    def save_clip(self, index: int, entry: dict) -> dict:
        rel = self.rel(self.clips[index])
        clean = L.validate_clip(entry)
        self.data["clips"].pop(self.clips[index].name, None)  # drop legacy file-name key
        if clean["segments"]:
            self.data["clips"][rel] = clean
        else:
            self.data["clips"].pop(rel, None)
        L.save(self.labels_path, self.data)
        return clean


def make_handler(state: LabelState, page: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, status, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _json(self, status, obj):
            self._send(status, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def _video(self, index: int):
            if not 0 <= index < len(state.clips):
                return self._send(HTTPStatus.NOT_FOUND, b"no such clip", "text/plain")
            path = state.clips[index]
            size = path.stat().st_size
            ctype = "video/mp4" if path.suffix.lower() in (".mp4", ".m4v") else "video/" + path.suffix.lower()[1:]
            rng = self.headers.get("Range")
            start, end, status = 0, size - 1, HTTPStatus.OK
            m = re.match(r"bytes=(\d*)-(\d*)", rng or "")
            if m:
                if m.group(1):
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else size - 1
                else:  # suffix range: last N bytes
                    start = max(0, size - int(m.group(2)))
                end = min(end, size - 1)
                status = HTTPStatus.PARTIAL_CONTENT
            with path.open("rb") as fh:
                fh.seek(start)
                body = fh.read(end - start + 1)
            extra = {"Accept-Ranges": "bytes"}
            if status == HTTPStatus.PARTIAL_CONTENT:
                extra["Content-Range"] = f"bytes {start}-{end}/{size}"
            self._send(status, body, ctype, extra)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(HTTPStatus.OK, page.encode(), "text/html; charset=utf-8")
            elif path == "/api/clips":
                self._json(HTTPStatus.OK, {"clips": state.listing(), "labels_path": str(state.labels_path),
                                           "behaviors": L.BEHAVIORS})
            elif path.startswith("/video/"):
                try:
                    self._video(int(path.rsplit("/", 1)[1]))
                except ValueError:
                    self._send(HTTPStatus.NOT_FOUND, b"bad id", "text/plain")
            else:
                self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")

        def do_POST(self):
            m = re.fullmatch(r"/api/clips/(\d+)", self.path.split("?", 1)[0])
            if not m:
                return self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain")
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
                index = int(m.group(1))
                if not 0 <= index < len(state.clips):
                    raise ValueError("no such clip")
                clean = state.save_clip(index, payload)
                self._json(HTTPStatus.OK, {"saved": True, "label": L.clip_label(clean) if clean["segments"] else None,
                                           "segments": clean["segments"]})
            except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})

    return Handler


def make_server(state: LabelState, port: int) -> ThreadingHTTPServer:
    b = load_branding()
    page = STATIC.read_text(encoding="utf-8").replace("{{PRODUCT}}", b.product_name).replace("{{MASCOT}}", b.mascot_name)
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(state, page))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Label clips: time segments + positive/negative/uncertain.")
    ap.add_argument("--folder", default="data/Videos")
    ap.add_argument("--labels", default="data/labels_videos.json")
    ap.add_argument("--prompts", default="prompts/training_video_prompts.json")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)
    state = LabelState(resolve(args.folder), resolve(args.labels), resolve(args.prompts))
    server = make_server(state, args.port)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Labeling tool: {url}  ({len(state.clips)} clips, saving to {state.labels_path}; Ctrl+C to stop)")
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
