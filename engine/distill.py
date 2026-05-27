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
- Do not repeat the title, the insight headline, or the first At a Glance sentence in the bullets.
- Do not use machinery language in public copy: no "layered authorization," "distributed affordances," "institutional role," "operationalizes," "formal transfer," "gradient," "rubric," "locus," "claimant," or "grammar."
- Also avoid internal model words in public copy: no "architecture," "custody," "receiving surface," "residue," "grain," "threshold," "entry," "compound," "upstream," "downstream," "phenomenology," "authorization," "typology," or "taxonomy."
- The insight headline must land like a proverb.
- The publicTitle is the finding page title: maximum 10 words, plain, memorable, and not academic.
- The plainSummary is for the Insights card: one sentence, maximum 28 words.
- The atAGlance section is for the finding page: one paragraph, 3 to 4 short sentences.
- The keyPoints are for the finding page: 3 short bullets, direct and useful. Use them for meaning, human risk, and what to test.
- Use one idea per sentence.

## Required JSON

Return exactly one JSON object with:

- insight: proverb-like headline, maximum 10 words
- publicTitle: finding page title, maximum 10 words
- plainSummary: one short sentence for the Insights card
- atAGlance: one paragraph of 3 to 4 short sentences
- keyPoints: array of 3 short bullet points, each one sentence and under 18 words
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
    "affordance": "support",
    "affordances": "supports",
    "barzakh": "threshold",
    "brahman": "the ground of being",
    "buddhism": "another path",
    "buddhist": "another path",
    "contemplative": "practice",
    "convergence": "agreement",
    "daoism": "a nature-centered path",
    "daoist": "a nature-centered path",
    "distributed affordances": "ordinary supports",
    "epistemic": "about knowing",
    "fana": "letting go",
    "formal transfer": "clear handoff",
    "gradient": "slow change",
    "handoff density": "repeated turning points",
    "inferential": "concluding",
    "institutional role": "the path's role",
    "layered authorization": "many forms of permission and support",
    "locus": "place",
    "metaphysical": "about what is real",
    "negation": "letting go",
    "neoplatonic": "ancient philosophical",
    "ontological": "about what is real",
    "operationalizes": "turns into a test",
    "phenomenological": "felt",
    "prasanga": "testing a claim by its consequences",
    "claimant": "owner",
    "compound": "combined",
    "custody": "care",
    "downstream": "later",
    "entry": "beginning",
    "rubric": "test",
    "grain": "habit",
    "layered": "many-sided",
    "mechanism": "way",
    "phenomenology": "experience",
    "policy": "rule",
    "receiving surface": "human opening",
    "residue": "what remains",
    "self-negation": "letting go of the self",
    "sufi": "a love-centered path",
    "sufism": "a love-centered path",
    "sunyata": "emptiness",
    "tajalli": "disclosure",
    "translation strain": "the bend in the bridge",
    "threshold": "beginning",
    "typology": "set of types",
    "taxonomy": "set of types",
    "upstream": "earlier",
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

PUBLIC_BANNED_TERMS = (
    "layered authorization",
    "distributed affordances",
    "institutional role",
    "operationalizes",
    "formal transfer",
    "handoff density",
    "first-break",
    "affordance",
    "affordances",
    "authorization",
    "architecture",
    "claimant",
    "compound",
    "contemplative",
    "custody",
    "downstream",
    "entry",
    "epistemic",
    "empirically",
    "framework",
    "gradient",
    "grammar",
    "grain",
    "inferential",
    "interface",
    "institutional",
    "layered",
    "ledger",
    "locus",
    "mechanism",
    "metaphysical",
    "normative",
    "ontological",
    "operationalize",
    "phenomenology",
    "phenomenological",
    "policy",
    "receiving surface",
    "residue",
    "rubric",
    "taxonomy",
    "threshold",
    "topology",
    "typology",
    "upstream",
)


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


def _fingerprint(value: str) -> str:
    plain = _plain_text(value).lower()
    plain = re.sub(r"[^a-z0-9\s]", " ", plain)
    plain = re.sub(
        r"\b(the|a|an|and|or|but|to|of|in|on|for|with|that|this|it|is|are|was|were|be|being|been)\b",
        " ",
        plain,
    )
    return re.sub(r"\s+", " ", plain).strip()


def _point_repeats_text(point: str, text: str) -> bool:
    point_key = _fingerprint(point)
    text_key = _fingerprint(text)
    if not point_key or not text_key:
        return False
    return point_key in text_key


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


def _normalize_key_point(value: str) -> str:
    point = _clip_words(_plain_text(value), 18)
    point = point.strip(" -•\t")
    if point and not point.endswith((".", "?", "!")):
        point += "."
    return point


def _fallback_key_points(idea: IdeaRecord, at_a_glance: str = "") -> list[str]:
    candidates = (
        _sentences(idea.original_claim)
        + _sentences(idea.why_it_might_be_new)
    )
    points: list[str] = []
    seen: set[str] = set()
    for sentence in [candidate for candidate in candidates if _word_count(candidate) <= 18]:
        point = _normalize_key_point(sentence)
        key = point.lower()
        if len(point) < 18 or key in seen or _point_repeats_text(point, at_a_glance):
            continue
        points.append(point)
        seen.add(key)
        if len(points) == 3:
            break
    for sentence in candidates:
        if len(points) == 3:
            break
        point = _normalize_key_point(sentence)
        key = point.lower()
        if len(point) < 18 or key in seen or _point_repeats_text(point, at_a_glance):
            continue
        points.append(point)
        seen.add(key)

    fallbacks = [
        "The idea matters only if it changes how a person sees.",
        "The strongest version must survive honest objections.",
        "The next test is whether practice and sources bear its weight.",
    ]
    for fallback in fallbacks:
        if len(points) == 3:
            break
        if fallback.lower() not in seen:
            points.append(fallback)
            seen.add(fallback.lower())
    return points[:3]


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


def _safe_public_copy(idea: IdeaRecord) -> dict[str, Any]:
    raw_haystack = (
        f"{idea.title} {idea.original_claim} {idea.why_it_might_be_new} {' '.join(idea.source_basis)}"
    ).lower()
    haystack = _fingerprint(
        f"{idea.title} {idea.original_claim} {idea.why_it_might_be_new} {' '.join(idea.source_basis)}"
    )

    def build(
        *,
        insight: str,
        plain_summary: str,
        at_a_glance: str,
        key_points: list[str],
        tags: list[str],
    ) -> dict[str, Any]:
        return {
            "agent": idea.agent,
            "atAGlance": at_a_glance,
            "created_at": now_local_iso(),
            "ideaId": idea.identity(),
            "insight": insight,
            "publicTitle": insight,
            "keyPoints": key_points,
            "match": [_title_phrase(idea.title)],
            "plainSummary": plain_summary,
            "tags": tags,
            "title": idea.title,
        }

    if "custody and receiving surface" in raw_haystack or "receiving surface" in raw_haystack:
        return build(
            insight="Change needs somewhere to land",
            plain_summary="A practice works only when something in the person can receive and carry the change.",
            at_a_glance=(
                "A path can ask a person to change, but something in the person still has to receive the change. "
                "That may be trust, attention, love, patience, or the willingness to be corrected. "
                "The useful question is simple: what must remain open for this practice to work? "
                "A good path protects that opening instead of crushing it."
            ),
            key_points=[
                "A practice needs a human opening.",
                "Support matters only if change can land.",
                "The test is whether the person becomes more available.",
            ],
            tags=["practice", "support", "change"],
        )
    if "threshold grammar" in raw_haystack or "translation strain" in raw_haystack:
        return build(
            insight="Every path begins differently",
            plain_summary="A path's first step often reveals what kind of help, warning, and discipline it will need.",
            at_a_glance=(
                "Different paths do not begin in the same way. "
                "Some begin with discipline, some with trust, some with a teacher, some with crisis, and some with a gift the seeker did not plan. "
                "Comparing them is useful only when we preserve those differences. "
                "The test is whether a comparison makes each path clearer, not flatter."
            ),
            key_points=[
                "A beginning carries the shape of the path.",
                "Comparison should protect difference, not erase it.",
                "The test is whether warnings become easier to predict.",
            ],
            tags=["beginning", "comparison", "practice"],
        )
    if "practice architecture" in raw_haystack or "remainder phenomenology" in raw_haystack:
        return build(
            insight="The method shapes what remains",
            plain_summary="A method can shape what a person later believes is left after deep practice.",
            at_a_glance=(
                "The way a person practices can shape what they later think remains. "
                "A method that trains effort, surrender, attention, or trust does not leave the seeker untouched. "
                "It can make some conclusions feel obvious and others hard to see. "
                "The test is whether reports from real practitioners show this pattern."
            ),
            key_points=[
                "Practice can shape later belief.",
                "Reports matter more than elegant theory.",
                "The test needs real practitioners, not only texts.",
            ],
            tags=["practice", "attention", "test"],
        )
    if "entry-residue architecture" in raw_haystack or "entry residue architecture" in raw_haystack:
        return build(
            insight="Beginnings shape what remains",
            plain_summary="The way a path starts may predict what it later protects, warns against, or leaves behind.",
            at_a_glance=(
                "How a path begins can shape what it allows to remain. "
                "If the first step is trust, discipline, surrender, or community, the later lesson may carry that beginning inside it. "
                "This does not prove the path is right or wrong. "
                "It gives us a better way to test whether beginnings predict later warnings and safeguards."
            ),
            key_points=[
                "The first step can echo later.",
                "A path's safeguards reveal what it fears.",
                "The test is whether early patterns predict later warnings.",
            ],
            tags=["beginning", "practice", "test"],
        )
    if "compound entry grammar" in raw_haystack:
        return build(
            insight="Not every path begins the same",
            plain_summary="Different people and paths need different kinds of help before real change can begin.",
            at_a_glance=(
                "Not every path asks for the same first step. "
                "One may ask for effort, another for trust, another for obedience, another for patient participation. "
                "The mistake is treating all beginnings as if they solve the same human problem. "
                "A serious practice must name what blocks the person from beginning and what kind of help fits that block."
            ),
            key_points=[
                "Different wounds need different first steps.",
                "A beginning should match the real obstacle.",
                "The test is whether the help fits the person.",
            ],
            tags=["beginning", "support", "practice"],
        )
    if "prescriptive custody" in raw_haystack:
        return build(
            insight="Something holds us before we choose",
            plain_summary="People often begin changing because something holds them before they fully understand the path.",
            at_a_glance=(
                "Before a person understands a path, something may already be holding them. "
                "A family, teacher, habit, crisis, ritual, or community can keep attention steady long enough for change to start. "
                "Later, the path may explain what was happening. "
                "The question is whether that explanation guides the person well or turns help into control."
            ),
            key_points=[
                "Support often comes before understanding.",
                "A path should guide help without controlling it.",
                "The test is whether the person gains freedom.",
            ],
            tags=["beginning", "community", "support"],
        )
    if "residue-to-grain" in raw_haystack or "residue to grain" in raw_haystack or "layered direction" in raw_haystack:
        return build(
            insight="A practice teaches the eye",
            plain_summary="A practice does more than produce an experience; it trains what a person notices next.",
            at_a_glance=(
                "A practice teaches a person what to notice, what to ignore, and what to trust. "
                "Over time, those lessons can become habit. "
                "That means a method is never just a tool; it also trains a way of seeing. "
                "The test is whether people carry that trained way of seeing into other parts of life."
            ),
            key_points=[
                "Practice trains attention over time.",
                "A tool can become a habit of seeing.",
                "The test is what follows the person afterward.",
            ],
            tags=["practice", "attention", "habit"],
        )

    if any(term in haystack for term in ("begin", "beginning", "entry", "start", "first step", "teacher")):
        insight = "No one begins alone"
        plain_summary = "Change often starts when support makes the first honest step possible."
        at_a_glance = (
            "A person rarely begins serious change by willpower alone. "
            "Support, trust, pain, and habit can carry the first step. "
            "The test is whether that help makes the person more honest and responsible. "
            "A path should make beginning safer without taking freedom away."
        )
        key_points = [
            "The first step often needs support.",
            "Help should deepen responsibility, not replace it.",
            "The test is whether the person becomes freer.",
        ]
        tags = ["beginning", "support", "practice"]
    elif any(term in haystack for term in ("surrender", "release", "letting go", "identity", "self")):
        insight = "Letting go still needs care"
        plain_summary = "Release matters only if ordinary life becomes more honest, careful, and whole."
        at_a_glance = (
            "Letting go is not the same as disappearing. "
            "Memory, care, duty, and relationship still have to remain. "
            "The risk is turning freedom into drift or pride. "
            "A path should loosen identity without breaking responsibility."
        )
        key_points = [
            "Release should not erase responsibility.",
            "The return to ordinary life is the test.",
            "Freedom becomes suspect when care weakens.",
        ]
        tags = ["release", "self", "responsibility"]
    elif any(term in haystack for term in ("effort", "work", "result", "achievement", "credit")):
        insight = "Do the work without becoming the work"
        plain_summary = "Careful effort can stay real without turning every result into self-worth."
        at_a_glance = (
            "Work can be sincere without becoming an identity. "
            "A person can take responsibility without making every result a verdict. "
            "The danger is using effort to prove worth. "
            "The test is whether care survives when self-judgment loosens."
        )
        key_points = [
            "This helps people trapped in achievement pressure.",
            "Responsibility remains, but self-judgment loosens.",
            "The test is whether care stays strong.",
        ]
        tags = ["effort", "work", "identity"]
    elif any(term in haystack for term in ("love", "relation", "relationship", "community", "person")):
        insight = "Some truths need another person"
        plain_summary = "Some forms of knowing appear only through love, trust, response, and repair."
        at_a_glance = (
            "Not every truth appears from a distance. "
            "Love, trust, and response can reveal what observation misses. "
            "The danger is calling detachment the only honest method. "
            "The test is whether knowing makes a person more available to life."
        )
        key_points = [
            "Distance can miss relational truth.",
            "Love must be tested by response and repair.",
            "Knowing should make a person more available.",
        ]
        tags = ["love", "relation", "knowing"]
    elif any(term in haystack for term in ("time", "death", "grief", "change", "loss")):
        insight = "Change asks how to live"
        plain_summary = "Ideas about time matter only if they help us meet loss, change, and duty honestly."
        at_a_glance = (
            "Time is not only an idea to solve. "
            "It is where grief, duty, aging, and change arrive. "
            "A finding about time matters when it changes how we live inside change. "
            "The test is whether it makes life more truthful, not more abstract."
        )
        key_points = [
            "Time must return to ordinary life.",
            "Grief should not be rushed by theory.",
            "The test is more truthful living.",
        ]
        tags = ["time", "change", "grief"]
    elif any(term in haystack for term in ("attention", "awareness", "mind", "seeing", "observer")):
        insight = "How we look changes what appears"
        plain_summary = "A trained way of looking changes what a person can notice, trust, and test."
        at_a_glance = (
            "The way we look shapes what we find. "
            "Attention, trust, love, and doubt each reveal different parts of life. "
            "The danger is mistaking one trained view for the whole truth. "
            "A path should know what its method helps us see and what it hides."
        )
        key_points = [
            "Attention is never completely neutral.",
            "Every method reveals and hides.",
            "The test is what the method corrects.",
        ]
        tags = ["attention", "method", "truth"]
    else:
        insight = "A finding must change a life"
        plain_summary = "An idea earns attention when it changes how people see, act, care, or test truth."
        at_a_glance = (
            "A finding should do more than sound interesting. "
            "It should change how a person sees, acts, cares, or tests truth. "
            "The danger is mistaking a clever frame for real guidance. "
            "The test is whether the idea survives contact with life."
        )
        key_points = [
            "A clever frame is not enough.",
            "The idea must meet ordinary life.",
            "The test is whether it changes conduct.",
        ]
        tags = ["method", "practice"]

    return {
        "agent": idea.agent,
        "atAGlance": at_a_glance,
        "created_at": now_local_iso(),
        "ideaId": idea.identity(),
        "insight": insight,
        "publicTitle": insight,
        "keyPoints": key_points,
        "match": [_title_phrase(idea.title)],
        "plainSummary": plain_summary,
        "tags": tags,
        "title": idea.title,
    }


def distillation_quality_issues(record: dict[str, Any]) -> list[str]:
    raw_public_text = " ".join(
        [
            str(record.get("insight") or ""),
            str(record.get("publicTitle") or record.get("insight") or ""),
            str(record.get("plainSummary") or ""),
            str(record.get("atAGlance") or ""),
            *[str(item) for item in record.get("keyPoints", [])],
        ]
    )
    insight = _plain_text(str(record.get("insight") or ""))
    public_title = _plain_text(str(record.get("publicTitle") or insight))
    plain_summary = _plain_text(str(record.get("plainSummary") or ""))
    at_a_glance = _plain_text(str(record.get("atAGlance") or ""))
    key_points = [
        _normalize_key_point(str(item))
        for item in record.get("keyPoints", [])
        if _normalize_key_point(str(item))
    ]
    public_text = raw_public_text.lower()
    issues: list[str] = []
    if "\u2014" in public_text:
        issues.append("contains em dash")
    if re.search(r"\bthis finding\b", public_text, flags=re.IGNORECASE):
        issues.append("uses 'This finding'")
    for term in PUBLIC_BANNED_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", public_text, flags=re.IGNORECASE):
            issues.append(f"uses machinery term: {term}")
    if _word_count(insight) > 10:
        issues.append("insight exceeds 10 words")
    if _word_count(public_title) > 10:
        issues.append("publicTitle exceeds 10 words")
    if _word_count(plain_summary) > 28:
        issues.append("plainSummary exceeds 28 words")
    at_sentences = _sentences(at_a_glance)
    if len(at_sentences) < 3 or len(at_sentences) > 4:
        issues.append("atAGlance must be 3 to 4 sentences")
    if len(key_points) != 3:
        issues.append("keyPoints must contain exactly 3 bullets")
    seen_points: set[str] = set()
    for point in key_points:
        key = _fingerprint(point)
        if key in seen_points:
            issues.append("repeats a key point")
        seen_points.add(key)
        if _point_repeats_text(point, at_a_glance):
            issues.append("key point repeats At a Glance")
        if insight and _point_repeats_text(point, insight):
            issues.append("key point repeats insight")
    return sorted(set(issues))


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
    public_title = _plain_text(str(raw.get("publicTitle") or insight))
    plain_summary = _plain_text(str(raw.get("plainSummary") or _fallback_plain_summary(idea)))
    at_a_glance = _plain_text(str(raw.get("atAGlance") or _fallback_at_a_glance(idea)))

    if _word_count(insight) > 10:
        insight = _fallback_insight(idea)
    if _word_count(public_title) > 10:
        public_title = insight
    if _word_count(plain_summary) > 28:
        plain_summary = _clip_words(plain_summary, 28)

    at_sentences = _sentences(at_a_glance)
    if len(at_sentences) < 3:
        at_a_glance = _fallback_at_a_glance(idea)
    elif len(at_sentences) > 4:
        at_a_glance = " ".join(at_sentences[:4])

    key_points = [
        _normalize_key_point(str(item))
        for item in raw.get("keyPoints", [])
        if _normalize_key_point(str(item))
    ]
    key_points = [point for point in key_points if not _point_repeats_text(point, at_a_glance)]
    if len(key_points) < 3:
        key_points = _fallback_key_points(idea, at_a_glance)

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

    record = {
        "agent": idea.agent,
        "atAGlance": at_a_glance,
        "created_at": now_local_iso(),
        "ideaId": idea.identity(),
        "insight": insight,
        "publicTitle": public_title,
        "keyPoints": key_points[:3],
        "match": match[:3],
        "plainSummary": plain_summary,
        "tags": tags[:5],
        "title": idea.title,
    }
    if distillation_quality_issues(record):
        return _safe_public_copy(idea)
    return record


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
        record = _distill_idea(config, idea)
        librarian.append_jsonl(DISTILLATION_STORE, record)
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
        if idea.status == "seed-fixture":
            continue
        ideas.append(idea)
        if limit and len(ideas) >= limit:
            break
    return distill_new_ideas(config, list(reversed(ideas)))


def backfill_key_points(config: EngineConfig, *, refresh: bool = False) -> int:
    store = config.root / DISTILLATION_STORE
    if not store.exists():
        return 0

    ideas_by_id = {
        str(record.get("idea_id") or ""): _idea_from_record(record)
        for record in _read_idea_records(config.root)
        if str(record.get("idea_id") or "")
    }
    changed = 0
    records: list[dict[str, Any]] = []
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        key_points = [
            _normalize_key_point(str(item))
            for item in record.get("keyPoints", [])
            if _normalize_key_point(str(item))
        ]
        if refresh or len(key_points) < 3:
            idea = ideas_by_id.get(str(record.get("ideaId") or ""))
            if idea:
                key_points = _fallback_key_points(idea, str(record.get("atAGlance") or ""))
            else:
                key_points = [
                    _normalize_key_point(sentence)
                    for sentence in _sentences(str(record.get("atAGlance") or record.get("plainSummary") or ""))
                ][:3]
            at_a_glance = str(record.get("atAGlance") or "")
            key_points = [point for point in key_points if not _point_repeats_text(point, at_a_glance)]
            while len(key_points) < 3:
                key_points.append("The strongest version must survive honest objections.")
            record["keyPoints"] = key_points[:3]
            changed += 1
        records.append(record)

    store.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return changed


def validate_distillation_store(config: EngineConfig) -> list[str]:
    store = config.root / DISTILLATION_STORE
    if not store.exists():
        return [f"{DISTILLATION_STORE} is missing"]
    issues: list[str] = []
    seen_ids: set[str] = set()
    for index, line in enumerate(store.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(f"line {index}: invalid JSON: {exc}")
            continue
        idea_id = str(record.get("ideaId") or record.get("idea_id") or "")
        if idea_id:
            seen_ids.add(idea_id)
        for issue in distillation_quality_issues(record):
            label = record.get("ideaId") or record.get("title") or f"line {index}"
            issues.append(f"{label}: {issue}")
    for record in _read_idea_records(config.root):
        idea_id = str(record.get("idea_id") or "")
        if idea_id and idea_id not in seen_ids:
            issues.append(f"{idea_id}: missing reader-facing distillation")
    return issues


def repair_distillation_store(config: EngineConfig) -> int:
    store = config.root / DISTILLATION_STORE
    if not store.exists():
        return 0

    ideas_by_id = {
        str(record.get("idea_id") or ""): _idea_from_record(record)
        for record in _read_idea_records(config.root)
        if str(record.get("idea_id") or "")
    }
    repaired = 0
    records: list[dict[str, Any]] = []
    raw_title_repair_terms = (
        "custody and receiving surface",
        "threshold grammar",
        "practice architecture",
        "entry-residue architecture",
        "compound entry grammar",
        "prescriptive custody",
        "layered direction",
        "residue-to-grain",
    )
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        idea_id = str(record.get("ideaId") or record.get("idea_id") or "")
        idea = ideas_by_id.get(idea_id)
        raw_title = str(record.get("title") or "").lower()
        needs_reader_repair = any(term in raw_title for term in raw_title_repair_terms)
        if idea and (distillation_quality_issues(record) or needs_reader_repair):
            candidate = _safe_public_copy(idea)
            public_keys = ("atAGlance", "insight", "publicTitle", "keyPoints", "plainSummary", "tags")
            if any(record.get(key) != candidate.get(key) for key in public_keys):
                record = candidate
                repaired += 1
        records.append(record)

    store.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n",
        encoding="utf-8",
    )
    return repaired


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Lumenary insight distillations.")
    parser.add_argument("--backfill", action="store_true", help="Create missing distillations from ideas.jsonl.")
    parser.add_argument(
        "--backfill-key-points",
        action="store_true",
        help="Add finding-page key points to existing distillations.",
    )
    parser.add_argument(
        "--refresh-key-points",
        action="store_true",
        help="Regenerate finding-page key points for existing distillations.",
    )
    parser.add_argument(
        "--validate-store",
        action="store_true",
        help="Validate publication/distillations.jsonl against public writing gates.",
    )
    parser.add_argument(
        "--repair-store",
        action="store_true",
        help="Replace failing distillations with safe reader-facing fallback copy.",
    )
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
    if args.backfill_key_points:
        count = backfill_key_points(config, refresh=args.refresh_key_points)
        print(f"key_points={count}")
    if args.repair_store:
        count = repair_distillation_store(config)
        print(f"repaired={count}")
    if args.validate_store:
        issues = validate_distillation_store(config)
        if issues:
            for issue in issues:
                print(f"distillation_quality_issue={issue}")
            raise SystemExit(1)
        print("distillation_quality=true")


if __name__ == "__main__":
    main()
