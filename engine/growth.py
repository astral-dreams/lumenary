from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .librarian import Librarian
from .schemas import IdeaRecord, IdeaScores, now_local_iso


GROWTH_LEDGER = "publication/growth/growth.jsonl"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clip(value: str, limit: int = 210) -> str:
    clean = _clean_text(value)
    if len(clean) <= limit:
        return clean
    clipped = clean[: limit - 3].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped}..."


def _first_sentence(value: str, limit: int = 210) -> str:
    clean = _clean_text(value)
    sentence = re.match(r"^.*?[.!?](\s|$)", clean)
    return _clip(sentence.group(0).strip() if sentence else clean, limit)


def _score(idea: IdeaRecord) -> float:
    scores = idea.scores
    weighted = (
        scores.publishability * 0.28
        + scores.generativity * 0.24
        + scores.novelty * 0.18
        + scores.counterargument_quality * 0.16
        + scores.source_reliability * 0.14
    )
    return round(weighted, 4)


def _method_source(idea: IdeaRecord) -> str | None:
    for item in idea.source_basis:
        lowered = item.lower()
        if "thinking method source" in lowered:
            return item.split(":", 1)[-1].strip()
    return None


def _protocol_direction(idea: IdeaRecord) -> str | None:
    for item in idea.next_research_directions:
        lowered = item.lower()
        if "protocol" in lowered or "method" in lowered or "practice" in lowered:
            return item
    return None


def _knowledge_item(idea: IdeaRecord) -> str:
    claim = _first_sentence(idea.original_claim)
    new = _first_sentence(idea.why_it_might_be_new)
    return _clip(f"{claim} {new}", 280)


def _method_item(idea: IdeaRecord) -> str:
    direction = _protocol_direction(idea)
    if direction:
        return _clip(f"Next step: {direction}", 240)
    critique = _first_sentence(idea.critique)
    return _clip(f"Open question: {critique}", 240)


def record_growth(
    root: Path,
    *,
    execution_id: str,
    ideas: list[IdeaRecord],
    run_ids: list[str] | None = None,
    created_at: str | None = None,
) -> Path:
    if not ideas:
        raise ValueError("record_growth requires at least one idea.")

    timestamp = created_at or now_local_iso()
    knowledge = [_knowledge_item(idea) for idea in ideas]
    method = [_method_item(idea) for idea in ideas]
    agents = sorted({idea.agent for idea in ideas})
    titles = [idea.title for idea in ideas]
    importance = round(sum(_score(idea) for idea in ideas) / len(ideas), 4)

    record = {
        "agents": agents,
        "created_at": timestamp,
        "date": timestamp[:10],
        "execution_id": execution_id,
        "importance": importance,
        "knowledge": knowledge,
        "method": method,
        "run_ids": run_ids or [execution_id],
        "titles": titles,
    }

    librarian = Librarian(root)
    librarian.ensure_workspace()
    return librarian.upsert_jsonl_by_key(GROWTH_LEDGER, record, key="execution_id")


def _read_idea_records(root: Path) -> list[dict[str, Any]]:
    path = root / "hypotheses" / "ideas.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _idea_from_record(record: dict[str, Any]) -> IdeaRecord:
    scores = record.get("scores") or {}
    return IdeaRecord(
        title=str(record["title"]),
        idea_type=str(record.get("idea_type", "observation")),
        agent=str(record.get("agent", "codex")),
        created_at=str(record.get("created_at") or now_local_iso()),
        source_basis=[str(item) for item in record.get("source_basis", [])],
        original_claim=str(record.get("original_claim", "")),
        why_it_might_be_new=str(record.get("why_it_might_be_new", "")),
        critique=str(record.get("critique", "")),
        epistemic_labels=[str(item) for item in record.get("epistemic_labels", [])],
        scores=IdeaScores(
            novelty=float(scores.get("novelty", 0.0)),
            generativity=float(scores.get("generativity", 0.0)),
            cross_tradition_support=float(scores.get("cross_tradition_support", 0.0)),
            logical_coherence=float(scores.get("logical_coherence", 0.0)),
            explanatory_compression=float(scores.get("explanatory_compression", 0.0)),
            empirical_adjacency=float(scores.get("empirical_adjacency", 0.0)),
            practice_testability=float(scores.get("practice_testability", 0.0)),
            counterargument_quality=float(scores.get("counterargument_quality", 0.0)),
            source_reliability=float(scores.get("source_reliability", 0.0)),
            publishability=float(scores.get("publishability", 0.0)),
        ),
        next_research_directions=[str(item) for item in record.get("next_research_directions", [])],
        status=str(record.get("status", "draft")),
    )


def backfill_growth(root: Path) -> int:
    count = 0
    for record in _read_idea_records(root):
        idea_id = str(record.get("idea_id") or "")
        if not idea_id:
            continue
        idea = _idea_from_record(record)
        record_growth(
            root,
            execution_id=f"backfill-{idea_id}",
            ideas=[idea],
            run_ids=[str(record.get("path") or idea_id)],
            created_at=idea.created_at,
        )
        count += 1
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or backfill Growth records.")
    parser.add_argument("--backfill", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    if args.backfill:
        count = backfill_growth(root)
        print(f"growth_records={count}")


if __name__ == "__main__":
    main()
