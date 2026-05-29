from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .schemas import now_local_iso


HEALTH_PATH = "runs/run-health.json"
EVENTS_PATH = "runs/run-health-events.jsonl"


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")


def _run(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _git_summary(root: Path) -> dict[str, Any]:
    head = _run(root, ["git", "rev-parse", "--short", "HEAD"])
    status = _run(root, ["git", "status", "--short"])
    return {
        "dirty_count": len([line for line in status.stdout.splitlines() if line.strip()]),
        "head": head.stdout.strip() if head.returncode == 0 else "",
    }


def _latest_jsonl(path: Path) -> dict[str, Any] | None:
    records = _read_jsonl(path)
    if not records:
        return None
    return records[-1]


def _latest_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def _latest_files(root: Path, relative_dir: str, suffix: str = ".md", limit: int = 5) -> list[dict[str, Any]]:
    directory = root / relative_dir
    if not directory.exists():
        return []
    files = sorted(
        [path for path in directory.iterdir() if path.is_file() and path.name.endswith(suffix)],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "path": str(path.relative_to(root)),
        }
        for path in files[:limit]
    ]


def _launchctl_job(label: str) -> dict[str, Any]:
    process = subprocess.run(
        ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    text = process.stdout
    if process.returncode != 0:
        return {"label": label, "loaded": False, "error": process.stderr.strip()}
    state = re.search(r"state = ([^\n]+)", text)
    runs = re.search(r"runs = ([^\n]+)", text)
    last_exit = re.search(r"last exit code = ([^\n]+)", text)
    return {
        "label": label,
        "last_exit_code": last_exit.group(1).strip() if last_exit else "",
        "loaded": True,
        "runs": runs.group(1).strip() if runs else "",
        "state": state.group(1).strip() if state else "",
    }


def _next_research_time(now: datetime) -> str:
    local = now.astimezone()
    if local.hour < 7:
        return local.replace(hour=7, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")
    if local.hour >= 17:
        tomorrow = local + timedelta(days=1)
        return tomorrow.replace(hour=7, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")
    minute = 30 if local.minute < 30 else 0
    hour = local.hour if local.minute < 30 else local.hour + 1
    if hour >= 17:
        tomorrow = local + timedelta(days=1)
        return tomorrow.replace(hour=7, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")
    return local.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat(timespec="seconds")


def _next_daily_time(now: datetime, *, hour: int, minute: int) -> str:
    local = now.astimezone()
    candidate = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if local >= candidate:
        candidate += timedelta(days=1)
    return candidate.isoformat(timespec="seconds")


def build_run_health(root: Path) -> dict[str, Any]:
    now = datetime.now().astimezone()
    ideas = _read_jsonl(root / "hypotheses" / "ideas.jsonl")
    tests = _read_jsonl(root / "tests" / "tests.jsonl")
    current_mode = _read_json(root / "state" / "current_run_mode.json", {})
    deploy_log = root / "runs" / "parallel-deploy.stdout.log"
    deploy_text = deploy_log.read_text(encoding="utf-8", errors="ignore") if deploy_log.exists() else ""
    deployment_urls = re.findall(r"https://[a-z0-9]+\.thelumenary\.pages\.dev", deploy_text)

    health = {
        "generated_at": now_local_iso(),
        "git": _git_summary(root),
        "jobs": {
            "daily_publish": _launchctl_job("com.lumenary.daily-publish"),
            "map_refresh": _launchctl_job("com.lumenary.map-refresh"),
            "research": _launchctl_job("com.lumenary.research"),
        },
        "latest": {
            "daily_posts": _latest_files(root, "publication/daily", limit=3),
            "deployment_url": deployment_urls[-1] if deployment_urls else "",
            "ideas": sorted(
                [
                    {
                        "agent": idea.get("agent"),
                        "created_at": idea.get("created_at"),
                        "idea_id": idea.get("idea_id"),
                        "title": idea.get("title"),
                    }
                    for idea in ideas
                ],
                key=lambda item: str(item.get("created_at") or ""),
                reverse=True,
            )[:6],
            "journal_posts": _latest_files(root, "publication/journal", limit=3),
            "parallel_stdout_mtime": _latest_mtime(root / "runs" / "parallel-research.stdout.log"),
        },
        "mode": current_mode,
        "next": {
            "journal": _next_daily_time(now, hour=17, minute=15),
            "map": _next_daily_time(now, hour=18, minute=0),
            "research": _next_research_time(now),
        },
        "recent_events": _read_jsonl(root / EVENTS_PATH)[-20:],
        "stats": {
            "idea_count": len(ideas),
            "pending_tests": sum(1 for test in tests if str(test.get("status") or "") in {"proposed", "running"}),
            "tests": len(tests),
        },
    }
    return health


def record_run_event(
    root: Path,
    *,
    event: str,
    execution_id: str,
    status: str,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "at": now_local_iso(),
        "detail": detail or {},
        "event": event,
        "execution_id": execution_id,
        "status": status,
    }
    _append_jsonl(root / EVENTS_PATH, payload)
    _write_json(root / HEALTH_PATH, build_run_health(root))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write or print Lumenary run health.")
    parser.add_argument("--write", action="store_true", help="Write runs/run-health.json.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd().resolve()
    health = build_run_health(root)
    if args.write:
        _write_json(root / HEALTH_PATH, health)
    print(json.dumps(health, indent=2, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
