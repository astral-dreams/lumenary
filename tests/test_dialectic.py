from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.config import EngineConfig
from engine.dialectic import _dialogue_markdown, _idea_from_candidate, detect_tensions, run_dialectic


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def scores(publishability: float = 0.82) -> dict[str, float]:
    return {
        "counterargument_quality": 0.82,
        "cross_tradition_support": 0.68,
        "empirical_adjacency": 0.24,
        "explanatory_compression": 0.82,
        "generativity": 0.88,
        "logical_coherence": 0.84,
        "novelty": 0.76,
        "practice_testability": 0.62,
        "publishability": publishability,
        "source_reliability": 0.72,
    }


def idea(agent: str, idea_id: str, title: str, claim: str) -> dict:
    return {
        "agent": agent,
        "created_at": "2026-05-26T12:00:00-07:00",
        "critique": "The idea needs a stronger source test before promotion.",
        "epistemic_labels": ["interpretive", "analogical"],
        "idea_id": idea_id,
        "idea_type": "model",
        "next_research_directions": ["Name the crux and test it against a practitioner source."],
        "original_claim": claim,
        "path": f"observations/{agent}/2026-05-26-{idea_id}.md",
        "scores": scores(),
        "source_basis": ["Primary source one", "Primary source two"],
        "status": "draft",
        "title": title,
        "why_it_might_be_new": "It makes a familiar comparison operational instead of decorative.",
    }


def audit(agent: str, idea_id: str, title: str) -> dict:
    return {
        "agent": agent,
        "anomaly_probe": {
            "anomaly_candidate": "A practitioner might reject the proposed translation strain as imported method pressure.",
            "confidence_effect": "Requires a dialogue or practitioner test.",
            "why_it_breaks_or_strains_model": "It would show that the method created the pressure it claims to find.",
        },
        "audit_id": f"audit-{idea_id}",
        "created_at": "2026-05-26T13:00:00-07:00",
        "idea_id": idea_id,
        "near_neighbors": [
            {
                "source": "Shared source pressure",
                "overlap": "Both ideas treat translation strain as a method.",
                "difference": "They disagree about whether it proves convergence.",
                "novelty_impact": "Moderate reduction.",
            }
        ],
        "next_loop_instructions": ["Stage a dialogue that names the unresolved crux."],
        "originality_status": "novel_synthesis",
        "title": title,
    }


class DialecticTests(unittest.TestCase):
    def test_dialogue_schemas_require_all_declared_properties_for_codex_cli(self) -> None:
        root = Path(__file__).resolve().parents[1]
        schema_paths = [
            root / "engine" / "json_schemas" / "dialogue_turn.schema.json",
            root / "engine" / "json_schemas" / "dialogue_verdict.schema.json",
        ]

        def assert_strict_object_shapes(node: object, path: str) -> None:
            if isinstance(node, dict):
                properties = node.get("properties")
                if isinstance(properties, dict):
                    self.assertEqual(
                        set(node.get("required") or []),
                        set(properties.keys()),
                        msg=f"{path} must require every declared property",
                    )
                for key, value in node.items():
                    assert_strict_object_shapes(value, f"{path}.{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    assert_strict_object_shapes(value, f"{path}[{index}]")

        for schema_path in schema_paths:
            with self.subTest(schema=schema_path.name):
                assert_strict_object_shapes(json.loads(schema_path.read_text(encoding="utf-8")), schema_path.name)

    def test_detect_tensions_prefers_shared_frontier_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = idea(
                "codex",
                "idea-codex",
                "Translation Strain As A Load Test",
                "Translation strain should test whether apparent convergence survives source pressure.",
            )
            claude = idea(
                "claude",
                "idea-claude",
                "Protocol Compatibility After Translation Strain",
                "Protocol compatibility should decide whether translation strain is procedural or propositional.",
            )
            write_jsonl(root / "hypotheses" / "ideas.jsonl", [codex, claude])
            write_jsonl(
                root / "reviews" / "originality" / "audits.jsonl",
                [audit("codex", "idea-codex", codex["title"]), audit("claude", "idea-claude", claude["title"])],
            )
            (root / "state").mkdir(parents=True, exist_ok=True)
            (root / "state" / "frontiers.json").write_text(
                json.dumps(
                    {
                        "frontiers": [
                            {
                                "frontier_id": "frontier-translation",
                                "idea_ids": ["idea-codex", "idea-claude"],
                                "priority": 0.9,
                                "title": "Translation strain methodology",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (root / "graph").mkdir(parents=True, exist_ok=True)
            (root / "graph" / "concept-graph.seed.json").write_text(
                json.dumps({"nodes": [], "edges": []}),
                encoding="utf-8",
            )

            pairs = detect_tensions(root, max_pairs=1)

            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0]["pair_id"], pairs[0]["pair_id"])
            self.assertEqual(pairs[0]["tension_type"], "shared_frontier")
            self.assertGreaterEqual(pairs[0]["priority"], 0.3)
            self.assertTrue((root / "state" / "dialogue_agenda.json").exists())

    def test_dry_run_writes_dialogue_artifacts_without_mutating_parent_ideas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex = idea(
                "codex",
                "idea-codex",
                "Translation Strain As A Load Test",
                "Translation strain should test whether apparent convergence survives source pressure.",
            )
            claude = idea(
                "claude",
                "idea-claude",
                "Protocol Compatibility After Translation Strain",
                "Protocol compatibility should decide whether translation strain is procedural or propositional.",
            )
            write_jsonl(root / "hypotheses" / "ideas.jsonl", [codex, claude])
            original_ideas = (root / "hypotheses" / "ideas.jsonl").read_text(encoding="utf-8")
            write_jsonl(
                root / "reviews" / "originality" / "audits.jsonl",
                [audit("codex", "idea-codex", codex["title"]), audit("claude", "idea-claude", claude["title"])],
            )
            (root / "state").mkdir(parents=True, exist_ok=True)
            (root / "state" / "frontiers.json").write_text(
                json.dumps(
                    {
                        "frontiers": [
                            {
                                "frontier_id": "frontier-translation",
                                "idea_ids": ["idea-codex", "idea-claude"],
                                "priority": 0.9,
                                "title": "Translation strain methodology",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (root / "graph").mkdir(parents=True, exist_ok=True)
            (root / "graph" / "concept-graph.seed.json").write_text(
                json.dumps({"nodes": [], "edges": []}),
                encoding="utf-8",
            )
            config = EngineConfig.load(root=root, agent="codex", provider="offline", dry_run=True)

            records = run_dialectic(config, max_pairs=1, audit_syntheses=False)

            self.assertEqual(len(records), 1)
            self.assertTrue((root / "reviews" / "dialogues" / "dialogues.jsonl").exists())
            self.assertTrue((root / "reviews" / "dialogues" / "outcomes.jsonl").exists())
            self.assertEqual(
                (root / "hypotheses" / "ideas.jsonl").read_text(encoding="utf-8"),
                original_ideas,
            )

    def test_dialogue_markdown_quotes_frontmatter_and_strips_banned_dashes(self) -> None:
        mark = chr(0x2014)
        dialogue = {
            "created_at": "2026-05-26T14:00:00-07:00",
            "dialogue_id": "dialogue-id",
            "pair": {
                "challenger_agent": "claude",
                "challenger_title": "Challenger Title",
                "proponent_agent": "codex",
                "proponent_title": 'Proponent "Title"',
                "tension_source": f'A title with "quotes" {mark} and a fence --- stays safe.',
            },
            "synthesis": {
                "convergence_claim": None,
                "new_frontier_question": None,
                "outcome": "revision",
                "summary": f"The synthesis used a banned dash {mark} but markdown should not keep it.",
                "unresolved_crux": None,
            },
            "title": f'A "quoted" dialogue {mark} with fence ---',
            "turns": [
                {
                    "argument": f"Challenge text {mark}",
                    "steelman": f"Steelman text {mark}",
                },
                {
                    "argument": "Rebuttal text",
                    "crux": "A crux",
                },
                {
                    "argument": "Counter text",
                },
            ],
        }

        markdown = _dialogue_markdown(dialogue)

        self.assertIn('title: "A \\"quoted\\" dialogue : with fence ---"', markdown)
        self.assertIn('proponent_idea: "Proponent \\"Title\\""', markdown)
        self.assertNotIn(mark, markdown)

    def test_candidate_synthesis_scores_are_clamped_and_sanitized(self) -> None:
        mark = chr(0x2014)
        candidate = {
            "critique": f"The candidate still needs pressure {mark} and source review.",
            "epistemic_labels": ["interpretive"],
            "idea_type": "synthesis",
            "next_research_directions": ["Run an originality audit."],
            "original_claim": f"This synthesis uses a banned dash {mark} in the source text.",
            "scores": {
                "counterargument_quality": 2,
                "cross_tradition_support": 0.5,
                "empirical_adjacency": 0.2,
                "explanatory_compression": 0.7,
                "generativity": 1.7,
                "logical_coherence": 0.8,
                "novelty": -0.4,
                "practice_testability": 0.6,
                "publishability": 0.9,
                "source_reliability": 0.75,
            },
            "source_basis": ["source one", "source two"],
            "title": "Candidate Synthesis",
            "why_it_might_be_new": "It joins the two parent claims under a new crux.",
        }

        record = _idea_from_candidate(
            candidate,
            agent="codex",
            dialogue_id="dialogue-id",
            parent_titles=["Parent A", "Parent B"],
        )

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.scores.novelty, 0.0)
        self.assertEqual(record.scores.generativity, 1.0)
        self.assertEqual(record.scores.counterargument_quality, 1.0)
        self.assertNotIn(mark, record.original_claim)


if __name__ == "__main__":
    unittest.main()
