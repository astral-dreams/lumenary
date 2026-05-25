from __future__ import annotations

import argparse
import json
import signal
import time

from .config import EngineConfig
from .librarian import Librarian
from .process_control import terminate_current_child
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
        help="Thinking provider. Use codex-cli for the local Codex subscription.",
    )
    parser.add_argument("--model", default=None, help="Model to pass to codex exec.")
    parser.add_argument("--search", action="store_true", help="Enable Codex web search.")
    parser.add_argument(
        "--interval-minutes",
        type=float,
        default=120.0,
        help="Delay between iterations.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=0,
        help="Number of iterations to run. Use 0 for continuous operation.",
    )
    parser.add_argument(
        "--focus",
        default="Generate original cross-tradition ideas with rigorous epistemic labeling.",
        help="Default focus passed to each run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use the offline deterministic thinker.",
    )
    return parser.parse_args()


def main() -> None:
    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    args = parse_args()
    config = EngineConfig.load(
        agent=args.agent,
        provider=args.provider,
        dry_run=args.dry_run,
        codex_model=args.model,
        codex_search=args.search,
    )
    librarian = Librarian(config.root)
    librarian.ensure_workspace()

    completed = 0
    while not _SHOULD_STOP:
        try:
            manifest = run_once(config, args.focus)
            librarian.append_exploration_log(
                f"- Scheduler completed run `{manifest.run_id}`."
            )
            print(f"{now_local_iso()} completed {manifest.run_id}", flush=True)
        except Exception as exc:
            error = {
                "at": now_local_iso(),
                "provider": config.provider,
                "error": repr(exc),
            }
            librarian.append_jsonl("runs/scheduler-errors.jsonl", error)
            print(json.dumps(error, sort_keys=True), flush=True)

        completed += 1
        if args.iterations and completed >= args.iterations:
            break

        sleep_seconds = max(1.0, args.interval_minutes * 60.0)
        end = time.monotonic() + sleep_seconds
        while not _SHOULD_STOP and time.monotonic() < end:
            time.sleep(min(5.0, end - time.monotonic()))


if __name__ == "__main__":
    main()
