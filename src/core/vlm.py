"""VLM backends behind one thin interface.

Mac (Stage I): mlx-vlm running Qwen2-VL-2B.
Hailo (Stage II, planned): hailo_platform.genai.VLM — Hailo's model table lists
only C++/Python APIs for its VLMs (not hailo-ollama), so the pipeline never
assumes an HTTP server.
"""

from __future__ import annotations

import json
import re
import time
from typing import Protocol

from .types import Decision, VLMRequest, VLMResult

DECISIONS: tuple[Decision, ...] = ("suspect", "normal", "insufficient")

PROMPT_TEMPLATE = (
    "You are checking a still frame from a fixed home camera. "
    "Focus on the dog and the {target}.\n"
    "Reply with JSON only, no other text: "
    '{{"decision": "suspect" | "normal" | "insufficient", "reason": "<at most 12 words>"}}\n'
    "- suspect: the dog's mouth is on the {target} and it is biting or chewing it.\n"
    "- normal: the dog is not chewing the {target} (resting, walking, sniffing, licking itself, "
    "or chewing its own toy elsewhere).\n"
    "- insufficient: the dog's mouth or the {target} is not clearly visible."
)


MULTI_FRAME_TEMPLATE = (
    "You are checking {n} frames from a fixed home camera, in time order, about {gap:.1f} s apart. "
    "Focus on the dog and the {target}.\n"
    "Reply with JSON only, no other text: "
    '{{"decision": "suspect" | "normal" | "insufficient", "reason": "<at most 12 words>"}}\n'
    "- suspect: in these frames the dog's mouth is on the {target} and it is biting, chewing or tugging it.\n"
    "- normal: the dog is not chewing the {target} (resting, walking, sniffing, licking itself, "
    "or chewing its own toy or something lying on the floor).\n"
    "- insufficient: the dog's mouth or the {target} is not clearly visible in any frame."
)


def build_prompt(target: str, n_frames: int = 1, gap_s: float = 0.5) -> str:
    if n_frames <= 1:
        return PROMPT_TEMPLATE.format(target=target)
    return MULTI_FRAME_TEMPLATE.format(target=target, n=n_frames, gap=gap_s)


# Visual assessment shown on an alert card after the classifier fired. Deliberately not told that an alert
# happened (so it cannot just agree) and asked for visible evidence only; independent of the alert decision.
EXPLAIN_TEMPLATE = (
    "You are looking at a still frame from a fixed home camera showing a dog near a {target}.\n"
    "Describe only what is visible. Do not guess motion from a single image.\n"
    "Reply with JSON only, no other text:\n"
    '{{"assessment": "suspect" | "normal" | "insufficient", '
    '"mouth_visibility": "clear" | "partial" | "hidden" | "unknown", '
    '"contact": "sofa" | "toy" | "other" | "none" | "unclear", '
    '"limitation": "none" | "occlusion" | "blur" | "crop" | "other" | "unknown", '
    '"observation": "<at most 12 words, visible evidence only>"}}\n'
    "- assessment suspect: the dog's teeth are visibly on the {target}; normal: they are not; "
    "insufficient: you cannot tell.\n"
    "- contact: what the dog's mouth is touching. Cushions and throw pillows on the {target} count as "
    "\"sofa\"; a toy, bone or scrap of cloth counts as \"toy\" or \"other\", even when it lies on the {target}."
)
EXPLANATION_FIELDS = {
    "assessment": DECISIONS,
    "mouth_visibility": ("clear", "partial", "hidden", "unknown"),
    "contact": ("sofa", "toy", "other", "none", "unclear"),
    "limitation": ("none", "occlusion", "blur", "crop", "other", "unknown"),
}


def build_explain_prompt(target: str) -> str:
    return EXPLAIN_TEMPLATE.format(target=target)


def parse_explanation(text: str) -> dict:
    """Validate the explanation JSON. Unknown/missing values become the field's "don't know" value;
    unparseable output gives assessment "insufficient" and ok=False."""
    out = {"assessment": "insufficient", "mouth_visibility": "unknown", "contact": "unclear",
           "limitation": "unknown", "observation": "", "ok": False}
    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if not match:
        return out
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return out
    for key, allowed in EXPLANATION_FIELDS.items():
        value = str(data.get(key, "")).strip().lower()
        if value in allowed:
            out[key] = value
    out["observation"] = " ".join(str(data.get("observation", "")).split()[:12])
    out["ok"] = True
    return out


def parse_decision(text: str) -> tuple[Decision, str]:
    """Extract (decision, reason) from model output. Unparseable output -> insufficient.

    Accepts the requested JSON, or an answer that is exactly one label (small VLMs
    often reply with just "suspect"). Anything else is treated as insufficient.
    """
    bare = text.strip().strip(".!\"'`").strip().lower()
    if bare in DECISIONS:
        return bare, ""  # type: ignore[return-value]
    match = re.search(r"\{.*?\}", text, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            decision = str(data.get("decision", "")).strip().lower()
            if decision in DECISIONS:
                return decision, str(data.get("reason", "")).strip()  # type: ignore[return-value]
        except json.JSONDecodeError:
            pass
    return "insufficient", "unparseable output"


class VLMBackend(Protocol):
    def infer(self, request: VLMRequest) -> VLMResult: ...

    def close(self) -> None: ...


class FakeVLMBackend:
    """Deterministic backend for tests and dry runs."""

    def __init__(self, reply: str = '{"decision": "suspect", "reason": "fake backend"}', delay_s: float = 0.0):
        self.reply = reply
        self.delay_s = delay_s
        self.calls = 0

    def infer(self, request: VLMRequest) -> VLMResult:
        self.calls += 1
        t0 = time.perf_counter()
        if self.delay_s:
            time.sleep(self.delay_s)
        decision, reason = parse_decision(self.reply)
        return VLMResult(decision, self.reply, (time.perf_counter() - t0) * 1000, reason)

    def close(self) -> None:
        pass


class MLXVLMBackend:
    """Qwen2-VL-2B (4-bit) via mlx-vlm on Apple Silicon. Loads the model once."""

    def __init__(self, model_id: str):
        from mlx_vlm import load  # imported lazily: only available on Apple Silicon
        from mlx_vlm.prompt_utils import apply_chat_template

        self._apply_chat_template = apply_chat_template
        self.model, self.processor = load(model_id)
        self.config = self.model.config

    def infer(self, request: VLMRequest) -> VLMResult:
        from mlx_vlm import generate

        t0 = time.perf_counter()
        images = list(request.images)
        prompt = self._apply_chat_template(self.processor, self.config, request.prompt, num_images=len(images))
        out = generate(
            self.model,
            self.processor,
            prompt,
            images,
            max_tokens=request.max_new_tokens,
            temperature=0.0,
            verbose=False,
        )
        text = getattr(out, "text", out)  # newer mlx-vlm returns a GenerationResult
        decision, reason = parse_decision(text)
        return VLMResult(decision, text, (time.perf_counter() - t0) * 1000, reason)

    def close(self) -> None:
        pass


class EitherBackend:
    """Alert if either judge says suspect: the trained probe (fast, runs first) or the VLM.

    Used because on the 75-clip evaluation the two caught different clips; the VLM is skipped
    when the probe already says suspect.
    """

    def __init__(self, probe: VLMBackend, vlm: VLMBackend):
        self.probe = probe
        self.vlm = vlm

    def infer(self, request: VLMRequest) -> VLMResult:
        t0 = time.perf_counter()
        p = self.probe.infer(request)
        if p.decision == "suspect":
            return VLMResult("suspect", f"probe: {p.raw_text}", (time.perf_counter() - t0) * 1000, p.reason, source="probe")
        v = self.vlm.infer(request)
        return VLMResult(v.decision, f"probe: {p.raw_text} | vlm: {v.raw_text}", (time.perf_counter() - t0) * 1000,
                         v.reason if v.decision != "normal" else f"{p.reason}; vlm normal", source="vlm")

    def close(self) -> None:
        self.probe.close()
        self.vlm.close()


def probe_crop(cfg: dict) -> str | None:
    """Crop the trained classifier expects (from classifier.json) when the judge uses it, else None."""
    if cfg.get("backend") not in ("probe", "either"):
        return None
    from .config import resolve
    from .probe import classifier_crop

    path = resolve(cfg.get("classifier", "models/classifier.json"))
    return classifier_crop(path) if path.exists() else None


def make_backend(cfg: dict) -> VLMBackend:
    kind = cfg.get("backend", "mlx")
    if kind == "either":
        return EitherBackend(make_backend({**cfg, "backend": "probe"}), make_backend({**cfg, "backend": "mlx"}))
    if kind == "fake":
        return FakeVLMBackend()
    if kind == "mlx":
        return MLXVLMBackend(cfg["model"])
    if kind == "probe":
        from .config import resolve
        from .probe import ProbeBackend

        return ProbeBackend(resolve(cfg.get("classifier", "models/classifier.json")))
    raise ValueError(f"Unknown judge backend {kind!r} (hailo backend is planned for Stage II)")
