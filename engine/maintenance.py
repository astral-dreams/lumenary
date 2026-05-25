from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .schemas import slugify


def _idea_id(record: dict[str, Any]) -> str:
    from hashlib import sha256

    basis = (
        f"{record.get('agent', '')}\n"
        f"{record.get('title', '')}\n"
        f"{record.get('original_claim', '')}"
    ).encode("utf-8")
    return sha256(basis).hexdigest()[:16]


def _observation_path(root: Path, record: dict[str, Any]) -> str | None:
    existing = record.get("path")
    if existing and (root / str(existing)).exists():
        return str(existing)

    agent = str(record.get("agent", "codex"))
    title = str(record.get("title", "untitled"))
    created_at = str(record.get("created_at", ""))
    date = created_at[:10] if len(created_at) >= 10 else "undated"
    candidate = f"observations/{agent}/{date}-{slugify(title)}.md"
    if (root / candidate).exists():
        return candidate
    return None


def dedupe_ideas(config: EngineConfig) -> Path:
    path = config.root / "hypotheses" / "ideas.jsonl"
    if not path.exists():
        return path

    deduped: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        record["idea_id"] = str(record.get("idea_id") or _idea_id(record))
        observation_path = _observation_path(config.root, record)
        if observation_path:
            record["path"] = observation_path

        if record["title"] == "The Interface Invariant Model":
            record["status"] = "seed-fixture"
            basis = record.get("source_basis") or []
            fixture_note = "Offline fixture for smoke tests; not a live research result."
            if fixture_note not in basis:
                record["source_basis"] = [fixture_note, *basis]

        previous = deduped.get(record["idea_id"])
        if previous is None:
            deduped[record["idea_id"]] = record
            continue

        # Prefer live generated records over fixture records, then newer records.
        previous_fixture = previous.get("status") == "seed-fixture"
        current_fixture = record.get("status") == "seed-fixture"
        if previous_fixture and not current_fixture:
            deduped[record["idea_id"]] = record
        elif previous_fixture == current_fixture and str(record.get("created_at", "")) > str(
            previous.get("created_at", "")
        ):
            deduped[record["idea_id"]] = record

    content = "".join(
        f"{json.dumps(record, ensure_ascii=True, sort_keys=True)}\n"
        for record in sorted(deduped.values(), key=lambda item: str(item.get("created_at", "")))
    )
    path.write_text(content, encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Maintain registry files.")
    parser.add_argument(
        "--dedupe-ideas",
        action="store_true",
        help="Deduplicate and backfill hypotheses/ideas.jsonl.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load()
    if args.dedupe_ideas:
        path = dedupe_ideas(config)
        print(f"deduped={path.relative_to(config.root)}")


if __name__ == "__main__":
    main()
