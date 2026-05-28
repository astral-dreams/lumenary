from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .config import EngineConfig
from .schemas import IdeaRecord, now_local_iso, slugify


LEDGER = "reviews/human-condition/audits.jsonl"


@dataclass(frozen=True)
class HumanConditionPattern:
    id: str
    keywords: tuple[str, ...]
    problem: str
    cohort: str
    non_fit: str
    why_it_matters: str
    practical_implication: str
    caution: str
    source_card_ids: tuple[str, ...]
    next_question: str


PATTERNS: tuple[HumanConditionPattern, ...] = (
    HumanConditionPattern(
        id="threshold-and-beginning",
        keywords=(
            "begin",
            "beginning",
            "entry",
            "start",
            "first step",
            "first-break",
            "support",
            "trust",
            "teacher",
            "family",
            "ritual",
            "community",
            "crisis",
            "imitation",
            "permission",
            "scaffold",
            "threshold",
        ),
        problem="Feeling unable to begin real change alone, and the shame that follows when a person thinks willpower should be enough.",
        cohort="People standing at the edge of a practice, recovery, faith, repair, or life change who need support before they can fully choose the next step.",
        non_fit="Not enough for emergencies, coercive groups, unsafe teachers, acute addiction withdrawal, psychosis, or any beginning that requires immediate human care.",
        why_it_matters="It tells beginners that needing help is not failure; it is often how serious change starts.",
        practical_implication="A practice derived from this finding should ask what support makes the first step safer, repeatable, and honest.",
        caution="Do not use support language to excuse dependency, coercion, or surrendering judgment to an unsafe authority.",
        source_card_ids=(
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-surgeon-general-social-connection-advisory",
            "modern-human-condition-pew-where-americans-find-meaning-in-life",
        ),
        next_question="What support would let a person begin without shame, and what support would make them less free?",
    ),
    HumanConditionPattern(
        id="practice-transfer-confusion",
        keywords=(
            "transfer",
            "cross-training",
            "method-switch",
            "trained function",
            "grain",
            "grained",
            "practice ecology",
            "procedural residue",
            "hybrid",
            "integration",
            "re-graining",
            "skill transfer",
            "method transfer",
            "practice transfer",
            "formal boundary",
            "formal boundaries",
            "dissolution",
            "surrender",
            "safeguard",
            "re-appropriation",
        ),
        problem="Spiritual confusion caused by borrowing practices without knowing what kind of person, danger, or transformation they were built for.",
        cohort="People blending meditation, therapy, spiritual teachings, productivity methods, or different traditions without knowing which habits each method leaves behind.",
        non_fit="Not enough for acute crisis, trauma treatment, coercive groups, or advanced practice that needs a qualified human teacher.",
        why_it_matters="It protects seekers from assuming that every useful practice can be safely moved into every life or every path.",
        practical_implication="A practice derived from this finding should ask what a method trains, what it leaves behind, and what happens when it is moved into another setting.",
        caution="Do not use this to make experimentation fearful; use it to make experimentation honest.",
        source_card_ids=(
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-surgeon-general-social-connection-advisory",
        ),
        next_question="What human problem appears when this method is borrowed by someone outside its original setting?",
    ),
    HumanConditionPattern(
        id="achievement-pressure",
        keywords=(
            "effort",
            "work",
            "doer",
            "doing",
            "claim",
            "claimant",
            "credit",
            "gift",
            "capacity",
            "result",
            "handoff",
            "ownership",
            "agency",
            "function",
        ),
        problem="Achievement pressure, perfectionism, burnout, and the habit of treating performance as proof of personal worth.",
        cohort="People whose sense of worth rises and falls with usefulness, praise, failure, correction, visible output, or being seen as capable.",
        non_fit="Not the primary lens for people whose main struggle is crisis, addiction withdrawal, severe depression, under-motivation, or work already done with ease and love.",
        why_it_matters="It can separate real responsibility from the extra burden of turning every act into a verdict on the self.",
        practical_implication="A practice derived from this finding should test whether effort stays careful when identity is no longer on trial.",
        caution="Do not use this to excuse carelessness, avoid repair, or deny the consequences of action.",
        source_card_ids=(
            "modern-human-condition-curran-hill-perfectionism-increasing",
            "modern-human-condition-who-burn-out-occupational-phenomenon",
            "modern-human-condition-apa-stress-in-america-2024",
            "modern-human-condition-gallup-state-global-workplace-2024",
        ),
        next_question="Where does this finding help a person work more cleanly, and where would it make them less responsible?",
    ),
    HumanConditionPattern(
        id="loneliness-and-disconnection",
        keywords=(
            "love",
            "devotion",
            "receiver",
            "person",
            "second-person",
            "other",
            "relation",
            "relationship",
            "community",
            "teacher",
            "transmission",
            "carrier",
            "availability",
            "available",
            "belonging",
        ),
        problem="Loneliness, disconnection, and the loss of being needed by a real person or community.",
        cohort="People who can become inwardly clear while remaining isolated, unavailable, unseen, or unused by the world around them.",
        non_fit="Not enough for acute social danger, abuse, coercive communities, or clinical loneliness that needs human care and support.",
        why_it_matters="It asks whether insight returns a person to life with more love, availability, and repair.",
        practical_implication="A practice derived from this finding should test whether calm or insight makes someone more reachable and more responsive.",
        caution="Do not turn relationship into a demand for self-erasure or forced availability.",
        source_card_ids=(
            "modern-human-condition-surgeon-general-social-connection-advisory",
            "modern-human-condition-world-happiness-report-2024",
            "modern-human-condition-gallup-state-global-workplace-2024",
        ),
        next_question="What real person, duty, or need would this finding make harder to ignore?",
    ),
    HumanConditionPattern(
        id="identity-and-meaning-loss",
        keywords=(
            "self",
            "no-self",
            "identity",
            "witness",
            "soul",
            "atman",
            "anatta",
            "consciousness",
            "negation",
            "remainder",
            "residue",
            "custody",
            "release",
            "meaning",
            "worth",
        ),
        problem="Meaning loss, identity confusion, and the danger of using self-negation in a way that leaves a person unmoored.",
        cohort="People asking who they are, what remains when old identities fall away, or how to loosen ego without losing care and responsibility.",
        non_fit="Not enough for dissociation, psychosis, suicidal crisis, or any state where self-inquiry increases instability.",
        why_it_matters="It can protect deep inquiry from becoming vague self-erasure or a new hidden ego claim.",
        practical_implication="A practice derived from this finding should name what must remain after letting go: care, memory, responsibility, or simple awareness.",
        caution="Do not turn metaphysical uncertainty into pressure to dissolve the person faster than life can safely hold.",
        source_card_ids=(
            "modern-human-condition-pew-where-americans-find-meaning-in-life",
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-cdc-suicide-facts",
        ),
        next_question="What must remain intact for this insight to make life more honest rather than more empty?",
    ),
    HumanConditionPattern(
        id="anxiety-and-uncertainty",
        keywords=(
            "proof",
            "burden",
            "verification",
            "audit",
            "uncertainty",
            "ambiguity",
            "contradiction",
            "failure",
            "wrong",
            "confidence",
            "authority",
            "test",
            "alarm",
            "warning",
        ),
        problem="Anxiety, uncertainty, and the need for trustworthy ways to test strong claims without surrendering judgment.",
        cohort="People who are drawn to spiritual claims but need a way to ask what would break them before they build a life around them.",
        non_fit="Not a substitute for clinical anxiety care, emergency support, or qualified guidance in high-risk spiritual practice.",
        why_it_matters="It turns belief from passive acceptance into a disciplined relationship with evidence, doubt, and repair.",
        practical_implication="A practice derived from this finding should ask the reader to name what would count against a cherished belief.",
        caution="Do not let testing become endless avoidance, cynicism, or fear of commitment.",
        source_card_ids=(
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-apa-stress-in-america-2024",
        ),
        next_question="What would make this finding safer for a person who is anxious, suggestible, or desperate for certainty?",
    ),
    HumanConditionPattern(
        id="attention-and-digital-comparison",
        keywords=(
            "attention",
            "salience",
            "interface",
            "observer",
            "instrument",
            "awareness",
            "aperture",
            "visibility",
            "comparison",
            "mind",
            "perception",
            "seeing",
        ),
        problem="Attention capture, digital comparison, and the habit of needing the world to prove that one exists.",
        cohort="People whose attention is trained by reaction, comparison, speed, visibility, or constant self-monitoring.",
        non_fit="Not enough for addiction, withdrawal, obsessive spirals, or attention problems that need professional support.",
        why_it_matters="It can show how attention becomes a place where identity, desire, and reality are quietly negotiated.",
        practical_implication="A practice derived from this finding should test whether attention can become steadier without needing performance or visibility.",
        caution="Do not make attention practice another arena for self-measurement.",
        source_card_ids=(
            "modern-human-condition-youth-mental-health-social-media-advisory",
            "modern-human-condition-surgeon-general-social-connection-advisory",
        ),
        next_question="How would this finding change the way a person uses attention before comparison begins?",
    ),
    HumanConditionPattern(
        id="grief-change-and-time",
        keywords=(
            "time",
            "temporal",
            "being-time",
            "death",
            "mortality",
            "change",
            "impermanence",
            "return",
            "loss",
            "memory",
        ),
        problem="Grief, change, mortality, and the need to live inside time without being crushed by it.",
        cohort="People facing loss, aging, transition, endings, or the shock that life cannot be held still.",
        non_fit="Not a substitute for grief care, crisis care, or human support after traumatic loss.",
        why_it_matters="It can help distinguish insight about change from pressure to become peaceful too quickly.",
        practical_implication="A practice derived from this finding should let grief and change be observed without forcing consolation.",
        caution="Do not use philosophy of time to rush mourning or escape a real loss.",
        source_card_ids=(
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-cdc-suicide-facts",
        ),
        next_question="Does this finding help a person meet change more truthfully, or does it abstract away the pain?",
    ),
    HumanConditionPattern(
        id="addiction-and-compulsion",
        keywords=(
            "addiction",
            "compulsion",
            "craving",
            "attachment",
            "withdrawal",
            "habit",
            "desire",
            "appetite",
            "urge",
            "grasping",
        ),
        problem="Addiction, compulsion, craving, and the use of repeated behavior to regulate pain.",
        cohort="People caught in loops of craving, relief, shame, and return, especially where isolation and despair reinforce the loop.",
        non_fit="Not a standalone intervention for substance use disorder, withdrawal, overdose risk, or any acute addiction crisis.",
        why_it_matters="It can help distinguish moral failure language from a clearer view of pain, habit, environment, and care.",
        practical_implication="A practice derived from this finding should be low-risk, supportive, and explicit about when human care is required.",
        caution="Do not spiritualize addiction or treat willpower language as enough.",
        source_card_ids=(
            "modern-human-condition-samhsa-2023-nsduh",
            "modern-human-condition-cdc-overdose-prevention",
            "modern-human-condition-who-world-mental-health-report",
        ),
        next_question="What would make this safer and more honest for someone in a real compulsion loop?",
    ),
    HumanConditionPattern(
        id="misapplied-teaching",
        keywords=(
            "teaching",
            "method",
            "practice",
            "safeguard",
            "misuse",
            "warning",
            "audience",
            "teacher",
            "failure",
            "shadow",
            "bypass",
            "diagnosis",
            "correction",
        ),
        problem="Misapplied advice, spiritual overgeneralization, and the harm caused when a teaching forgets who it was meant to help.",
        cohort="People adopting strong teachings or practices without knowing whether the lesson fits their condition, danger, or stage.",
        non_fit="Not enough for emergency decisions, clinical crisis, coercive groups, or cases where a qualified human guide is needed.",
        why_it_matters="It keeps doctrine from becoming a weapon by forcing every lesson to remember its intended audience.",
        practical_implication="A practice derived from this finding should ask who the lesson is for before asking whether it is true.",
        caution="Do not use context-sensitivity to avoid a hard teaching that actually applies.",
        source_card_ids=(
            "modern-human-condition-who-world-mental-health-report",
            "modern-human-condition-surgeon-general-social-connection-advisory",
        ),
        next_question="Who could be harmed if this finding were taught without naming its audience?",
    ),
)


FALLBACK_SOURCES = (
    "modern-human-condition-pew-where-americans-find-meaning-in-life",
    "modern-human-condition-who-world-mental-health-report",
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _now_id(execution_id: str, idea_id: str) -> str:
    return hashlib.sha256(f"human-condition:{execution_id}:{idea_id}".encode("utf-8")).hexdigest()[:16]


def _idea_dict(idea: IdeaRecord | dict[str, Any]) -> dict[str, Any]:
    if isinstance(idea, IdeaRecord):
        return idea.to_dict()
    return idea


def _human_sources_from_basis(source_basis: Iterable[Any]) -> list[str]:
    found: list[str] = []
    for item in source_basis:
        for match in re.findall(r"modern-human-condition-[a-z0-9-]+", str(item).lower()):
            if match not in found:
                found.append(match)
    return found


def _candidate_target(record: dict[str, Any]) -> tuple[str, str, str]:
    candidates = [record.get("practice_candidate") or {}, record.get("teaching_candidate") or {}]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        problem = _clean(candidate.get("target_human_problem"))
        cohort = _clean(candidate.get("target_cohort"))
        non_fit = _clean(candidate.get("non_fit"))
        if problem or cohort:
            return problem, cohort, non_fit
    return "", "", ""


def _score_patterns(text: str) -> list[tuple[int, HumanConditionPattern, list[str]]]:
    normalized = text.lower()
    scored: list[tuple[int, HumanConditionPattern, list[str]]] = []
    for pattern in PATTERNS:
        matches = [keyword for keyword in pattern.keywords if keyword in normalized]
        if matches:
            scored.append((len(matches), pattern, matches[:8]))
    return sorted(scored, key=lambda item: (-item[0], item[1].id))


def audit_record(
    record: dict[str, Any],
    *,
    execution_id: str,
    run_ids: list[str] | None = None,
) -> dict[str, Any]:
    source_basis = [str(item) for item in record.get("source_basis") or []]
    idea_id = _clean(record.get("idea_id")) or hashlib.sha256(
        f"{record.get('agent')}:{record.get('title')}:{record.get('original_claim')}".encode("utf-8")
    ).hexdigest()[:16]
    direct_problem, direct_cohort, direct_non_fit = _candidate_target(record)
    text = " ".join(
        [
            _clean(record.get("title")),
            _clean(record.get("idea_type")),
            _clean(record.get("original_claim")),
            _clean(record.get("why_it_might_be_new")),
            _clean(record.get("critique")),
            " ".join(source_basis),
            " ".join(_clean(item) for item in record.get("next_research_directions") or []),
        ]
    )
    scored = _score_patterns(text)
    top_score, top_pattern, matches = scored[0] if scored else (0, None, [])
    basis_sources = _human_sources_from_basis(source_basis)

    if direct_problem or direct_cohort:
        pattern = top_pattern or PATTERNS[2]
        fit_status = "direct"
        primary_problem = direct_problem or pattern.problem
        target_cohort = direct_cohort or pattern.cohort
        non_fit = direct_non_fit or pattern.non_fit
        confidence = 0.82
        keywords = matches
    elif top_pattern and top_score >= 3:
        pattern = top_pattern
        fit_status = "direct"
        primary_problem = pattern.problem
        target_cohort = pattern.cohort
        non_fit = pattern.non_fit
        confidence = min(0.78, 0.48 + top_score * 0.06)
        keywords = matches
    elif top_pattern:
        pattern = top_pattern
        fit_status = "indirect"
        primary_problem = pattern.problem
        target_cohort = pattern.cohort
        non_fit = pattern.non_fit
        confidence = min(0.62, 0.38 + top_score * 0.06)
        keywords = matches
    else:
        pattern = None
        fit_status = "unclear"
        primary_problem = "No direct modern human problem is named yet."
        target_cohort = "Researchers and readers who may use the finding as background, not as a teaching or practice."
        non_fit = "Do not turn this finding into public advice until a real human problem, target cohort, and non-fit case are named."
        confidence = 0.24
        keywords = []

    source_card_ids = basis_sources or list(pattern.source_card_ids if pattern else FALLBACK_SOURCES)
    if basis_sources:
        confidence = min(0.9, confidence + 0.08)

    why_it_matters = (
        pattern.why_it_matters
        if pattern
        else "It may matter only after another step connects the abstract claim to conduct, belonging, care, or meaning."
    )
    practical_implication = (
        pattern.practical_implication
        if pattern
        else "The next step is to decide whether this finding should remain research background or become a targeted teaching candidate."
    )
    caution = (
        pattern.caution
        if pattern
        else "Do not promote this as guidance until the human problem and audience are explicit."
    )
    next_question = (
        pattern.next_question
        if pattern
        else "What recognizable human wound would this finding help clarify, and for whom?"
    )

    return {
        "agent": _clean(record.get("agent")),
        "audit_id": _now_id(execution_id, idea_id),
        "confidence": round(confidence, 2),
        "created_at": now_local_iso(),
        "execution_id": execution_id,
        "fit_status": fit_status,
        "idea_id": idea_id,
        "keywords_matched": keywords,
        "next_question": next_question,
        "non_fit": non_fit,
        "practical_implication": practical_implication,
        "primary_problem": primary_problem,
        "run_ids": run_ids or [],
        "source_card_ids": source_card_ids,
        "target_cohort": target_cohort,
        "title": _clean(record.get("title")),
        "why_it_matters": why_it_matters,
        "caution": caution,
    }


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


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n" for record in records)
    path.write_text(text, encoding="utf-8")


def audit_human_condition_fit(
    root: Path,
    ideas: list[IdeaRecord | dict[str, Any]],
    *,
    execution_id: str,
    run_ids: list[str] | None = None,
) -> int:
    records = [_idea_dict(idea) for idea in ideas]
    audits = [audit_record(record, execution_id=execution_id, run_ids=run_ids) for record in records]
    ledger_path = root / LEDGER
    existing = _read_jsonl(ledger_path)
    audited_ids = {audit["idea_id"] for audit in audits}
    retained = [record for record in existing if record.get("idea_id") not in audited_ids]
    _write_jsonl(ledger_path, [*retained, *audits])
    return len(audits)


def _read_ideas(root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(root / "hypotheses" / "ideas.jsonl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Lumenary findings against the modern human condition.")
    parser.add_argument(
        "mode",
        choices=["backfill"],
        help="backfill audits every idea in hypotheses/ideas.jsonl.",
    )
    parser.add_argument("--execution-id", default=f"human-condition-backfill-{slugify(now_local_iso())}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load()
    if args.mode == "backfill":
        ideas = _read_ideas(config.root)
        count = audit_human_condition_fit(
            config.root,
            ideas,
            execution_id=args.execution_id,
            run_ids=[args.execution_id],
        )
        print(f"human_condition_audits={count}")
        print(f"ledger={LEDGER}")


if __name__ == "__main__":
    main()
