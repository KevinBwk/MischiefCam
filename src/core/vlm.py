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


def build_prompt(target: str) -> str:
    return PROMPT_TEMPLATE.format(target=target)


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


def make_backend(cfg: dict) -> VLMBackend:
    kind = cfg.get("backend", "mlx")
    if kind == "fake":
        return FakeVLMBackend()
    if kind == "mlx":
        return MLXVLMBackend(cfg["model"])
    if kind == "probe":
        from .config import resolve
        from .probe import ProbeBackend

        return ProbeBackend(resolve(cfg.get("classifier", "models/classifier.json")))
    raise ValueError(f"Unknown VLM backend {kind!r} (hailo backend is planned for Stage II)")
