from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .schemas import IdeaRecord, now_local_iso


TESTS_STORE = "tests/tests.jsonl"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _stable_id(*parts: str) -> str:
    return "test_" + hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


def _idea_id(record: IdeaRecord | dict[str, Any]) -> str:
    if isinstance(record, IdeaRecord):
        return record.identity()
    return str(record.get("idea_id") or "")


def _title(record: IdeaRecord | dict[str, Any]) -> str:
    return record.title if isinstance(record, IdeaRecord) else str(record.get("title") or "Untitled")


def _agent(record: IdeaRecord | dict[str, Any]) -> str:
    return record.agent if isinstance(record, IdeaRecord) else str(record.get("agent") or "codex")


def _created_at(record: IdeaRecord | dict[str, Any]) -> str:
    return record.created_at if isinstance(record, IdeaRecord) else str(record.get("created_at") or now_local_iso())


def _source_basis(record: IdeaRecord | dict[str, Any]) -> list[str]:
    value = record.source_basis if isinstance(record, IdeaRecord) else record.get("source_basis")
    return [str(item) for item in value or [] if str(item).strip()]


def _source_ids(record: IdeaRecord | dict[str, Any]) -> list[str]:
    return [_idea_id(record)] if _idea_id(record) else []


def _prediction_base(record: IdeaRecord | dict[str, Any]) -> str:
    if isinstance(record, IdeaRecord):
        return record.original_claim
    return str(record.get("original_claim") or record.get("doctrine_claim") or record.get("purpose") or _title(record))


def _record(
    *,
    source: IdeaRecord | dict[str, Any],
    target_id: str,
    target_type: str,
    test_type: str,
    title: str,
    prediction: str,
    next_action: str,
    run_id: str,
) -> dict[str, Any]:
    return {
        "agent": _agent(source),
        "created_at": _created_at(source),
        "impact": "pending",
        "last_run_id": run_id,
        "next_action": next_action,
        "prediction": prediction,
        "result": "not run yet",
        "source_basis": _source_basis(source),
        "source_idea_ids": _source_ids(source),
        "status": "proposed",
        "target_id": target_id,
        "target_type": target_type,
        "test_id": _stable_id(target_id, target_type, test_type, title, prediction),
        "test_type": test_type,
        "title": title,
        "updated_at": now_local_iso(),
    }


def _upsert(records: list[dict[str, Any]], record: dict[str, Any]) -> bool:
    for index, existing in enumerate(records):
        if existing.get("test_id") == record.get("test_id"):
            merged = {**existing, **record, "created_at": existing.get("created_at") or record["created_at"]}
            records[index] = merged
            return False
    records.append(record)
    return True


def _target_has(records: list[dict[str, Any]], target_id: str, test_type: str) -> bool:
    return any(
        str(record.get("target_id") or "") == target_id and str(record.get("test_type") or "") == test_type
        for record in records
    )


def ensure_test_records(
    root: Path,
    ideas: list[IdeaRecord] | list[dict[str, Any]],
    *,
    execution_id: str,
    run_ids: list[str] | None = None,
) -> int:
    path = root / TESTS_STORE
    records = _read_jsonl(path)
    created = 0

    run_id = ",".join(run_ids or [execution_id])
    for idea in ideas:
        idea_id = _idea_id(idea)
        if not idea_id:
            continue
        claim = _prediction_base(idea)
        title = _title(idea)

        candidates = [
            _record(
                source=idea,
                target_id=idea_id,
                target_type="idea",
                test_type="prior-art",
                title=f"Prior-art check: {title}",
                prediction=(
                    "If this claim is genuinely new, exact searches should find near-neighbors but not the same "
                    "structural argument. If the same argument appears, novelty should be lowered."
                ),
                next_action="Search for the exact structural claim in scholarship, not only the broad topic.",
                run_id=run_id,
            ),
            _record(
                source=idea,
                target_id=idea_id,
                target_type="idea",
                test_type="falsification-attempt",
                title=f"Break test: {title}",
                prediction=(
                    f"If the claim is right, the pattern should survive a strong anomaly search against: {claim[:180]}. "
                    "If a primary source or practitioner report breaks the pattern, revise or weaken the claim."
                ),
                next_action="Find one text, practice report, or tradition that should not fit, then test it directly.",
                run_id=run_id,
            ),
            _record(
                source=idea,
                target_id=idea_id,
                target_type="idea",
                test_type="cross-domain",
                title=f"Cross-domain test: {title}",
                prediction=(
                    "If the structure is real and not only a restatement, it should make a useful prediction in "
                    "another domain such as psychology, ethics, physics interpretation, or organizational life."
                ),
                next_action="Translate the structure into one outside domain and name what it predicts there.",
                run_id=run_id,
            ),
        ]
        for candidate in candidates:
            if _target_has(records, idea_id, str(candidate["test_type"])):
                continue
            if _upsert(records, candidate):
                created += 1

    if created:
        _write_jsonl(path, records)

    event_path = root / "runs" / "test-record-events.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "at": now_local_iso(),
                    "created": created,
                    "execution_id": execution_id,
                    "idea_ids": [_idea_id(idea) for idea in ideas],
                    "run_ids": run_ids or [],
                },
                ensure_ascii=True,
                sort_keys=True,
            )
            + "\n"
        )
    return created


def backfill_test_records(root: Path) -> int:
    ideas = _read_jsonl(root / "hypotheses" / "ideas.jsonl")
    return ensure_test_records(root, ideas, execution_id="test-record-backfill", run_ids=["test-record-backfill"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ensure Lumenary ideas have proposed test records.")
    parser.add_argument("--backfill", action="store_true", help="Backfill proposed tests for existing ideas.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    if args.backfill:
        print(f"created={backfill_test_records(root)}")
        return
    raise SystemExit("Nothing to do. Use --backfill.")


if __name__ == "__main__":
    main()
