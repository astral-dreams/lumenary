from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "promotion-rules.json"
STAGE_ORDER = ("review_candidate", "public_claim", "synthesis_ready")


@dataclass(frozen=True)
class PromotionDecision:
    stage: str
    label: str
    public_claim: bool
    synthesis_ready: bool
    reasons: list[str]


def load_promotion_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _score(record: dict[str, Any], key: str) -> float:
    return float((record.get("scores") or {}).get(key, 0.0))


def _source_count(record: dict[str, Any]) -> int:
    basis = record.get("source_basis") or []
    return len([item for item in basis if str(item).strip()])


def _stage_failures(record: dict[str, Any], stage: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ("source_reliability", "counterargument_quality", "publishability"):
        threshold = float(stage.get(key, 1.0))
        value = _score(record, key)
        if value < threshold:
            failures.append(f"{key} {value:.2f} below {threshold:.2f}")

    minimum_sources = int(stage.get("min_source_basis_items", 0))
    count = _source_count(record)
    if count < minimum_sources:
        failures.append(f"source_basis count {count} below {minimum_sources}")

    return failures


def decide_promotion(
    record: dict[str, Any], rules: dict[str, Any] | None = None
) -> PromotionDecision:
    rules = rules or load_promotion_rules()
    blocked_statuses = set(rules.get("blocked_statuses") or [])
    blocked_labels = set(rules.get("blocked_epistemic_labels") or [])
    status = str(record.get("status") or "draft")
    labels = {str(label) for label in record.get("epistemic_labels") or []}

    blocker_reasons: list[str] = []
    if status in blocked_statuses:
        blocker_reasons.append(f"blocked status: {status}")
    blocked_label_hits = sorted(labels.intersection(blocked_labels))
    for label in blocked_label_hits:
        blocker_reasons.append(f"blocked epistemic label: {label}")
    if blocker_reasons:
        return PromotionDecision(
            stage="draft",
            label="Draft",
            public_claim=False,
            synthesis_ready=False,
            reasons=blocker_reasons,
        )

    stages = rules.get("stages") or {}
    selected = "draft"
    selected_label = "Draft"
    selected_reasons = _stage_failures(record, stages.get("review_candidate", {}))

    for stage_name in STAGE_ORDER:
        stage = stages.get(stage_name) or {}
        failures = _stage_failures(record, stage)
        if failures:
            if selected == "draft":
                selected_reasons = failures
            else:
                selected_reasons = [
                    f"meets {selected_label} thresholds",
                    *[f"next gate: {failure}" for failure in failures],
                ]
            break
        selected = stage_name
        selected_label = str(stage.get("label") or stage_name.replace("_", " ").title())
        selected_reasons = [f"meets {selected_label} thresholds"]

    return PromotionDecision(
        stage=selected,
        label=selected_label,
        public_claim=selected in {"public_claim", "synthesis_ready"},
        synthesis_ready=selected == "synthesis_ready",
        reasons=selected_reasons,
    )
