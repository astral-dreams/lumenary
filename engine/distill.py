"""Generate reader-facing insight distillations for findings."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .process_control import register_child, unregister_child
from .schemas import IdeaRecord, IdeaScores, now_local_iso, slugify


DISTILLATION_STORE = "publication/distillations.jsonl"
DISTILL_TIMEOUT_SECONDS = 300

DISTILL_PROMPT = """# Lumenary Insight Distillation

You are writing the public insight card and At a Glance text for The Lumenary.

Read the finding below. Distill it into reader-facing language.

## Writing Rules

- Write like the texts we study: simple, memorable, and direct.
- Do not use Sanskrit, Pali, Arabic, Greek, or Chinese terms.
- Do not use academic hedging.
- Do not use research jargon.
- Do not use em dashes.
- Do not start with "This finding".
- Lead with the human question or the living insight.
- The insight headline must land like a proverb.
- The plainSummary is for the Insights card: one sentence, maximum 28 words.
- The atAGlance section is for the finding page: one paragraph, 3 to 4 short sentences.
- Use one idea per sentence.

## Required JSON

Return exactly one JSON object with:

- insight: proverb-like headline, maximum 10 words
- plainSummary: one short sentence for the Insights card
- atAGlance: one paragraph of 3 to 4 short sentences
- match: array with one unique lowercased phrase from the title
- tags: array of 1 to 5 simple tags

## Finding

Title: {title}
Type: {idea_type}
Agent: {agent}

Original Claim:
{original_claim}

Why It Might Be New:
{why_it_might_be_new}

Critique:
{critique}
"""

ACADEMIC_REPLACEMENTS = {
    "advaita": "one path",
    "anatta": "no fixed self",
    "anatman": "no fixed self",
    "atman": "self",
    "barzakh": "threshold",
    "brahman": "the ground of being",
    "buddhism": "another path",
    "buddhist": "another path",
    "contemplative": "practice",
    "convergence": "agreement",
    "daoism": "a nature-centered path",
    "daoist": "a nature-centered path",
    "epistemic": "about knowing",
    "fana": "letting go",
    "inferential": "concluding",
    "metaphysical": "about what is real",
    "negation": "letting go",
    "neoplatonic": "ancient philosophical",
    "ontological": "about what is real",
    "phenomenological": "felt",
    "prasanga": "testing a claim by its consequences",
    "self-negation": "letting go of the self",
    "sufi": "a love-centered path",
    "sufism": "a love-centered path",
    "sunyata": "emptiness",
    "tajalli": "disclosure",
    "translation strain": "the bend in the bridge",
    "wu wei": "unforced action",
    "xinzhai": "empty listening",
    "zhuangzi": "an old teacher",
    "zuowang": "forgetting the self",
}

INSIGHT_STOPWORDS = {
    "as",
    "in",
    "of",
    "on",
    "the",
    "to",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _without_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _plain_text(value: str) -> str:
    plain = _without_diacritics(value)
    plain = plain.replace("\u2014", ":")
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\([^)]*\)", "", plain)
    plain = re.sub(r"\bThis finding says\s+", "", plain, flags=re.IGNORECASE)
    plain = re.sub(r"\bThis finding\b", "This", plain, flags=re.IGNORECASE)
    for technical, readable in ACADEMIC_REPLACEMENTS.items():
        plain = re.sub(
            rf"\b{re.escape(technical)}\b",
            readable,
            plain,
            flags=re.IGNORECASE,
        )
    return _clean_text(plain)


def _sentences(value: str) -> list[str]:
    plain = _plain_text(value)
    parts = re.findall(r"[^.!?]+[.!?]", plain)
    if parts:
        return [_clean_text(part) for part in parts]
    return [_clean_text(plain)] if plain else []


def _clip_words(value: str, limit: int) -> str:
    words = _clean_text(value).split()
    if len(words) <= limit:
        return _clean_text(value)
    clipped = " ".join(words[:limit]).rstrip(".,;:")
    return f"{clipped}."


def _word_count(value: str) -> int:
    return len(re.findall(r"\b[\w']+\b", value))


def _title_phrase(title: str) -> str:
    phrase = title.split(":", 1)[0]
    phrase = re.sub(r"\s+", " ", phrase).strip().lower()
    return phrase[:90] or title.lower()[:90]


def _fallback_insight(idea: IdeaRecord) -> str:
    title = _plain_text(idea.title.split(":", 1)[0])
    words = [
        word.strip(".,;:!?")
        for word in title.split()
        if word.strip(".,;:!?").lower() not in INSIGHT_STOPWORDS
    ]
    if not words:
        words = ["Look", "again"]
    headline = " ".join(words[:10]).strip()
    if not headline.endswith((".", "?", "!")):
        headline += "."
    return headline[:1].upper() + headline[1:]


def _fallback_plain_summary(idea: IdeaRecord) -> str:
    for sentence in _sentences(idea.original_claim):
        if sentence:
            return _clip_words(sentence, 28)
    return _fallback_insight(idea)


def _fallback_at_a_glance(idea: IdeaRecord) -> str:
    candidates = _sentences(idea.original_claim) + _sentences(idea.why_it_might_be_new)
    clean = [sentence for sentence in candidates if sentence]
    if len(clean) < 3:
        clean.append("The question is what changes when the idea is carried into ordinary life.")
    if len(clean) < 3:
        clean.append("A good insight should leave the reader seeing one familiar thing differently.")
    return " ".join(_clip_words(sentence, 22) for sentence in clean[:4])


def _fallback_tags(idea: IdeaRecord) -> list[str]:
    haystack = f"{idea.title} {idea.original_claim} {' '.join(idea.source_basis)}".lower()
    tags: list[str] = []
    for tag, terms in [
        ("advaita", ["advaita", "vedanta", "atman", "brahman", "upanishad"]),
        ("buddhism", ["buddh", "anatta", "sunyata", "zen", "dogen"]),
        ("daoism", ["dao", "wu wei", "zhuangzi"]),
        ("sufism", ["sufi", "ibn arabi", "fana", "barzakh"]),
        ("consciousness", ["consciousness", "attention", "self-model"]),
        ("time and matter", ["time", "matter", "physics", "quantum", "field"]),
        ("method", ["method", "comparison", "convergence", "translation"]),
        ("practice", ["practice", "meditation", "inquiry"]),
    ]:
        if any(term in haystack for term in terms):
            tags.append(tag)
    return tags[:5] or ["general"]


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return json.loads(stripped[start : end + 1])
    raise ValueError("Output did not contain a JSON object.")


def _run_codex_distiller(config: EngineConfig, prompt: str, idea: IdeaRecord) -> dict[str, Any] | None:
    run_id = f"{now_local_iso().replace(':', '').replace('+', '-')}-distill-{slugify(idea.title)[:48]}"
    run_dir = config.root / "runs" / "distillations" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "codex-distillation.json"
    schema_path = config.root / "engine" / "json_schemas" / "insight_distillation.schema.json"
    command = [
        "codex",
        "exec",
        "--cd",
        str(config.root),
        "--sandbox",
        config.codex_sandbox,
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(output_path),
        "--color",
        "never",
    ]
    if config.codex_model:
        command.extend(["--model", config.codex_model])
    command.append("-")

    process = subprocess.Popen(
        command,
        cwd=config.root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    register_child(process)
    try:
        stdout, stderr = process.communicate(
            input=prompt,
            timeout=min(config.codex_timeout_seconds, DISTILL_TIMEOUT_SECONDS),
        )
    except subprocess.TimeoutExpired:
        process.terminate()
        process.communicate(timeout=15)
        return None
    finally:
        unregister_child(process)

    (run_dir / "codex-distillation.stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "codex-distillation.stderr.log").write_text(stderr, encoding="utf-8")
    if process.returncode != 0:
        return None

    raw = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
    try:
        return _extract_json_object(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def _run_claude_distiller(config: EngineConfig, prompt: str) -> dict[str, Any] | None:
    schema_path = config.root / "engine" / "json_schemas" / "insight_distillation.schema.json"
    schema_json = schema_path.read_text(encoding="utf-8")
    command = [
        "claude",
        "-p",
        "--output-format",
        "json",
        "--json-schema",
        schema_json,
        "--no-session-persistence",
    ]
    if config.claude_model:
        command.extend(["--model", config.claude_model])

    process = subprocess.Popen(
        command,
        cwd=config.root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    register_child(process)
    try:
        stdout, _stderr = process.communicate(input=prompt, timeout=DISTILL_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.communicate(timeout=15)
        return None
    finally:
        unregister_child(process)

    if process.returncode != 0:
        return None

    try:
        outer = json.loads(stdout)
        result = outer.get("result", outer) if isinstance(outer, dict) else stdout
        if isinstance(result, str):
            return _extract_json_object(result)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError, TypeError):
        return None
    return None


def _normalize_result(raw: dict[str, Any] | None, idea: IdeaRecord) -> dict[str, Any]:
    raw = raw or {}
    insight = _plain_text(str(raw.get("insight") or _fallback_insight(idea)))
    plain_summary = _plain_text(str(raw.get("plainSummary") or _fallback_plain_summary(idea)))
    at_a_glance = _plain_text(str(raw.get("atAGlance") or _fallback_at_a_glance(idea)))

    if _word_count(insight) > 10:
        insight = _fallback_insight(idea)
    if _word_count(plain_summary) > 28:
        plain_summary = _clip_words(plain_summary, 28)

    at_sentences = _sentences(at_a_glance)
    if len(at_sentences) < 3:
        at_a_glance = _fallback_at_a_glance(idea)
    elif len(at_sentences) > 4:
        at_a_glance = " ".join(at_sentences[:4])

    match = [
        _plain_text(str(item)).lower()
        for item in raw.get("match", [])
        if _plain_text(str(item))
    ]
    if not match:
        match = [_title_phrase(idea.title)]

    tags = [
        _plain_text(str(item)).lower()
        for item in raw.get("tags", [])
        if _plain_text(str(item))
    ] or _fallback_tags(idea)

    return {
        "agent": idea.agent,
        "atAGlance": at_a_glance,
        "created_at": now_local_iso(),
        "ideaId": idea.identity(),
        "insight": insight,
        "match": match[:3],
        "plainSummary": plain_summary,
        "tags": tags[:5],
        "title": idea.title,
    }


def _distill_idea(config: EngineConfig, idea: IdeaRecord) -> dict[str, Any]:
    prompt = DISTILL_PROMPT.format(
        title=idea.title,
        idea_type=idea.idea_type,
        agent=idea.agent,
        original_claim=idea.original_claim,
        why_it_might_be_new=idea.why_it_might_be_new,
        critique=idea.critique,
    )
    raw: dict[str, Any] | None = None
    if config.provider == "codex-cli" and not config.dry_run:
        raw = _run_codex_distiller(config, prompt, idea)
    elif config.provider == "claude-code" and not config.dry_run:
        raw = _run_claude_distiller(config, prompt)
    return _normalize_result(raw, idea)


def _existing_idea_ids(root: Path) -> set[str]:
    store = root / DISTILLATION_STORE
    if not store.exists():
        return set()
    ids: set[str] = set()
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        idea_id = str(record.get("ideaId") or "")
        if idea_id:
            ids.add(idea_id)
    return ids


def _content_ts_matches(root: Path) -> set[str]:
    path = root / "src" / "lib" / "content.ts"
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8").lower()
    matches: set[str] = set()
    for match_block in re.findall(r"match:\s*\[([^\]]+)\]", text):
        for term in re.findall(r'"([^"]+)"', match_block):
            matches.add(term.lower())
    return matches


def _has_static_distillation(root: Path, idea: IdeaRecord) -> bool:
    haystack = f"{idea.title} {idea.original_claim}".lower()
    return any(match in haystack for match in _content_ts_matches(root))


def distill_new_ideas(config: EngineConfig, ideas: list[IdeaRecord]) -> int:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()
    existing_ids = _existing_idea_ids(config.root)
    count = 0

    for idea in ideas:
        if idea.status == "seed-fixture":
            continue
        if idea.identity() in existing_ids:
            continue
        if _has_static_distillation(config.root, idea):
            continue

        record = _distill_idea(config, idea)
        librarian.upsert_jsonl_by_key(DISTILLATION_STORE, record, key="ideaId")
        existing_ids.add(idea.identity())
        count += 1

    return count


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


def backfill_distillations(config: EngineConfig, *, limit: int = 0) -> int:
    existing_ids = _existing_idea_ids(config.root)
    ideas: list[IdeaRecord] = []
    for record in reversed(_read_idea_records(config.root)):
        idea_id = str(record.get("idea_id") or "")
        if not idea_id or idea_id in existing_ids:
            continue
        idea = _idea_from_record(record)
        if idea.status == "seed-fixture" or _has_static_distillation(config.root, idea):
            continue
        ideas.append(idea)
        if limit and len(ideas) >= limit:
            break
    return distill_new_ideas(config, list(reversed(ideas)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Lumenary insight distillations.")
    parser.add_argument("--backfill", action="store_true", help="Create missing distillations from ideas.jsonl.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum backfill records. Use 0 for all.")
    parser.add_argument("--provider", default="codex-cli", help="codex-cli, claude-code, or offline.")
    parser.add_argument("--model", default=None, help="Optional provider model.")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic fallback text.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_kwargs: dict[str, str | None] = {}
    if args.provider == "claude-code":
        model_kwargs["claude_model"] = args.model
    else:
        model_kwargs["codex_model"] = args.model
    config = EngineConfig.load(
        provider=args.provider,
        dry_run=args.dry_run or args.provider == "offline",
        **model_kwargs,
    )
    if args.backfill:
        count = backfill_distillations(config, limit=args.limit)
        print(f"distillations={count}")


if __name__ == "__main__":
    main()
