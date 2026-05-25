from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from .config import EngineConfig
from .librarian import Librarian
from .schemas import slugify


def _publishability_score(path: Path) -> float:
    content = path.read_text(encoding="utf-8")
    match = re.search(r"^- publishability:\s*([0-9.]+)\s*$", content, re.MULTILINE)
    if not match:
        return 0.0
    return float(match.group(1))


def _best_markdown(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda path: (_publishability_score(path), path.stat().st_mtime))


def _title_from_markdown(content: str, fallback: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _section(content: str, heading: str) -> str:
    marker = f"## {heading}"
    if marker not in content:
        return ""
    tail = content.split(marker, 1)[1].strip()
    next_heading = tail.find("\n## ")
    if next_heading >= 0:
        tail = tail[:next_heading].strip()
    return tail


def _clip_at_word(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    clipped = clean[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped}..."


def generate_daily_update(config: EngineConfig) -> tuple[Path, Path]:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    observation_paths = list((config.root / "observations").glob("*/*.md"))
    latest = _best_markdown(observation_paths)
    if latest is None:
        raise FileNotFoundError("No observations found for publication.")

    content = latest.read_text(encoding="utf-8")
    title = _title_from_markdown(content, latest.stem)
    claim = _section(content, "Original Claim")
    critique = _section(content, "Critique")
    labels = _section(content, "Epistemic Labels")

    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    daily_content = f"""# {today}: {title}

Source observation: `{latest.relative_to(config.root)}`

## Finding

{claim}

## Epistemic Status

{labels}

## Current Critique

{critique}
"""
    daily_path = librarian.write_text(f"publication/daily/{today}-{slugify(title)}.md", daily_content)

    post_text = _clip_at_word(
        f"{title}: {claim} Epistemic status: draft, under critique.",
        275,
    )
    x_draft = f"""# X Draft: {title}

Status: draft
Source: `{daily_path.relative_to(config.root)}`

{post_text}
"""
    x_path = librarian.write_text(f"publication/x/queue/{today}-{slugify(title)}.md", x_draft)
    librarian.append_exploration_log(
        f"- Published daily draft `{daily_path.relative_to(config.root)}`.\n"
        f"- Created X draft `{x_path.relative_to(config.root)}`."
    )
    return daily_path, x_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate daily publication artifacts.")
    return parser.parse_args()


def main() -> None:
    parse_args()
    config = EngineConfig.load()
    daily_path, x_path = generate_daily_update(config)
    print(f"daily={daily_path.relative_to(config.root)}")
    print(f"x_draft={x_path.relative_to(config.root)}")


if __name__ == "__main__":
    main()
