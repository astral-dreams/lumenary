from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from engine.doctrine import run_doctrine_council
from engine.run_mode import select_run_mode
from engine.test_registry import ensure_test_records
from engine.writing_gate import validate_public_writing


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def idea(idea_id: str = "idea-time") -> dict:
    return {
        "agent": "codex",
        "created_at": "2026-05-29T08:00:00+02:00",
        "critique": "The claim needs pressure from an unlike source before promotion.",
        "epistemic_labels": ["interpretive", "analogical"],
        "idea_id": idea_id,
        "idea_type": "model",
        "next_research_directions": ["Run a prior-art search and a break test."],
        "original_claim": "A useful claim should predict where a lived report and a formal model separate.",
        "path": "observations/codex/2026-05-29-time.md",
        "scores": {
            "counterargument_quality": 0.82,
            "cross_tradition_support": 0.70,
            "empirical_adjacency": 0.40,
            "explanatory_compression": 0.80,
            "generativity": 0.84,
            "logical_coherence": 0.86,
            "novelty": 0.72,
            "practice_testability": 0.75,
            "publishability": 0.82,
            "source_reliability": 0.78,
        },
        "source_basis": ["Primary source one", "Scientific source two"],
        "status": "draft",
        "title": "Time Needs Witness",
        "why_it_might_be_new": "It turns a familiar theme into a pressure test.",
    }


class LoopControlTests(unittest.TestCase):
    def test_select_run_mode_prioritizes_ready_teaching_without_practice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_jsonl(
                root / "doctrine" / "teachings.jsonl",
                [
                    {
                        "created_at": "2026-05-29T08:00:00+02:00",
                        "status": "teaching_ready",
                        "teaching_id": "teach-1",
                        "title": "A ready teaching",
                    }
                ],
            )

            selected = select_run_mode(root, requested="auto", focus="test")

            self.assertEqual(selected["mode"], "practice")
            self.assertTrue((root / "state" / "current_run_mode.json").exists())
            self.assertTrue((root / "runs" / "run-mode-events.jsonl").exists())

    def test_ensure_test_records_adds_three_supplemental_tests_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            records = [idea()]

            first = ensure_test_records(root, records, execution_id="run-1", run_ids=["run-1"])
            second = ensure_test_records(root, records, execution_id="run-2", run_ids=["run-2"])
            tests = [
                json.loads(line)
                for line in (root / "tests" / "tests.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(first, 3)
            self.assertEqual(second, 0)
            self.assertEqual({test["test_type"] for test in tests}, {"prior-art", "falsification-attempt", "cross-domain"})

    def test_writing_gate_blocks_jargon_title_and_short_at_a_glance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = idea("idea-jargon")
            write_jsonl(
                root / "publication" / "distillations.jsonl",
                [
                    {
                        "atAGlance": "This is too short.",
                        "ideaId": "idea-jargon",
                        "insight": "Compound Entry Grammar",
                        "keyPoints": ["One", "Two"],
                        "plainSummary": "A short sentence.",
                        "publicTitle": "Compound Entry Grammar",
                    }
                ],
            )

            issues = validate_public_writing(root, [record], require_distillation=True)
            codes = {issue.code for issue in issues}

            self.assertIn("public_title_jargon", codes)
            self.assertIn("at_a_glance_sentence_count", codes)
            self.assertIn("key_point_count", codes)

    def test_doctrine_council_weakens_teaching_when_originality_audit_finds_prior_art(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_jsonl(root / "hypotheses" / "ideas.jsonl", [idea("idea-known")])
            write_jsonl(
                root / "reviews" / "originality" / "audits.jsonl",
                [
                    {
                        "created_at": "2026-05-29T09:00:00+02:00",
                        "idea_id": "idea-known",
                        "originality_status": "known",
                    }
                ],
            )
            write_jsonl(
                root / "doctrine" / "teachings.jsonl",
                [
                    {
                        "created_at": "2026-05-29T08:00:00+02:00",
                        "falsifying_pressure": "A known prior argument would lower the claim.",
                        "source_idea_ids": ["idea-known"],
                        "status": "under_dialogue",
                        "teaching_id": "teach-known",
                        "title": "A teaching under pressure",
                    }
                ],
            )
            write_jsonl(root / "practices" / "protocols.jsonl", [])

            run_doctrine_council(root, date="2026-05-29")
            updated = [
                json.loads(line)
                for line in (root / "doctrine" / "teachings.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(updated[0]["status"], "weakened")
            self.assertTrue((root / "doctrine" / "councils" / "2026-05-29.json").exists())


if __name__ == "__main__":
    unittest.main()
