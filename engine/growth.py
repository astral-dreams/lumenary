from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .librarian import Librarian
from .schemas import IdeaRecord, IdeaScores, now_local_iso


GROWTH_LEDGER = "publication/growth/growth.jsonl"
GROWTH_ITEM_LIMIT = 150

KNOWN_GROWTH_DISTILLATIONS = [
    {
        "matches": ["convergence as translation strain"],
        "knowledge": "We learned that agreement matters most when it shows what each side must bend.",
        "method": "We learned to test every bridge by asking what it distorts.",
    },
    {
        "matches": ["interface invariant"],
        "knowledge": "We learned that different paths may meet because human attention keeps presenting the same doors.",
        "method": "We learned to look for shared human pressures before naming hidden truths.",
    },
    {
        "matches": ["translation strain as a load test"],
        "knowledge": "We learned that a good comparison shows the cost of translation, not just the comfort of agreement.",
        "method": "We learned to score the bend, not just the bridge.",
    },
    {
        "matches": ["residue policy"],
        "knowledge": "We learned that when the self is stripped away, each path decides what may remain.",
        "method": "We learned to ask who is allowed to speak after letting go.",
    },
    {
        "matches": ["residual burden"],
        "knowledge": "We learned that after every no, a path still decides what the no permits.",
        "method": "We learned to watch the move that comes after refusal.",
    },
    {
        "matches": ["remainder pressure"],
        "knowledge": "We learned that when everything is denied, the mind still feels pressure to name what remains.",
        "method": "We learned to measure that pressure before calling it truth.",
    },
    {
        "matches": ["inferential gap"],
        "knowledge": "We learned that two paths can share an experience and draw opposite lessons from it.",
        "method": "We learned to separate what is seen from what is concluded.",
    },
    {
        "matches": ["processual remainder"],
        "knowledge": "We learned that what remains may be a passage, not a thing.",
        "method": "We learned to look for the doorway, not only the room.",
    },
    {
        "matches": ["expressive realism"],
        "knowledge": "We learned that time may not carry things; it may be how things shine.",
        "method": "We learned to test time by asking how life appears, not where it sits.",
    },
    {
        "matches": ["formal recurrence"],
        "knowledge": "We learned that modern models can repeat old questions instead of solving them.",
        "method": "We learned to ask whether a new language has only changed the costume.",
    },
    {
        "matches": ["same negation, the opposite inference"],
        "knowledge": "We learned that the same refusal can open two opposite roads.",
        "method": "We learned to follow identical methods to their different endings.",
    },
    {
        "matches": ["generative negation"],
        "knowledge": "We learned that some silences do not erase; they make room.",
        "method": "We learned to ask whether a no clears space for a new kind of yes.",
    },
    {
        "matches": ["reflexivity policy"],
        "knowledge": "We learned that every method changes when it turns back on itself.",
        "method": "We learned to ask what a tool does when it becomes the thing examined.",
    },
    {
        "matches": ["custody policy"],
        "knowledge": "We learned that when the old owner disappears, care still needs a keeper.",
        "method": "We learned to ask what carries responsibility after the self loosens.",
    },
    {
        "matches": ["instrument problem"],
        "knowledge": "We learned that agreement is stronger when different ways of seeing reach the same place.",
        "method": "We learned to inspect the instrument before trusting the report.",
    },
    {
        "matches": ["remainder grammar"],
        "knowledge": "We learned that what a path lets you say after silence reveals what it protects.",
        "method": "We learned to listen for the grammar that survives letting go.",
    },
    {
        "matches": ["epistemic organ"],
        "knowledge": "We learned that a path's idea of knowing shapes what it can find.",
        "method": "We learned to ask what part of the person a path trusts most.",
    },
    {
        "matches": ["negation has an address"],
        "knowledge": "We learned that a teaching's no depends on whom it is trying to free.",
        "method": "We learned to ask who the medicine is for before naming the cure.",
    },
    {
        "matches": ["realization topology"],
        "knowledge": "We learned that some awakenings arrive as events; others unfold as weather.",
        "method": "We learned to place an insight in time before comparing it.",
    },
    {
        "matches": ["comparison has a self"],
        "knowledge": "We learned that even comparison can try to possess what it studies.",
        "method": "We learned to empty our own grip before building a bridge.",
    },
    {
        "matches": ["determination gap"],
        "knowledge": "We learned that knowing yourself and knowing the world may not change together.",
        "method": "We learned to test self-insight and world-insight separately.",
    },
    {
        "matches": ["return is the audit"],
        "knowledge": "We learned that the real test of insight is how it returns to ordinary life.",
        "method": "We learned to judge depth by re-entry, not by the peak.",
    },
    {
        "matches": ["shadow of attainment"],
        "knowledge": "We learned that every cure can become its own disease.",
        "method": "We learned to ask what a path breaks when it succeeds.",
    },
    {
        "matches": ["each path has a different alarm"],
        "knowledge": "We learned that every path trains the heart to notice a different danger.",
        "method": "We learned to listen for the alarm before comparing the lesson.",
    },
    {
        "matches": ["verification architecture"],
        "knowledge": "We learned that a path proves insight by the kind of proof it already trusts.",
        "method": "We learned to ask who gets to certify awakening.",
    },
    {
        "matches": ["every insight has an appeal court"],
        "knowledge": "We learned that every insight eventually stands before a judge.",
        "method": "We learned to name the judge before trusting the verdict.",
    },
    {
        "matches": ["attentional commons"],
        "knowledge": "We learned that paths may look most alike where their deepest claims matter least.",
        "method": "We learned to question agreement when attention becomes quiet and plain.",
    },
    {
        "matches": ["silence has a stopping rule"],
        "knowledge": "We learned that every silence has a moment where more searching becomes noise.",
        "method": "We learned to ask where inquiry should stop.",
    },
    {
        "matches": ["devotional remainder"],
        "knowledge": "We learned that love may know what attention cannot see.",
        "method": "We learned to stop treating sight as the only form of knowing.",
    },
    {
        "matches": ["protected variable"],
        "knowledge": "We learned that after silence, each path protects one thing it will not surrender.",
        "method": "We learned to find the protected thing before declaring common ground.",
    },
]

ACADEMIC_REPLACEMENTS = {
    "advaita": "one path",
    "buddhist": "another path",
    "buddhism": "another path",
    "sufi": "a love-centered path",
    "sufism": "a love-centered path",
    "daoist": "a nature-centered path",
    "daoism": "a nature-centered path",
    "neoplatonic": "ancient philosophical",
    "epistemic": "about knowing",
    "ontological": "about what is real",
    "metaphysical": "about what is real",
    "phenomenological": "felt",
    "inferential": "concluding",
    "convergence": "agreement",
    "self-negation": "letting go of the self",
    "negation": "letting go",
    "contemplative": "practice",
    "translation strain": "the bend in the bridge",
    "remainder": "what remains",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _clip(value: str, limit: int = 210) -> str:
    clean = _clean_text(value)
    if len(clean) <= limit:
        return clean
    clipped = clean[: limit - 3].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{clipped}..."


def _without_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _plain_growth_text(value: str) -> str:
    plain = _without_diacritics(value)
    plain = plain.replace("\u2014", ":")
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\([^)]*\)", "", plain)
    plain = re.sub(
        r"\b[Aa]tman\b|\b[Aa]natta\b|\b[Aa]natman\b|\b[Bb]rahman\b|\b[Ss]unyata\b",
        "the self",
        plain,
    )
    plain = re.sub(r"\b[Ww]u wei\b|\b[Xx]inzhai\b|\b[Zz]uowang\b", "unforced seeing", plain)
    for academic, readable in ACADEMIC_REPLACEMENTS.items():
        plain = re.sub(rf"\b{re.escape(academic)}\b", readable, plain, flags=re.IGNORECASE)
    plain = _clean_text(plain)
    return plain.rstrip(".")


def _lower_first(value: str) -> str:
    if not value:
        return value
    return value[0].lower() + value[1:]


def _as_learned_that(value: str) -> str:
    plain = _plain_growth_text(value)
    if plain.lower().startswith("i learned that "):
        return _clip(plain, GROWTH_ITEM_LIMIT)
    return _clip(f"We learned that {_lower_first(plain)}.", GROWTH_ITEM_LIMIT)


def _as_learned_to(value: str) -> str:
    plain = _plain_growth_text(value)
    if plain.lower().startswith("i learned to "):
        return _clip(plain, GROWTH_ITEM_LIMIT)
    return _clip(f"We learned to {_lower_first(plain)}.", GROWTH_ITEM_LIMIT)


def _known_distillation(idea: IdeaRecord, field: str) -> str | None:
    haystack = idea.title.lower()
    ranked = sorted(
        KNOWN_GROWTH_DISTILLATIONS,
        key=lambda item: max(len(match) for match in item["matches"]),
        reverse=True,
    )
    for item in ranked:
        if any(match in haystack for match in item["matches"]):
            return item[field]
    return None


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
    known = _known_distillation(idea, "knowledge")
    if known:
        return known
    return _as_learned_that(_first_sentence(idea.original_claim, GROWTH_ITEM_LIMIT))


def _method_item(idea: IdeaRecord) -> str:
    known = _known_distillation(idea, "method")
    if known:
        return known
    direction = _protocol_direction(idea)
    if direction:
        return _as_learned_to(direction)
    if _method_source(idea):
        return "We learned to borrow a practice as a lens, then test where it fails."
    return "We learned to turn the critique into the next way of seeing."


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
