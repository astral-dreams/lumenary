"""Build and select live research frontiers for Lumenary."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .librarian import Librarian
from .promotion import decide_promotion, load_promotion_rules
from .schemas import now_local_iso, slugify


FRONTIER_STATE = "state/frontiers.json"
FRONTIER_MARKDOWN = "state/frontiers.md"
NEXT_FRONTIER_PROMPT = "state/next_frontier_prompt.md"
FRONTIER_EVENTS = "runs/frontier-events.jsonl"
FRONTIER_RULES = "config/frontier-rules.json"
DIALOGUE_OUTCOMES = "reviews/dialogues/outcomes.jsonl"

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "has",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}

DEFAULT_FRONTIER_RULES: dict[str, Any] = {
    "version": "default",
    "topics": [
        {
            "id": "frontier-translation-strain",
            "title": "Translation strain as a test of convergence",
            "keywords": ["translation strain", "convergence", "bridge", "comparison", "load test"],
        },
        {
            "id": "frontier-inferential-gap",
            "title": "Inferential policy after objectless awareness",
            "keywords": [
                "inferential gap",
                "burden of proof",
                "objectless awareness",
                "atman",
                "anatta",
                "witness",
                "self-luminosity",
            ],
        },
        {
            "id": "frontier-remainder-pressure",
            "title": "Remainder pressure after self-negation",
            "keywords": ["remainder", "residue", "negation", "self-negation", "protected variable", "minimum self"],
        },
        {
            "id": "frontier-method-reckoning",
            "title": "What a method does with its own authority",
            "keywords": ["method", "licensed training", "reckoning", "authority", "ladder", "raft", "self-canceling"],
        },
        {
            "id": "frontier-gap-report",
            "title": "How silence becomes evidence after the gap",
            "keywords": ["gap report", "post-gap", "silence", "cessation", "deep sleep", "objectless", "memory"],
        },
        {
            "id": "frontier-attention-custody",
            "title": "Where freed attention is allowed to rest",
            "keywords": ["attention", "custody", "unclaimed attention", "receiver", "revelation", "interruption"],
        },
        {
            "id": "frontier-effort-and-practice",
            "title": "The boundary between effort and gift",
            "keywords": ["effort", "practice", "attainment", "produce", "training"],
        },
        {
            "id": "frontier-love-and-knowing",
            "title": "Love as a way of knowing",
            "keywords": ["love", "longing", "devotional", "beloved", "relation", "second-person"],
        },
        {
            "id": "frontier-verification",
            "title": "How insight is verified and overruled",
            "keywords": ["verification", "appeal court", "judge", "certify", "proof", "authority"],
        },
    ],
    "priority_weights": {
        "strongest_generativity": 0.22,
        "audit_pressure": 0.18,
        "public_value": 0.16,
        "unresolved_anomaly": 0.14,
        "source_gap": 0.12,
        "cross_agent_signal": 0.10,
        "recency": 0.08,
        "duplicate_penalty": 0.18,
        "cooldown_penalty": 0.12,
    },
    "audit_status_weights": {
        "audit_incomplete": 0.95,
        "known": 0.32,
        "renamed": 0.38,
        "extended": 0.72,
        "novel_synthesis": 0.86,
        "candidate_discovery": 0.90,
        "strong_original_contribution": 0.82,
        "rejected": 0.15,
        "default": 0.55,
        "none": 0.82,
    },
    "selection": {
        "cooldown_penalty": 0.35,
        "duplicate_penalty": 0.70,
        "exploration_bonus": 0.09,
        "exploration_generativity_floor": 0.72,
        "exploration_novelty_floor": 0.66,
        "public_value_bonus": 0.08,
        "single_agent_signal": 0.55,
        "source_instruction_bonus": 0.22,
        "source_reliability_target": 0.82,
        "unresolved_anomaly_default": 0.45,
    },
    "limits": {
        "blockers": 3,
        "closest_prior_art": 3,
        "core_claim_clip": 460,
        "cross_domain_tests": 2,
        "falsifiable_tests": 3,
        "instructions": 7,
        "missing_sources": 5,
        "next_prompt_clip": 720,
        "open_anomalies": 3,
        "practitioner_tests": 3,
        "prior_art_clip": 180,
        "text_clip": 260,
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_frontier_rules(root: Path) -> dict[str, Any]:
    path = root / FRONTIER_RULES
    if not path.exists():
        return DEFAULT_FRONTIER_RULES
    try:
        configured = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_FRONTIER_RULES
    return _deep_merge(DEFAULT_FRONTIER_RULES, configured)


def _limit(rules: dict[str, Any], key: str) -> int:
    return int((rules.get("limits") or {}).get(key, DEFAULT_FRONTIER_RULES["limits"][key]))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def _clean(value: Any, *, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.replace("\u2014", ":").replace("\u2013", "-")
    text = text.encode("ascii", "ignore").decode("ascii")
    if limit and len(text) > limit:
        clipped = text[: limit - 3].rsplit(" ", 1)[0].rstrip(".,;:")
        return f"{clipped}..."
    return text


def _score(record: dict[str, Any], key: str) -> float:
    try:
        return float((record.get("scores") or {}).get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _iso_timestamp(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def _title_words(title: str) -> list[str]:
    return [
        word
        for word in re.findall(r"[a-z0-9]+", title.lower())
        if len(word) > 2 and word not in STOPWORDS
    ]


def _fallback_topic(record: dict[str, Any]) -> dict[str, Any]:
    words = _title_words(str(record.get("title") or "frontier"))[:5]
    label = " ".join(word.capitalize() for word in words) or "Untitled Frontier"
    return {
        "id": f"frontier-{slugify('-'.join(words) or label)}",
        "title": label,
        "keywords": words,
        "configured": False,
    }


def _audit_text(audit: dict[str, Any] | None) -> str:
    if not audit:
        return ""
    parts: list[str] = [
        str(audit.get("title") or ""),
        str(audit.get("exact_claim") or ""),
        str(audit.get("unlike_statement") or ""),
        str(audit.get("novelty_adjustment") or ""),
    ]
    parts.extend(str(item) for item in audit.get("claim_units") or [])
    parts.extend(str(item) for item in audit.get("next_loop_instructions") or [])
    for neighbor in audit.get("near_neighbors") or []:
        parts.extend(
            [
                str(neighbor.get("source") or ""),
                str(neighbor.get("overlap") or ""),
                str(neighbor.get("difference") or ""),
            ]
        )
    return " ".join(parts)


def _record_haystack(record: dict[str, Any], audit: dict[str, Any] | None) -> str:
    parts = [
        record.get("title") or "",
        record.get("original_claim") or "",
        record.get("why_it_might_be_new") or "",
        record.get("critique") or "",
        " ".join(record.get("source_basis") or []),
        " ".join(record.get("next_research_directions") or []),
        _audit_text(audit),
    ]
    return " ".join(str(part) for part in parts).lower()


def _topic_for(
    record: dict[str, Any],
    audit: dict[str, Any] | None,
    rules: dict[str, Any],
) -> dict[str, Any]:
    haystack = _record_haystack(record, audit)
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, topic in enumerate(rules.get("topics") or []):
        score = 0
        for keyword in topic.get("keywords") or []:
            if keyword in haystack:
                score += max(1, len(keyword.split()))
        if score:
            ranked.append((score, -index, {**topic, "configured": True}))
    if ranked:
        return sorted(ranked, reverse=True)[0][2]
    return _fallback_topic(record)


def _latest_audits_by_idea(root: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for audit in _read_jsonl(root / "reviews" / "originality" / "audits.jsonl"):
        idea_id = str(audit.get("idea_id") or "")
        if not idea_id:
            continue
        existing = latest.get(idea_id)
        if not existing:
            latest[idea_id] = audit
            continue
        if existing.get("originality_status") == "audit_incomplete" and audit.get("originality_status") != "audit_incomplete":
            latest[idea_id] = audit
            continue
        if _iso_timestamp(str(audit.get("created_at") or "")) > _iso_timestamp(str(existing.get("created_at") or "")):
            latest[idea_id] = audit
    return latest


def _publication_paths(root: Path) -> dict[str, dict[str, Any]]:
    posts: dict[str, dict[str, Any]] = {}
    daily_dir = root / "publication" / "daily"
    if not daily_dir.exists():
        return posts
    for path in sorted(daily_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r"Source observation:\s*`([^`]+)`", text)
        if not match:
            continue
        source_path = match.group(1)
        posts[source_path] = {
            "path": str(path.relative_to(root)),
            "source_path": source_path,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        }
    return posts


def _dialogue_outcomes_by_idea(root: Path) -> dict[str, list[dict[str, Any]]]:
    outcomes: dict[str, list[dict[str, Any]]] = {}
    for record in _read_jsonl(root / DIALOGUE_OUTCOMES):
        for idea_id in record.get("idea_ids") or []:
            if not idea_id:
                continue
            outcomes.setdefault(str(idea_id), []).append(record)
    return outcomes


def _apply_dialogue_pressure(
    frontier: dict[str, Any],
    outcomes_by_idea: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    outcomes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idea_id in frontier.get("idea_ids") or []:
        for outcome in outcomes_by_idea.get(str(idea_id), []):
            dialogue_id = str(outcome.get("dialogue_id") or "")
            if not dialogue_id or dialogue_id in seen:
                continue
            seen.add(dialogue_id)
            outcomes.append(outcome)
    if not outcomes:
        frontier["dialogue_ids"] = []
        frontier["dialogue_outcomes"] = []
        frontier["dialogue_count"] = 0
        return frontier

    labels = [str(outcome.get("outcome") or "unknown") for outcome in outcomes]
    boost = 0.0
    if any(label in {"convergence", "revision", "candidate_transcendence"} for label in labels):
        boost += 0.04
    if any(label == "standoff" for label in labels):
        boost += 0.02
    if any(label == "demolition" for label in labels):
        boost -= 0.12
    frontier["priority"] = round(max(0.0, min(1.0, float(frontier.get("priority") or 0.0) + boost)), 4)
    frontier["dialogue_ids"] = sorted(seen)
    frontier["dialogue_outcomes"] = sorted(set(labels))
    frontier["dialogue_count"] = len(outcomes)

    questions = [
        _clean(outcome.get("new_frontier_question"), limit=260)
        for outcome in outcomes
        if outcome.get("new_frontier_question")
    ]
    existing_anomalies = list(frontier.get("open_anomalies") or [])
    for question in questions:
        if question and question not in existing_anomalies:
            existing_anomalies.append(question)
    frontier["open_anomalies"] = existing_anomalies[:5]
    if labels and "dialogue pressure" not in frontier.get("why_now", ""):
        frontier["why_now"] = f"{frontier.get('why_now', '')}; dialogue pressure".strip("; ")
    return frontier


def _latest(items: list[str], limit: int, *, clip: int = 260) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        clean = _clean(item, limit=clip)
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _frontier_action(audits: list[dict[str, Any]], ideas: list[dict[str, Any]], published: bool) -> tuple[str, str]:
    statuses = {str(audit.get("originality_status") or "") for audit in audits}
    instructions = " ".join(
        str(item)
        for audit in audits
        for item in audit.get("next_loop_instructions") or []
    ).lower()
    directions = " ".join(
        str(item)
        for idea in ideas
        for item in idea.get("next_research_directions") or []
    ).lower()
    combined = f"{instructions} {directions}"

    if "audit_incomplete" in statuses or not audits:
        return "complete_audit", "source_grounding"
    if statuses and statuses.issubset({"known", "renamed"}):
        return "merge_or_retire", "probe"
    if "rubric" in combined or "code " in combined or "coding" in combined:
        return "build_rubric", "rubric"
    if "close-read" in combined or "search" in combined or "source" in combined or "translation" in combined:
        return "source_ground", "source_grounding"
    if "practitioner" in combined or "ask " in combined or "interview" in combined:
        return "practitioner_test", "practitioner_test"
    if "anomaly" in combined or "falsif" in combined or "weaken" in combined:
        return "falsify", "probe"
    if not published:
        return "publish", "publication"
    return "advance", "probe"


def _audit_pressure(audits: list[dict[str, Any]], rules: dict[str, Any]) -> float:
    weights = rules.get("audit_status_weights") or {}
    if not audits:
        return float(weights.get("none", 0.82))
    default = float(weights.get("default", 0.55))
    return max(float(weights.get(str(audit.get("originality_status") or ""), default)) for audit in audits)


def _recency_score(records: list[dict[str, Any]], audits: list[dict[str, Any]]) -> float:
    latest = max(
        [
            *[_iso_timestamp(str(record.get("created_at") or "")) for record in records],
            *[_iso_timestamp(str(audit.get("created_at") or "")) for audit in audits],
            0.0,
        ]
    )
    if not latest:
        return 0.35
    age_days = max(0.0, (datetime.now().astimezone().timestamp() - latest) / 86400)
    return max(0.18, min(1.0, 1.0 / (1.0 + age_days)))


def _source_gap_score(
    records: list[dict[str, Any]],
    audits: list[dict[str, Any]],
    rules: dict[str, Any],
) -> float:
    selection = rules.get("selection") or {}
    reliability = max([_score(record, "source_reliability") for record in records] or [0.0])
    instruction_text = " ".join(
        str(item)
        for audit in audits
        for item in audit.get("next_loop_instructions") or []
    ).lower()
    gap = max(0.0, float(selection.get("source_reliability_target", 0.82)) - reliability)
    if "source" in instruction_text or "close-read" in instruction_text or "search" in instruction_text:
        gap += float(selection.get("source_instruction_bonus", 0.22))
    return min(1.0, gap)


def _priority(
    records: list[dict[str, Any]],
    audits: list[dict[str, Any]],
    *,
    agents: list[str],
    publication_paths: list[str],
    rules: dict[str, Any],
    topic: dict[str, Any],
) -> float:
    weights = rules.get("priority_weights") or {}
    selection = rules.get("selection") or {}
    strongest_generativity = max([_score(record, "generativity") for record in records] or [0.0])
    strongest_novelty = max([_score(record, "novelty") for record in records] or [0.0])
    strongest_publishability = max([_score(record, "publishability") for record in records] or [0.0])
    public_value = min(1.0, strongest_publishability + float(selection.get("public_value_bonus", 0.08)))
    unresolved_anomaly = (
        1.0
        if any((audit.get("anomaly_probe") or {}).get("anomaly_candidate") for audit in audits)
        else float(selection.get("unresolved_anomaly_default", 0.45))
    )
    source_gap = _source_gap_score(records, audits, rules)
    cross_agent = 1.0 if len(set(agents)) > 1 else float(selection.get("single_agent_signal", 0.55))
    recency = _recency_score(records, audits)
    statuses = {str(audit.get("originality_status") or "") for audit in audits}
    duplicate_penalty = float(selection.get("duplicate_penalty", 0.7)) if statuses.intersection({"known", "renamed"}) else 0.0
    cooldown_penalty = float(selection.get("cooldown_penalty", 0.35)) if publication_paths and not source_gap else 0.0
    value = (
        float(weights.get("strongest_generativity", 0.22)) * strongest_generativity
        + float(weights.get("audit_pressure", 0.18)) * _audit_pressure(audits, rules)
        + float(weights.get("public_value", 0.16)) * public_value
        + float(weights.get("unresolved_anomaly", 0.14)) * unresolved_anomaly
        + float(weights.get("source_gap", 0.12)) * source_gap
        + float(weights.get("cross_agent_signal", 0.10)) * cross_agent
        + float(weights.get("recency", 0.08)) * recency
        - float(weights.get("duplicate_penalty", 0.18)) * duplicate_penalty
        - float(weights.get("cooldown_penalty", 0.12)) * cooldown_penalty
    )
    if not topic.get("configured"):
        novelty_floor = float(selection.get("exploration_novelty_floor", 0.66))
        generativity_floor = float(selection.get("exploration_generativity_floor", 0.72))
        if strongest_novelty >= novelty_floor or strongest_generativity >= generativity_floor:
            value += float(selection.get("exploration_bonus", 0.09))
    return round(max(0.0, min(1.0, value)), 4)


def _best_public_claim(records: list[dict[str, Any]]) -> dict[str, Any] | None:
    rules = load_promotion_rules()
    candidates: list[tuple[dict[str, Any], Any]] = []
    for record in records:
        decision = decide_promotion(record, rules)
        if decision.public_claim:
            candidates.append((record, decision))
    if not candidates:
        return None
    record, decision = max(
        candidates,
        key=lambda item: (
            int(item[1].synthesis_ready),
            _score(item[0], "source_reliability"),
            _score(item[0], "counterargument_quality"),
            _score(item[0], "publishability"),
            str(item[0].get("created_at") or ""),
        ),
    )
    return {
        "idea_id": record.get("idea_id"),
        "title": record.get("title"),
        "promotion_stage": decision.label,
        "path": record.get("path"),
    }


def _build_prompt(frontier: dict[str, Any], focus: str | None = None) -> str:
    tests = frontier.get("tests") or {}
    falsifiable = tests.get("falsifiable") or []
    practitioner = tests.get("practitioner") or []
    cross_domain = tests.get("cross_domain") or []
    lines = [
        "# Active Frontier Brief",
        "",
        f"Frontier: {frontier['title']}",
        f"Recommended action: {frontier['recommended_next_action']}",
        f"Why now: {frontier['why_now']}",
        "",
        "Core claim:",
        frontier["core_claim"],
        "",
        "Closest prior art or near-neighbor pressure:",
    ]
    for item in frontier.get("closest_prior_art") or []:
        lines.append(
            f"- {item.get('source', 'Unknown source')}: overlap: {item.get('overlap', '')}; difference: {item.get('difference', '')}"
        )
    if not frontier.get("closest_prior_art"):
        lines.append("- No close prior-art pressure has been recorded yet.")
    lines.extend(["", "Open anomalies:"])
    for anomaly in frontier.get("open_anomalies") or ["No anomaly has been recorded yet. Find one."]:
        lines.append(f"- {anomaly}")
    lines.extend(["", "Required next move:", frontier["next_prompt"], "", "Required tests:"])
    for item in [*falsifiable, *practitioner, *cross_domain]:
        lines.append(f"- {item}")
    if focus:
        lines.extend(["", "User or scheduler focus:", focus])
    lines.extend(
        [
            "",
            "Success criteria:",
            "- Advance, merge, falsify, or retire this frontier. Do not produce an unrelated one-off finding.",
            "- Name the closest prior argument and the exact difference from it.",
            "- Name one anomaly that would weaken the frontier.",
            "- Keep epistemic labels explicit and do not collapse analogy into evidence.",
            "- Return exactly one structured idea record.",
        ]
    )
    return "\n".join(_clean(line) for line in lines).strip() + "\n"


def _frontier_from_group(
    topic: dict[str, Any],
    records: list[dict[str, Any]],
    audits_by_idea: dict[str, dict[str, Any]],
    publications: dict[str, dict[str, Any]],
    rules: dict[str, Any],
) -> dict[str, Any]:
    text_clip = _limit(rules, "text_clip")
    prior_art_clip = _limit(rules, "prior_art_clip")
    audits = [
        audits_by_idea[str(record.get("idea_id"))]
        for record in records
        if str(record.get("idea_id")) in audits_by_idea
    ]
    agents = sorted({str(record.get("agent") or "unknown") for record in records})
    idea_ids = [str(record.get("idea_id")) for record in records if record.get("idea_id")]
    audit_ids = [str(audit.get("audit_id")) for audit in audits if audit.get("audit_id")]
    publication_paths = [
        publications[str(record.get("path"))]["path"]
        for record in records
        if str(record.get("path")) in publications
    ]
    published = bool(publication_paths)
    action, stage = _frontier_action(audits, records, published)
    best_record = max(
        records,
        key=lambda record: (
            _score(record, "publishability"),
            _score(record, "generativity"),
            _score(record, "counterargument_quality"),
            str(record.get("created_at") or ""),
        ),
    )
    closest_prior_art: list[dict[str, str]] = []
    seen_neighbors: set[str] = set()
    for audit in audits:
        for neighbor in audit.get("near_neighbors") or []:
            source = _clean(neighbor.get("source"), limit=prior_art_clip)
            if not source or source.lower() in seen_neighbors:
                continue
            seen_neighbors.add(source.lower())
            closest_prior_art.append(
                {
                    "source": source,
                    "overlap": _clean(neighbor.get("overlap"), limit=prior_art_clip),
                    "difference": _clean(neighbor.get("difference"), limit=prior_art_clip),
                    "novelty_impact": _clean(neighbor.get("novelty_impact"), limit=prior_art_clip),
                }
            )
            if len(closest_prior_art) >= _limit(rules, "closest_prior_art"):
                break
        if len(closest_prior_art) >= _limit(rules, "closest_prior_art"):
            break
    anomalies = _latest(
        [
            (audit.get("anomaly_probe") or {}).get("anomaly_candidate", "")
            for audit in audits
        ],
        _limit(rules, "open_anomalies"),
        clip=text_clip,
    )
    instructions = _latest(
        [
            item
            for audit in audits
            for item in audit.get("next_loop_instructions") or []
        ]
        + [
            item
            for record in records
            for item in record.get("next_research_directions") or []
        ],
        _limit(rules, "instructions"),
        clip=text_clip,
    )
    missing_sources = _latest(
        [
            item
            for audit in audits
            for item in audit.get("literature_search_queries") or []
        ],
        _limit(rules, "missing_sources"),
        clip=text_clip,
    )
    falsifiable = _latest(
        [
            f"If: {prediction.get('if_model_is_right', '')} Then: {prediction.get('expected_observation', '')} Weakens if: {prediction.get('would_weaken_or_falsify', '')}"
            for audit in audits
            for prediction in audit.get("falsifiable_predictions") or []
        ],
        _limit(rules, "falsifiable_tests"),
        clip=text_clip,
    )
    practitioner = _latest(
        [
            question
            for audit in audits
            for question in ((audit.get("practitioner_test") or {}).get("questions") or [])
        ],
        _limit(rules, "practitioner_tests"),
        clip=text_clip,
    )
    cross_domain = _latest(
        [
            (audit.get("cross_domain_prediction") or {}).get("prediction", "")
            for audit in audits
        ],
        _limit(rules, "cross_domain_tests"),
        clip=text_clip,
    )
    priority = _priority(
        records,
        audits,
        agents=agents,
        publication_paths=publication_paths,
        rules=rules,
        topic=topic,
    )
    statuses = sorted({str(audit.get("originality_status") or "audit_incomplete") for audit in audits})
    if statuses and set(statuses).issubset({"known", "renamed", "rejected"}):
        status = "cooldown"
    else:
        status = "active"
    core_claim = _clean(best_record.get("original_claim"), limit=_limit(rules, "core_claim_clip"))
    next_prompt = instructions[0] if instructions else f"Advance the frontier by testing {topic['title']} against its strongest anomaly."
    why_now_bits = [
        f"priority {priority:.2f}",
        f"{len(records)} related idea records",
        f"{len(audits)} originality audits",
    ]
    if len(agents) > 1:
        why_now_bits.append("cross-agent signal")
    if anomalies:
        why_now_bits.append("live anomaly pressure")
    return {
        "frontier_id": topic["id"],
        "title": topic["title"],
        "configured_topic": bool(topic.get("configured")),
        "status": status,
        "stage": stage,
        "priority": priority,
        "last_advanced_at": max(
            [
                *[str(record.get("created_at") or "") for record in records],
                *[str(audit.get("created_at") or "") for audit in audits],
            ]
        ),
        "agents": agents,
        "idea_ids": idea_ids,
        "audit_ids": audit_ids,
        "publication_paths": sorted(set(publication_paths)),
        "core_claim": core_claim,
        "strongest_public_claim": _best_public_claim(records),
        "closest_prior_art": closest_prior_art,
        "open_anomalies": anomalies,
        "missing_sources": missing_sources,
        "tests": {
            "falsifiable": falsifiable,
            "practitioner": practitioner,
            "cross_domain": cross_domain,
        },
        "recommended_next_action": action,
        "next_prompt": _clean(next_prompt, limit=_limit(rules, "next_prompt_clip")),
        "why_now": "; ".join(why_now_bits),
        "blockers": _latest(
            [
                (audit.get("novelty_adjustment") or "")
                for audit in audits
                if audit.get("novelty_adjustment")
            ],
            _limit(rules, "blockers"),
            clip=text_clip,
        ),
        "audit_statuses": statuses,
    }


def _markdown_for_state(state: dict[str, Any]) -> str:
    lines = [
        "# Lumenary Frontiers",
        "",
        f"Generated: {state['generated_at']}",
        "",
        "These are live research agendas derived from idea records, originality audits, publication history, and next-loop instructions.",
        "",
    ]
    for frontier in state.get("frontiers") or []:
        lines.extend(
            [
                f"## {frontier['title']}",
                "",
                f"- Frontier ID: `{frontier['frontier_id']}`",
                f"- Status: `{frontier['status']}`",
                f"- Stage: `{frontier['stage']}`",
                f"- Priority: {frontier['priority']:.4f}",
                f"- Next action: `{frontier['recommended_next_action']}`",
                f"- Agents: {', '.join(frontier['agents'])}",
                f"- Idea records: {len(frontier['idea_ids'])}",
                f"- Audits: {len(frontier['audit_ids'])}",
                "",
                "### Core Claim",
                "",
                frontier["core_claim"],
                "",
                "### Next Prompt",
                "",
                frontier["next_prompt"],
                "",
            ]
        )
        if frontier.get("open_anomalies"):
            lines.extend(["### Open Anomalies", ""])
            lines.extend(f"- {item}" for item in frontier["open_anomalies"])
            lines.append("")
        if frontier.get("blockers"):
            lines.extend(["### Blockers", ""])
            lines.extend(f"- {item}" for item in frontier["blockers"])
            lines.append("")
    return "\n".join(_clean(line) for line in lines).strip() + "\n"


def refresh_frontiers(root: Path) -> dict[str, Any]:
    rules = load_frontier_rules(root)
    ideas = _read_jsonl(root / "hypotheses" / "ideas.jsonl")
    audits_by_idea = _latest_audits_by_idea(root)
    publications = _publication_paths(root)
    dialogue_outcomes = _dialogue_outcomes_by_idea(root)
    grouped: dict[str, tuple[dict[str, Any], list[dict[str, Any]]]] = {}

    for record in ideas:
        if str(record.get("status") or "") == "seed-fixture":
            continue
        audit = audits_by_idea.get(str(record.get("idea_id") or ""))
        topic = _topic_for(record, audit, rules)
        existing = grouped.setdefault(topic["id"], (topic, []))
        existing[1].append(record)

    frontiers = [
        _apply_dialogue_pressure(
            _frontier_from_group(topic, records, audits_by_idea, publications, rules),
            dialogue_outcomes,
        )
        for topic, records in grouped.values()
        if records
    ]
    frontiers.sort(
        key=lambda frontier: (
            frontier["status"] != "active",
            -float(frontier["priority"]),
            str(frontier["title"]),
        )
    )
    state = {
        "generated_at": now_local_iso(),
        "rules_version": rules.get("version", "unknown"),
        "version": "2026-05-26",
        "frontiers": frontiers,
    }
    librarian = Librarian(root)
    librarian.write_text(
        FRONTIER_STATE,
        json.dumps(state, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
    )
    librarian.write_text(FRONTIER_MARKDOWN, _markdown_for_state(state))
    if frontiers:
        librarian.write_text(NEXT_FRONTIER_PROMPT, _build_prompt(frontiers[0]))
    return state


def select_frontier(root: Path, *, refresh: bool = True) -> dict[str, Any] | None:
    state = refresh_frontiers(root) if refresh else json.loads((root / FRONTIER_STATE).read_text(encoding="utf-8"))
    for frontier in state.get("frontiers") or []:
        if frontier.get("status") == "active":
            return frontier
    return (state.get("frontiers") or [None])[0]


def prepare_frontier_brief(
    root: Path,
    *,
    focus: str,
    execution_id: str,
    enabled: bool = True,
) -> str:
    if not enabled:
        return ""
    frontier = select_frontier(root, refresh=True)
    if not frontier:
        return ""
    brief = _build_prompt(frontier, focus)
    librarian = Librarian(root)
    librarian.write_text(NEXT_FRONTIER_PROMPT, brief)
    librarian.append_jsonl(
        FRONTIER_EVENTS,
        {
            "at": now_local_iso(),
            "event": "frontier-selected",
            "execution_id": execution_id,
            "focus": focus,
            "frontier_id": frontier["frontier_id"],
            "priority": frontier["priority"],
            "recommended_next_action": frontier["recommended_next_action"],
            "title": frontier["title"],
        },
    )
    return brief


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh or select Lumenary research frontiers.")
    parser.add_argument("command", choices=("refresh", "select"), nargs="?", default="refresh")
    parser.add_argument("--focus", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    if args.command == "refresh":
        state = refresh_frontiers(root)
        print(f"frontiers={len(state.get('frontiers') or [])}")
        return
    frontier = select_frontier(root)
    if frontier:
        print(json.dumps(frontier, indent=2, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
