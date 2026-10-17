"""User-facing names (product, mascot) loaded from config/branding.toml."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "branding.toml"


@dataclass(frozen=True)
class Branding:
    product_name: str
    mascot_name: str
    tagline: str = ""
    messages: dict[str, str] = field(default_factory=dict)

    def message(self, key: str, **values: str) -> str:
        template = self.messages.get(key, "{mascot}: " + key)
        return template.format(mascot=self.mascot_name, product=self.product_name, **values)


def load_branding(path: Path | str = DEFAULT_PATH) -> Branding:
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return Branding(
        product_name=data["product_name"],
        mascot_name=data["mascot_name"],
        tagline=data.get("tagline", ""),
        messages=dict(data.get("messages", {})),
    )
