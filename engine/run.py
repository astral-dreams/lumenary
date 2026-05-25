from __future__ import annotations

import argparse
from datetime import datetime

from .config import EngineConfig
from .librarian import Librarian
from .prompts import build_originality_prompt
from .schemas import RunManifest, now_local_iso, slugify
from .thinker import get_thinker


def build_run_id(agent: str, focus: str) -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{agent}-{slugify(focus)[:48]}"


def run_once(config: EngineConfig, focus: str) -> RunManifest:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    current_state = librarian.read_optional("state/current_focus.md")
    codex_findings = librarian.read_optional("findings/codex-findings.md")
    claude_findings = librarian.read_optional("findings/claude-code-findings.md")
    prompt = build_originality_prompt(
        focus=focus,
        current_state=current_state,
        prior_codex_findings=codex_findings,
        prior_claude_findings=claude_findings,
    )

    manifest = RunManifest(
        run_id=build_run_id(config.agent, focus),
        agent=config.agent,
        provider=config.provider,
        dry_run=config.dry_run or config.provider == "offline",
        focus=focus,
        started_at=now_local_iso(),
    )

    thinker = get_thinker(config)
    idea = thinker.generate(
        focus=focus,
        agent=config.agent,
        prompt=prompt,
        root=config.root,
        run_id=manifest.run_id,
    )
    idea_path = librarian.save_idea(idea)
    manifest.generated_observations.append(str(idea_path.relative_to(config.root)))
    manifest.notes.append("Generated one draft idea record.")
    manifest.completed_at = now_local_iso()

    output = idea.to_markdown()
    librarian.save_run(manifest, prompt=prompt, generated_output=output)
    librarian.append_exploration_log(
        f"- Run `{manifest.run_id}` generated `{idea.title}`.\n"
        f"- Observation file: `{manifest.generated_observations[0]}`."
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one recursive research cycle.")
    parser.add_argument("--agent", default=None, help="Attribution agent name.")
    parser.add_argument("--provider", default=None, help="Thinking provider.")
    parser.add_argument("--dry-run", action="store_true", help="Use offline dry-run mode.")
    parser.add_argument("--model", default=None, help="Model to pass to codex exec.")
    parser.add_argument(
        "--search",
        action="store_true",
        help="Enable Codex CLI web search for the codex-cli provider.",
    )
    parser.add_argument(
        "--focus",
        default=(
            "Generate an original model for cross-tradition convergence without "
            "collapsing analogy into evidence."
        ),
        help="Research focus for this iteration.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = EngineConfig.load(
        agent=args.agent,
        provider=args.provider,
        dry_run=args.dry_run,
        codex_model=args.model,
        codex_search=args.search,
    )
    manifest = run_once(config, args.focus)
    print(f"run_id={manifest.run_id}")
    for observation in manifest.generated_observations:
        print(f"observation={observation}")


if __name__ == "__main__":
    main()
