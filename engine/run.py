from __future__ import annotations

import argparse
from datetime import datetime

from .config import EngineConfig
from .distill import distill_new_ideas
from .frontier import prepare_frontier_brief, refresh_frontiers
from .growth import record_growth
from .librarian import Librarian
from .prompts import build_claude_collaborative_prompt, build_originality_prompt
from .schemas import RunManifest, now_local_iso, slugify
from .thinker import get_thinker


def build_run_id(agent: str, focus: str) -> str:
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    return f"{stamp}-{agent}-{slugify(focus)[:48]}"


def _gather_codex_observations(librarian: Librarian) -> str:
    obs_dir = librarian.root / "observations" / "codex"
    if not obs_dir.is_dir():
        return ""
    parts: list[str] = []
    for path in sorted(obs_dir.glob("*.md")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n---\n".join(parts)


def run_once(config: EngineConfig, focus: str, *, use_frontier: bool = True) -> RunManifest:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    manifest = RunManifest(
        run_id=build_run_id(config.agent, focus),
        agent=config.agent,
        provider=config.provider,
        dry_run=config.dry_run or config.provider == "offline",
        focus=focus,
        started_at=now_local_iso(),
    )
    frontier_brief = prepare_frontier_brief(
        config.root,
        focus=focus,
        execution_id=manifest.run_id,
        enabled=use_frontier,
    )

    current_state = librarian.read_optional("state/current_focus.md")
    thinking_protocol = librarian.read_optional("state/thinking_protocol.md")
    codex_findings = librarian.read_optional("findings/codex-findings.md")
    claude_findings = librarian.read_optional("findings/claude-code-findings.md")

    if config.provider == "claude-code":
        codex_observations = _gather_codex_observations(librarian)
        concept_graph = librarian.read_optional("graph/concept-graph.seed.json")
        next_directions = librarian.read_optional("state/next_directions.md")
        prompt = build_claude_collaborative_prompt(
            focus=focus,
            current_state=current_state,
            thinking_protocol=thinking_protocol,
            prior_codex_findings=codex_findings,
            prior_claude_findings=claude_findings,
            codex_observations=codex_observations,
            concept_graph=concept_graph,
            next_directions=next_directions,
            frontier_brief=frontier_brief,
        )
    else:
        prompt = build_originality_prompt(
            focus=focus,
            current_state=current_state,
            thinking_protocol=thinking_protocol,
            prior_codex_findings=codex_findings,
            prior_claude_findings=claude_findings,
            frontier_brief=frontier_brief,
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
    record_growth(
        config.root,
        execution_id=manifest.run_id,
        ideas=[idea],
        run_ids=[manifest.run_id],
        created_at=manifest.completed_at,
    )
    if config.provider == "claude-code" and not config.dry_run:
        distill_new_ideas(config, [idea])
    if use_frontier:
        refresh_frontiers(config.root)
    librarian.append_exploration_log(
        f"- Run `{manifest.run_id}` generated `{idea.title}`.\n"
        f"- Observation file: `{manifest.generated_observations[0]}`."
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one recursive research cycle.")
    parser.add_argument("--agent", default=None, help="Attribution agent name.")
    parser.add_argument("--provider", default=None, help="Thinking provider (offline, codex-cli, claude-code).")
    parser.add_argument("--dry-run", action="store_true", help="Use offline dry-run mode.")
    parser.add_argument("--model", default=None, help="Model to pass to the provider.")
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
    parser.add_argument(
        "--no-frontier",
        action="store_true",
        help="Do not steer this run with the generated frontier brief.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider = args.provider
    model_kwargs: dict[str, str | None] = {}
    if provider == "claude-code":
        model_kwargs["claude_model"] = args.model
    else:
        model_kwargs["codex_model"] = args.model
    config = EngineConfig.load(
        agent=args.agent,
        provider=provider,
        dry_run=args.dry_run,
        codex_search=args.search,
        **model_kwargs,
    )
    manifest = run_once(config, args.focus, use_frontier=not args.no_frontier)
    print(f"run_id={manifest.run_id}")
    for observation in manifest.generated_observations:
        print(f"observation={observation}")


if __name__ == "__main__":
    main()
