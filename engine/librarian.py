from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import IdeaRecord, RunManifest, now_local_iso, slugify


class Librarian:
    def __init__(self, root: Path) -> None:
        self.root = root

    def ensure_workspace(self) -> None:
        for relative in [
            "corpus/traditions",
            "corpus/science",
            "claims",
            "concepts",
            "docs",
            "findings/claude",
            "findings/codex",
            "findings/convergences",
            "graph",
            "hypotheses",
            "notes/source-cards",
            "observations/claude",
            "observations/codex",
            "runs",
            "sources",
            "state",
            "syntheses",
        ]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)

    def read_optional(self, relative_path: str) -> str:
        path = self.root / relative_path
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def append_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def append_jsonl(self, relative_path: str, record: dict[str, Any]) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True))
            handle.write("\n")
        return path

    def save_idea(self, idea: IdeaRecord) -> Path:
        filename = f"{idea.created_at[:10]}-{slugify(idea.title)}.md"
        relative = f"observations/{idea.agent}/{filename}"
        path = self.write_text(relative, idea.to_markdown())
        self.append_jsonl("hypotheses/ideas.jsonl", idea.to_dict())
        return path

    def save_run(
        self,
        manifest: RunManifest,
        *,
        prompt: str,
        generated_output: str,
    ) -> Path:
        run_dir = self.root / "runs" / manifest.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=True, sort_keys=True),
            encoding="utf-8",
        )
        (run_dir / "prompt.md").write_text(prompt, encoding="utf-8")
        (run_dir / "output.md").write_text(generated_output, encoding="utf-8")
        return run_dir

    def append_exploration_log(self, text: str) -> None:
        stamp = now_local_iso()
        self.append_text("state/exploration_log.md", f"\n## {stamp}\n\n{text}\n")

