from __future__ import annotations

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        score_lines = "\n".join(
            f"- {key}: {value:.2f}" for key, value in self.scores.__dict__.items()
        )
        source_lines = "\n".join(f"- {item}" for item in self.source_basis)
        label_lines = "\n".join(f"- `{label}`" for label in self.epistemic_labels)
        direction_lines = "\n".join(
            f"- {item}" for item in self.next_research_directions
        )
        return f"""# {self.title}

Agent: {self.agent}
Date: {self.created_at}
Type: {self.idea_type}
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

