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
from .doctrine import write_candidates_from_idea
from .distill import (
    backfill_distillations,
    distill_new_ideas,
    validate_distillation_store,
)
from .dialectic import run_dialectic
from .frontier import prepare_frontier_brief, refresh_frontiers
from .growth import record_growth
from .human_condition import audit_human_condition_fit
from .librarian import Librarian
from .originality_audit import audit_new_ideas, write_incomplete_audits
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
    parser.add_argument("--skip-originality-audit", action="store_true")
    parser.add_argument("--no-frontier", action="store_true")
    parser.add_argument(
        "--dialectic-after",
        type=int,
        default=int(os.getenv("SPIRITUALITY_DIALECTIC_AFTER", "0")),
        help="Run one dialogue sidecar after every N successful parallel runs. Use 0 to disable.",
    )
    parser.add_argument("--no-dialectic", action="store_true")
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
    lock_dir = root / "runs" / "locks" / "parallel-research.lock"
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


def _build_prompt(
    config: EngineConfig,
    focus: str,
    librarian: Librarian,
    *,
    frontier_brief: str = "",
) -> str:
    current_state = "\n\n".join(
        part
        for part in [
            librarian.read_optional("state/current_focus.md"),
            librarian.read_optional("docs/modern-human-condition.md"),
        ]
        if part.strip()
    )
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
            frontier_brief=frontier_brief,
        )

    return build_originality_prompt(
        focus=focus,
        current_state=current_state,
        thinking_protocol=thinking_protocol,
        prior_codex_findings=codex_findings,
        prior_claude_findings=claude_findings,
        frontier_brief=frontier_brief,
    )


def _generate(config: EngineConfig, focus: str, frontier_brief: str = "") -> GeneratedIdea:
    librarian = Librarian(config.root)
    librarian.ensure_workspace()
    prompt = _build_prompt(config, focus, librarian, frontier_brief=frontier_brief)
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
    doctrine_counts = write_candidates_from_idea(
        root,
        generated.idea,
        run_id=generated.manifest.run_id,
    )
    generated.manifest.generated_observations.append(str(idea_path.relative_to(root)))
    if any(doctrine_counts.values()):
        generated.manifest.notes.append(
            "Updated doctrine candidates: "
            f"{doctrine_counts['teachings']} teaching, "
            f"{doctrine_counts['practices']} practice, "
            f"{doctrine_counts['tests']} test."
        )
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
    stdout_path = root / "runs" / f"parallel-{label}.stdout.log"
    stderr_path = root / "runs" / f"parallel-{label}.stderr.log"
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


def _maybe_run_dialectic_sidecar(
    root: Path,
    args: argparse.Namespace,
    *,
    execution_id: str,
) -> None:
    if args.no_dialectic or int(args.dialectic_after or 0) <= 0:
        return

    state_path = root / "state" / "dialectic_cadence.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = {"successful_parallel_runs": 0}
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {"successful_parallel_runs": 0}

    count = int(state.get("successful_parallel_runs") or 0) + 1
    due = count % int(args.dialectic_after) == 0
    state.update(
        {
            "dialectic_after": int(args.dialectic_after),
            "last_parallel_execution_id": execution_id,
            "last_checked_at": now_local_iso(),
            "successful_parallel_runs": count,
        }
    )
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not due:
        return

    dialectic_config = EngineConfig.load(
        root=root,
        agent="codex",
        provider="codex-cli",
        codex_model=args.codex_model,
        codex_search=True,
        claude_model=args.claude_model,
    )
    try:
        dialogues = run_dialectic(
            dialectic_config,
            max_pairs=1,
            execution_id=f"parallel-dialogue-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}",
            audit_syntheses=not args.skip_originality_audit,
            notify=True,
        )
        state["last_dialogue_at"] = now_local_iso()
        state["last_dialogue_count"] = len(dialogues)
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        Librarian(root).append_jsonl(
            "runs/dialogue-sidecar-events.jsonl",
            {
                "at": now_local_iso(),
                "count": len(dialogues),
                "execution_id": execution_id,
            },
        )
        print(
            json.dumps(
                {"event": "dialogue-sidecar", "count": len(dialogues)},
                sort_keys=True,
            ),
            flush=True,
        )
    except Exception as exc:
        state["last_dialogue_error"] = repr(exc)
        state["last_dialogue_error_at"] = now_local_iso()
        state_path.write_text(
            json.dumps(state, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        Librarian(root).append_jsonl(
            "runs/dialogue-sidecar-errors.jsonl",
            {
                "at": now_local_iso(),
                "error": repr(exc),
                "execution_id": execution_id,
            },
        )
        print(
            json.dumps(
                {"event": "dialogue-sidecar-error", "error": repr(exc)},
                sort_keys=True,
            ),
            flush=True,
        )


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
        ["git", "commit", "-m", f"Parallel research run {stamp}"],
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

    distill_config = EngineConfig.load(
        root=root,
        agent="codex",
        provider="offline",
        dry_run=True,
    )
    missing_count = backfill_distillations(distill_config)
    quality_issues = validate_distillation_store(distill_config)
    if quality_issues:
        raise RuntimeError(
            "Refusing to build public site because reader-facing copy failed: "
            + "; ".join(quality_issues[:5])
        )
    print(
        json.dumps(
            {
                "event": "public-copy-gate",
                "missing_distillations": missing_count,
            },
            sort_keys=True,
        ),
        flush=True,
    )

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
        frontier_brief = prepare_frontier_brief(
            root,
            focus=args.focus,
            execution_id=f"parallel-{datetime.now().astimezone().strftime('%Y%m%d-%H%M%S')}",
            enabled=not args.no_frontier,
        )
        configs = [codex_config, claude_config]
        generated: list[GeneratedIdea] = []
        errors: list[str] = []

        with ThreadPoolExecutor(max_workers=len(configs)) as executor:
            futures = {
                executor.submit(_generate, config, args.focus, frontier_brief): config
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

        distillation_ok = True
        if generated:
            execution_id = "parallel-" + "-".join(
                sorted(item.manifest.run_id[:15] for item in generated)
            )
            distill_config = EngineConfig.load(
                root=root,
                agent="codex",
                provider="codex-cli",
                codex_search=False,
            )
            try:
                distillation_count = distill_new_ideas(
                    distill_config,
                    [item.idea for item in generated],
                )
                quality_issues = validate_distillation_store(distill_config)
                if quality_issues:
                    raise RuntimeError(
                        "Distillation quality gate failed: " + "; ".join(quality_issues[:5])
                    )
                librarian.append_jsonl(
                    "runs/distillation-events.jsonl",
                    {
                        "at": now_local_iso(),
                        "count": distillation_count,
                        "titles": [item.idea.title for item in generated],
                    },
                )
                print(
                    json.dumps(
                        {
                            "event": "insight-distillation",
                            "count": distillation_count,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            except Exception as exc:
                distillation_ok = False
                librarian.append_jsonl(
                    "runs/distillation-errors.jsonl",
                    {
                        "at": now_local_iso(),
                        "error": repr(exc),
                        "titles": [item.idea.title for item in generated],
                    },
                )
                print(
                    json.dumps(
                        {
                            "event": "insight-distillation-error",
                            "error": repr(exc),
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

            record_growth(
                root,
                execution_id=execution_id,
                ideas=[item.idea for item in generated],
                run_ids=[item.manifest.run_id for item in generated],
                created_at=now_local_iso(),
            )
            human_condition_count = audit_human_condition_fit(
                root,
                [item.idea for item in generated],
                execution_id=execution_id,
                run_ids=[item.manifest.run_id for item in generated],
            )
            librarian.append_jsonl(
                "runs/human-condition-audit-events.jsonl",
                {
                    "at": now_local_iso(),
                    "count": human_condition_count,
                    "execution_id": execution_id,
                    "titles": [item.idea.title for item in generated],
                },
            )
            print(
                json.dumps(
                    {"event": "human-condition-audit", "count": human_condition_count},
                    sort_keys=True,
                ),
                flush=True,
            )

            if not args.skip_originality_audit:
                audit_config = EngineConfig.load(
                    root=root,
                    agent="codex",
                    provider="codex-cli",
                    codex_model=args.codex_model,
                    codex_search=True,
                )
                try:
                    audit_count = audit_new_ideas(
                        audit_config,
                        [item.idea for item in generated],
                        run_ids=[item.manifest.run_id for item in generated],
                        execution_id=execution_id,
                    )
                    librarian.append_jsonl(
                        "runs/originality-audit-events.jsonl",
                        {
                            "at": now_local_iso(),
                            "count": audit_count,
                            "execution_id": execution_id,
                            "titles": [item.idea.title for item in generated],
                        },
                    )
                    print(
                        json.dumps(
                            {"event": "originality-audit", "count": audit_count},
                            sort_keys=True,
                        ),
                        flush=True,
                    )
                except Exception as exc:
                    fallback_count = write_incomplete_audits(
                        root,
                        [item.idea for item in generated],
                        run_ids=[item.manifest.run_id for item in generated],
                        execution_id=execution_id,
                        reason=repr(exc),
                    )
                    librarian.append_jsonl(
                        "runs/originality-audit-errors.jsonl",
                        {
                            "at": now_local_iso(),
                            "error": repr(exc),
                            "execution_id": execution_id,
                            "fallback_count": fallback_count,
                            "titles": [item.idea.title for item in generated],
                        },
                    )
                    print(
                        json.dumps(
                            {
                                "event": "originality-audit-error",
                                "error": repr(exc),
                                "fallback_count": fallback_count,
                            },
                            sort_keys=True,
                        ),
                        flush=True,
                    )

            if not args.no_frontier:
                refresh_frontiers(root)

            _maybe_run_dialectic_sidecar(root, args, execution_id=execution_id)

        if errors:
            librarian.append_jsonl(
                "runs/parallel-errors.jsonl",
                {"at": now_local_iso(), "errors": errors},
            )
            print(json.dumps({"event": "parallel-errors", "errors": errors}))

        if generated:
            if not distillation_ok:
                raise RuntimeError("Refusing to deploy because insight distillation failed quality gates.")
            _publish_and_deploy(root, skip_deploy=args.skip_deploy)
        else:
            raise RuntimeError("No agents produced an idea.")

    finally:
        _release_lock(lock_dir)


if __name__ == "__main__":
    main()
