from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def now_local_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


@dataclass
class IdeaScores:
    novelty: float
    generativity: float
    cross_tradition_support: float
    logical_coherence: float
    explanatory_compression: float
    empirical_adjacency: float
    practice_testability: float
    counterargument_quality: float
    source_reliability: float
    publishability: float


@dataclass
class TeachingCandidate:
    title: str
    teaching_line: str
    doctrine_claim: str
    body: str
    target_human_problem: str
    target_cohort: str
    pressure_survived: str
    falsifying_pressure: str
    status: str = "seed"
    tags: list[str] = field(default_factory=list)


@dataclass
class PracticeCandidate:
    title: str
    practice_line: str
    purpose: str
    target_human_problem: str
    target_cohort: str
    non_fit: str
    duration: str
    frequency: str
    minimum_attempt: str
    steps: list[str]
    notice: list[str]
    caution: str
    weakens_if: str
    risk_level: str = "low"
    status: str = "seed"
    tags: list[str] = field(default_factory=list)


@dataclass
class IdeaTestRecord:
    test_type: str
    prediction: str
    result: str
    impact: str
    next_action: str
    target_type: str = "idea"
    status: str = "proposed"
    title: str = ""


@dataclass
class IdeaRecord:
    title: str
    idea_type: str
    agent: str
    created_at: str
    source_basis: list[str]
    original_claim: str
    why_it_might_be_new: str
    critique: str
    epistemic_labels: list[str]
    scores: IdeaScores
    next_research_directions: list[str]
    status: str = "draft"
    teaching_candidate: TeachingCandidate | None = None
    practice_candidate: PracticeCandidate | None = None
    tests: list[IdeaTestRecord] = field(default_factory=list)

    def identity(self) -> str:
        basis = f"{self.agent}\n{self.title}\n{self.original_claim}".encode("utf-8")
        return hashlib.sha256(basis).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        record["idea_id"] = self.identity()
        return record

    def to_markdown(self) -> str:
        score_lines = "\n".join(
            f"- {key}: {value:.2f}" for key, value in self.scores.__dict__.items()
        )
        source_lines = "\n".join(f"- {item}" for item in self.source_basis)
        label_lines = "\n".join(f"- `{label}`" for label in self.epistemic_labels)
        direction_lines = "\n".join(
            f"- {item}" for item in self.next_research_directions
        )
        teaching_section = ""
        if self.teaching_candidate:
            tags = ", ".join(self.teaching_candidate.tags) or "none"
            teaching_section = f"""
## Teaching Candidate

Status: {self.teaching_candidate.status}
Tags: {tags}

### Teaching Line

{self.teaching_candidate.teaching_line}

### Doctrine Claim

{self.teaching_candidate.doctrine_claim}

### Teaching Body

{self.teaching_candidate.body}

### Human Problem

{self.teaching_candidate.target_human_problem}

### For

{self.teaching_candidate.target_cohort}

### Pressure Survived

{self.teaching_candidate.pressure_survived}

### Falsifying Pressure

{self.teaching_candidate.falsifying_pressure}
"""

        practice_section = ""
        if self.practice_candidate:
            steps = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(self.practice_candidate.steps))
            notice = "\n".join(f"- {item}" for item in self.practice_candidate.notice)
            tags = ", ".join(self.practice_candidate.tags) or "none"
            practice_section = f"""
## Practice Candidate

Status: {self.practice_candidate.status}
Risk level: {self.practice_candidate.risk_level}
Tags: {tags}

### Practice Line

{self.practice_candidate.practice_line}

### Purpose

{self.practice_candidate.purpose}

### Human Problem

{self.practice_candidate.target_human_problem}

### For

{self.practice_candidate.target_cohort}

### Not For

{self.practice_candidate.non_fit}

### Time

- Duration: {self.practice_candidate.duration}
- Frequency: {self.practice_candidate.frequency}
- Minimum attempt: {self.practice_candidate.minimum_attempt}

### Steps

{steps}

### Notice

{notice}

### Caution

{self.practice_candidate.caution}

### Weakens If

{self.practice_candidate.weakens_if}
"""

        test_section = ""
        if self.tests:
            test_lines = []
            for item in self.tests:
                title = item.title or f"{item.test_type} test"
                test_lines.append(
                    "\n".join(
                        [
                            f"### {title}",
                            "",
                            f"- Type: {item.test_type}",
                            f"- Target: {item.target_type}",
                            f"- Status: {item.status}",
                            f"- Prediction: {item.prediction}",
                            f"- Result: {item.result}",
                            f"- Impact: {item.impact}",
                            f"- Next action: {item.next_action}",
                        ]
                    )
                )
            test_section = "\n## Tests\n\n" + "\n\n".join(test_lines) + "\n"
        return f"""# {self.title}

Agent: {self.agent}
Date: {self.created_at}
Type: {self.idea_type}
Idea ID: {self.identity()}
Status: {self.status}

## Original Claim

{self.original_claim}

## Why It Might Be New

{self.why_it_might_be_new}

## Source Basis

{source_lines}

## Critique

{self.critique}

## Epistemic Labels

{label_lines}

## Scores

{score_lines}

{teaching_section}

{practice_section}

{test_section}

## Next Research Directions

{direction_lines}
"""


@dataclass
class RunManifest:
    run_id: str
    agent: str
    provider: str
    dry_run: bool
    focus: str
    started_at: str
    completed_at: str | None = None
    generated_observations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def teaching_candidate_from_dict(value: Any) -> TeachingCandidate | None:
    if not isinstance(value, dict):
        return None
    return TeachingCandidate(
        title=str(value.get("title") or ""),
        teaching_line=str(value.get("teaching_line") or ""),
        doctrine_claim=str(value.get("doctrine_claim") or ""),
        body=str(value.get("body") or ""),
        target_human_problem=str(value.get("target_human_problem") or ""),
        target_cohort=str(value.get("target_cohort") or ""),
        pressure_survived=str(value.get("pressure_survived") or ""),
        falsifying_pressure=str(value.get("falsifying_pressure") or ""),
        status=str(value.get("status") or "seed"),
        tags=_string_list(value.get("tags")),
    )


def practice_candidate_from_dict(value: Any) -> PracticeCandidate | None:
    if not isinstance(value, dict):
        return None
    return PracticeCandidate(
        title=str(value.get("title") or ""),
        practice_line=str(value.get("practice_line") or ""),
        purpose=str(value.get("purpose") or ""),
        target_human_problem=str(value.get("target_human_problem") or ""),
        target_cohort=str(value.get("target_cohort") or ""),
        non_fit=str(value.get("non_fit") or ""),
        duration=str(value.get("duration") or ""),
        frequency=str(value.get("frequency") or ""),
        minimum_attempt=str(value.get("minimum_attempt") or ""),
        steps=_string_list(value.get("steps")),
        notice=_string_list(value.get("notice")),
        caution=str(value.get("caution") or ""),
        weakens_if=str(value.get("weakens_if") or ""),
        risk_level=str(value.get("risk_level") or "low"),
        status=str(value.get("status") or "seed"),
        tags=_string_list(value.get("tags")),
    )


def idea_tests_from_dict(value: Any) -> list[IdeaTestRecord]:
    if not isinstance(value, list):
        return []
    records: list[IdeaTestRecord] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        records.append(
            IdeaTestRecord(
                title=str(item.get("title") or ""),
                test_type=str(item.get("test_type") or "observational"),
                target_type=str(item.get("target_type") or "idea"),
                prediction=str(item.get("prediction") or ""),
                result=str(item.get("result") or "not run yet"),
                impact=str(item.get("impact") or "pending"),
                next_action=str(item.get("next_action") or ""),
                status=str(item.get("status") or "proposed"),
            )
        )
    return records
