"""Generate insight distillation entries for new findings.

After each research run, call distill_new_ideas() to produce writing-style-
compliant insight text for any idea that lacks a distillation entry in
src/lib/content.ts. Writes the distillation as a sidecar JSON file that the
build step can merge, or appends directly to the distillations array.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .process_control import register_child, unregister_child
from .schemas import IdeaRecord, now_local_iso


DISTILLATION_STORE = "publication/distillations.jsonl"

DISTILL_PROMPT = """You are writing for The Lumenary, a research project that studies spirituality and philosophy.

Read the finding below. Write three things:

1. "insight": A proverb-like headline, maximum 10 words. No technical terms. Quotable after one reading. Examples: "The same silence can license opposite beliefs." "Every path has one thing it will not surrender."

2. "plainSummary": 2-4 sentences a thoughtful 16-year-old would understand. No Sanskrit, Pali, Arabic, Greek, or Chinese terms. No academic hedging. Lead with the human question. Use "you" when it helps. Do not use em dashes; use colons, semicolons, and commas.

3. "atAGlance": 3-4 sentences, slightly more reflective. Still plain language. Let one image do more work than five abstractions. No em dashes.

Return exactly one JSON object with keys: insight, plainSummary, atAGlance, match (an array with one unique multi-word phrase from the finding's title, lowercased).

## The Finding

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


def _existing_matches(root: Path) -> set[str]:
    store = root / DISTILLATION_STORE
    if not store.exists():
        return set()
    matches: set[str] = []
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        for m in record.get("match", []):
            matches.add(m.lower())
    return set(matches)


def _content_ts_matches(root: Path) -> set[str]:
    path = root / "src" / "lib" / "content.ts"
    if not path.exists():
        return set()
    text = path.read_text(encoding="utf-8").lower()
    matches = set()
    for m in re.findall(r'match:\s*\[([^\]]+)\]', text):
        for term in re.findall(r'"([^"]+)"', m):
            matches.add(term)
    return matches


def _idea_needs_distillation(idea: IdeaRecord, known: set[str]) -> bool:
    haystack = f"{idea.title} {idea.original_claim}".lower()
    return not any(m in haystack for m in known)


def distill_idea(config: EngineConfig, idea: IdeaRecord) -> dict[str, Any] | None:
    prompt = DISTILL_PROMPT.format(
        title=idea.title,
        idea_type=idea.idea_type,
        agent=idea.agent,
        original_claim=idea.original_claim,
        why_it_might_be_new=idea.why_it_might_be_new,
        critique=idea.critique,
    )

    command = [
        "claude", "-p",
        "--output-format", "json",
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
        stdout, stderr = process.communicate(input=prompt, timeout=120)
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
            result = json.loads(result)
        if isinstance(result, dict) and "insight" in result:
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def distill_new_ideas(config: EngineConfig, ideas: list[IdeaRecord]) -> int:
    known = _existing_matches(config.root) | _content_ts_matches(config.root)
    count = 0
    store_path = config.root / DISTILLATION_STORE

    for idea in ideas:
        if idea.status == "seed-fixture":
            continue
        if not _idea_needs_distillation(idea, known):
            continue

        result = distill_idea(config, idea)
        if result is None:
            continue

        tags: list[str] = []
        haystack = f"{idea.title} {idea.original_claim}".lower()
        for tag, terms in [
            ("advaita", ["advaita", "vedanta", "atman", "brahman"]),
            ("buddhism", ["buddh", "anatta", "sunyata", "dogen", "zen"]),
            ("daoism", ["dao", "wu wei", "zhuangzi"]),
            ("sufism", ["sufi", "ibn arabi", "fana", "barzakh"]),
            ("consciousness", ["consciousness", "attention", "self-model"]),
            ("method", ["method", "comparison", "convergence"]),
            ("practice", ["practice", "meditation", "contemplative"]),
        ]:
            if any(t in haystack for t in terms):
                tags.append(tag)
        if not tags:
            tags = ["general"]

        record = {
            "insight": str(result.get("insight", "")),
            "plainSummary": str(result.get("plainSummary", "")),
            "atAGlance": str(result.get("atAGlance", "")),
            "match": [str(m) for m in result.get("match", [])],
            "tags": tags,
            "agent": idea.agent,
            "created_at": now_local_iso(),
        }

        store_path.parent.mkdir(parents=True, exist_ok=True)
        with store_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")

        for m in record["match"]:
            known.add(m.lower())
        count += 1

    return count
