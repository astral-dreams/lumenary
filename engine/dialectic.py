"""Detect and stage cross-agent dialogues for Lumenary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .frontier import refresh_frontiers
from .librarian import Librarian
from .originality_audit import audit_new_ideas
from .schemas import IdeaRecord, IdeaScores, now_local_iso, slugify
from .structured_thinker import generate_structured_json


DIALECTIC_RULES = "config/dialectic-rules.json"
DIALOGUE_LEDGER = "reviews/dialogues/dialogues.jsonl"
DIALOGUE_OUTCOMES = "reviews/dialogues/outcomes.jsonl"
DIALOGUE_AGENDA = "state/dialogue_agenda.json"
DASH_REPLACEMENTS = {
    "\u2014": ":",
    "\u2013": "-",
    "&mdash;": ":",
    "&#8212;": ":",
    "&#x2014;": ":",
    "&#x2014": ":",
}


@dataclass(frozen=True)
class DialogueRunOptions:
    max_pairs: int = 1
    execution_id: str | None = None
    force_pair: tuple[str, str] | None = None
    detect_only: bool = False
    audit_syntheses: bool = True
    notify: bool = False


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        records.append(json.loads(raw))
    return records


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
        handle.write("\n")


def _read_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def load_dialectic_rules(root: Path) -> dict[str, Any]:
    defaults = {
        "version": "default",
        "min_publishability": 0.55,
        "min_source_basis_items": 2,
        "require_cross_agent": True,
        "require_originality_audit": True,
        "cooldown_dialogues": 2,
        "wildcard_every": 4,
        "blocked_statuses": ["seed-fixture", "rejected"],
        "blocked_epistemic_labels": ["rejected"],
        "demolition_blocks_future_pairing": True,
        "weights": {
            "shared_frontier": 0.24,
            "frontier_priority": 0.16,
            "concept_graph_contradiction": 0.18,
            "translation_strain": 0.12,
            "audit_anomaly_overlap": 0.12,
            "near_neighbor_conflict": 0.08,
            "source_overlap_with_divergent_conclusion": 0.06,
            "recency": 0.04,
        },
    }
    path = root / DIALECTIC_RULES
    if not path.exists():
        return defaults
    loaded = json.loads(path.read_text(encoding="utf-8"))
    merged = {**defaults, **loaded}
    merged["weights"] = {**defaults["weights"], **(loaded.get("weights") or {})}
    return merged


def _clean(value: Any, *, limit: int = 1000) -> str:
    text = re.sub(r"\s+", " ", _sanitize_text(str(value or ""))).strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _sanitize_text(value: str) -> str:
    text = str(value)
    for needle, replacement in DASH_REPLACEMENTS.items():
        text = text.replace(needle, replacement)
    return text


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    return value


def _yaml_string(value: Any, *, limit: int = 500) -> str:
    return json.dumps(_clean(value, limit=limit), ensure_ascii=True)


def _clamp_score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _tokens(value: str) -> set[str]:
    stop = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", value.lower())
        if token not in stop
    }


def _idea_text(record: dict[str, Any]) -> str:
    return " ".join(
        [
            str(record.get("title") or ""),
            str(record.get("original_claim") or ""),
            str(record.get("why_it_might_be_new") or ""),
            str(record.get("critique") or ""),
            " ".join(str(item) for item in record.get("source_basis") or []),
            " ".join(str(item) for item in record.get("next_research_directions") or []),
        ]
    )


def _score(record: dict[str, Any], key: str) -> float:
    return float((record.get("scores") or {}).get(key, 0.0))


def _idea_id(record: dict[str, Any]) -> str:
    return str(record.get("idea_id") or "")


def _pair_id(a: str, b: str) -> str:
    left, right = sorted([a, b])
    return hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()[:16]


def _iso_seconds(value: str) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def _latest_audits(root: Path) -> dict[str, dict[str, Any]]:
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
        if _iso_seconds(str(audit.get("created_at") or "")) > _iso_seconds(str(existing.get("created_at") or "")):
            latest[idea_id] = audit
    return latest


def _eligible_ideas(
    root: Path,
    rules: dict[str, Any],
    audits: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    blocked_statuses = {str(item) for item in rules.get("blocked_statuses") or []}
    blocked_labels = {str(item) for item in rules.get("blocked_epistemic_labels") or []}
    min_publishability = float(rules.get("min_publishability", 0.55))
    min_sources = int(rules.get("min_source_basis_items", 2))
    require_audit = bool(rules.get("require_originality_audit", True))
    ideas: list[dict[str, Any]] = []

    for record in _read_jsonl(root / "hypotheses" / "ideas.jsonl"):
        idea_id = _idea_id(record)
        if not idea_id:
            continue
        if str(record.get("status") or "draft") in blocked_statuses:
            continue
        labels = {str(label) for label in record.get("epistemic_labels") or []}
        if labels.intersection(blocked_labels):
            continue
        if _score(record, "publishability") < min_publishability:
            continue
        source_count = len([item for item in record.get("source_basis") or [] if str(item).strip()])
        if source_count < min_sources:
            continue
        if require_audit and idea_id not in audits:
            continue
        ideas.append(record)
    return ideas


def _completed_pair_ids(root: Path) -> set[str]:
    return {
        str(record.get("pair", {}).get("pair_id") or "")
        for record in _read_jsonl(root / DIALOGUE_LEDGER)
        if str(record.get("status") or "") == "complete"
    }


def _recent_dialogue_idea_ids(root: Path, count: int) -> set[str]:
    if count <= 0:
        return set()
    records = _read_jsonl(root / DIALOGUE_LEDGER)
    recent = records[-count:]
    ids: set[str] = set()
    for record in recent:
        pair = record.get("pair") or {}
        ids.add(str(pair.get("idea_a") or ""))
        ids.add(str(pair.get("idea_b") or ""))
    return {idea_id for idea_id in ids if idea_id}


def _blocked_by_dialogue_outcome(root: Path, rules: dict[str, Any]) -> set[str]:
    if not bool(rules.get("demolition_blocks_future_pairing", True)):
        return set()
    blocked: set[str] = set()
    for outcome in _read_jsonl(root / DIALOGUE_OUTCOMES):
        if str(outcome.get("outcome") or "") != "demolition":
            continue
        for idea_id in outcome.get("idea_ids") or []:
            if idea_id:
                blocked.add(str(idea_id))
    return blocked


def _frontier_index(root: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]]]:
    state = _read_json(root / "state" / "frontiers.json", {"frontiers": []})
    by_idea: dict[str, list[dict[str, Any]]] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for frontier in state.get("frontiers") or []:
        frontier_id = str(frontier.get("frontier_id") or "")
        if frontier_id:
            by_id[frontier_id] = frontier
        for idea_id in frontier.get("idea_ids") or []:
            by_idea.setdefault(str(idea_id), []).append(frontier)
    return by_idea, by_id


def _concepts_for_idea(record: dict[str, Any], graph: dict[str, Any]) -> set[str]:
    text = _idea_text(record).lower()
    concepts: set[str] = set()
    for node in graph.get("nodes") or []:
        node_id = str(node.get("id") or "").lower()
        label = str(node.get("label") or "").lower()
        candidates = {
            node_id,
            node_id.replace("-", " "),
            slugify(label).replace("-", " "),
        }
        for part in re.split(r"[/()]", label):
            phrase = re.sub(r"[^a-z0-9]+", " ", part).strip()
            if len(phrase) >= 5:
                candidates.add(phrase)
        if any(candidate and re.search(rf"\b{re.escape(candidate)}\b", text) for candidate in candidates):
            concepts.add(str(node.get("id")))
    return concepts


def _source_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    a_sources = {re.sub(r"\W+", " ", str(item).lower()).strip() for item in a.get("source_basis") or []}
    b_sources = {re.sub(r"\W+", " ", str(item).lower()).strip() for item in b.get("source_basis") or []}
    for left in a_sources:
        left_tokens = _tokens(left)
        if not left_tokens:
            continue
        for right in b_sources:
            if len(left_tokens.intersection(_tokens(right))) >= 4:
                return True
    return False


def _audit_text(audit: dict[str, Any]) -> str:
    pieces = [
        str((audit.get("anomaly_probe") or {}).get("anomaly_candidate") or ""),
        str((audit.get("anomaly_probe") or {}).get("why_it_breaks_or_strains_model") or ""),
        str(audit.get("novelty_adjustment") or ""),
        " ".join(str(item) for item in audit.get("next_loop_instructions") or []),
    ]
    for neighbor in audit.get("near_neighbors") or []:
        pieces.extend(
            [
                str(neighbor.get("source") or ""),
                str(neighbor.get("overlap") or ""),
                str(neighbor.get("difference") or ""),
            ]
        )
    return " ".join(pieces)


def _near_neighbor_conflict(
    a: dict[str, Any],
    b: dict[str, Any],
    audits: dict[str, dict[str, Any]],
) -> bool:
    a_audit = audits.get(_idea_id(a)) or {}
    b_audit = audits.get(_idea_id(b)) or {}
    a_text = _audit_text(a_audit).lower()
    b_text = _audit_text(b_audit).lower()
    a_title_tokens = _tokens(str(a.get("title") or ""))
    b_title_tokens = _tokens(str(b.get("title") or ""))
    if len(a_title_tokens.intersection(_tokens(b_text))) >= 2:
        return True
    if len(b_title_tokens.intersection(_tokens(a_text))) >= 2:
        return True
    return len(_tokens(a_text).intersection(_tokens(b_text))) >= 8


def _anomaly_overlap(
    a: dict[str, Any],
    b: dict[str, Any],
    audits: dict[str, dict[str, Any]],
) -> bool:
    a_audit = audits.get(_idea_id(a)) or {}
    b_audit = audits.get(_idea_id(b)) or {}
    a_anomaly = str((a_audit.get("anomaly_probe") or {}).get("anomaly_candidate") or "")
    b_anomaly = str((b_audit.get("anomaly_probe") or {}).get("anomaly_candidate") or "")
    if a_anomaly and len(_tokens(a_anomaly).intersection(_tokens(_idea_text(b)))) >= 3:
        return True
    if b_anomaly and len(_tokens(b_anomaly).intersection(_tokens(_idea_text(a)))) >= 3:
        return True
    return bool(a_anomaly and b_anomaly and len(_tokens(a_anomaly).intersection(_tokens(b_anomaly))) >= 3)


def _recent(record: dict[str, Any], *, hours: int = 48) -> bool:
    timestamp = _iso_seconds(str(record.get("created_at") or ""))
    if not timestamp:
        return False
    age = datetime.now().astimezone().timestamp() - timestamp
    return age <= hours * 3600


def _role_counts(root: Path) -> dict[str, dict[str, int]]:
    counts = {"codex": {"proponent": 0, "challenger": 0}, "claude": {"proponent": 0, "challenger": 0}}
    for record in _read_jsonl(root / DIALOGUE_LEDGER):
        pair = record.get("pair") or {}
        proponent = str(pair.get("proponent_agent") or "")
        challenger = str(pair.get("challenger_agent") or "")
        if proponent in counts:
            counts[proponent]["proponent"] += 1
        if challenger in counts:
            counts[challenger]["challenger"] += 1
    return counts


def _assign_roles(
    root: Path,
    a: dict[str, Any],
    b: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    counts = _role_counts(root)
    a_agent = str(a.get("agent") or "")
    b_agent = str(b.get("agent") or "")
    if a_agent in counts and b_agent in counts:
        a_challenge_gap = counts[a_agent]["challenger"] - counts[a_agent]["proponent"]
        b_challenge_gap = counts[b_agent]["challenger"] - counts[b_agent]["proponent"]
        if a_challenge_gap < b_challenge_gap:
            return b, a
        if b_challenge_gap < a_challenge_gap:
            return a, b
    a_strength = _score(a, "generativity") + _score(a, "publishability")
    b_strength = _score(b, "generativity") + _score(b, "publishability")
    return (a, b) if a_strength >= b_strength else (b, a)


def _signal(name: str, weight: float, reason: str) -> dict[str, Any]:
    return {"name": name, "weight": round(weight, 4), "reason": _clean(reason, limit=260)}


def _candidate_pair(
    root: Path,
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    audits: dict[str, dict[str, Any]],
    rules: dict[str, Any],
    frontier_by_idea: dict[str, list[dict[str, Any]]],
    graph: dict[str, Any],
) -> dict[str, Any] | None:
    weights = rules.get("weights") or {}
    a_id = _idea_id(a)
    b_id = _idea_id(b)
    signals: list[dict[str, Any]] = []
    shared_concepts = sorted(_concepts_for_idea(a, graph).intersection(_concepts_for_idea(b, graph)))

    a_frontiers = {str(item.get("frontier_id") or ""): item for item in frontier_by_idea.get(a_id, [])}
    b_frontiers = {str(item.get("frontier_id") or ""): item for item in frontier_by_idea.get(b_id, [])}
    common_frontiers = [a_frontiers[key] for key in a_frontiers.keys() & b_frontiers.keys()]
    if common_frontiers:
        frontier = max(common_frontiers, key=lambda item: float(item.get("priority") or 0.0))
        signals.append(
            _signal(
                "shared_frontier",
                float(weights.get("shared_frontier", 0.24)),
                f"Both ideas sit on {frontier.get('title', 'a shared frontier')}.",
            )
        )
        signals.append(
            _signal(
                "frontier_priority",
                float(weights.get("frontier_priority", 0.16)) * min(1.0, float(frontier.get("priority") or 0.0)),
                f"Shared frontier priority is {float(frontier.get('priority') or 0.0):.2f}.",
            )
        )

    a_concepts = _concepts_for_idea(a, graph)
    b_concepts = _concepts_for_idea(b, graph)
    for edge in graph.get("edges") or []:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        relation = str(edge.get("relation") or "").lower()
        relation_terms = set(re.split(r"[^a-z0-9]+", relation))
        connects = (source in a_concepts and target in b_concepts) or (target in a_concepts and source in b_concepts)
        if not connects:
            continue
        if relation_terms.intersection({"tension", "contradiction", "divergence"}):
            signals.append(
                _signal(
                    "concept_graph_contradiction",
                    float(weights.get("concept_graph_contradiction", 0.18)),
                    str(edge.get("note") or f"{source} and {target} are in tension."),
                )
            )
            break
    for edge in graph.get("edges") or []:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        relation = str(edge.get("relation") or "").lower()
        relation_terms = set(re.split(r"[^a-z0-9]+", relation))
        connects = (source in a_concepts and target in b_concepts) or (target in a_concepts and source in b_concepts)
        if connects and (relation_terms.intersection({"strain", "translation"}) or "translation" in source or "translation" in target):
            signals.append(
                _signal(
                    "translation_strain",
                    float(weights.get("translation_strain", 0.12)),
                    str(edge.get("note") or f"{source} and {target} create translation strain."),
                )
            )
            break

    if _anomaly_overlap(a, b, audits):
        signals.append(
            _signal(
                "audit_anomaly_overlap",
                float(weights.get("audit_anomaly_overlap", 0.12)),
                "An anomaly or audit instruction for one idea pressures the other idea.",
            )
        )
    if _near_neighbor_conflict(a, b, audits):
        signals.append(
            _signal(
                "near_neighbor_conflict",
                float(weights.get("near_neighbor_conflict", 0.08)),
                "Originality audits share near-neighbor or prior-art pressure.",
            )
        )
    if _source_overlap(a, b) and str(a.get("title")) != str(b.get("title")):
        signals.append(
            _signal(
                "source_overlap_with_divergent_conclusion",
                float(weights.get("source_overlap_with_divergent_conclusion", 0.06)),
                "The ideas draw on overlapping source material but make different moves.",
            )
        )
    if _recent(a) or _recent(b):
        signals.append(
            _signal(
                "recency",
                float(weights.get("recency", 0.04)),
                "At least one idea is recent enough to keep the dialogue timely.",
            )
        )
    if not signals:
        overlap = len(_tokens(_idea_text(a)).intersection(_tokens(_idea_text(b))))
        if overlap >= 10:
            signals.append(
                _signal(
                    "wildcard",
                    0.02,
                    "The ideas share enough claim language to be worth a low-priority wildcard check.",
                )
            )
    if not signals:
        return None

    proponent, challenger = _assign_roles(root, a, b)
    primary = max(signals, key=lambda item: float(item["weight"]))
    priority = min(1.0, sum(float(item["weight"]) for item in signals))
    return {
        "pair_id": _pair_id(a_id, b_id),
        "idea_a": _idea_id(proponent),
        "idea_b": _idea_id(challenger),
        "proponent_agent": str(proponent.get("agent") or ""),
        "challenger_agent": str(challenger.get("agent") or ""),
        "proponent_title": str(proponent.get("title") or ""),
        "challenger_title": str(challenger.get("title") or ""),
        "tension_type": primary["name"],
        "tension_source": primary["reason"],
        "priority": round(priority, 4),
        "shared_concepts": shared_concepts,
        "signals": signals,
    }


def detect_tensions(
    root: Path,
    *,
    max_pairs: int = 1,
    force_pair: tuple[str, str] | None = None,
    ignore_cooldown: bool = False,
) -> list[dict[str, Any]]:
    rules = load_dialectic_rules(root)
    audits = _latest_audits(root)
    ideas = _eligible_ideas(root, rules, audits)
    ideas_by_id = {_idea_id(record): record for record in ideas}
    if force_pair:
        ideas = [record for idea_id in force_pair if (record := ideas_by_id.get(idea_id))]
    completed = _completed_pair_ids(root)
    cooldown = _recent_dialogue_idea_ids(root, int(rules.get("cooldown_dialogues", 2)))
    dialogue_blocked = _blocked_by_dialogue_outcome(root, rules)
    frontier_by_idea, _ = _frontier_index(root)
    graph = _read_json(root / "graph" / "concept-graph.seed.json", {"nodes": [], "edges": []})
    candidates: list[dict[str, Any]] = []

    for index, a in enumerate(ideas):
        for b in ideas[index + 1 :]:
            a_id = _idea_id(a)
            b_id = _idea_id(b)
            pair_id = _pair_id(a_id, b_id)
            if force_pair and set(force_pair) != {a_id, b_id}:
                continue
            if bool(rules.get("require_cross_agent", True)) and str(a.get("agent")) == str(b.get("agent")):
                continue
            if pair_id in completed and not force_pair:
                continue
            if not force_pair and not ignore_cooldown and (a_id in cooldown or b_id in cooldown):
                continue
            if a_id in dialogue_blocked or b_id in dialogue_blocked:
                continue
            candidate = _candidate_pair(
                root,
                a,
                b,
                audits=audits,
                rules=rules,
                frontier_by_idea=frontier_by_idea,
                graph=graph,
            )
            if candidate:
                candidates.append(candidate)

    candidates.sort(
        key=lambda item: (
            -float(item.get("priority") or 0.0),
            str(item.get("proponent_title") or ""),
        )
    )
    selected = candidates[:max_pairs]
    agenda = {
        "generated_at": now_local_iso(),
        "rules_version": rules.get("version"),
        "candidate_count": len(candidates),
        "selected_pairs": selected,
        "reason": "selected" if selected else "no eligible cross-agent tension found",
    }
    agenda_path = root / DIALOGUE_AGENDA
    agenda_path.parent.mkdir(parents=True, exist_ok=True)
    agenda_path.write_text(
        json.dumps(agenda, indent=2, ensure_ascii=True, sort_keys=True),
        encoding="utf-8",
    )
    return selected


def _agent_config(base: EngineConfig, agent: str) -> EngineConfig:
    if base.provider == "offline" or base.dry_run:
        provider = "offline"
    else:
        provider = "codex-cli" if agent == "codex" else "claude-code"
    return EngineConfig.load(
        root=base.root,
        agent=agent,
        provider=provider,
        dry_run=base.dry_run,
        codex_model=base.codex_model,
        codex_search=True,
        codex_sandbox=base.codex_sandbox,
        codex_timeout_seconds=base.codex_timeout_seconds,
        claude_model=base.claude_model,
        claude_timeout_seconds=base.claude_timeout_seconds,
    )


def _idea_payload(record: dict[str, Any]) -> str:
    keys = [
        "idea_id",
        "agent",
        "title",
        "idea_type",
        "source_basis",
        "original_claim",
        "why_it_might_be_new",
        "critique",
        "epistemic_labels",
        "scores",
        "next_research_directions",
        "status",
    ]
    return json.dumps({key: record.get(key) for key in keys}, indent=2, ensure_ascii=True)


def _challenge_prompt(pair: dict[str, Any], proponent: dict[str, Any], challenger: dict[str, Any], audit: dict[str, Any] | None) -> str:
    return f"""# Lumenary Dialectic: Challenge

You are the Challenger in a structured Lumenary dialogue.

Your task is not to be contrarian. Your task is to understand the Proponent's
idea fairly, then find the real pressure point that could strengthen, revise,
or break it.

Do not use em dashes. Use commas, colons, semicolons, or periods.

## Tension Pair

{json.dumps(pair, indent=2, ensure_ascii=True)}

## Proponent Idea

{_idea_payload(proponent)}

## Your Related Idea

{_idea_payload(challenger)}

## Latest Originality Audit For Proponent

{json.dumps(audit or {}, indent=2, ensure_ascii=True)}

## Required Posture

First steelman the Proponent's idea in a way they would accept. Only then make
the challenge. Name the hidden assumption, a counter-model, and one primary,
practitioner, or scholarly source that would complicate the claim.

Return exactly one JSON object matching the dialogue_turn schema with
turn=1, turn_type="challenge", role="challenger", and agent="{pair['challenger_agent']}".
"""


def _rebuttal_prompt(pair: dict[str, Any], proponent: dict[str, Any], challenge: dict[str, Any]) -> str:
    return f"""# Lumenary Dialectic: Rebuttal

You are the Proponent in a structured Lumenary dialogue.

Your counterpart challenged your idea. Do not be defensive. Concede real flaws,
defend only what survives, revise the claim if needed, and name the deepest
crux.

Do not use em dashes. Use commas, colons, semicolons, or periods.

## Your Original Idea

{_idea_payload(proponent)}

## Challenge

{json.dumps(challenge, indent=2, ensure_ascii=True)}

## Required Output

Return exactly one JSON object matching the dialogue_turn schema with
turn=2, turn_type="rebuttal", role="proponent", and agent="{pair['proponent_agent']}".
Include concessions, defense, revised_claim, crux, and test_that_would_settle_it.
"""


def _counter_prompt(pair: dict[str, Any], proponent: dict[str, Any], challenge: dict[str, Any], rebuttal: dict[str, Any]) -> str:
    return f"""# Lumenary Dialectic: Counter-Rebuttal

You are the Challenger. This is your final turn.

Assess whether the Proponent's revision became stronger, weaker, or transformed.
Do not try to win. Identify the remaining risk and whether the named crux is
the real crux.

Do not use em dashes. Use commas, colons, semicolons, or periods.

## Original Idea

{_idea_payload(proponent)}

## Challenge

{json.dumps(challenge, indent=2, ensure_ascii=True)}

## Rebuttal

{json.dumps(rebuttal, indent=2, ensure_ascii=True)}

## Required Output

Return exactly one JSON object matching the dialogue_turn schema with
turn=3, turn_type="counter_rebuttal", role="challenger", and agent="{pair['challenger_agent']}".
"""


def _synthesis_prompt(pair: dict[str, Any], proponent: dict[str, Any], challenger: dict[str, Any], turns: list[dict[str, Any]]) -> str:
    return f"""# Lumenary Dialectic: Synthesis Verdict

You are synthesizing a structured philosophical dialogue between two Lumenary
agents. Do not pick a winner. Identify what the exchange produced, what remains
unresolved, and whether any candidate synthesis should be created.

A dialogue alone does not prove originality. Use outcome "candidate_transcendence"
only if the exchange creates a new candidate synthesis that neither source idea
already contained. That candidate still needs originality audit before promotion.

Do not use em dashes. Use commas, colons, semicolons, or periods.

## Pair

{json.dumps(pair, indent=2, ensure_ascii=True)}

## Proponent Idea

{_idea_payload(proponent)}

## Challenger Idea

{_idea_payload(challenger)}

## Turns

{json.dumps(turns, indent=2, ensure_ascii=True)}

Return exactly one JSON object matching the dialogue_verdict schema.
"""


def _normalize_turn(
    turn: dict[str, Any],
    *,
    turn_number: int,
    turn_type: str,
    role: str,
    agent: str,
) -> dict[str, Any]:
    normalized = _sanitize_value(dict(turn))
    normalized["turn"] = turn_number
    normalized["turn_type"] = turn_type
    normalized["role"] = role
    normalized["agent"] = agent
    for key in ["claim_units", "concessions", "sources_cited"]:
        value = normalized.get(key)
        if not isinstance(value, list):
            normalized[key] = []
    for key in [
        "steelman",
        "fairness_check",
        "strongest_objection",
        "hidden_assumption",
        "counter_model",
        "new_source",
        "defense",
        "revised_claim",
        "crux",
        "test_that_would_settle_it",
        "crux_assessment",
        "verdict_on_revision",
        "remaining_risk",
    ]:
        normalized.setdefault(key, None)
    normalized["argument"] = _clean(normalized.get("argument"), limit=4000)
    return _sanitize_value(normalized)


def _normalize_synthesis(synthesis: dict[str, Any], *, synthesizer_agent: str) -> dict[str, Any]:
    normalized = _sanitize_value(dict(synthesis))
    normalized["synthesizer_agent"] = synthesizer_agent
    normalized.setdefault("candidate_synthesis", None)
    normalized.setdefault("new_concept_edges", [])
    normalized.setdefault("recommended_adjustments", {"proponent": {}, "challenger": {}})
    adjustments = normalized.get("recommended_adjustments")
    if not isinstance(adjustments, dict):
        normalized["recommended_adjustments"] = {"proponent": {}, "challenger": {}}
    else:
        for role in ("proponent", "challenger"):
            role_adjustments = adjustments.get(role)
            if not isinstance(role_adjustments, dict):
                adjustments[role] = {}
                continue
            cleaned_adjustments: dict[str, float] = {}
            for key, value in role_adjustments.items():
                try:
                    cleaned_adjustments[str(key)] = max(-1.0, min(1.0, float(value)))
                except (TypeError, ValueError):
                    continue
            adjustments[role] = cleaned_adjustments
    return normalized


def _next_synthesizer(root: Path) -> str:
    for record in reversed(_read_jsonl(root / DIALOGUE_LEDGER)):
        last = str((record.get("synthesis") or {}).get("synthesizer_agent") or "")
        if last == "codex":
            return "claude"
        if last == "claude":
            return "codex"
    return "codex"


def _notify(enabled: bool, title: str, body: str) -> None:
    if not enabled:
        return
    subprocess.run(
        [
            "osascript",
            "-e",
            "on run argv",
            "-e",
            'display notification (item 2 of argv) with title (item 1 of argv) subtitle "Lumenary"',
            "-e",
            "end run",
            title,
            body[:240],
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _dialogue_title(pair: dict[str, Any], synthesis: dict[str, Any]) -> str:
    crux = _clean(synthesis.get("unresolved_crux"), limit=84)
    if crux:
        return crux[0].upper() + crux[1:]
    return f"{pair.get('proponent_title', 'A finding')} under pressure"


def _idea_from_candidate(
    candidate: dict[str, Any],
    *,
    agent: str,
    dialogue_id: str,
    parent_titles: list[str],
) -> IdeaRecord | None:
    candidate = _sanitize_value(candidate)
    required = [
        "title",
        "idea_type",
        "source_basis",
        "original_claim",
        "why_it_might_be_new",
        "critique",
        "epistemic_labels",
        "scores",
        "next_research_directions",
    ]
    if not candidate or any(key not in candidate for key in required):
        return None
    scores = candidate.get("scores") or {}
    score_keys = [
        "novelty",
        "generativity",
        "cross_tradition_support",
        "logical_coherence",
        "explanatory_compression",
        "empirical_adjacency",
        "practice_testability",
        "counterargument_quality",
        "source_reliability",
        "publishability",
    ]
    if any(key not in scores for key in score_keys):
        return None
    source_basis = [str(item) for item in candidate.get("source_basis") or []]
    source_basis.extend(
        [
            f"Dialogue origin: {dialogue_id}.",
            "Parent ideas: " + "; ".join(parent_titles),
        ]
    )
    return IdeaRecord(
        title=str(candidate["title"]),
        idea_type=str(candidate["idea_type"]),
        agent=agent,
        created_at=now_local_iso(),
        source_basis=source_basis,
        original_claim=str(candidate["original_claim"]),
        why_it_might_be_new=str(candidate["why_it_might_be_new"]),
        critique=str(candidate["critique"]),
        epistemic_labels=[str(item) for item in candidate.get("epistemic_labels") or []],
        scores=IdeaScores(**{key: _clamp_score(scores[key]) for key in score_keys}),
        next_research_directions=[str(item) for item in candidate.get("next_research_directions") or []],
        status="draft",
    )


def stage_dialogue(
    config: EngineConfig,
    pair: dict[str, Any],
    *,
    execution_id: str,
    notify: bool = False,
) -> dict[str, Any]:
    root = config.root
    pair = _sanitize_value(dict(pair))
    ideas = {_idea_id(record): record for record in _read_jsonl(root / "hypotheses" / "ideas.jsonl")}
    audits = _latest_audits(root)
    proponent = ideas[pair["idea_a"]]
    challenger = ideas[pair["idea_b"]]
    run_dir = root / "runs" / f"dialectic-{execution_id}" / pair["pair_id"]
    turn_schema = root / "engine" / "json_schemas" / "dialogue_turn.schema.json"
    verdict_schema = root / "engine" / "json_schemas" / "dialogue_verdict.schema.json"

    _notify(
        notify,
        "Dialectic starting",
        f"Staging {pair.get('proponent_title')} against {pair.get('challenger_title')}.",
    )

    challenger_config = _agent_config(config, str(pair["challenger_agent"]))
    proponent_config = _agent_config(config, str(pair["proponent_agent"]))

    challenge = generate_structured_json(
        challenger_config,
        prompt=_challenge_prompt(pair, proponent, challenger, audits.get(pair["idea_a"])),
        schema_path=turn_schema,
        run_dir=run_dir,
        output_stem="01-challenge",
        search=True,
    )
    challenge = _normalize_turn(
        challenge,
        turn_number=1,
        turn_type="challenge",
        role="challenger",
        agent=str(pair["challenger_agent"]),
    )
    _notify(
        notify,
        "Challenge delivered",
        _clean(challenge.get("strongest_objection") or challenge.get("argument"), limit=220),
    )

    rebuttal = generate_structured_json(
        proponent_config,
        prompt=_rebuttal_prompt(pair, proponent, challenge),
        schema_path=turn_schema,
        run_dir=run_dir,
        output_stem="02-rebuttal",
        search=True,
    )
    rebuttal = _normalize_turn(
        rebuttal,
        turn_number=2,
        turn_type="rebuttal",
        role="proponent",
        agent=str(pair["proponent_agent"]),
    )

    counter = generate_structured_json(
        challenger_config,
        prompt=_counter_prompt(pair, proponent, challenge, rebuttal),
        schema_path=turn_schema,
        run_dir=run_dir,
        output_stem="03-counter-rebuttal",
        search=True,
    )
    counter = _normalize_turn(
        counter,
        turn_number=3,
        turn_type="counter_rebuttal",
        role="challenger",
        agent=str(pair["challenger_agent"]),
    )

    synth_agent = _next_synthesizer(root)
    synth_config = _agent_config(config, synth_agent)
    turns = [challenge, rebuttal, counter]
    synthesis = generate_structured_json(
        synth_config,
        prompt=_synthesis_prompt(pair, proponent, challenger, turns),
        schema_path=verdict_schema,
        run_dir=run_dir,
        output_stem="04-synthesis",
        search=True,
    )
    synthesis = _normalize_synthesis(synthesis, synthesizer_agent=synth_agent)

    created_at = now_local_iso()
    dialogue_id = hashlib.sha256(f"{pair['pair_id']}:{created_at}".encode("utf-8")).hexdigest()[:16]
    title = _dialogue_title(pair, synthesis)
    slug = f"{created_at[:10]}-{slugify(title)[:72]}"
    _notify(
        notify,
        "Synthesis complete",
        f"{synthesis.get('outcome', 'unknown')}: {_clean(synthesis.get('public_brief') or synthesis.get('summary'), limit=180)}",
    )

    return {
        "dialogue_id": dialogue_id,
        "slug": slug,
        "title": title,
        "created_at": created_at,
        "pair": pair,
        "turns": turns,
        "synthesis": synthesis,
        "execution_id": execution_id,
        "run_dir": str(run_dir.relative_to(root)),
        "run_ids": [],
        "status": "complete",
    }


def _dialogue_markdown(dialogue: dict[str, Any]) -> str:
    pair = dialogue["pair"]
    synthesis = dialogue["synthesis"]
    turns = dialogue.get("turns") or []
    challenge = turns[0] if len(turns) > 0 else {}
    rebuttal = turns[1] if len(turns) > 1 else {}
    counter = turns[2] if len(turns) > 2 else {}
    return f"""---
title: {_yaml_string(dialogue.get('title'), limit=180)}
date: {_yaml_string(str(dialogue.get('created_at'))[:10], limit=32)}
dialogue_id: {_yaml_string(dialogue.get('dialogue_id'), limit=80)}
outcome: {_yaml_string(synthesis.get('outcome'), limit=80)}
proponent: {_yaml_string(pair.get('proponent_agent'), limit=80)}
challenger: {_yaml_string(pair.get('challenger_agent'), limit=80)}
proponent_idea: {_yaml_string(pair.get('proponent_title'), limit=180)}
challenger_idea: {_yaml_string(pair.get('challenger_title'), limit=180)}
---

# {_clean(dialogue.get('title'), limit=180)}

**The tension:** {_clean(pair.get('tension_source'), limit=400)}

## Steelman And Challenge

**Steelman:** {_clean(challenge.get('steelman'), limit=1200)}

{_clean(challenge.get('argument'), limit=5000)}

## Rebuttal

{_clean(rebuttal.get('argument'), limit=5000)}

**Crux:** {_clean(rebuttal.get('crux'), limit=1200)}

## Counter-Rebuttal

{_clean(counter.get('argument'), limit=5000)}

## What Emerged

**Outcome:** {synthesis.get('outcome')}

{_clean(synthesis.get('summary'), limit=5000)}

**Convergence claim:** {_clean(synthesis.get('convergence_claim'), limit=1600) or "None recorded."}

**Unresolved crux:** {_clean(synthesis.get('unresolved_crux'), limit=1600) or "None recorded."}

**Next frontier question:** {_clean(synthesis.get('new_frontier_question'), limit=1600) or "None recorded."}
"""


def _write_convergence(root: Path, dialogue: dict[str, Any], rules: dict[str, Any]) -> str | None:
    outcome = str((dialogue.get("synthesis") or {}).get("outcome") or "")
    allowed = {str(item) for item in rules.get("outcomes_that_write_convergence") or []}
    if outcome not in allowed:
        return None
    pair = dialogue["pair"]
    synthesis = dialogue["synthesis"]
    filename = f"{str(dialogue.get('created_at'))[:10]}-{slugify(str(dialogue.get('title') or 'dialogue'))}.md"
    relative = f"findings/convergences/{filename}"
    content = f"""# Dialogue Convergence: {_clean(dialogue.get('title'), limit=180)}

Dialogue ID: {dialogue.get('dialogue_id')}
Outcome: {outcome}
Agents: {pair.get('proponent_agent')} and {pair.get('challenger_agent')}

## Shared Movement

{_clean(synthesis.get('convergence_claim') or synthesis.get('summary'), limit=5000)}

## Remaining Crux

{_clean(synthesis.get('unresolved_crux') or 'No unresolved crux was recorded.', limit=2000)}

## Next Question

{_clean(synthesis.get('new_frontier_question') or 'No new frontier question was recorded.', limit=2000)}
"""
    Librarian(root).write_text(relative, content)
    return relative


def _append_concept_edges(root: Path, edges: list[dict[str, Any]]) -> None:
    if not edges:
        return
    path = root / "graph" / "concept-graph.seed.json"
    graph = _read_json(path, {"nodes": [], "edges": []})
    existing = {
        (
            str(edge.get("source") or ""),
            str(edge.get("target") or ""),
            str(edge.get("relation") or ""),
        )
        for edge in graph.get("edges") or []
    }
    changed = False
    for edge in edges:
        key = (
            str(edge.get("source") or ""),
            str(edge.get("target") or ""),
            str(edge.get("relation") or ""),
        )
        if not all(key) or key in existing:
            continue
        graph.setdefault("edges", []).append(edge)
        existing.add(key)
        changed = True
    if changed:
        path.write_text(
            json.dumps(graph, indent=2, ensure_ascii=True, sort_keys=False),
            encoding="utf-8",
        )


def write_artifacts(
    config: EngineConfig,
    dialogue: dict[str, Any],
    *,
    audit_syntheses: bool = True,
    notify: bool = False,
) -> None:
    root = config.root
    rules = load_dialectic_rules(root)
    librarian = Librarian(root)
    (root / "reviews" / "dialogues").mkdir(parents=True, exist_ok=True)

    sanitized_dialogue = _sanitize_value(dialogue)
    dialogue.clear()
    dialogue.update(sanitized_dialogue)
    synthesis = dialogue["synthesis"]
    candidate = synthesis.get("candidate_synthesis")
    if candidate:
        idea = _idea_from_candidate(
            candidate,
            agent=str(synthesis.get("synthesizer_agent") or "codex"),
            dialogue_id=str(dialogue["dialogue_id"]),
            parent_titles=[
                str(dialogue["pair"].get("proponent_title") or ""),
                str(dialogue["pair"].get("challenger_title") or ""),
            ],
        )
        if idea:
            idea_path = librarian.save_idea(idea)
            synthesis["candidate_synthesis_idea_id"] = idea.identity()
            synthesis["candidate_synthesis_path"] = str(idea_path.relative_to(root))
            if audit_syntheses and not config.dry_run and config.provider != "offline":
                audit_config = _agent_config(config, "codex")
                audit_new_ideas(
                    audit_config,
                    [idea],
                    run_ids=[],
                    execution_id=f"dialogue-{dialogue['dialogue_id']}",
                )

    convergence_path = _write_convergence(root, dialogue, rules)
    if convergence_path:
        dialogue["convergence_path"] = convergence_path

    outcome_record = {
        "created_at": dialogue["created_at"],
        "dialogue_id": dialogue["dialogue_id"],
        "idea_ids": [dialogue["pair"]["idea_a"], dialogue["pair"]["idea_b"]],
        "outcome": synthesis.get("outcome"),
        "summary": synthesis.get("summary"),
        "public_brief": synthesis.get("public_brief"),
        "unresolved_crux": synthesis.get("unresolved_crux"),
        "new_frontier_question": synthesis.get("new_frontier_question"),
        "recommended_adjustments": synthesis.get("recommended_adjustments") or {},
        "candidate_synthesis_idea_id": synthesis.get("candidate_synthesis_idea_id"),
    }
    _append_jsonl(root / DIALOGUE_OUTCOMES, outcome_record)

    json_path = root / "reviews" / "dialogues" / f"{dialogue['slug']}.json"
    markdown_path = root / "reviews" / "dialogues" / f"{dialogue['slug']}.md"
    dialogue["json_path"] = str(json_path.relative_to(root))
    dialogue["markdown_path"] = str(markdown_path.relative_to(root))
    json_path.write_text(
        json.dumps(dialogue, indent=2, ensure_ascii=True, sort_keys=True),
        encoding="utf-8",
    )
    markdown_path.write_text(_dialogue_markdown(dialogue), encoding="utf-8")
    _append_jsonl(root / DIALOGUE_LEDGER, dialogue)

    _append_concept_edges(root, synthesis.get("new_concept_edges") or [])

    method_growth = _clean(synthesis.get("method_growth"), limit=220)
    public_brief = _clean(synthesis.get("public_brief") or synthesis.get("summary"), limit=220)
    if method_growth or public_brief:
        _append_jsonl(
            root / "publication" / "growth" / "growth.jsonl",
            {
                "agents": sorted({dialogue["pair"]["proponent_agent"], dialogue["pair"]["challenger_agent"]}),
                "created_at": dialogue["created_at"],
                "date": str(dialogue["created_at"])[:10],
                "execution_id": dialogue["execution_id"],
                "importance": 0.72,
                "knowledge": [public_brief] if public_brief else [],
                "method": [method_growth] if method_growth else [],
                "run_ids": [],
                "titles": [dialogue["title"]],
            },
        )

    refresh_frontiers(root)
    _notify(notify, "Artifacts written", f"Dialogue written: {dialogue['title']}")


def run_dialectic(
    config: EngineConfig,
    *,
    max_pairs: int = 1,
    execution_id: str | None = None,
    force_pair: tuple[str, str] | None = None,
    detect_only: bool = False,
    audit_syntheses: bool = True,
    notify: bool = False,
    ignore_cooldown: bool = False,
) -> list[dict[str, Any]]:
    execution_id = execution_id or datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    pairs = detect_tensions(
        config.root,
        max_pairs=max_pairs,
        force_pair=force_pair,
        ignore_cooldown=ignore_cooldown,
    )
    if detect_only:
        return []
    records: list[dict[str, Any]] = []
    for pair in pairs:
        dialogue = stage_dialogue(config, pair, execution_id=execution_id, notify=notify)
        write_artifacts(
            config,
            dialogue,
            audit_syntheses=audit_syntheses,
            notify=notify,
        )
        records.append(dialogue)
    return records


def backfill_dialogues(
    config: EngineConfig,
    *,
    max_dialogues: int,
    execution_id: str | None = None,
    audit_syntheses: bool = False,
    notify: bool = False,
) -> list[dict[str, Any]]:
    execution_id = execution_id or "backfill-" + datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    records: list[dict[str, Any]] = []
    librarian = Librarian(config.root)
    while len(records) < max_dialogues:
        pairs = detect_tensions(
            config.root,
            max_pairs=1,
            ignore_cooldown=True,
        )
        if not pairs:
            break
        pair = pairs[0]
        try:
            dialogue = stage_dialogue(config, pair, execution_id=execution_id, notify=notify)
            write_artifacts(
                config,
                dialogue,
                audit_syntheses=audit_syntheses,
                notify=notify,
            )
            records.append(dialogue)
        except Exception as exc:
            librarian.append_jsonl(
                "runs/dialogue-backfill-errors.jsonl",
                {
                    "at": now_local_iso(),
                    "error": repr(exc),
                    "execution_id": execution_id,
                    "pair_id": pair.get("pair_id"),
                },
            )
            raise
    librarian.append_jsonl(
        "runs/dialogue-backfill-events.jsonl",
        {
            "at": now_local_iso(),
            "count": len(records),
            "execution_id": execution_id,
            "max_dialogues": max_dialogues,
        },
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or inspect Lumenary cross-agent dialogues.")
    parser.add_argument("--max-pairs", type=int, default=1)
    parser.add_argument("--max-dialogues", type=int, default=None)
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--detect-only", action="store_true")
    parser.add_argument("--force-pair", nargs=2, metavar=("IDEA_ID_A", "IDEA_ID_B"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-originality-audit", action="store_true")
    parser.add_argument("--notify", action="store_true")
    parser.add_argument("--ignore-cooldown", action="store_true")
    parser.add_argument("--codex-model", default=None)
    parser.add_argument("--claude-model", default="opus")
    parser.add_argument("--provider", default=None, help="Compatibility option. Dialogues use both configured agents.")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    provider = "offline" if args.dry_run else "codex-cli"
    config = EngineConfig.load(
        root=root,
        agent="codex",
        provider=provider,
        dry_run=args.dry_run,
        codex_model=args.codex_model,
        codex_search=True,
        claude_model=args.claude_model,
    )
    if args.backfill:
        records = backfill_dialogues(
            config,
            max_dialogues=args.max_dialogues or args.max_pairs,
            audit_syntheses=not args.skip_originality_audit,
            notify=args.notify,
        )
    else:
        records = run_dialectic(
            config,
            max_pairs=args.max_pairs,
            force_pair=tuple(args.force_pair) if args.force_pair else None,
            detect_only=args.detect_only,
            audit_syntheses=not args.skip_originality_audit,
            notify=args.notify,
            ignore_cooldown=args.ignore_cooldown,
        )
    if args.detect_only:
        agenda = _read_json(root / DIALOGUE_AGENDA, {"selected_pairs": []})
        print(json.dumps({"event": "dialogue-detect", "selected": len(agenda.get("selected_pairs") or [])}, sort_keys=True))
        return
    print(
        json.dumps(
            {
                "event": "dialogue-backfill-complete" if args.backfill else "dialogue-complete",
                "count": len(records),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
