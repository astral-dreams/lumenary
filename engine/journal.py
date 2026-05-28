from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, tzinfo
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .local_time import resolve_timezone, timezone_label
from .process_control import register_child, unregister_child
from .promotion import decide_promotion, load_promotion_rules
from .schemas import now_local_iso, slugify


def _local_date(value: str, timezone: tzinfo) -> str | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone)
    return parsed.astimezone(timezone).date().isoformat()


def _read_idea_records(root: Path) -> list[dict[str, Any]]:
    path = root / "hypotheses" / "ideas.jsonl"
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _clip(text: str, limit: int = 900) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit].rsplit(' ', 1)[0].rstrip('.,;:')}..."


def _markdown_title(markdown: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def _word_count(markdown: str) -> int:
    body = re.sub(r"^#\s+.+?\n+", "", markdown.strip(), count=1)
    return len(re.findall(r"\b[\w']+\b", body))


def _sentence_count(text: str) -> int:
    return max(1, len(re.findall(r"[.!?](?:\s|$)", text.strip())))


def _journal_quality_issues(markdown: str) -> list[str]:
    issues: list[str] = []
    clean = markdown.strip()
    body = re.sub(r"^#\s+.+?\n+", "", clean, count=1)
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", body)
        if paragraph.strip() and not paragraph.strip().startswith("<!--")
    ]
    word_count = _word_count(markdown)

    if not clean.startswith("# "):
        issues.append("missing H1 title")
    if word_count < 350 or word_count > 500:
        issues.append(f"word count must be 350 to 500, got {word_count}")
    if "—" in clean:
        issues.append("contains em dash")

    one_sentence = [paragraph for paragraph in paragraphs if _sentence_count(paragraph) <= 1]
    if len(paragraphs) >= 6 and len(one_sentence) / len(paragraphs) > 0.35:
        issues.append("too many one-sentence poetic paragraphs")

    lower = clean.lower()
    banned_fragments = [
        "ownership is",
        "the hand must",
        "open the hand",
        "worship the hand",
        "refuse the crown",
        "building a throne",
        "private achievement",
        "hard mercy",
        "cleaner wound",
    ]
    for fragment in banned_fragments:
        if fragment in lower:
            issues.append(f"manifesto-like fragment: {fragment}")

    coverage_terms = ["finding", "dialogue", "method", "practice", "test", "source", "teaching"]
    coverage = sum(1 for term in coverage_terms if term in lower)
    if coverage < 3:
        issues.append("does not clearly reflect the day's research breadth")

    if lower.count("we ") + lower.count("we\n") < 5:
        issues.append("not enough first-person plural reflection")

    return issues


def _existing_journal_path(root: Path, date: str) -> Path | None:
    journal_dir = root / "publication" / "journal"
    for path in sorted(journal_dir.glob(f"{date}-*.md")):
        return path
    return None


def _idea_summary(root: Path, date: str, timezone: tzinfo) -> str:
    rules = load_promotion_rules()
    parts: list[str] = []
    for record in _read_idea_records(root):
        if _local_date(str(record.get("created_at", "")), timezone) != date:
            continue
        decision = decide_promotion(record, rules)
        scores = record.get("scores") or {}
        parts.append(
            "\n".join(
                [
                    f"Title: {record.get('title', 'Untitled')}",
                    f"Agent: {record.get('agent', 'unknown')}",
                    f"Type: {record.get('idea_type', 'unknown')}",
                    f"Promotion: {decision.label}",
                    (
                        "Scores: "
                        f"source_reliability={float(scores.get('source_reliability', 0.0)):.2f}, "
                        f"counterargument_quality={float(scores.get('counterargument_quality', 0.0)):.2f}, "
                        f"publishability={float(scores.get('publishability', 0.0)):.2f}"
                    ),
                    f"Claim: {_clip(str(record.get('original_claim', '')))}",
                    f"Critique: {_clip(str(record.get('critique', '')), 650)}",
                ]
            )
        )
    return "\n\n---\n\n".join(parts) or "No idea records were created for this date."


def _daily_post_summary(root: Path, date: str) -> str:
    parts: list[str] = []
    for path in sorted((root / "publication" / "daily").glob(f"{date}-*.md")):
        markdown = path.read_text(encoding="utf-8")
        parts.append(
            "\n".join(
                [
                    f"Post: {_markdown_title(markdown, path.stem)}",
                    f"Path: {path.relative_to(root)}",
                    _clip(markdown, 1000),
                ]
            )
        )
    return "\n\n---\n\n".join(parts) or "No daily posts were published for this date."


def _build_prompt(root: Path, date: str, timezone_name: str) -> str:
    timezone = resolve_timezone(timezone_name)
    style = (root / "docs" / "writing-style.md").read_text(encoding="utf-8")
    return f"""# Lumenary Journal Entry

Write the end-of-day Journal entry for The Lumenary.

Date: {date}
Timezone: {timezone_label(timezone_name)}

This is not a research memo. It is the human-facing reflection after the research is done.

Rules:

- Return only Markdown.
- Begin with one H1 title.
- Write in first person plural: We discovered, We noticed, We carried, We were wrong, We learned.
- 350 to 500 words after the title.
- No bullet lists.
- No Sanskrit, Pali, Arabic, Greek, or Chinese terms.
- No academic hedging.
- Use normal paragraphs of 3 to 5 sentences. Do not write a poem made of single-sentence paragraphs.
- One idea per sentence, but do not isolate every sentence on its own line.
- Lead with the human question.
- Let it feel personal, clear, and memorable.
- Make the reader feel the day of learning, not the machinery behind it.
- This is a daily journal, not a manifesto, sermon, doctrine release, or poetic monologue.
- Do not make the entry about one charged metaphor. Cover the day.
- Reflect at least three concrete developments from today's records: findings, dialogues, method changes, practices, tests, sources, or teachings.
- Do not make ownership, work, credit, property, or effort sound morally evil. If those topics appear, write with balance and precision.
- Avoid grand final lines like "open the hand," "refuse the crown," "worship the hand," "cleaner wound," or similar theatrical language.
- Include what changed in our thinking and where we may have been wrong.

## Writing Style

{style}

## Today's Idea Records

{_idea_summary(root, date, timezone)}

## Today's Published Findings

{_daily_post_summary(root, date)}
"""


def _normalize_markdown(markdown: str) -> str:
    clean = markdown.strip()
    if not clean.startswith("# "):
        clean = f"# Evening Journal\n\n{clean}"
    return f"{clean}\n"


def _run_codex_journal(config: EngineConfig, prompt: str, run_id: str) -> str:
    run_dir = config.root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "codex-cli-journal-last-message.md"

    command = [
        "codex",
        "exec",
        "--cd",
        str(config.root),
        "--sandbox",
        config.codex_sandbox,
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
            timeout=config.codex_timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        process.terminate()
        stdout, stderr = process.communicate(timeout=30)
        raise TimeoutError(
            f"codex exec timed out after {config.codex_timeout_seconds} seconds."
        )
    finally:
        unregister_child(process)

    (run_dir / "codex-cli-journal.stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "codex-cli-journal.stderr.log").write_text(stderr, encoding="utf-8")

    if process.returncode != 0:
        raise RuntimeError(
            "codex exec failed while writing the journal with exit code "
            f"{process.returncode}. See {run_dir / 'codex-cli-journal.stderr.log'}."
        )

    return output_path.read_text(encoding="utf-8") if output_path.exists() else stdout


def _offline_journal(date: str) -> str:
    return f"""# What Remained After The Search

We ended the day with a quieter question than the one we began with.

We wanted to know what the old paths and the new sciences could prove.

We found something more useful than proof.

We found pressure.

Not the pressure to believe.

The pressure that appears when a path removes every easy answer.

That pressure is honest.

It does not flatter the seeker.

It asks what remains when comfort is no longer allowed to dress itself as truth.

Every path asks a person to let go of what they mistake for themselves.

But after the letting go, each path must answer a harder question.

What is allowed to remain?

Some teachings protect a witness.

Some refuse to protect anything.

Some say the empty room becomes fertile only after the furniture is carried out.

This changed how we understood the day's work.

The difference between paths is not always found in their highest words.

It is found in the small mercy they grant at the end.

One keeps a final light.

One blows out even the lamp.

One waits in the dark until the dark begins to sing.

We also saw a danger in our own mind.

We wanted agreement to mean truth.

That is too easy.

When two traditions sound alike, the bridge may be real.

But the bending required to build it is part of the truth too.

The bend matters.

The strain matters.

The refusal to fit may matter most of all.

So today we learned to look for what survives translation.

We learned to ask what each practice trains a person to notice, and what it trains them to miss.

We learned that wisdom is not only a claim about the world.

It is a way of becoming able to see.

The old practices kept teaching this in different ways.

Do not only gather answers.

Change the eyes that gather them.

But even that can become a trap.

A trained eye can become proud of its training.

So the method must turn back on itself.

It must ask what its own discipline hides.

Tonight, the question we carry is simple.

What do we still need to remain, before we will believe we are free?

<!-- generated_for: {date} -->
"""


def generate_journal_entry(
    config: EngineConfig,
    *,
    date: str | None = None,
    timezone_name: str = "local",
    force: bool = False,
) -> Path | None:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()
    local_now = datetime.now(resolve_timezone(timezone_name))
    journal_date = date or local_now.date().isoformat()

    existing = _existing_journal_path(config.root, journal_date)
    if existing is not None and not force:
        librarian.append_exploration_log(
            f"- Journal entry already exists for `{journal_date}`: `{existing.relative_to(config.root)}`."
        )
        return None

    run_id = f"{local_now.strftime('%Y%m%d-%H%M%S')}-journal-{journal_date}"
    if config.provider == "codex-cli" and not config.dry_run:
        prompt = _build_prompt(config.root, journal_date, timezone_name)
        output = _run_codex_journal(config, prompt, run_id)
        markdown = _normalize_markdown(output)
        issues = _journal_quality_issues(markdown)
        if issues:
            revision_prompt = (
                f"{prompt}\n\n## Revision Required\n\n"
                "The previous draft failed the Journal self-audit:\n"
                + "\n".join(f"- {issue}" for issue in issues)
                + "\n\nRewrite it as a clear daily journal entry, not a poetic manifesto. "
                "Use normal paragraphs, cover the breadth of the day's research, and preserve the first-person plural voice.\n\n"
                f"## Previous Draft\n\n{markdown}"
            )
            markdown = _normalize_markdown(
                _run_codex_journal(config, revision_prompt, f"{run_id}-revision")
            )
        final_issues = _journal_quality_issues(markdown)
        if final_issues:
            raise RuntimeError(
                "Journal self-audit failed after revision: " + "; ".join(final_issues)
            )
    else:
        markdown = _offline_journal(journal_date)

    title = _markdown_title(markdown, "Evening Journal")
    relative = f"publication/journal/{journal_date}-{slugify(title)}.md"
    path = librarian.write_text(relative, markdown)
    librarian.append_exploration_log(
        f"- Wrote Journal entry `{path.relative_to(config.root)}` after the day's research."
    )
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the daily Lumenary Journal entry.")
    parser.add_argument("--agent", default=None, help="Attribution agent name.")
    parser.add_argument("--provider", default="codex-cli", help="Provider for the Journal writer.")
    parser.add_argument("--model", default=None, help="Model to pass to Codex CLI.")
    parser.add_argument("--dry-run", action="store_true", help="Use the offline Journal fixture.")
    parser.add_argument("--date", default=None, help="Journal date in YYYY-MM-DD.")
    parser.add_argument(
        "--timezone",
        default="local",
        help="Timezone for cadence. Use local to follow the machine's current timezone.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite by creating a new Journal file for the date.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load(
        agent=args.agent,
        provider=args.provider,
        dry_run=args.dry_run,
        codex_model=args.model,
    )
    path = generate_journal_entry(
        config,
        date=args.date,
        timezone_name=args.timezone,
        force=args.force,
    )
    if path is None:
        print("journal=skipped")
    else:
        print(f"journal={path.relative_to(config.root)}")
        print(f"generated_at={now_local_iso()}")


if __name__ == "__main__":
    main()
