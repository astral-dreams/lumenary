from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import EngineConfig
from .growth import record_growth
from .librarian import Librarian
from .prompts import build_claude_collaborative_prompt, build_originality_prompt
from .publisher import generate_daily_update
from .run import _gather_codex_observations, build_run_id
from .schemas import IdeaRecord, RunManifest, now_local_iso
from .thinker import get_thinker


@dataclass
class GeneratedIdea:
    config: EngineConfig
    idea: IdeaRecord
    manifest: RunManifest
    prompt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Codex and Claude research in parallel, then publish safely."
    )
    parser.add_argument(
        "--focus",
        default=(
            "Generate an original cross-tradition finding for The Lumenary. "
            "Use source grounding, engage prior Codex and Claude findings, "
            "follow docs/writing-style.md, and do not use em dashes."
        ),
    )
    parser.add_argument("--codex-model", default=None)
    parser.add_argument("--claude-model", default="opus")
    parser.add_argument("--stop-at", default=os.getenv("SPIRITUALITY_STOP_AT"))
    parser.add_argument(
        "--launchagent-plist",
        default=os.getenv(
            "SPIRITUALITY_LAUNCHAGENT_PLIST",
            "/Users/johnforrester/Library/LaunchAgents/com.lumenary.overnight-parallel.plist",
        ),
    )
    parser.add_argument("--unload-after-stop", action="store_true")
    parser.add_argument("--skip-deploy", action="store_true")
    return parser.parse_args()


def _deadline_reached(stop_at: str | None) -> bool:
    if not stop_at:
        return False
    cutoff = datetime.fromisoformat(stop_at)
    now = datetime.now(cutoff.tzinfo) if cutoff.tzinfo else datetime.now().astimezone()
    return now >= cutoff


def _self_unload(plist_path: str) -> None:
    subprocess.run(
        ["launchctl", "bootout", f"gui/{os.getuid()}", plist_path],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _acquire_lock(root: Path) -> Path | None:
    lock_dir = root / "runs" / "locks" / "overnight-parallel.lock"
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock_dir.mkdir()
    except FileExistsError:
        return None
    (lock_dir / "pid").write_text(str(os.getpid()), encoding="utf-8")
    (lock_dir / "started_at").write_text(now_local_iso(), encoding="utf-8")
    return lock_dir


def _release_lock(lock_dir: Path) -> None:
    shutil.rmtree(lock_dir, ignore_errors=True)


def _build_prompt(config: EngineConfig, focus: str, librarian: Librarian) -> str:
    current_state = librarian.read_optional("state/current_focus.md")
    thinking_protocol = librarian.read_optional("state/thinking_protocol.md")
    codex_findings = librarian.read_optional("findings/codex-findings.md")
    claude_findings = librarian.read_optional("findings/claude-code-findings.md")

    if config.provider == "claude-code":
        return build_claude_collaborative_prompt(
            focus=focus,
            current_state=current_state,
            thinking_protocol=thinking_protocol,
            prior_codex_findings=codex_findings,
            prior_claude_findings=claude_findings,
            codex_observations=_gather_codex_observations(librarian),
            concept_graph=librarian.read_optional("graph/concept-graph.seed.json"),
            next_directions=librarian.read_optional("state/next_directions.md"),
        )

    return build_originality_prompt(
        focus=focus,
        current_state=current_state,
        thinking_protocol=thinking_protocol,
        prior_codex_findings=codex_findings,
        prior_claude_findings=claude_findings,
    )


def _generate(config: EngineConfig, focus: str) -> GeneratedIdea:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()
    prompt = _build_prompt(config, focus, librarian)
    manifest = RunManifest(
        run_id=build_run_id(config.agent, focus),
        agent=config.agent,
        provider=config.provider,
        dry_run=config.dry_run or config.provider == "offline",
        focus=focus,
        started_at=now_local_iso(),
    )
    idea = get_thinker(config).generate(
        focus=focus,
        agent=config.agent,
        prompt=prompt,
        root=config.root,
        run_id=manifest.run_id,
    )
    manifest.completed_at = now_local_iso()
    manifest.notes.append("Generated one draft idea record in a parallel run.")
    return GeneratedIdea(config=config, idea=idea, manifest=manifest, prompt=prompt)


def _save_generated(root: Path, generated: GeneratedIdea) -> None:
    librarian = Librarian(root)
    idea_path = librarian.save_idea(generated.idea)
    generated.manifest.generated_observations.append(str(idea_path.relative_to(root)))
    librarian.save_run(
        generated.manifest,
        prompt=generated.prompt,
        generated_output=generated.idea.to_markdown(),
    )
    librarian.append_exploration_log(
        f"- Parallel run `{generated.manifest.run_id}` generated "
        f"`{generated.idea.title}`.\n"
        f"- Observation file: `{generated.manifest.generated_observations[0]}`."
    )


def _run_command(
    root: Path,
    command: list[str],
    *,
    label: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path = root / "runs" / f"overnight-{label}.stdout.log"
    stderr_path = root / "runs" / f"overnight-{label}.stderr.log"
    stdout_path.write_text(process.stdout, encoding="utf-8")
    stderr_path.write_text(process.stderr, encoding="utf-8")
    if check and process.returncode != 0:
        raise RuntimeError(
            f"{label} failed with exit code {process.returncode}. "
            f"See {stderr_path.relative_to(root)}."
        )
    return process


def _scan_public_copy(root: Path) -> None:
    dist = root / "dist"
    mark = chr(0x2014)
    escaped = "\\u" + "2014"
    entities = ["&m" + "dash;", "&#" + "8212;"]
    bad: list[str] = []
    for path in dist.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        count = text.count(mark) + text.count(escaped)
        count += sum(text.count(entity) for entity in entities)
        if count:
            bad.append(f"{path.relative_to(root)}: {count}")
    if bad:
        raise RuntimeError("Public copy contains banned punctuation: " + "; ".join(bad))


def _commit_and_push(root: Path) -> None:
    _run_command(root, ["git", "add", "-A"], label="git-add")
    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=root,
        check=False,
    )
    if diff.returncode == 0:
        print("No staged changes to commit.", flush=True)
        return

    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    _run_command(
        root,
        ["git", "commit", "-m", f"Overnight parallel research run {stamp}"],
        label="git-commit",
    )
    _run_command(root, ["git", "push", "origin", "main"], label="git-push")


def _publish_and_deploy(root: Path, *, skip_deploy: bool) -> None:
    config = EngineConfig.load(root=root, agent="codex", provider="codex-cli")
    try:
        daily_path, x_path = generate_daily_update(config)
        print(
            json.dumps(
                {
                    "event": "daily-publication",
                    "daily": str(daily_path.relative_to(root)),
                    "x_draft": str(x_path.relative_to(root)),
                },
                sort_keys=True,
            ),
            flush=True,
        )
    except FileNotFoundError as exc:
        print(json.dumps({"event": "daily-publication-skipped", "error": str(exc)}))

    _run_command(root, ["npm", "run", "build"], label="build")
    _scan_public_copy(root)
    _commit_and_push(root)

    if not skip_deploy:
        _run_command(
            root,
            [
                "npx",
                "wrangler",
                "pages",
                "deploy",
                "dist",
                "--project-name",
                "thelumenary",
                "--branch",
                "main",
            ],
            label="deploy",
        )


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()

    if _deadline_reached(args.stop_at):
        print(
            json.dumps(
                {
                    "event": "deadline-reached",
                    "stop_at": args.stop_at,
                    "at": now_local_iso(),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if args.unload_after_stop and args.launchagent_plist:
            _self_unload(args.launchagent_plist)
        return

    lock_dir = _acquire_lock(root)
    if lock_dir is None:
        print(
            json.dumps({"event": "locked", "message": "Another run is active."}),
            flush=True,
        )
        return

    try:
        _run_command(root, ["git", "pull", "origin", "main", "--ff-only"], label="git-pull")
        codex_config = EngineConfig.load(
            root=root,
            agent="codex",
            provider="codex-cli",
            codex_model=args.codex_model,
            codex_search=True,
        )
        claude_config = EngineConfig.load(
            root=root,
            agent="claude",
            provider="claude-code",
            claude_model=args.claude_model,
        )
        configs = [codex_config, claude_config]
        generated: list[GeneratedIdea] = []
        errors: list[str] = []

        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            futures = {
                executor.submit(_generate, config, args.focus): config
                for config in configs
            }
            for future in as_completed(futures):
                config = futures[future]
                try:
                    generated.append(future.result())
                except Exception as exc:
                    errors.append(f"{config.agent}: {exc!r}")

        librarian = Librarian(root)
        for item in sorted(generated, key=lambda result: result.config.agent):
            _save_generated(root, item)

        if generated:
            execution_id = "parallel-" + "-".join(
                sorted(item.manifest.run_id[:15] for item in generated)
            )
            record_growth(
                root,
                execution_id=execution_id,
                ideas=[item.idea for item in generated],
                run_ids=[item.manifest.run_id for item in generated],
                created_at=now_local_iso(),
            )

        if errors:
            librarian.append_jsonl(
                "runs/parallel-errors.jsonl",
                {"at": now_local_iso(), "errors": errors},
            )
            print(json.dumps({"event": "parallel-errors", "errors": errors}))

        if generated:
            _publish_and_deploy(root, skip_deploy=args.skip_deploy)
        else:
            raise RuntimeError("No agents produced an idea.")

    finally:
        _release_lock(lock_dir)


if __name__ == "__main__":
    main()
