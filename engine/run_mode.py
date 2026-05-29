from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .schemas import now_local_iso


RUN_MODES = {
    "discovery": {
        "label": "Discovery",
        "instruction": (
            "Ground the run in sources. Add or use source pressure, close-read primary material, "
            "and produce a finding that opens a stronger doctrine or test question."
        ),
    },
    "doctrine": {
        "label": "Doctrine",
        "instruction": (
            "Ask what Lumenary now holds. Strengthen, narrow, weaken, or revise a teaching candidate, "
            "and name the pressure that would break it."
        ),
    },
    "practice": {
        "label": "Practice",
        "instruction": (
            "Derive or challenge a low-risk practice from an existing teaching candidate. Name the target "
            "human problem, the non-fit case, safety risks, and what would weaken the protocol."
        ),
    },
    "critique": {
        "label": "Critique",
        "instruction": (
            "Hunt for anomalies, near-duplicates, prior art, and failures. The best output may weaken, "
            "retire, or sharply narrow an existing claim."
        ),
    },
    "originality_audit": {
        "label": "Originality Audit",
        "instruction": (
            "Treat novelty as unproven. Search for close prior arguments, compare the exact claim, and "
            "state what remains original only after the audit."
        ),
    },
}


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


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


def _days_since(value: str | None) -> float:
    if not value:
        return 999.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 999.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds() / 86400)


def _latest_created(records: list[dict[str, Any]]) -> str | None:
    values = [str(record.get("created_at") or record.get("updated_at") or "") for record in records]
    values = [value for value in values if value]
    return max(values) if values else None


def _audit_statuses(root: Path) -> dict[str, str]:
    statuses: dict[str, str] = {}
    latest: dict[str, str] = {}
    for audit in _read_jsonl(root / "reviews" / "originality" / "audits.jsonl"):
        idea_id = str(audit.get("idea_id") or "")
        if not idea_id:
            continue
        created_at = str(audit.get("created_at") or "")
        if idea_id not in latest or created_at >= latest[idea_id]:
            latest[idea_id] = created_at
            statuses[idea_id] = str(audit.get("originality_status") or "")
    return statuses


def _pressure_metrics(root: Path) -> dict[str, Any]:
    ideas = _read_jsonl(root / "hypotheses" / "ideas.jsonl")
    teachings = _read_jsonl(root / "doctrine" / "teachings.jsonl")
    practices = _read_jsonl(root / "practices" / "protocols.jsonl")
    tests = _read_jsonl(root / "tests" / "tests.jsonl")
    sources = _read_jsonl(root / "sources" / "sources_index.jsonl")
    frontiers = _read_json(root / "state" / "frontiers.json", {"frontiers": []}).get("frontiers", [])
    statuses = _audit_statuses(root)

    incomplete_audits = sum(1 for idea in ideas if statuses.get(str(idea.get("idea_id"))) in {"", "audit_incomplete"})
    pending_tests = sum(1 for test in tests if str(test.get("status") or "proposed") in {"proposed", "running"})
    weak_tests = sum(1 for test in tests if str(test.get("impact") or "") in {"weakens", "breaks"})
    under_dialogue_teachings = [
        teaching for teaching in teachings if str(teaching.get("status") or "") in {"seed", "under_dialogue", "weakened"}
    ]
    ready_teachings = [
        teaching for teaching in teachings if str(teaching.get("status") or "") in {"teaching_ready", "practice_linked"}
    ]
    published_practices_by_teaching = {
        str(practice.get("teaching_id"))
        for practice in practices
        if str(practice.get("status") or "") == "published"
    }
    ready_without_practice = [
        teaching for teaching in ready_teachings if str(teaching.get("teaching_id") or "") not in published_practices_by_teaching
    ]
    missing_source_frontiers = sum(len(frontier.get("missing_sources") or []) for frontier in frontiers)
    high_priority_frontier = max((float(frontier.get("priority") or 0.0) for frontier in frontiers), default=0.0)
    latest_idea_age = _days_since(_latest_created(ideas))
    latest_source_age = _days_since(_latest_created(sources))

    return {
        "frontier_count": len(frontiers),
        "high_priority_frontier": high_priority_frontier,
        "idea_count": len(ideas),
        "incomplete_audits": incomplete_audits,
        "latest_idea_age_days": round(latest_idea_age, 2),
        "latest_source_age_days": round(latest_source_age, 2),
        "missing_source_frontiers": missing_source_frontiers,
        "pending_tests": pending_tests,
        "ready_teachings_without_practice": len(ready_without_practice),
        "source_count": len(sources),
        "teaching_pressure_count": len(under_dialogue_teachings),
        "weak_tests": weak_tests,
    }


def select_run_mode(root: Path, *, requested: str = "auto", focus: str = "") -> dict[str, Any]:
    requested = (requested or "auto").strip().lower().replace("-", "_")
    metrics = _pressure_metrics(root)

    if requested in RUN_MODES:
        mode = requested
        reason = f"Mode forced by runtime argument: {requested}."
    else:
        scores = {
            "practice": metrics["ready_teachings_without_practice"] * 2.0,
            "doctrine": metrics["teaching_pressure_count"] * 0.35 + metrics["weak_tests"] * 0.8,
            "critique": metrics["pending_tests"] * 0.08 + metrics["weak_tests"] * 1.2,
            "originality_audit": metrics["incomplete_audits"] * 0.25,
            "discovery": (
                metrics["missing_source_frontiers"] * 0.25
                + metrics["high_priority_frontier"] * 0.8
                + min(1.0, metrics["latest_source_age_days"] / 14)
                + min(1.0, metrics["latest_idea_age_days"] / 2)
            ),
        }
        tie_breaker = {
            "practice": 4,
            "doctrine": 3,
            "critique": 2,
            "originality_audit": 1,
            "discovery": 0,
        }
        mode = max(scores, key=lambda key: (scores[key], tie_breaker[key]))
        reason = (
            f"Selected by pressure scores: "
            + ", ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
            + "."
        )

    mode_def = RUN_MODES[mode]
    record = {
        "focus": focus,
        "instruction": mode_def["instruction"],
        "label": mode_def["label"],
        "metrics": metrics,
        "mode": mode,
        "reason": reason,
        "selected_at": now_local_iso(),
    }
    write_run_mode(root, record)
    return record


def mode_prompt(record: dict[str, Any]) -> str:
    metrics = record.get("metrics") or {}
    return "\n".join(
        [
            f"## Selected Run Mode: {record.get('label')}",
            "",
            str(record.get("instruction") or ""),
            "",
            f"Selection reason: {record.get('reason')}",
            "",
            "Current pressure metrics:",
            *[f"- {key}: {value}" for key, value in sorted(metrics.items())],
        ]
    )


def write_run_mode(root: Path, record: dict[str, Any]) -> None:
    state_dir = root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "current_run_mode.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (state_dir / "current_run_mode.md").write_text(mode_prompt(record) + "\n", encoding="utf-8")

    events_path = root / "runs" / "run-mode-events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
