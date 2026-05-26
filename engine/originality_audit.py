"""Run post-generation originality audits for new Lumenary findings."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .process_control import register_child, unregister_child
from .schemas import IdeaRecord, now_local_iso, slugify


AUDIT_LEDGER = "reviews/originality/audits.jsonl"
AUDIT_TIMEOUT_SECONDS = int(os.getenv("SPIRITUALITY_ORIGINALITY_AUDIT_TIMEOUT_SECONDS", "1200"))

AUDIT_PROMPT = """# Lumenary Originality Audit

You are auditing newly generated Lumenary findings for real originality.

Your job is not to praise the ideas. Your job is to find prior art, anomalies, and tests that could prove the ideas are only refined framings rather than discoveries.

## Required Posture

- Search for exact structural near-neighbors, not just the topic.
- Close-read primary texts against each other when possible. Prefer source-to-source comparison over summaries of what scholars say.
- Hunt for anomalies that break the proposed model. If you cannot find an anomaly, say that this lowers confidence.
- Generate falsifiable predictions. A prediction must say what should be observed if the model is right and what would weaken it.
- Include a practitioner test. Ask whether the idea is obvious to a practitioner and whether it changes practice understanding.
- Include one cross-domain prediction. If the structure is real, it should travel outside the domain that generated it.
- Use academic sources, primary texts, and practitioner-facing sources where possible.
- Do not claim "truly unique" unless the audit has no close near-neighbor and the idea generates usable predictions.
- Do not use em dashes. Use commas, colons, semicolons, or periods.

## Originality Status Labels

- known: already present in a close prior source.
- renamed: mostly old work in new language.
- extended: meaningfully extends a prior idea.
- novel_synthesis: new combination of known elements.
- candidate_discovery: no close prior match found and it generates tests.
- strong_original_contribution: unusually strong candidate with clear difference, predictions, and cross-domain power.
- rejected: pattern fails under critique.
- audit_incomplete: search or source access was not strong enough.

## Output

Return exactly one JSON object matching the provided schema. Include one audit per idea.

## Current Thinking Protocol

{thinking_protocol}

## Suggested Next Directions

{next_directions}

## Recent Originality Audits

{prior_audits}

## Candidate Ideas

{ideas_json}
"""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _tail_text(value: str, limit: int = 16000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


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


def _sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\u2014", ":").replace("\u2013", "-")
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    return value


def _idea_payload(idea: IdeaRecord) -> dict[str, Any]:
    record = idea.to_dict()
    return {
        "idea_id": record["idea_id"],
        "agent": idea.agent,
        "title": idea.title,
        "idea_type": idea.idea_type,
        "source_basis": idea.source_basis,
        "original_claim": idea.original_claim,
        "why_it_might_be_new": idea.why_it_might_be_new,
        "critique": idea.critique,
        "epistemic_labels": idea.epistemic_labels,
        "scores": record["scores"],
        "next_research_directions": idea.next_research_directions,
    }


def _build_prompt(root: Path, ideas: list[IdeaRecord]) -> str:
    librarian = Librarian(root)
    prior_audits = librarian.read_optional(AUDIT_LEDGER)
    return AUDIT_PROMPT.format(
        thinking_protocol=librarian.read_optional("state/thinking_protocol.md"),
        next_directions=librarian.read_optional("state/next_directions.md"),
        prior_audits=_tail_text(prior_audits, 14000) or "No prior audits yet.",
        ideas_json=json.dumps([_idea_payload(idea) for idea in ideas], indent=2, ensure_ascii=True),
    )


def _run_codex_audit(config: EngineConfig, ideas: list[IdeaRecord], execution_id: str) -> dict[str, Any]:
    run_id = f"{now_local_iso().replace(':', '').replace('+', '-')}-originality-audit-{slugify(execution_id)[:48]}"
    run_dir = config.root / "runs" / "originality-audits" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_path = run_dir / "codex-originality-audit.json"
    schema_path = config.root / "engine" / "json_schemas" / "originality_audit.schema.json"
    prompt = _build_prompt(config.root, ideas)
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")

    command = [
        "codex",
        "--search",
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
        stdout, stderr = process.communicate(input=prompt, timeout=AUDIT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.terminate()
        stdout, stderr = process.communicate(timeout=30)
        raise TimeoutError(
            f"originality audit timed out after {AUDIT_TIMEOUT_SECONDS} seconds."
        )
    finally:
        unregister_child(process)

    (run_dir / "codex-originality-audit.stdout.log").write_text(stdout, encoding="utf-8")
    (run_dir / "codex-originality-audit.stderr.log").write_text(stderr, encoding="utf-8")

    if process.returncode != 0:
        raise RuntimeError(
            "codex originality audit failed with exit code "
            f"{process.returncode}. See {run_dir / 'codex-originality-audit.stderr.log'}."
        )

    raw_output = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
    result = _sanitize(_extract_json_object(raw_output))
    (run_dir / "output.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True),
        encoding="utf-8",
    )
    return result


def _audit_id(execution_id: str, idea_id: str) -> str:
    return hashlib.sha256(f"{execution_id}:{idea_id}".encode("utf-8")).hexdigest()[:16]


def _list(items: list[Any]) -> str:
    if not items:
        return "- None recorded."
    return "\n".join(f"- {_clean_text(str(item))}" for item in items)


def _near_neighbors(items: list[dict[str, Any]]) -> str:
    if not items:
        return "- No close near-neighbor recorded."
    lines: list[str] = []
    for item in items:
        lines.append(
            "- "
            + _clean_text(str(item.get("source", "Unknown source")))
            + ": overlap: "
            + _clean_text(str(item.get("overlap", "")))
            + "; difference: "
            + _clean_text(str(item.get("difference", "")))
            + "; novelty impact: "
            + _clean_text(str(item.get("novelty_impact", "")))
        )
    return "\n".join(lines)


def _predictions(items: list[dict[str, Any]]) -> str:
    if not items:
        return "- No prediction recorded."
    lines: list[str] = []
    for item in items:
        lines.append(
            "- If: "
            + _clean_text(str(item.get("if_model_is_right", "")))
            + " Then: "
            + _clean_text(str(item.get("expected_observation", "")))
            + " Weakens if: "
            + _clean_text(str(item.get("would_weaken_or_falsify", "")))
            + " Test surface: "
            + _clean_text(str(item.get("test_surface", "")))
        )
    return "\n".join(lines)


def _audit_markdown(audit: dict[str, Any]) -> str:
    close_read = audit.get("primary_text_close_read") or {}
    anomaly = audit.get("anomaly_probe") or {}
    practitioner = audit.get("practitioner_test") or {}
    cross_domain = audit.get("cross_domain_prediction") or {}
    scores = audit.get("recommended_scores") or {}
    return f"""# Originality Audit: {audit.get("title", "Untitled")}

Audit ID: {audit.get("audit_id", "")}
Idea ID: {audit.get("idea_id", "")}
Agent: {audit.get("agent", "")}
Created: {audit.get("created_at", "")}
Status: {audit.get("originality_status", "audit_incomplete")}
Confidence: {float(audit.get("confidence", 0.0)):.2f}

## Exact Claim

{audit.get("exact_claim", "")}

## Claim Units

{_list(list(audit.get("claim_units") or []))}

## Primary Text Close Read

Sources:
{_list(list(close_read.get("primary_pair") or []))}

Structural observation: {close_read.get("structural_observation", "")}

Secondary literature gap: {close_read.get("secondary_literature_gap", "")}

Risk of overread: {close_read.get("risk_of_overread", "")}

## Literature Search Queries

{_list(list(audit.get("literature_search_queries") or []))}

## Near Neighbors

{_near_neighbors(list(audit.get("near_neighbors") or []))}

## Unlike Statement

{audit.get("unlike_statement", "")}

## Anomaly Probe

Candidate: {anomaly.get("anomaly_candidate", "")}

Why it strains the model: {anomaly.get("why_it_breaks_or_strains_model", "")}

Confidence effect: {anomaly.get("confidence_effect", "")}

## Falsifiable Predictions

{_predictions(list(audit.get("falsifiable_predictions") or []))}

## Practitioner Test

Relevant practitioners:
{_list(list(practitioner.get("relevant_practitioners") or []))}

Questions:
{_list(list(practitioner.get("questions") or []))}

Answers that reduce originality: {practitioner.get("answers_that_reduce_originality", "")}

Answers that support contribution: {practitioner.get("answers_that_support_contribution", "")}

## Cross-Domain Prediction

Domain: {cross_domain.get("domain", "")}

Structural translation: {cross_domain.get("structural_translation", "")}

Prediction: {cross_domain.get("prediction", "")}

Would count against it: {cross_domain.get("would_count_against_it", "")}

## Score Recommendations

- novelty: {float(scores.get("novelty", 0.0)):.2f}
- source_reliability: {float(scores.get("source_reliability", 0.0)):.2f}
- counterargument_quality: {float(scores.get("counterargument_quality", 0.0)):.2f}

Novelty adjustment: {audit.get("novelty_adjustment", "")}

## Next Loop Instructions

{_list(list(audit.get("next_loop_instructions") or []))}
"""


def _append_next_directions(librarian: Librarian, audits: list[dict[str, Any]], created_at: str) -> None:
    lines = [f"\n## Originality Audit Follow-Up {created_at}\n"]
    for audit in audits:
        title = audit.get("title", "Untitled")
        status = audit.get("originality_status", "audit_incomplete")
        lines.append(f"\n### {title} ({status})\n")
        for instruction in audit.get("next_loop_instructions") or []:
            lines.append(f"- {_clean_text(str(instruction))}\n")
    librarian.append_text("state/next_directions.md", "".join(lines))


def _write_audits(
    root: Path,
    *,
    result: dict[str, Any],
    ideas: list[IdeaRecord],
    run_ids: list[str],
    execution_id: str,
) -> int:
    librarian = Librarian(root)
    librarian.ensure_workspace()
    created_at = now_local_iso()
    idea_by_id = {idea.identity(): idea for idea in ideas}
    written: list[dict[str, Any]] = []

    for audit in result.get("audits") or []:
        idea_id = str(audit.get("idea_id") or "")
        idea = idea_by_id.get(idea_id)
        if idea is None:
            continue

        audit["audit_id"] = _audit_id(execution_id, idea_id)
        audit["created_at"] = created_at
        audit["execution_id"] = execution_id
        audit["run_ids"] = run_ids
        audit["idea_path"] = f"observations/{idea.agent}/{idea.created_at[:10]}-{slugify(idea.title)}.md"
        audit = _sanitize(audit)

        filename = f"{created_at[:10]}-{slugify(str(audit.get('title') or idea.title))}-{audit['audit_id']}"
        json_path = librarian.write_text(
            f"reviews/originality/{filename}.json",
            json.dumps(audit, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        )
        md_path = librarian.write_text(
            f"reviews/originality/{filename}.md",
            _audit_markdown(audit),
        )
        audit["path"] = str(json_path.relative_to(root))
        audit["markdown_path"] = str(md_path.relative_to(root))
        librarian.upsert_jsonl_by_key(AUDIT_LEDGER, audit, key="audit_id")
        written.append(audit)

    if written:
        _append_next_directions(librarian, written, created_at)
        librarian.append_exploration_log(
            "- Originality audit completed for "
            + ", ".join(f"`{item.get('title')}`" for item in written)
            + ".\n"
            + "- Audit records: "
            + ", ".join(f"`{item.get('markdown_path')}`" for item in written)
            + "."
        )

    return len(written)


def audit_new_ideas(
    config: EngineConfig,
    ideas: list[IdeaRecord],
    *,
    run_ids: list[str],
    execution_id: str,
) -> int:
    if not ideas:
        return 0
    result = _run_codex_audit(config, ideas, execution_id)
    return _write_audits(
        config.root,
        result=result,
        ideas=ideas,
        run_ids=run_ids,
        execution_id=execution_id,
    )


def _fallback_sources(idea: IdeaRecord) -> list[str]:
    sources = [source for source in idea.source_basis if str(source).strip()]
    while len(sources) < 2:
        sources.append("Source basis requires follow-up during the next originality audit.")
    return sources[:4]


def _incomplete_audit_payload(
    idea: IdeaRecord,
    *,
    execution_id: str,
    run_ids: list[str],
    reason: str,
) -> dict[str, Any]:
    source_reliability = float(getattr(idea.scores, "source_reliability", 0.0))
    counterargument_quality = float(getattr(idea.scores, "counterargument_quality", 0.0))
    novelty = min(float(getattr(idea.scores, "novelty", 0.0)), 0.35)
    clean_reason = _clean_text(reason)[:500] or "The audit did not complete."
    return {
        "idea_id": idea.identity(),
        "agent": idea.agent,
        "title": idea.title,
        "exact_claim": _clean_text(idea.original_claim)[:900] or idea.title,
        "claim_units": [_clean_text(idea.original_claim)[:600] or idea.title],
        "primary_text_close_read": {
            "primary_pair": _fallback_sources(idea)[:2],
            "structural_observation": "The originality audit did not complete, so no reliable primary-text comparison should be inferred yet.",
            "secondary_literature_gap": "No literature gap has been established yet. Treat any novelty claim as provisional until prior art is checked.",
            "risk_of_overread": "High. The finding may be a renamed or extended version of prior work until the audit is completed.",
        },
        "literature_search_queries": [
            f'"{idea.title}" prior art',
            f'"{idea.title}" comparative religion',
            f'"{idea.title}" consciousness philosophy',
        ],
        "near_neighbors": [],
        "unlike_statement": "No unlike statement is available until the originality audit completes.",
        "anomaly_probe": {
            "anomaly_candidate": "The missing audit itself is the current anomaly: prior work may already contain the claim.",
            "why_it_breaks_or_strains_model": clean_reason,
            "confidence_effect": "Confidence is held low until the audit is completed.",
        },
        "falsifiable_predictions": [
            {
                "if_model_is_right": "A later audit should find a clear difference from the closest prior work.",
                "expected_observation": "The finding keeps a distinct claim after close prior art, anomaly, practitioner, and cross-domain checks.",
                "would_weaken_or_falsify": "A close prior source already makes the same structural argument.",
                "test_surface": "Originality audit backfill and practitioner review.",
            }
        ],
        "practitioner_test": {
            "relevant_practitioners": ["Practitioners and scholars in the traditions named by the finding"],
            "questions": [
                "Is this obvious from inside your practice?",
                "Does this change how you understand the practice, or only rename what you already know?",
            ],
            "answers_that_reduce_originality": "A practitioner or scholar recognizes the claim as standard teaching or standard scholarship.",
            "answers_that_support_contribution": "A practitioner or scholar finds that the claim changes interpretation or predicts a real practice difference.",
        },
        "cross_domain_prediction": {
            "domain": "Comparative method",
            "structural_translation": "A genuine structure should travel beyond the first tradition pair that generated it.",
            "prediction": "If this is more than a redescription, it should generate a useful prediction in another domain.",
            "would_count_against_it": "The structure only restates the source tradition's own vocabulary.",
        },
        "originality_status": "audit_incomplete",
        "confidence": 0.0,
        "recommended_scores": {
            "novelty": novelty,
            "source_reliability": source_reliability,
            "counterargument_quality": counterargument_quality,
        },
        "novelty_adjustment": "Do not raise novelty until the originality audit is completed.",
        "next_loop_instructions": [
            "Run the full originality audit for this finding before treating it as a discovery.",
            "Search for exact structural near-neighbors, not only the general topic.",
            "Add at least one anomaly probe, one practitioner test, and one cross-domain prediction.",
        ],
    }


def write_incomplete_audits(
    root: Path,
    ideas: list[IdeaRecord],
    *,
    run_ids: list[str],
    execution_id: str,
    reason: str,
) -> int:
    if not ideas:
        return 0
    return _write_audits(
        root,
        result={
            "audits": [
                _incomplete_audit_payload(
                    idea,
                    execution_id=execution_id,
                    run_ids=run_ids,
                    reason=reason,
                )
                for idea in ideas
            ]
        },
        ideas=ideas,
        run_ids=run_ids,
        execution_id=execution_id,
    )


def _record_to_idea(record: dict[str, Any]) -> IdeaRecord:
    from .schemas import IdeaScores

    return IdeaRecord(
        title=str(record["title"]),
        idea_type=str(record["idea_type"]),
        agent=str(record["agent"]),
        created_at=str(record["created_at"]),
        source_basis=list(record.get("source_basis") or []),
        original_claim=str(record["original_claim"]),
        why_it_might_be_new=str(record["why_it_might_be_new"]),
        critique=str(record["critique"]),
        epistemic_labels=list(record.get("epistemic_labels") or []),
        scores=IdeaScores(**record["scores"]),
        next_research_directions=list(record.get("next_research_directions") or []),
        status=str(record.get("status", "draft")),
    )


def _audited_idea_ids(root: Path) -> set[str]:
    path = root / AUDIT_LEDGER
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("originality_status") == "audit_incomplete":
            continue
        idea_id = str(record.get("idea_id") or "")
        if idea_id:
            ids.add(idea_id)
    return ids


def _read_idea_records(root: Path) -> list[dict[str, Any]]:
    path = root / "hypotheses" / "ideas.jsonl"
    if not path.exists():
        return []
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records.sort(key=lambda item: item.get("created_at", ""))
    return records


def _read_missing_ideas(root: Path, limit: int) -> list[IdeaRecord]:
    audited = _audited_idea_ids(root)
    ideas: list[IdeaRecord] = []
    for record in _read_idea_records(root):
        idea = _record_to_idea(record)
        if idea.identity() not in audited:
            ideas.append(idea)
        if len(ideas) >= limit:
            break
    return ideas


def _read_latest_ideas(root: Path, limit: int) -> list[IdeaRecord]:
    return [_record_to_idea(record) for record in _read_idea_records(root)[-limit:]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run originality audits for recent ideas.")
    parser.add_argument("--latest", type=int, default=2)
    parser.add_argument("--missing", action="store_true", help="Audit the oldest findings without audit records.")
    parser.add_argument("--execution-id", default=f"manual-{now_local_iso()}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    config = EngineConfig.load(root=root, agent="codex", provider="codex-cli", codex_search=True)
    ideas = _read_missing_ideas(root, args.latest) if args.missing else _read_latest_ideas(root, args.latest)
    count = audit_new_ideas(
        config,
        ideas,
        run_ids=[args.execution_id],
        execution_id=args.execution_id,
    )
    print(f"originality_audits={count}")


if __name__ == "__main__":
    main()
