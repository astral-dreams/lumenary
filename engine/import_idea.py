from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import EngineConfig
from .librarian import Librarian
from .schemas import (
    IdeaRecord,
    IdeaScores,
    idea_tests_from_dict,
    now_local_iso,
    practice_candidate_from_dict,
    teaching_candidate_from_dict,
)


def _float_score(scores: dict[str, Any], key: str) -> float:
    value = float(scores.get(key, 0.0))
    return max(0.0, min(1.0, value))


def idea_from_json(data: dict[str, Any], *, agent: str) -> IdeaRecord:
    scores = data.get("scores") or {}
    return IdeaRecord(
        title=str(data["title"]),
        idea_type=str(data["idea_type"]),
        agent=agent,
        created_at=str(data.get("created_at") or now_local_iso()),
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
        status=str(data.get("status") or "draft"),
        teaching_candidate=teaching_candidate_from_dict(data.get("teaching_candidate")),
        practice_candidate=practice_candidate_from_dict(data.get("practice_candidate")),
        tests=idea_tests_from_dict(data.get("tests")),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import an idea record from JSON.")
    parser.add_argument(
        "--agent",
        required=True,
        choices=["codex", "claude"],
        help="Attribution namespace for the imported idea.",
    )
    parser.add_argument(
        "input",
        help="Path to JSON idea record, or '-' to read from stdin.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Parse and validate shape without writing project files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    idea = idea_from_json(json.loads(raw), agent=args.agent)
    if args.validate_only:
        print(f"valid=true")
        print(f"idea_id={idea.identity()}")
        return

    config = EngineConfig.load()
    librarian = Librarian(config.root)
    librarian.ensure_workspace()
    path = librarian.save_idea(idea)
    from .doctrine import write_candidates_from_idea
    from .distill import distill_new_ideas
    from .human_condition import audit_human_condition_fit

    write_candidates_from_idea(config.root, idea, run_id=f"import-{idea.identity()}")
    audit_human_condition_fit(
        config.root,
        [idea],
        execution_id=f"import-{idea.identity()}",
        run_ids=[f"import-{idea.identity()}"],
    )
    distill_config = EngineConfig.load(provider="codex-cli", codex_search=False)
    distill_new_ideas(distill_config, [idea])
    librarian.append_exploration_log(
        f"- Imported `{idea.title}` for agent `{args.agent}` at `{path.relative_to(config.root)}`."
    )
    print(f"observation={path.relative_to(config.root)}")
    print(f"idea_id={idea.identity()}")


if __name__ == "__main__":
    main()
