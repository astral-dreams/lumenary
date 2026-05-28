from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .process_control import register_child, unregister_child
from .schemas import (
    IdeaRecord,
    IdeaScores,
    IdeaTestRecord,
    PracticeCandidate,
    TeachingCandidate,
    idea_tests_from_dict,
    now_local_iso,
    practice_candidate_from_dict,
    teaching_candidate_from_dict,
)


class OfflineThinker:
    """Deterministic fixture thinker for smoke tests.

    This provider is not a research generator. It returns a seed fixture so the
    storage and scheduling code can be tested without spending model calls.
    """

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
                "Offline fixture for smoke tests; not a live research result.",
                "User research goal and methodology notes.",
                "Codex architecture notes on epistemic labels.",
                "Imported Claude Code plan on convergence weighting.",
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
            status="seed-fixture",
            teaching_candidate=TeachingCandidate(
                title="The Same Door Wears Different Names",
                teaching_line="The same door may open into different rooms.",
                doctrine_claim=(
                    "Repeated spiritual patterns should be treated as shared pressure on human attention, "
                    "not as proof that every path has found the same object."
                ),
                body=(
                    "Agreement is not enough. When two teachings sound alike, ask what each one changes "
                    "in a person's next choice. Similar language can hide different duties, risks, and "
                    "hopes. The teaching is useful only if it keeps those differences visible."
                ),
                target_human_problem=(
                    "People often borrow a teaching because it sounds inspiring before asking whether it fits their life."
                ),
                target_cohort=(
                    "Readers comparing traditions, teachers, or practices and trying to decide what to trust."
                ),
                pressure_survived=(
                    "This seed keeps the value of convergence while refusing to turn likeness into proof."
                ),
                falsifying_pressure=(
                    "It weakens if close reading shows that the repeated pattern is not about attention, "
                    "agency, salience, or boundary-making."
                ),
                tags=["attention", "discernment", "method"],
            ),
            practice_candidate=PracticeCandidate(
                title="The Difference After Agreement",
                practice_line="When two teachings agree, ask what each one asks you to do next.",
                purpose=(
                    "Test whether surface agreement hides different practical demands."
                ),
                target_human_problem=(
                    "The tendency to confuse inspiring agreement with practical guidance."
                ),
                target_cohort=(
                    "People choosing between teachings, practices, or advice that sound similar but may train different lives."
                ),
                non_fit=(
                    "Not for moments that require urgent action, grief care, or help from another person."
                ),
                duration="10 minutes",
                frequency="Once when comparing two teachings",
                minimum_attempt="One pair of teachings",
                steps=[
                    "Write the shared sentence in plain language.",
                    "Write what the first teaching asks you to do next.",
                    "Write what the second teaching asks you to do next.",
                    "Circle the first real difference in action, duty, danger, or hope.",
                ],
                notice=[
                    "Whether the agreement becomes smaller after action is named.",
                    "Whether one teaching asks for effort and the other asks for release.",
                    "Whether one teaching changes conduct while the other changes attention.",
                ],
                caution=(
                    "Stop if the exercise turns into proving one path superior. The task is discernment."
                ),
                weakens_if=(
                    "It weakens if repeated examples show that shared language reliably leads to the same action."
                ),
                risk_level="low",
                tags=["discernment", "comparison", "attention"],
            ),
            tests=[
                IdeaTestRecord(
                    title="Agreement to action test",
                    test_type="observational",
                    prediction=(
                        "If this model is right, teachings that sound alike should often diverge when translated into action."
                    ),
                    result="not run yet",
                    impact="pending",
                    next_action="Apply the test to three source-card pairs before promotion.",
                )
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

        command = ["codex"]
        if self.config.codex_search:
            command.append("--search")
        command.extend(
            [
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
        )
        if self.config.codex_model:
            command.extend(["--model", self.config.codex_model])
        command.append("-")

        process = subprocess.Popen(
            command,
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        register_child(process)
        try:
            stdout, stderr = process.communicate(
                input=prompt,
                timeout=self.config.codex_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            process.terminate()
            stdout, stderr = process.communicate(timeout=30)
            raise TimeoutError(
                f"codex exec timed out after {self.config.codex_timeout_seconds} seconds."
            )
        finally:
            unregister_child(process)

        (run_dir / "codex-cli.stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "codex-cli.stderr.log").write_text(stderr, encoding="utf-8")

        if process.returncode != 0:
            raise RuntimeError(
                "codex exec failed with exit code "
                f"{process.returncode}. See {run_dir / 'codex-cli.stderr.log'}."
            )

        raw_output = (
            output_path.read_text(encoding="utf-8")
            if output_path.exists()
            else stdout
        )
        data = _extract_json_object(raw_output)
        return _idea_from_dict(data, agent=agent)


class ClaudeCodeThinker:
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

        schema_path = root / "engine" / "json_schemas" / "idea_record.schema.json"
        schema_json = schema_path.read_text(encoding="utf-8").strip()

        command = [
            "claude",
            "-p",
            "--output-format", "json",
            "--json-schema", schema_json,
            "--allowedTools", "WebSearch,WebFetch,Read",
            "--no-session-persistence",
        ]
        if self.config.claude_model:
            command.extend(["--model", self.config.claude_model])

        process = subprocess.Popen(
            command,
            cwd=root,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        register_child(process)
        try:
            stdout, stderr = process.communicate(
                input=prompt,
                timeout=self.config.claude_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            process.terminate()
            stdout, stderr = process.communicate(timeout=30)
            raise TimeoutError(
                f"claude -p timed out after {self.config.claude_timeout_seconds} seconds."
            )
        finally:
            unregister_child(process)

        (run_dir / "claude-code.stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / "claude-code.stderr.log").write_text(stderr, encoding="utf-8")

        if process.returncode != 0:
            raise RuntimeError(
                f"claude -p failed with exit code {process.returncode}. "
                f"See {run_dir / 'claude-code.stderr.log'}."
            )

        data = _extract_claude_result(stdout)
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

    raise ValueError("Output did not contain a JSON object.")


def _extract_claude_result(raw_output: str) -> dict[str, Any]:
    outer = json.loads(raw_output)
    if isinstance(outer, dict) and "result" in outer:
        result = outer["result"]
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            return _extract_json_object(result)
    if isinstance(outer, dict) and all(
        k in outer for k in ("title", "original_claim")
    ):
        return outer
    return _extract_json_object(raw_output)


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
        teaching_candidate=teaching_candidate_from_dict(data.get("teaching_candidate")),
        practice_candidate=practice_candidate_from_dict(data.get("practice_candidate")),
        tests=idea_tests_from_dict(data.get("tests")),
    )


def get_thinker(
    config: EngineConfig,
) -> OfflineThinker | CodexCliThinker | ClaudeCodeThinker:
    if config.provider == "claude-code" and not config.dry_run:
        return ClaudeCodeThinker(config)
    if config.provider == "codex-cli" and not config.dry_run:
        return CodexCliThinker(config)
    if config.provider == "offline" or config.dry_run:
        return OfflineThinker()
    raise NotImplementedError(f"Unsupported provider: {config.provider}")
