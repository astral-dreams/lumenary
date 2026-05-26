from __future__ import annotations

import argparse
import json
import signal
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from .config import EngineConfig
from .journal import generate_journal_entry
from .librarian import Librarian
from .local_time import is_local_timezone, resolve_timezone, timezone_label
from .process_control import register_child, terminate_current_child, unregister_child
from .publisher import generate_daily_update
from .run import run_once
from .schemas import now_local_iso


_SHOULD_STOP = False


def _request_stop(signum: int, frame: object) -> None:
    global _SHOULD_STOP
    _SHOULD_STOP = True
    terminate_current_child()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run recursive research continuously.")
    parser.add_argument("--agent", default=None, help="Attribution agent name.")
    parser.add_argument(
        "--provider",
        default="codex-cli",
        help="Thinking provider (codex-cli, claude-code, offline).",
    )
    parser.add_argument("--model", default=None, help="Model to pass to the provider.")
    parser.add_argument("--search", action="store_true", help="Enable Codex web search (codex-cli only).")
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=30.0,
        help="Delay between iterations.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of iterations to run. Use 0 for continuous operation.",
    )
    parser.add_argument(
        "--max-failures",
        type=int,
        default=3,
        help="Stop supervised runs after this many consecutive failures.",
    )
    parser.add_argument(
        "--focus",
        default="Generate original cross-tradition ideas with rigorous epistemic labeling.",
        help="Default focus passed to each run.",
    )
    parser.add_argument(
        "--cadence",
        choices=("interval", "hourly-day"),
        default="interval",
        help="interval sleeps after each run; hourly-day runs on interval during the local research window.",
    )
    parser.add_argument(
        "--timezone",
        default="local",
        help="Timezone for cadence and Journal cutoff. Use local to follow the machine's current timezone.",
    )
    parser.add_argument(
        "--active-start-hour",
        type=int,
        default=7,
        help="Local hour when hourly-day research starts. Default: 7.",
    )
    parser.add_argument(
        "--end-hour",
        type=int,
        default=17,
        help="Local hour when research stops and Journal generation begins. Default: 17 for 5pm.",
    )
    parser.add_argument(
        "--publish-after-run",
        action="store_true",
        help="After each successful research run, generate publication artifacts and deploy the site.",
    )
    parser.add_argument(
        "--journal-after-window",
        action="store_true",
        help="After the daily research window closes, write the Journal entry and deploy it once.",
    )
    parser.add_argument(
        "--deploy-script",
        default="scripts/deploy_site.sh",
        help="Script used to build and deploy the website when publishing is enabled.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use the offline deterministic thinker.",
    )
    return parser.parse_args()


def _validate_window(args: argparse.Namespace) -> None:
    if not 0 <= args.active_start_hour <= 23:
        raise ValueError("--active-start-hour must be between 0 and 23.")
    if not 1 <= args.end_hour <= 24:
        raise ValueError("--end-hour must be between 1 and 24.")
    if args.active_start_hour >= args.end_hour:
        raise ValueError("--active-start-hour must be earlier than --end-hour.")


def _log_event(
    librarian: Librarian,
    event: str,
    message: str,
    *,
    extra: dict[str, object] | None = None,
) -> None:
    record = {
        "at": now_local_iso(),
        "event": event,
        "message": message,
        **(extra or {}),
    }
    librarian.append_jsonl("runs/scheduler-events.jsonl", record)
    print(json.dumps(record, sort_keys=True), flush=True)


def _run_deploy_script(
    config: EngineConfig,
    librarian: Librarian,
    *,
    deploy_script: str,
    reason: str,
) -> None:
    script_path = Path(deploy_script)
    if not script_path.is_absolute():
        script_path = config.root / script_path
    if not script_path.exists():
        raise FileNotFoundError(f"Deploy script does not exist: {script_path}")

    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    log_dir = config.root / "runs" / "deployments"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = log_dir / f"{stamp}.stdout.log"
    stderr_path = log_dir / f"{stamp}.stderr.log"

    process = subprocess.Popen(
        [str(script_path)],
        cwd=config.root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    register_child(process)
    try:
        stdout, stderr = process.communicate()
    finally:
        unregister_child(process)

    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    if process.returncode != 0:
        raise RuntimeError(
            f"Deploy script failed with exit code {process.returncode}. "
            f"See {stderr_path}."
        )

    _log_event(
        librarian,
        "deploy",
        "Deployed website.",
        extra={
            "reason": reason,
            "stdout": str(stdout_path.relative_to(config.root)),
            "stderr": str(stderr_path.relative_to(config.root)),
        },
    )


def _publish_site(
    config: EngineConfig,
    args: argparse.Namespace,
    librarian: Librarian,
    *,
    reason: str,
    update_daily: bool,
) -> None:
    if not args.publish_after_run:
        return

    if update_daily:
        try:
            daily_path, x_path = generate_daily_update(config)
            _log_event(
                librarian,
                "daily-publication",
                "Generated daily publication artifacts.",
                extra={
                    "daily": str(daily_path.relative_to(config.root)),
                    "x_draft": str(x_path.relative_to(config.root)),
                    "reason": reason,
                },
            )
        except FileNotFoundError as exc:
            _log_event(
                librarian,
                "daily-publication-skipped",
                str(exc),
                extra={"reason": reason},
            )

    if args.deploy_script:
        _run_deploy_script(
            config,
            librarian,
            deploy_script=args.deploy_script,
            reason=reason,
        )


def _run_research_cycle(
    config: EngineConfig,
    args: argparse.Namespace,
    librarian: Librarian,
) -> None:
    manifest = run_once(config, args.focus)
    librarian.append_exploration_log(f"- Scheduler completed run `{manifest.run_id}`.")
    print(f"{now_local_iso()} completed {manifest.run_id}", flush=True)
    _publish_site(
        config,
        args,
        librarian,
        reason=f"research run {manifest.run_id}",
        update_daily=True,
    )


def _sleep_until(target: datetime, timezone_name: str) -> None:
    while not _SHOULD_STOP:
        if is_local_timezone(timezone_name):
            current_local = datetime.now().astimezone()
            if current_local.utcoffset() != target.utcoffset():
                return
        remaining = (target - datetime.now(target.tzinfo)).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(30.0, remaining))


def _next_interval_boundary(now: datetime, interval_minutes: float) -> datetime:
    interval_seconds = max(60, int(interval_minutes * 60))
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elapsed_seconds = (now - day_start).total_seconds()
    next_elapsed = (int(elapsed_seconds // interval_seconds) + 1) * interval_seconds
    return day_start + timedelta(seconds=next_elapsed)


def _next_window_start(now: datetime, start_hour: int) -> datetime:
    candidate = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if now < candidate:
        return candidate
    return candidate + timedelta(days=1)


def _maybe_write_journal(
    config: EngineConfig,
    args: argparse.Namespace,
    librarian: Librarian,
) -> None:
    if not args.journal_after_window:
        return
    timezone = resolve_timezone(args.timezone)
    journal_date = datetime.now(timezone).date().isoformat()
    path = generate_journal_entry(
        config,
        date=journal_date,
        timezone_name=args.timezone,
    )
    if path is None:
        return
    _log_event(
        librarian,
        "journal",
        "Generated end-of-day Journal entry.",
        extra={"journal": str(path.relative_to(config.root))},
    )
    _publish_site(
        config,
        args,
        librarian,
        reason=f"journal {journal_date}",
        update_daily=False,
    )


def _handle_cycle_error(
    config: EngineConfig,
    librarian: Librarian,
    exc: Exception,
) -> None:
    error = {
        "at": now_local_iso(),
        "provider": config.provider,
        "error": repr(exc),
    }
    librarian.append_jsonl("runs/scheduler-errors.jsonl", error)
    print(json.dumps(error, sort_keys=True), flush=True)


def _run_interval_loop(
    config: EngineConfig,
    args: argparse.Namespace,
    librarian: Librarian,
) -> None:
    completed = 0
    consecutive_failures = 0
    while not _SHOULD_STOP:
        try:
            _run_research_cycle(config, args, librarian)
            completed += 1
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            _handle_cycle_error(config, librarian, exc)
            if args.iterations and consecutive_failures >= args.max_failures:
                break

        if args.iterations and completed >= args.iterations:
            break

        sleep_seconds = max(1.0, args.interval_minutes * 60.0)
        end = time.monotonic() + sleep_seconds
        while not _SHOULD_STOP and time.monotonic() < end:
            time.sleep(min(5.0, end - time.monotonic()))


def _run_hourly_day_loop(
    config: EngineConfig,
    args: argparse.Namespace,
    librarian: Librarian,
) -> None:
    _validate_window(args)
    completed = 0
    consecutive_failures = 0

    while not _SHOULD_STOP:
        timezone = resolve_timezone(args.timezone)
        now = datetime.now(timezone)

        if now.hour < args.active_start_hour:
            start = now.replace(
                hour=args.active_start_hour,
                minute=0,
                second=0,
                microsecond=0,
            )
            _log_event(
                librarian,
                "sleep",
                "Waiting for research window to open.",
                extra={
                    "timezone": timezone_label(args.timezone),
                    "until": start.isoformat(),
                },
            )
            _sleep_until(start, args.timezone)
            continue

        if now.hour >= args.end_hour:
            _maybe_write_journal(config, args, librarian)
            start = _next_window_start(now, args.active_start_hour)
            _log_event(
                librarian,
                "sleep",
                "Research window closed; waiting for next day.",
                extra={
                    "timezone": timezone_label(args.timezone),
                    "until": start.isoformat(),
                },
            )
            _sleep_until(start, args.timezone)
            continue

        try:
            _run_research_cycle(config, args, librarian)
            completed += 1
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            _handle_cycle_error(config, librarian, exc)
            if args.iterations and consecutive_failures >= args.max_failures:
                break

        if args.iterations and completed >= args.iterations:
            break

        timezone = resolve_timezone(args.timezone)
        now = datetime.now(timezone)
        if now.hour >= args.end_hour:
            continue

        next_run = _next_interval_boundary(now, args.interval_minutes)
        _log_event(
            librarian,
            "sleep",
            "Waiting for next research run.",
            extra={
                "timezone": timezone_label(args.timezone),
                "until": next_run.isoformat(),
            },
        )
        _sleep_until(next_run, args.timezone)


def main() -> None:
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    args = parse_args()
    model_kwargs: dict[str, str | None] = {}
    if args.provider == "claude-code":
        model_kwargs["claude_model"] = args.model
    else:
        model_kwargs["codex_model"] = args.model
    config = EngineConfig.load(
        agent=args.agent,
        provider=args.provider,
        dry_run=args.dry_run,
        codex_search=args.search,
        **model_kwargs,
    )
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    if args.cadence == "hourly-day":
        _run_hourly_day_loop(config, args, librarian)
    else:
        _run_interval_loop(config, args, librarian)


if __name__ == "__main__":
    main()
