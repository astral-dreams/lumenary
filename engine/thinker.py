from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .schemas import IdeaRecord, IdeaScores, now_local_iso


class OfflineThinker:
    """Deterministic starter thinker for dry runs before model APIs are wired in."""

    def generate(
        self,
        *,
        focus: str,
        agent: str,
        prompt: str,
        root: Path,
        run_id: str,
    ) -> IdeaRecord:
        return IdeaRecord(
            title="The Interface Invariant Model",
            idea_type="model",
            agent=agent,
            created_at=now_local_iso(),
            source_basis=[
                "User research goal and methodology notes",
                "Codex architecture notes on epistemic labels",
                "Imported Claude Code plan on convergence weighting",
            ],
            original_claim=(
                "Independent spiritual traditions may converge less because they "
                "identify the same hidden metaphysical substance and more because "
                "they repeatedly encounter the same interface invariants: attention, "
                "identity, salience, agency, and boundary-making. The recurring "
                "motifs of witness-consciousness, emptiness, nondual awareness, "
                "wu wei, and surrender may be different reports about what happens "
                "when that interface is altered or de-emphasized."
            ),
            why_it_might_be_new=(
                "This reframes convergence as evidence for recurring structures in "
                "human world-disclosure rather than as immediate proof of a shared "
                "metaphysical object. It preserves the value of cross-tradition "
                "convergence while reducing the risk of vague universalism."
            ),
            critique=(
                "The model may over-psychologize traditions that make explicit "
                "ontological claims. It is also currently source-light: it needs "
                "direct textual comparison across Advaita, Buddhist, Daoist, Sufi, "
                "and Neoplatonic material before it can be promoted beyond draft."
            ),
            epistemic_labels=[
                "interpretive",
                "phenomenological",
                "analogical",
                "speculative",
            ],
            scores=IdeaScores(
                novelty=0.76,
                generativity=0.86,
                cross_tradition_support=0.42,
                logical_coherence=0.78,
                explanatory_compression=0.82,
                empirical_adjacency=0.45,
                practice_testability=0.62,
                counterargument_quality=0.70,
                source_reliability=0.30,
                publishability=0.58,
            ),
            next_research_directions=[
                "Compare witness-consciousness in Advaita with no-self and emptiness in Buddhism.",
                "Test whether wu wei fits the interface-invariant model or requires a separate dynamics model.",
                "Search contemplative neuroscience for attention, self-modeling, and salience-network evidence.",
                "Create a contradiction note for traditions that insist the convergence is ontological, not phenomenological.",
            ],
        )


class CodexCliThinker:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config

    def generate(
        self,
        *,
        focus: str,
        agent: str,
        prompt: str,
        root: Path,
        run_id: str,
    ) -> IdeaRecord:
        run_dir = root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        output_path = run_dir / "codex-cli-last-message.json"
        schema_path = root / "engine" / "json_schemas" / "idea_record.schema.json"

        command = [
            "codex",
            "exec",
            "--cd",
            str(root),
            "--sandbox",
            self.config.codex_sandbox,
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "--color",
            "never",
        ]
        if self.config.codex_search:
            command.append("--search")
        if self.config.codex_model:
            command.extend(["--model", self.config.codex_model])
        command.append("-")

        result = subprocess.run(
            command,
            input=prompt,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=self.config.codex_timeout_seconds,
        )
        (run_dir / "codex-cli.stdout.log").write_text(result.stdout, encoding="utf-8")
        (run_dir / "codex-cli.stderr.log").write_text(result.stderr, encoding="utf-8")

        if result.returncode != 0:
            raise RuntimeError(
                "codex exec failed with exit code "
                f"{result.returncode}. See {run_dir / 'codex-cli.stderr.log'}."
            )

        raw_output = (
            output_path.read_text(encoding="utf-8")
            if output_path.exists()
            else result.stdout
        )
        data = _extract_json_object(raw_output)
        return _idea_from_dict(data, agent=agent)


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

    raise ValueError("Codex CLI output did not contain a JSON object.")


def _float_score(scores: dict[str, Any], key: str) -> float:
    value = float(scores.get(key, 0.0))
    return max(0.0, min(1.0, value))


def _idea_from_dict(data: dict[str, Any], *, agent: str) -> IdeaRecord:
    scores = data.get("scores") or {}
    return IdeaRecord(
        title=str(data["title"]),
        idea_type=str(data["idea_type"]),
        agent=agent,
        created_at=now_local_iso(),
        source_basis=[str(item) for item in data.get("source_basis", [])],
        original_claim=str(data["original_claim"]),
        why_it_might_be_new=str(data["why_it_might_be_new"]),
        critique=str(data["critique"]),
        epistemic_labels=[str(item) for item in data.get("epistemic_labels", [])],
        scores=IdeaScores(
            novelty=_float_score(scores, "novelty"),
            generativity=_float_score(scores, "generativity"),
            cross_tradition_support=_float_score(scores, "cross_tradition_support"),
            logical_coherence=_float_score(scores, "logical_coherence"),
            explanatory_compression=_float_score(scores, "explanatory_compression"),
            empirical_adjacency=_float_score(scores, "empirical_adjacency"),
            practice_testability=_float_score(scores, "practice_testability"),
            counterargument_quality=_float_score(scores, "counterargument_quality"),
            source_reliability=_float_score(scores, "source_reliability"),
            publishability=_float_score(scores, "publishability"),
        ),
        next_research_directions=[
            str(item) for item in data.get("next_research_directions", [])
        ],
    )


def get_thinker(config: EngineConfig) -> OfflineThinker | CodexCliThinker:
    if config.provider == "codex-cli" and not config.dry_run:
        return CodexCliThinker(config)
    if config.provider == "offline" or config.dry_run:
        return OfflineThinker()
    raise NotImplementedError(f"Unsupported provider: {config.provider}")
