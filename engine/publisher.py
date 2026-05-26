from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .promotion import PromotionDecision, decide_promotion, load_promotion_rules
from .schemas import slugify


def _read_idea_records(root: Path) -> list[dict[str, Any]]:
    path = root / "hypotheses" / "ideas.jsonl"
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _publishability_score(record: dict[str, Any]) -> float:
    return float((record.get("scores") or {}).get("publishability", 0.0))


def _score(record: dict[str, Any], key: str) -> float:
    return float((record.get("scores") or {}).get(key, 0.0))


def _timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def _published_observation_times(root: Path) -> dict[str, float]:
    published: dict[str, float] = {}
    daily_dir = root / "publication" / "daily"
    if not daily_dir.exists():
        return published
    for path in daily_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"Source observation:\s*`([^`]+)`", text)
        if match:
            published[match.group(1)] = max(
                published.get(match.group(1), 0.0),
                path.stat().st_mtime,
            )
    return published


def _audit_times_by_idea(root: Path) -> dict[str, float]:
    path = root / "reviews" / "originality" / "audits.jsonl"
    if not path.exists():
        return {}
    latest: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            audit = json.loads(line)
        except json.JSONDecodeError:
            continue
        idea_id = str(audit.get("idea_id") or "")
        if not idea_id:
            continue
        latest[idea_id] = max(latest.get(idea_id, 0.0), _timestamp(str(audit.get("created_at") or "")))
    return latest


def _frontier_priority_by_idea(root: Path) -> dict[str, float]:
    path = root / "state" / "frontiers.json"
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    priority: dict[str, float] = {}
    for frontier in state.get("frontiers") or []:
        value = float(frontier.get("priority") or 0.0)
        for idea_id in frontier.get("idea_ids") or []:
            priority[str(idea_id)] = max(priority.get(str(idea_id), 0.0), value)
    return priority


def _best_public_record(root: Path) -> tuple[dict[str, Any], PromotionDecision] | None:
    rules = load_promotion_rules()
    records = [
        record
        for record in _read_idea_records(root)
        if record.get("path") and (root / str(record["path"])).exists()
    ]
    if not records:
        return None

    public_records: list[tuple[dict[str, Any], PromotionDecision]] = []
    for record in records:
        decision = decide_promotion(record, rules)
        if decision.public_claim:
            public_records.append((record, decision))

    if not public_records:
        return None

    published_times = _published_observation_times(root)
    audit_times = _audit_times_by_idea(root)
    frontier_priorities = _frontier_priority_by_idea(root)
    eligible: list[tuple[dict[str, Any], PromotionDecision]] = []
    for record, decision in public_records:
        record_path = str(record.get("path") or "")
        idea_id = str(record.get("idea_id") or "")
        published_at = published_times.get(record_path, 0.0)
        audit_at = audit_times.get(idea_id, 0.0)
        if not published_at or audit_at > published_at:
            eligible.append((record, decision))

    if not eligible:
        return None

    return max(
        eligible,
        key=lambda item: (
            frontier_priorities.get(str(item[0].get("idea_id") or ""), 0.0),
            int(item[1].synthesis_ready),
            _score(item[0], "source_reliability"),
            _score(item[0], "counterargument_quality"),
            _publishability_score(item[0]),
            str(item[0].get("created_at", "")),
        ),
    )


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

    selected = _best_public_record(config.root)
    if selected is None:
        raise FileNotFoundError(
            "No unpublished or newly advanced idea records satisfy the public-claim promotion gate."
        )

    record, decision = selected
    latest = config.root / str(record["path"])
    content = latest.read_text(encoding="utf-8")
    title = _title_from_markdown(content, latest.stem)
    claim = _section(content, "Original Claim")
    critique = _section(content, "Critique")
    labels = _section(content, "Epistemic Labels")
    scores = record.get("scores") or {}
    promotion_reasons = "\n".join(f"- {reason}" for reason in decision.reasons)

    today = datetime.now().astimezone().strftime("%Y-%m-%d")
    daily_content = f"""# {today}: {title}

Source observation: `{latest.relative_to(config.root)}`
Promotion stage: {decision.label}

## Finding

{claim}

## Epistemic Status

{labels}

## Promotion Gate

- source_reliability: {float(scores.get("source_reliability", 0.0)):.2f}
- counterargument_quality: {float(scores.get("counterargument_quality", 0.0)):.2f}
- publishability: {float(scores.get("publishability", 0.0)):.2f}

{promotion_reasons}

## Current Critique

{critique}
"""
    daily_path = librarian.write_text(f"publication/daily/{today}-{slugify(title)}.md", daily_content)

    post_text = _clip_at_word(
        f"{title}: {claim} Epistemic status: {decision.label.lower()}, under critique.",
        275,
    )
    x_draft = f"""# X Draft: {title}

Status: queued for human review
Promotion stage: {decision.label}
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
