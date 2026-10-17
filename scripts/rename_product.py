"""Rename the product across user-facing files.

Usage:
    uv run python scripts/rename_product.py "MischiefCam" "NewName" [--dry-run]

Touches: config/branding.toml, README.md, docs/**/*.md, notes/**/*.md, pyproject.toml (project name, lower-case).
Code is unaffected: the Python package is named `core` and reads names from config/branding.toml.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def targets() -> list[Path]:
    files = [ROOT / "config" / "branding.toml", ROOT / "README.md", ROOT / "pyproject.toml"]
    for folder in ("docs", "notes"):
        files += sorted((ROOT / folder).rglob("*.md"))
    return [f for f in files if f.exists()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    slug_old, slug_new = re.sub(r"\W", "", args.old).lower(), re.sub(r"\W", "", args.new).lower()
    changed = 0
    for path in targets():
        text = path.read_text(encoding="utf-8")
        new = text.replace(args.old, args.new)
        if path.name == "pyproject.toml":
            new = new.replace(f'name = "{slug_old}"', f'name = "{slug_new}"')
        if new != text:
            changed += 1
            print(f"{'would update' if args.dry_run else 'updated'}: {path.relative_to(ROOT)}")
            if not args.dry_run:
                path.write_text(new, encoding="utf-8")
        new_name = path.name.replace(args.old, args.new)
        if new_name != path.name:
            print(f"{'would rename' if args.dry_run else 'renamed'}: {path.name} -> {new_name}")
            if not args.dry_run:
                path.rename(path.with_name(new_name))
    print(f"{changed} file(s) {'would change' if args.dry_run else 'changed'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
