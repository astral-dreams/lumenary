from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EngineConfig:
    root: Path
    agent: str = "codex"
    provider: str = "offline"
    dry_run: bool = False
    codex_model: str | None = None
    codex_search: bool = False
    codex_sandbox: str = "read-only"
    codex_timeout_seconds: int = 1800
    claude_model: str | None = None
    claude_timeout_seconds: int = 1800
    max_sources_per_run: int = 5
    max_ideas_per_run: int = 1

    @classmethod
    def load(
        cls,
        *,
        root: str | Path | None = None,
        agent: str | None = None,
        provider: str | None = None,
        dry_run: bool = False,
        codex_model: str | None = None,
        codex_search: bool | None = None,
        codex_sandbox: str | None = None,
        codex_timeout_seconds: int | None = None,
        claude_model: str | None = None,
        claude_timeout_seconds: int | None = None,
        max_sources_per_run: int | None = None,
        max_ideas_per_run: int | None = None,
    ) -> "EngineConfig":
        project_root = Path(root or os.getcwd()).resolve()
        return cls(
            root=project_root,
            agent=agent or os.getenv("SPIRITUALITY_AGENT", "codex"),
            provider=provider or os.getenv("SPIRITUALITY_PROVIDER", "offline"),
            dry_run=dry_run,
            codex_model=codex_model or os.getenv("SPIRITUALITY_CODEX_MODEL") or None,
            codex_search=(
                codex_search
                if codex_search is not None
                else os.getenv("SPIRITUALITY_CODEX_SEARCH", "false").lower()
                in {"1", "true", "yes", "on"}
            ),
            codex_sandbox=codex_sandbox
            or os.getenv("SPIRITUALITY_CODEX_SANDBOX", "read-only"),
            codex_timeout_seconds=codex_timeout_seconds
            or int(os.getenv("SPIRITUALITY_CODEX_TIMEOUT_SECONDS", "1800")),
            claude_model=claude_model or os.getenv("SPIRITUALITY_CLAUDE_MODEL") or None,
            claude_timeout_seconds=claude_timeout_seconds
            or int(os.getenv("SPIRITUALITY_CLAUDE_TIMEOUT_SECONDS", "1800")),
            max_sources_per_run=max_sources_per_run
            or int(os.getenv("SPIRITUALITY_MAX_SOURCES", "5")),
            max_ideas_per_run=max_ideas_per_run
            or int(os.getenv("SPIRITUALITY_MAX_IDEAS", "1")),
        )
