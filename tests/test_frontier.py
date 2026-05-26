from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.frontier import prepare_frontier_brief, refresh_frontiers, select_frontier


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


class FrontierTests(unittest.TestCase):
    def test_refresh_clusters_audited_ideas_and_writes_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            idea = {
                "agent": "codex",
                "created_at": "2026-05-26T12:00:00-07:00",
                "critique": "The rubric may mistake translation strain for genuine disagreement.",
                "epistemic_labels": ["interpretive", "analogical"],
                "idea_id": "idea-translation",
                "idea_type": "model",
                "next_research_directions": [
                    "Build a translation-strain rubric and test it against a close anomaly."
                ],
                "original_claim": "Translation strain reveals whether apparent convergence is doing real comparative work.",
                "path": "observations/codex/2026-05-26-translation.md",
                "scores": {
                    "counterargument_quality": 0.8,
                    "cross_tradition_support": 0.75,
                    "empirical_adjacency": 0.2,
                    "explanatory_compression": 0.8,
                    "generativity": 0.9,
                    "logical_coherence": 0.82,
                    "novelty": 0.7,
                    "practice_testability": 0.7,
                    "publishability": 0.82,
                    "source_reliability": 0.74,
                },
                "source_basis": ["source a", "source b"],
                "status": "draft",
                "title": "Translation Strain As A Test",
                "why_it_might_be_new": "It makes convergence operational instead of decorative.",
            }
            audit = {
                "agent": "codex",
                "audit_id": "audit-translation",
                "created_at": "2026-05-26T13:00:00-07:00",
                "idea_id": "idea-translation",
                "near_neighbors": [],
                "next_loop_instructions": [
                    "Build a one-page translation-strain rubric before publishing."
                ],
                "originality_status": "novel_synthesis",
                "title": "Translation Strain As A Test",
            }
            write_jsonl(root / "hypotheses" / "ideas.jsonl", [idea])
            write_jsonl(root / "reviews" / "originality" / "audits.jsonl", [audit])

            state = refresh_frontiers(root)
            selected = select_frontier(root, refresh=False)
            brief = prepare_frontier_brief(
                root,
                focus="Test frontier steering.",
                execution_id="test-run",
            )

            self.assertEqual(len(state["frontiers"]), 1)
            self.assertEqual(selected["frontier_id"], "frontier-translation-strain")
            self.assertIn("translation-strain rubric", brief)
            self.assertTrue((root / "state" / "frontiers.json").exists())
            self.assertTrue((root / "state" / "next_frontier_prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
