"""Run model calls that return arbitrary structured JSON."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import EngineConfig
from .process_control import register_child, unregister_child


def extract_json_object(text: str) -> dict[str, Any]:
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


def _extract_claude_json(raw_output: str) -> dict[str, Any]:
    outer = json.loads(raw_output)
    if isinstance(outer, dict) and "result" in outer:
        result = outer["result"]
        if isinstance(result, dict):
            return result
        if isinstance(result, str):
            return extract_json_object(result)
    if isinstance(outer, dict):
        return outer
    raise ValueError("Claude output did not contain a JSON object.")


def _sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\u2014", ":").replace("\u2013", "-")
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _sanitize(item) for key, item in value.items()}
    return value


def _offline_structured(
    schema_path: Path,
    *,
    agent: str,
    output_stem: str,
) -> dict[str, Any]:
    schema_name = schema_path.name
    if schema_name == "dialogue_turn.schema.json":
        if "rebuttal" in output_stem and "counter" not in output_stem:
            return {
                "turn": 2,
                "turn_type": "rebuttal",
                "role": "proponent",
                "agent": agent,
                "steelman": None,
                "fairness_check": None,
                "claim_units": [],
                "strongest_objection": None,
                "hidden_assumption": None,
                "counter_model": None,
                "new_source": None,
                "concessions": [
                    "The challenge is right that a method can invent pressure unless it is checked against sources."
                ],
                "defense": "The idea survives as a disciplined review method when every pressure point is converted into a test.",
                "revised_claim": "Dialogue should not prove originality by itself. It should create a crux and a test that later audits can evaluate.",
                "crux": "Whether source-grounded pressure can be separated from method-imposed pressure.",
                "test_that_would_settle_it": "Ask a source or practitioner test to decide whether the named pressure is recognized outside the agent's frame.",
                "crux_assessment": None,
                "verdict_on_revision": None,
                "remaining_risk": None,
                "argument": "Offline rebuttal fixture. I concede the central risk: dialogue can become a staged performance if it rewards clever pressure more than sourced pressure. The surviving claim is narrower. Dialogue is valuable when it converts an objection into a crux and a test that can be audited later.",
                "sources_cited": ["offline-fixture"]
            }
        if "counter" in output_stem:
            return {
                "turn": 3,
                "turn_type": "counter_rebuttal",
                "role": "challenger",
                "agent": agent,
                "steelman": None,
                "fairness_check": None,
                "claim_units": [],
                "strongest_objection": None,
                "hidden_assumption": None,
                "counter_model": None,
                "new_source": None,
                "concessions": [],
                "defense": None,
                "revised_claim": None,
                "crux": None,
                "test_that_would_settle_it": None,
                "crux_assessment": "The revised crux is real and should be carried into the next frontier test.",
                "verdict_on_revision": "stronger",
                "remaining_risk": "The engine still needs a hard gate against publishing a candidate synthesis before originality audit.",
                "argument": "Offline counter-rebuttal fixture. The revision is stronger because it stops treating dialogue as proof and starts treating it as pressure that must leave a test behind. The remaining risk is publication discipline: the transcript should not make the revised claim look settled before an originality audit.",
                "sources_cited": ["offline-fixture"]
            }
        return {
            "turn": 1,
            "turn_type": "challenge",
            "role": "challenger",
            "agent": agent,
            "steelman": "The proponent is trying to make a comparison more exact by naming the pressure that a claim must survive.",
            "fairness_check": "This restatement preserves the claim's constructive aim before criticism.",
            "claim_units": [
                "The comparison must be decomposed into smaller claim units.",
                "A genuine pressure point should change the next research move."
            ],
            "strongest_objection": "The claim may confuse a useful research heuristic with evidence about the traditions being compared.",
            "hidden_assumption": "It assumes the agent can identify pressure without smuggling in its own frame.",
            "counter_model": "Treat the tension as an audit question first and a synthesis question only after source review.",
            "new_source": "Offline fixture source for smoke testing.",
            "concessions": [],
            "defense": None,
            "revised_claim": None,
            "crux": None,
            "test_that_would_settle_it": None,
            "crux_assessment": None,
            "verdict_on_revision": None,
            "remaining_risk": None,
            "argument": "Offline challenge fixture. The proponent's idea is promising because it makes comparison operational, but its weakness is that the pressure point could be invented by the method rather than discovered in the sources. A safer next step is to treat the dialogue as a review artifact and demand a source or practitioner test before calling the revision original.",
            "sources_cited": ["offline-fixture"]
        }
    if schema_name == "dialogue_verdict.schema.json":
        return {
            "outcome": "revision",
            "summary": "The offline dialogue found that the claim is useful as a research method but should not be promoted as an original synthesis until source pressure confirms the revised crux.",
            "convergence_claim": "Both sides agree that critique should become a next test rather than a decorative objection.",
            "unresolved_crux": "Can the method identify pressure from the sources rather than from its own framing habits?",
            "candidate_synthesis": None,
            "recommended_adjustments": {
                "proponent": {"counterargument_quality": 0.05},
                "challenger": {"generativity": 0.03}
            },
            "new_frontier_question": "Which source or practitioner test can distinguish real translation pressure from method-imposed pressure?",
            "new_concept_edges": [],
            "public_brief": "A dialogue revised the claim by turning its central weakness into the next source test.",
            "method_growth": "I learned to make critique leave a test behind."
        }
    return {}


def generate_structured_json(
    config: EngineConfig,
    *,
    prompt: str,
    schema_path: Path,
    run_dir: Path,
    output_stem: str,
    search: bool | None = None,
) -> dict[str, Any]:
    """Call the configured provider and parse a JSON object matching schema_path."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"{output_stem}.prompt.md").write_text(prompt, encoding="utf-8")

    if config.dry_run or config.provider == "offline":
        result = _offline_structured(
            schema_path,
            agent=config.agent,
            output_stem=output_stem,
        )
        (run_dir / f"{output_stem}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        return result

    if config.provider == "codex-cli":
        output_path = run_dir / f"{output_stem}.last-message.json"
        command = ["codex"]
        use_search = config.codex_search if search is None else search
        if use_search:
            command.append("--search")
        command.extend(
            [
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
        )
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
                f"codex structured call timed out after {config.codex_timeout_seconds} seconds."
            )
        finally:
            unregister_child(process)

        (run_dir / f"{output_stem}.stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / f"{output_stem}.stderr.log").write_text(stderr, encoding="utf-8")
        if process.returncode != 0:
            raise RuntimeError(
                "codex structured call failed with exit code "
                f"{process.returncode}. See {run_dir / f'{output_stem}.stderr.log'}."
            )

        raw_output = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
        result = _sanitize(extract_json_object(raw_output))
        (run_dir / f"{output_stem}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        return result

    if config.provider == "claude-code":
        schema_json = schema_path.read_text(encoding="utf-8").strip()
        command = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--json-schema",
            schema_json,
            "--allowedTools",
            "WebSearch,WebFetch,Read",
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
            stdout, stderr = process.communicate(
                input=prompt,
                timeout=config.claude_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            process.terminate()
            stdout, stderr = process.communicate(timeout=30)
            raise TimeoutError(
                f"claude structured call timed out after {config.claude_timeout_seconds} seconds."
            )
        finally:
            unregister_child(process)

        (run_dir / f"{output_stem}.stdout.log").write_text(stdout, encoding="utf-8")
        (run_dir / f"{output_stem}.stderr.log").write_text(stderr, encoding="utf-8")
        if process.returncode != 0:
            raise RuntimeError(
                "claude structured call failed with exit code "
                f"{process.returncode}. See {run_dir / f'{output_stem}.stderr.log'}."
            )

        result = _sanitize(_extract_claude_json(stdout))
        (run_dir / f"{output_stem}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        return result

    raise ValueError(f"Unsupported structured provider: {config.provider}")
