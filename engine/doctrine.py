from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .promotion import decide_promotion, load_promotion_rules
from .schemas import IdeaRecord, now_local_iso, slugify


TEACHINGS_STORE = "doctrine/teachings.jsonl"
PRACTICES_STORE = "practices/protocols.jsonl"
TESTS_STORE = "tests/tests.jsonl"
COUNCIL_STORE = "doctrine/councils"

TEACHING_STATUSES = {
    "seed",
    "under_dialogue",
    "teaching_ready",
    "practice_linked",
    "revised",
    "weakened",
    "retired",
    "falsified",
}
PRACTICE_STATUSES = {
    "seed",
    "under_dialogue",
    "published",
    "revised",
    "weakened",
    "retired",
    "falsified",
}
TEST_IMPACTS = {
    "pending",
    "strengthens",
    "weakens",
    "breaks",
    "revises",
    "inconclusive",
}


def _stable_id(prefix: str, *parts: str) -> str:
    value = "\n".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(value).hexdigest()[:16]}"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            f"{json.dumps(record, ensure_ascii=True, sort_keys=True)}\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _upsert_by_key(path: Path, record: dict[str, Any], key: str) -> None:
    records = _read_jsonl(path)
    next_records: list[dict[str, Any]] = []
    replaced = False
    for existing in records:
        if existing.get(key) == record.get(key):
            merged = {**existing, **record}
            next_records.append(merged)
            replaced = True
        else:
            next_records.append(existing)
    if not replaced:
        next_records.append(record)
    _write_jsonl(path, next_records)


def _safe_status(value: str, allowed: set[str], fallback: str) -> str:
    normalized = str(value or "").lower().replace("-", "_").strip()
    return normalized if normalized in allowed else fallback


def _today(date: str | None = None) -> str:
    return date or datetime.now().astimezone().date().isoformat()


def write_candidates_from_idea(
    root: Path,
    idea: IdeaRecord,
    *,
    run_id: str,
) -> dict[str, int]:
    librarian = Librarian(root)
    librarian.ensure_workspace()

    created_at = idea.created_at or now_local_iso()
    idea_id = idea.identity()
    counts = {"teachings": 0, "practices": 0, "tests": 0}
    teaching_id = ""

    if idea.teaching_candidate:
        candidate = idea.teaching_candidate
        teaching_id = _stable_id("teach", idea_id, candidate.title, candidate.teaching_line)
        record = {
            "agent": idea.agent,
            "created_at": created_at,
            "dialogue_ids": [],
            "doctrine_claim": candidate.doctrine_claim,
            "falsifying_pressure": candidate.falsifying_pressure,
            "last_run_id": run_id,
            "pressure_survived": candidate.pressure_survived,
            "practice_ids": [],
            "source_basis": idea.source_basis,
            "source_idea_ids": [idea_id],
            "status": _safe_status(candidate.status, TEACHING_STATUSES, "seed"),
            "tags": candidate.tags,
            "target_cohort": candidate.target_cohort,
            "target_human_problem": candidate.target_human_problem,
            "teaching_body": candidate.body,
            "teaching_id": teaching_id,
            "teaching_line": candidate.teaching_line,
            "test_ids": [],
            "title": candidate.title,
            "updated_at": now_local_iso(),
            "version": 1,
        }
        if record["status"] in {"teaching_ready", "practice_linked"}:
            record["status"] = "under_dialogue"
        _upsert_by_key(root / TEACHINGS_STORE, record, "teaching_id")
        counts["teachings"] += 1

    if idea.practice_candidate:
        candidate = idea.practice_candidate
        target_teaching_id = teaching_id or _stable_id("teach", idea_id, idea.title, "implicit")
        practice_id = _stable_id("practice", idea_id, candidate.title, candidate.practice_line)
        record = {
            "agent": idea.agent,
            "caution": candidate.caution,
            "created_at": created_at,
            "duration": candidate.duration,
            "frequency": candidate.frequency,
            "last_run_id": run_id,
            "minimum_attempt": candidate.minimum_attempt,
            "non_fit": candidate.non_fit,
            "notice": candidate.notice,
            "practice_id": practice_id,
            "practice_line": candidate.practice_line,
            "purpose": candidate.purpose,
            "risk_level": candidate.risk_level,
            "source_basis": idea.source_basis,
            "source_idea_ids": [idea_id],
            "status": _safe_status(candidate.status, PRACTICE_STATUSES, "seed"),
            "steps": candidate.steps,
            "tags": candidate.tags,
            "target_cohort": candidate.target_cohort,
            "target_human_problem": candidate.target_human_problem,
            "teaching_id": target_teaching_id,
            "test_ids": [],
            "title": candidate.title,
            "updated_at": now_local_iso(),
            "weakens_if": candidate.weakens_if,
        }
        if record["status"] == "published":
            record["status"] = "under_dialogue"
        _upsert_by_key(root / PRACTICES_STORE, record, "practice_id")
        counts["practices"] += 1

    for index, test in enumerate(idea.tests):
        target_type = test.target_type if test.target_type in {"idea", "teaching", "practice"} else "idea"
        target_id = idea_id if target_type == "idea" else teaching_id or idea_id
        test_id = _stable_id("test", idea_id, test.title or str(index), test.prediction)
        record = {
            "agent": idea.agent,
            "created_at": created_at,
            "impact": test.impact if test.impact in TEST_IMPACTS else "pending",
            "last_run_id": run_id,
            "next_action": test.next_action,
            "prediction": test.prediction,
            "result": test.result or "not run yet",
            "source_basis": idea.source_basis,
            "source_idea_ids": [idea_id],
            "status": test.status or "proposed",
            "target_id": target_id,
            "target_type": target_type,
            "test_id": test_id,
            "test_type": test.test_type or "observational",
            "title": test.title or f"{test.test_type} test",
            "updated_at": now_local_iso(),
        }
        _upsert_by_key(root / TESTS_STORE, record, "test_id")
        counts["tests"] += 1

    if any(counts.values()):
        librarian.append_jsonl(
            "runs/doctrine-events.jsonl",
            {
                "at": now_local_iso(),
                "counts": counts,
                "idea_id": idea_id,
                "run_id": run_id,
                "title": idea.title,
            },
        )

    return counts


def _ideas_by_id(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(record.get("idea_id")): record
        for record in _read_jsonl(root / "hypotheses" / "ideas.jsonl")
        if record.get("idea_id")
    }


def _tests_by_target(root: Path) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in _read_jsonl(root / TESTS_STORE):
        target_id = str(record.get("target_id") or "")
        if not target_id:
            continue
        groups.setdefault(target_id, []).append(record)
    return groups


def _audits_by_idea(root: Path) -> dict[str, dict[str, Any]]:
    audits: dict[str, dict[str, Any]] = {}
    for record in _read_jsonl(root / "reviews" / "originality" / "audits.jsonl"):
        idea_id = str(record.get("idea_id") or "")
        if not idea_id:
            continue
        existing = audits.get(idea_id)
        if not existing or str(record.get("created_at") or "") >= str(existing.get("created_at") or ""):
            audits[idea_id] = record
    return audits


def _has_completed_or_reviewed_test(tests: list[dict[str, Any]]) -> bool:
    for test in tests:
        status = str(test.get("status") or "").lower()
        impact = str(test.get("impact") or "").lower()
        result = str(test.get("result") or "").strip().lower()
        if status == "complete" and impact not in {"weakens", "breaks"}:
            return True
        if result and result not in {"not run yet", "pending"} and impact not in {"weakens", "breaks"}:
            return True
    return False


def _test_pressure(tests: list[dict[str, Any]]) -> str:
    impacts = {str(test.get("impact") or "").lower() for test in tests}
    if "breaks" in impacts:
        return "falsified"
    if "weakens" in impacts:
        return "weakened"
    if "revises" in impacts:
        return "revised"
    return ""


def _audit_pressure(audits: list[dict[str, Any]]) -> str:
    statuses = {str(audit.get("originality_status") or "").lower() for audit in audits}
    if "rejected" in statuses:
        return "falsified"
    if statuses.intersection({"known", "renamed"}):
        return "weakened"
    return ""


def _has_required_fields(record: dict[str, Any], fields: list[str]) -> bool:
    return all(str(record.get(field) or "").strip() for field in fields)


def _candidate_date(record: dict[str, Any]) -> str:
    return str(record.get("created_at") or "")[:10]


def run_doctrine_council(root: Path, *, date: str | None = None) -> Path:
    council_date = _today(date)
    teachings = _read_jsonl(root / TEACHINGS_STORE)
    practices = _read_jsonl(root / PRACTICES_STORE)
    ideas = _ideas_by_id(root)
    tests_by_target = _tests_by_target(root)
    audits_by_idea = _audits_by_idea(root)
    rules = load_promotion_rules()

    promoted_teachings: list[str] = []
    weakened_teachings: list[str] = []
    revised_teachings: list[str] = []
    falsified_teachings: list[str] = []
    updated_teachings: list[dict[str, Any]] = []
    for teaching in teachings:
        if _candidate_date(teaching) != council_date:
            updated_teachings.append(teaching)
            continue
        status = _safe_status(str(teaching.get("status") or ""), TEACHING_STATUSES, "seed")
        if status in {"retired", "falsified"}:
            updated_teachings.append(teaching)
            continue

        source_ids = [str(item) for item in teaching.get("source_idea_ids") or []]
        source_records = [ideas[item] for item in source_ids if item in ideas]
        teaching_tests = tests_by_target.get(str(teaching.get("teaching_id") or ""), [])
        source_tests = [test for item in source_ids for test in tests_by_target.get(item, [])]
        linked_audits = [audits_by_idea[item] for item in source_ids if item in audits_by_idea]
        pressure_status = _test_pressure([*teaching_tests, *source_tests]) or _audit_pressure(linked_audits)
        if pressure_status in {"falsified", "weakened", "revised"}:
            teaching["status"] = pressure_status
            teaching["status_reason"] = "Doctrine council changed status because tests or originality audits applied pressure."
            if pressure_status == "falsified":
                falsified_teachings.append(str(teaching.get("teaching_id")))
            elif pressure_status == "weakened":
                weakened_teachings.append(str(teaching.get("teaching_id")))
            else:
                revised_teachings.append(str(teaching.get("teaching_id")))
            teaching["updated_at"] = now_local_iso()
            updated_teachings.append(teaching)
            continue

        if status not in {"seed", "under_dialogue", "weakened", "revised"}:
            updated_teachings.append(teaching)
            continue

        has_completed_test = _has_completed_or_reviewed_test([*teaching_tests, *source_tests])
        public_sources = [
            record
            for record in source_records
            if decide_promotion(record, rules).public_claim
        ]
        has_multiple_supports = len(public_sources) >= 2 or bool(teaching.get("dialogue_ids"))
        has_pressure = bool(str(teaching.get("falsifying_pressure") or "").strip())
        has_human_target = _has_required_fields(teaching, ["target_human_problem", "target_cohort"])
        has_teaching_quality = _has_required_fields(teaching, ["teaching_body", "teaching_line", "pressure_survived"])
        if has_multiple_supports and has_completed_test and has_pressure and has_human_target and has_teaching_quality:
            teaching["status"] = "teaching_ready"
            teaching["promoted_at"] = now_local_iso()
            promoted_teachings.append(str(teaching.get("teaching_id")))
        else:
            teaching["status"] = "under_dialogue"
        teaching["updated_at"] = now_local_iso()
        updated_teachings.append(teaching)

    promoted_set = set(promoted_teachings)
    published_practices: list[str] = []
    weakened_practices: list[str] = []
    falsified_practices: list[str] = []
    updated_practices: list[dict[str, Any]] = []
    for practice in practices:
        if _candidate_date(practice) != council_date:
            updated_practices.append(practice)
            continue
        status = _safe_status(str(practice.get("status") or ""), PRACTICE_STATUSES, "seed")
        if status in {"retired", "falsified"}:
            updated_practices.append(practice)
            continue
        practice_tests = tests_by_target.get(str(practice.get("practice_id") or ""), [])
        pressure_status = _test_pressure(practice_tests)
        if pressure_status in {"falsified", "weakened", "revised"}:
            practice["status"] = pressure_status
            practice["status_reason"] = "Doctrine council changed status because linked tests applied pressure."
            if pressure_status == "falsified":
                falsified_practices.append(str(practice.get("practice_id")))
            else:
                weakened_practices.append(str(practice.get("practice_id")))
            practice["updated_at"] = now_local_iso()
            updated_practices.append(practice)
            continue
        if status not in {"seed", "under_dialogue", "weakened", "revised"}:
            updated_practices.append(practice)
            continue
        if (
            str(practice.get("teaching_id") or "") in promoted_set
            and str(practice.get("risk_level") or "low") == "low"
            and str(practice.get("weakens_if") or "").strip()
            and _has_required_fields(practice, ["target_human_problem", "target_cohort", "non_fit", "caution"])
        ):
            practice["status"] = "published"
            practice["published_at"] = now_local_iso()
            published_practices.append(str(practice.get("practice_id")))
        else:
            practice["status"] = "under_dialogue"
        practice["updated_at"] = now_local_iso()
        updated_practices.append(practice)

    _write_jsonl(root / TEACHINGS_STORE, updated_teachings)
    _write_jsonl(root / PRACTICES_STORE, updated_practices)

    summary = {
        "created_at": now_local_iso(),
        "date": council_date,
        "falsified_practices": falsified_practices,
        "falsified_teachings": falsified_teachings,
        "published_practices": published_practices,
        "promoted_teachings": promoted_teachings,
        "revised_teachings": revised_teachings,
        "reviewed_practices": [
            str(item.get("practice_id"))
            for item in practices
            if _candidate_date(item) == council_date
        ],
        "reviewed_teachings": [
            str(item.get("teaching_id"))
            for item in teachings
            if _candidate_date(item) == council_date
        ],
        "weakened_practices": weakened_practices,
        "weakened_teachings": weakened_teachings,
    }
    path = root / COUNCIL_STORE / f"{council_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    Librarian(root).append_jsonl("runs/doctrine-council-events.jsonl", summary)
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage Lumenary doctrine and practice records.")
    parser.add_argument("--council", action="store_true", help="Run the end-of-day doctrine council.")
    parser.add_argument("--date", default=None, help="Date to review, YYYY-MM-DD. Defaults to today.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load()
    Librarian(config.root).ensure_workspace()
    if args.council:
        path = run_doctrine_council(config.root, date=args.date)
        print(f"council={path.relative_to(config.root)}")
        return
    raise SystemExit("Nothing to do. Use --council.")


if __name__ == "__main__":
    main()
