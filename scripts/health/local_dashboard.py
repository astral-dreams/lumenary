#!/usr/bin/env python3
"""Local-only run health dashboard for The Lumenary."""

from __future__ import annotations

import html
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PORT = int(os.environ.get("LUMENARY_HEALTH_PORT", "8790"))


def health() -> dict:
    subprocess.run(
        ["python3", "-m", "engine.run_health", "--write"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    path = ROOT / "runs" / "run-health.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def e(value) -> str:
    return html.escape(str(value or ""))


def card(title: str, value: str, note: str = "") -> str:
    return f"""
      <section class="card">
        <span>{e(title)}</span>
        <strong>{e(value)}</strong>
        <p>{e(note)}</p>
      </section>
    """


def render() -> str:
    data = health()
    jobs = data.get("jobs", {})
    latest = data.get("latest", {})
    mode = data.get("mode", {})
    stats = data.get("stats", {})
    next_times = data.get("next", {})
    ideas = latest.get("ideas", [])
    events = data.get("recent_events", [])

    idea_rows = "".join(
        f"<tr><td>{e(item.get('created_at'))}</td><td>{e(item.get('agent'))}</td><td>{e(item.get('title'))}</td></tr>"
        for item in ideas
    )
    event_rows = "".join(
        f"<tr><td>{e(item.get('at'))}</td><td>{e(item.get('event'))}</td><td>{e(item.get('status'))}</td><td>{e(item.get('detail'))}</td></tr>"
        for item in events[-10:]
    )
    job_rows = "".join(
        f"<tr><td>{e(name)}</td><td>{e(job.get('state'))}</td><td>{e(job.get('runs'))}</td><td>{e(job.get('last_exit_code'))}</td></tr>"
        for name, job in jobs.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="refresh" content="30" />
  <title>Lumenary Run Health</title>
  <style>
    :root {{ --bg:#f6f4ef; --panel:#fffaf1; --ink:#172017; --muted:#667061; --line:#d8d0c2; --green:#315f45; }}
    body {{ background:var(--bg); color:var(--ink); font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin:0; }}
    main {{ max-width:1180px; margin:0 auto; padding:32px 22px 60px; }}
    h1 {{ font-size:clamp(2rem,4vw,3.8rem); line-height:1; margin:0 0 8px; }}
    h2 {{ font-size:1.1rem; margin:28px 0 10px; }}
    .lead {{ color:var(--muted); margin:0 0 24px; }}
    .grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:16px; }}
    .card span {{ color:var(--muted); display:block; font-size:.8rem; font-weight:800; text-transform:uppercase; }}
    .card strong {{ display:block; font-size:1.35rem; margin-top:5px; }}
    .card p {{ color:var(--muted); font-size:.88rem; line-height:1.35; min-height:2.4em; }}
    table {{ border-collapse:collapse; width:100%; background:var(--panel); border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
    th, td {{ border-bottom:1px solid var(--line); font-size:.9rem; padding:10px 12px; text-align:left; vertical-align:top; }}
    th {{ color:var(--muted); font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; }}
    code {{ white-space:pre-wrap; }}
    @media (max-width:800px) {{ .grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
<main>
  <h1>Lumenary Run Health</h1>
  <p class="lead">Local-only dashboard. Auto-refreshes every 30 seconds.</p>
  <div class="grid">
    {card("Current mode", mode.get("label", "Unknown"), mode.get("reason", ""))}
    {card("Ideas", str(stats.get("idea_count", 0)), f"Tests: {stats.get('tests', 0)}; pending: {stats.get('pending_tests', 0)}")}
    {card("Next research", next_times.get("research", ""), "Half-hourly from 7am to 5pm local time.")}
    {card("Latest deploy", latest.get("deployment_url", ""), "Most recent Pages deployment seen in logs.")}
  </div>
  <h2>Jobs</h2>
  <table><thead><tr><th>Job</th><th>State</th><th>Runs</th><th>Last Exit</th></tr></thead><tbody>{job_rows}</tbody></table>
  <h2>Latest Ideas</h2>
  <table><thead><tr><th>Created</th><th>Agent</th><th>Title</th></tr></thead><tbody>{idea_rows}</tbody></table>
  <h2>Recent Events</h2>
  <table><thead><tr><th>At</th><th>Event</th><th>Status</th><th>Detail</th></tr></thead><tbody>{event_rows}</tbody></table>
</main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/", "/health/"}:
            self.send_response(404)
            self.end_headers()
            return
        body = render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Local run health dashboard: http://127.0.0.1:{PORT}/health/")
    server.serve_forever()


if __name__ == "__main__":
    main()
