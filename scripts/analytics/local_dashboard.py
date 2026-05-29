#!/usr/bin/env python3
"""Local-only analytics dashboard for The Lumenary.

This intentionally does not live under src/pages or public. Run it on the
local machine when you want the private marketing dashboard.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PORT = int(os.environ.get("LUMENARY_ANALYTICS_PORT", "8789"))
UPDATE_STATUS_PATH = ROOT / "data" / "analytics" / "update-status.json"


def read_json(relative_path: str, fallback):
    path = ROOT / relative_path
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_jsonl(relative_path: str):
    path = ROOT / relative_path
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def public_claim_count(ideas):
    return sum(
        1
        for idea in ideas
        if float(idea.get("scores", {}).get("source_reliability", 0)) >= 0.70
        and float(idea.get("scores", {}).get("counterargument_quality", 0)) >= 0.75
        and float(idea.get("scores", {}).get("publishability", 0)) >= 0.78
        and len([item for item in idea.get("source_basis", []) if str(item).strip()]) >= 2
        and idea.get("status") not in {"rejected"}
    )


def status_label(value: str) -> str:
    return value.replace("_", " ").title()


def num(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def whole(value) -> str:
    return f"{int(round(num(value))):,}"


def pct(value) -> str:
    return f"{num(value) * 100:.1f}%"


def metric_sum(report: dict, metric: str) -> float:
    return sum(num(row.get(metric)) for row in report.get("rows", []))


def weighted_average(report: dict, metric: str, weight: str) -> float:
    weighted_total = 0.0
    weight_total = 0.0
    for row in report.get("rows", []):
        row_weight = num(row.get(weight))
        weighted_total += num(row.get(metric)) * row_weight
        weight_total += row_weight
    return weighted_total / weight_total if weight_total else 0.0


def snapshot_meta(snapshot: dict, missing_label: str) -> str:
    collected = snapshot.get("collected_at")
    if not collected:
        return missing_label
    return f"Collected {collected}"


def empty_panel(title: str, message: str) -> str:
    return (
        f'<section class="panel"><h2>{escape(title)}</h2>'
        f'<p class="empty-state">{escape(message)}</p></section>'
    )


def table_panel(title: str, rows: list[str], empty_message: str) -> str:
    if not rows:
        return empty_panel(title, empty_message)
    return f'<section class="panel"><h2>{escape(title)}</h2>{"".join(rows)}</section>'


def ga4_snapshot():
    return read_json("data/analytics/ga4-snapshot.json", {})


def gsc_snapshot():
    return read_json("data/analytics/gsc-snapshot.json", {})


def update_status():
    return read_json("data/analytics/update-status.json", {})


def analytics_env() -> dict[str, str]:
    setup = read_json("data/analytics/setup-status.json", {})
    env = os.environ.copy()
    property_id = str(setup.get("ga4", {}).get("property_id", "538957338")).strip()
    site_url = str(setup.get("gsc", {}).get("site_url", "sc-domain:thelumenary.org")).strip()
    if property_id:
        env.setdefault("GA4_PROPERTY_ID", property_id)
    if site_url:
        env.setdefault("GSC_SITE_URL", site_url)
    return env


def run_analytics_update() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    steps = [
        {
            "id": "ga4",
            "label": "GA4",
            "command": ["python3", "scripts/analytics/ga4_report.py"],
        },
        {
            "id": "gsc",
            "label": "Search Console",
            "command": ["python3", "scripts/analytics/gsc_report.py"],
        },
        {
            "id": "aeo",
            "label": "AEO readiness",
            "command": ["python3", "scripts/analytics/aeo_readiness.py"],
        },
    ]
    status = {
        "status": "running",
        "started_at": started,
        "finished_at": None,
        "duration_seconds": None,
        "steps": {},
    }
    write_json(UPDATE_STATUS_PATH, status)

    start_time = time.monotonic()
    env = analytics_env()
    for step in steps:
        step_started = datetime.now(timezone.utc).isoformat()
        status["steps"][step["id"]] = {
            "label": step["label"],
            "status": "running",
            "started_at": step_started,
        }
        write_json(UPDATE_STATUS_PATH, status)
        try:
            result = subprocess.run(
                step["command"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                timeout=240,
                check=False,
            )
            status["steps"][step["id"]].update(
                {
                    "status": "complete" if result.returncode == 0 else "error",
                    "returncode": result.returncode,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                }
            )
        except subprocess.TimeoutExpired as exc:
            status["steps"][step["id"]].update(
                {
                    "status": "error",
                    "returncode": None,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                    "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                    "stderr": "Timed out after 240 seconds.",
                }
            )
        write_json(UPDATE_STATUS_PATH, status)

    failed = [step for step in status["steps"].values() if step.get("status") != "complete"]
    status["status"] = "error" if failed else "complete"
    status["finished_at"] = datetime.now(timezone.utc).isoformat()
    status["duration_seconds"] = round(time.monotonic() - start_time, 2)
    write_json(UPDATE_STATUS_PATH, status)
    return status


def ga4_event_count(snapshot: dict, event_name: str) -> float:
    for row in snapshot.get("events", {}).get("rows", []):
        if row.get("eventName") == event_name:
            return num(row.get("eventCount"))
    return 0.0


SEARCH_SOURCES = {
    "google",
    "bing",
    "duckduckgo",
    "yahoo",
    "search.yahoo.com",
    "baidu",
    "yandex",
}

AEO_SOURCES = {
    "perplexity",
    "perplexity.ai",
    "chatgpt.com",
    "chat.openai.com",
    "gemini.google.com",
    "bard.google.com",
    "claude.ai",
    "anthropic.com",
    "copilot.microsoft.com",
    "you.com",
    "phind.com",
}


def format_date(value: str) -> str:
    if len(value) == 8 and value.isdigit():
        return f"{value[4:6]}/{value[6:8]}"
    return value or "-"


def fmt_duration(seconds) -> str:
    seconds = int(round(num(seconds)))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remainder = seconds % 60
    return f"{minutes}m {remainder:02d}s"


def pages_per_session(views: float, sessions: float) -> str:
    if not sessions:
        return "0.00"
    return f"{views / sessions:.2f}"


def status_class(value: str) -> str:
    lowered = str(value or "").lower()
    if lowered in {"ready", "wired", "complete", "verified", "configured", "local_report_pull_verified"}:
        return "good"
    if lowered in {"issue", "error", "failed"}:
        return "bad"
    return "neutral"


def normalized_source(source: str) -> str:
    return str(source or "").lower().replace("www.", "")


def is_aeo_source(source: str) -> bool:
    normalized = normalized_source(source)
    return normalized in AEO_SOURCES or any(normalized.endswith(f".{engine}") for engine in AEO_SOURCES)


def is_seo_source(source: str, medium: str) -> bool:
    normalized = normalized_source(source)
    return str(medium or "").lower() == "organic" or normalized in SEARCH_SOURCES or normalized.startswith("search.")


def source_label(source: str, medium: str) -> str:
    if source == "(direct)" and medium == "(none)":
        return "Direct"
    if source == "(not set)" and medium == "(not set)":
        return "Unknown"
    if medium == "organic":
        return f"{source.title()} Organic"
    if medium == "referral":
        return source
    return f"{source} / {medium}"


def source_group(row: dict) -> str:
    source = row.get("sessionSource", "")
    medium = row.get("sessionMedium", "")
    if is_aeo_source(source):
        return "AEO"
    if is_seo_source(source, medium):
        return "SEO"
    if source == "(direct)" and medium == "(none)":
        return "Direct / unknown"
    if source == "(not set)" and medium == "(not set)":
        return "Direct / unknown"
    if str(medium).lower() == "referral":
        return "Referral"
    channel = row.get("sessionDefaultChannelGroup", "")
    return channel if channel and channel != "Unassigned" else "Other"


def group_acquisition_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in rows:
        label = source_group(row)
        item = grouped.setdefault(label, {"label": label, "sessions": 0.0, "users": 0.0, "views": 0.0})
        item["sessions"] += num(row.get("sessions"))
        item["users"] += num(row.get("totalUsers"))
        item["views"] += num(row.get("screenPageViews"))
    return sorted(grouped.values(), key=lambda item: item["sessions"], reverse=True)


def card(label: str, value: str, subtitle: str = "", tone: str = "") -> str:
    return (
        f'<article class="score-card {escape(tone)}">'
        f'<p class="score-label">{escape(label)}</p>'
        f'<p class="score-value">{escape(str(value))}</p>'
        f'<p class="score-subtitle">{escape(subtitle)}</p>'
        "</article>"
    )


def panel(title: str, body: str, subtitle: str = "") -> str:
    subtitle_html = f'<span class="panel-subtitle">{escape(subtitle)}</span>' if subtitle else ""
    return (
        '<section class="panel">'
        f'<div class="panel-heading"><h2>{escape(title)}</h2>{subtitle_html}</div>'
        f"{body}</section>"
    )


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="badge {escape(tone)}">{escape(text)}</span>'


def table(headers: list[str], rows: list[list[str]], empty_message: str) -> str:
    if not rows:
        return f'<p class="empty-state">{escape(empty_message)}</p>'
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body += f"<tr>{cells}</tr>"
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def bars(rows: list[tuple[str, float, str]], empty_message: str) -> str:
    if not rows:
        return f'<p class="empty-state">{escape(empty_message)}</p>'
    maximum = max(value for _, value, _ in rows) or 1
    output = '<div class="bar-list">'
    for label, value, detail in rows:
        width = max(2, min(100, (value / maximum) * 100))
        output += (
            '<div class="bar-row">'
            '<div class="bar-copy">'
            f'<strong>{escape(label)}</strong>'
            f'<span>{escape(detail)}</span>'
            "</div>"
            '<div class="bar-track">'
            f'<span style="width: {width:.1f}%"></span>'
            "</div>"
            "</div>"
        )
    output += "</div>"
    return output


def traffic_chart(rows: list[dict]) -> str:
    if not rows:
        return '<p class="empty-state">GA4 has not returned daily traffic rows yet.</p>'
    sorted_rows = sorted(rows, key=lambda row: row.get("date", ""))
    values = [num(row.get("sessions")) for row in sorted_rows]
    users = [num(row.get("totalUsers")) for row in sorted_rows]
    maximum = max(values + users + [1])
    width = 720
    height = 210
    left = 38
    right = 18
    top = 18
    bottom = 34
    plot_width = width - left - right
    plot_height = height - top - bottom

    def points(series: list[float]) -> str:
        if len(series) == 1:
            x = left + plot_width / 2
            y = top + plot_height - (series[0] / maximum) * plot_height
            return f"{x:.1f},{y:.1f}"
        output = []
        for index, value in enumerate(series):
            x = left + (index / (len(series) - 1)) * plot_width
            y = top + plot_height - (value / maximum) * plot_height
            output.append(f"{x:.1f},{y:.1f}")
        return " ".join(output)

    labels = ""
    for index, row in enumerate(sorted_rows):
        if index not in {0, len(sorted_rows) - 1} and len(sorted_rows) > 5:
            continue
        x = left + (index / max(1, len(sorted_rows) - 1)) * plot_width
        labels += f'<text x="{x:.1f}" y="{height - 10}" text-anchor="middle">{escape(format_date(row.get("date", "")))}</text>'

    return f"""
      <div class="chart-shell">
        <svg class="traffic-chart" viewBox="0 0 {width} {height}" role="img" aria-label="Daily sessions and users">
          <line x1="{left}" y1="{top + plot_height}" x2="{width - right}" y2="{top + plot_height}" />
          <line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" />
          <polyline class="line sessions" points="{points(values)}" />
          <polyline class="line users" points="{points(users)}" />
          {labels}
        </svg>
        <div class="legend"><span class="legend-item sessions">Sessions</span><span class="legend-item users">Users</span></div>
      </div>
    """


def page_shell(title: str, active: str, body: str) -> bytes:
    tabs = [
        ("Overview", "/analytics/"),
        ("Acquisition", "/analytics/acquisition/"),
        ("AEO", "/analytics/aeo/"),
    ]
    tab_html = "".join(
        f'<a class="{"active" if label == active else ""}" href="{href}">{label}</a>'
        for label, href in tabs
    )
    status = update_status()
    status_value = status.get("status", "idle")
    status_class = "ok" if status_value == "complete" else "error" if status_value == "error" else "idle"
    finished_at = status.get("finished_at") or status.get("started_at")
    if finished_at:
        status_text = f"Last update: {finished_at}"
    else:
        status_text = "No local update has run yet."
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>{escape(title)} | Lumenary Local Analytics</title>
    <style>
      :root {{
        color-scheme: light;
        --bg: #f9fafb;
        --panel: #ffffff;
        --line: #e5e7eb;
        --line-soft: #f3f4f6;
        --text: #111827;
        --muted: #6b7280;
        --faint: #9ca3af;
        --soft: #f8fafc;
        --accent: #0891b2;
        --accent-strong: #0e7490;
        --indigo: #6366f1;
        --violet: #8b5cf6;
        --danger: #b91c1c;
        --success: #16a34a;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.5;
      }}
      header {{
        background: var(--panel);
        border-bottom: 1px solid var(--line);
        padding: 0 24px;
      }}
      .header-inner {{
        align-items: center;
        display: flex;
        justify-content: space-between;
        gap: 24px;
        margin: 0 auto;
        max-width: 1280px;
        padding: 16px 0;
      }}
      main {{
        max-width: 1280px;
        width: calc(100% - 48px);
        margin: 0 auto;
        padding: 24px 0 64px;
      }}
      .kicker {{
        color: var(--faint);
        font-size: 0.75rem;
        margin: 2px 0 0;
      }}
      h1 {{
        color: var(--text);
        font-size: 1.25rem;
        font-weight: 800;
        line-height: 1.15;
        margin: 0;
      }}
      .lead {{
        color: var(--faint);
        font-size: 0.75rem;
        margin: 2px 0 0;
      }}
      .header-actions {{
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: flex-end;
      }}
      .range-chip {{
        align-items: center;
        background: #f1f5f9;
        border: 1px solid var(--line);
        border-radius: 999px;
        color: #475569;
        display: inline-flex;
        font-size: 0.75rem;
        font-weight: 700;
        gap: 6px;
        padding: 8px 12px;
      }}
      .update-button {{
        appearance: none;
        background: var(--accent);
        border: 1px solid var(--accent);
        border-radius: 8px;
        color: #ffffff;
        cursor: pointer;
        font: inherit;
        font-size: 0.88rem;
        font-weight: 700;
        padding: 8px 14px;
      }}
      .update-button:hover {{ background: var(--accent-strong); }}
      .update-button[disabled] {{
        background: #e2e8f0;
        border-color: #e2e8f0;
        color: #94a3b8;
        cursor: wait;
      }}
      .update-status {{
        border: 1px solid var(--line);
        border-radius: 8px;
        color: var(--muted);
        font-size: 0.75rem;
        max-width: 360px;
        padding: 8px 10px;
      }}
      .update-status.ok {{
        background: #ecfdf5;
        border-color: #bbf7d0;
        color: var(--success);
      }}
      .update-status.error {{
        background: #fef2f2;
        border-color: #fecaca;
        color: var(--danger);
      }}
      nav {{
        display: flex;
        gap: 4px;
        margin: 0 0 20px;
        overflow-x: auto;
        border-bottom: 1px solid var(--line);
      }}
      nav a {{
        border-bottom: 2px solid transparent;
        color: var(--muted);
        font-size: 0.88rem;
        font-weight: 700;
        padding: 10px 16px;
        text-decoration: none;
        white-space: nowrap;
        transition: color 0.16s ease, border-color 0.16s ease;
      }}
      nav a:hover {{ color: var(--text); }}
      nav a.active {{
        border-color: var(--accent);
        color: var(--accent);
      }}
      .stack {{
        display: flex;
        flex-direction: column;
        gap: 20px;
      }}
      .score-grid {{
        display: grid;
        gap: 12px;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      }}
      .panel {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 20px;
      }}
      .panel-heading {{
        align-items: baseline;
        display: flex;
        gap: 8px;
        margin: 0 0 14px;
      }}
      h2 {{
        color: var(--text);
        font-size: 1.08rem;
        font-weight: 800;
        line-height: 1.2;
        margin: 0;
      }}
      .panel-subtitle {{
        color: var(--faint);
        font-size: 0.75rem;
      }}
      .score-card {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 16px;
        position: relative;
      }}
      .score-label {{
        color: var(--muted);
        font-size: 0.86rem;
        font-weight: 700;
        margin: 0;
      }}
      .score-value {{
        color: var(--text);
        font-size: clamp(1.5rem, 3vw, 2rem);
        font-weight: 850;
        line-height: 1;
        margin: 8px 0 0;
      }}
      .score-subtitle {{
        color: var(--faint);
        font-size: 0.82rem;
        margin: 6px 0 0;
      }}
      .two-col {{
        display: grid;
        gap: 20px;
        grid-template-columns: minmax(0, 1fr) minmax(320px, 0.55fr);
      }}
      .empty-state {{
        color: var(--faint);
        font-size: 0.9rem;
        margin: 0;
      }}
      .table-wrap {{
        overflow-x: auto;
      }}
      table {{
        border-collapse: collapse;
        font-size: 0.88rem;
        width: 100%;
      }}
      th {{
        border-bottom: 1px solid var(--line);
        color: var(--faint);
        font-size: 0.75rem;
        font-weight: 800;
        padding: 0 0 8px;
        text-align: left;
      }}
      td {{
        border-bottom: 1px solid var(--line-soft);
        color: #4b5563;
        padding: 8px 0;
        vertical-align: top;
      }}
      th:not(:first-child), td:not(:first-child) {{
        padding-left: 14px;
        text-align: right;
      }}
      code {{
        color: var(--accent-strong);
        overflow-wrap: anywhere;
      }}
      a {{ color: var(--accent-strong); }}
      .badge {{
        border: 1px solid var(--line);
        border-radius: 999px;
        color: #64748b;
        display: inline-flex;
        font-size: 0.72rem;
        font-weight: 800;
        padding: 3px 8px;
        white-space: nowrap;
      }}
      .badge.good {{
        background: #ecfdf5;
        border-color: #bbf7d0;
        color: #15803d;
      }}
      .badge.bad {{
        background: #fef2f2;
        border-color: #fecaca;
        color: #b91c1c;
      }}
      .badge.neutral {{
        background: #f8fafc;
      }}
      .bar-list {{
        display: grid;
        gap: 12px;
      }}
      .bar-row {{
        display: grid;
        gap: 8px;
      }}
      .bar-copy {{
        align-items: baseline;
        display: flex;
        gap: 10px;
        justify-content: space-between;
      }}
      .bar-copy strong {{
        color: #374151;
        font-size: 0.9rem;
      }}
      .bar-copy span {{
        color: var(--faint);
        font-size: 0.78rem;
      }}
      .bar-track {{
        background: #f1f5f9;
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
      }}
      .bar-track span {{
        background: linear-gradient(90deg, var(--indigo), var(--violet));
        border-radius: inherit;
        display: block;
        height: 100%;
      }}
      .chart-shell {{
        width: 100%;
      }}
      .traffic-chart {{
        display: block;
        height: auto;
        width: 100%;
      }}
      .traffic-chart line {{
        stroke: #e5e7eb;
        stroke-width: 1;
      }}
      .traffic-chart text {{
        fill: var(--faint);
        font-size: 12px;
      }}
      .traffic-chart .line {{
        fill: none;
        stroke-linecap: round;
        stroke-linejoin: round;
        stroke-width: 3;
      }}
      .traffic-chart .sessions {{ stroke: var(--indigo); }}
      .traffic-chart .users {{ stroke: #10b981; }}
      .legend {{
        display: flex;
        gap: 14px;
        margin-top: 4px;
      }}
      .legend-item {{
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 700;
      }}
      .legend-item::before {{
        border-radius: 999px;
        content: "";
        display: inline-block;
        height: 8px;
        margin-right: 6px;
        width: 8px;
      }}
      .legend-item.sessions::before {{ background: var(--indigo); }}
      .legend-item.users::before {{ background: #10b981; }}
      .setup-list {{
        display: grid;
        gap: 10px;
      }}
      .setup-row {{
        align-items: start;
        border-bottom: 1px solid var(--line-soft);
        display: grid;
        gap: 10px;
        grid-template-columns: minmax(120px, 0.5fr) auto minmax(260px, 1.5fr);
        padding: 10px 0;
      }}
      .setup-row:last-child {{ border-bottom: 0; }}
      .setup-row strong {{
        color: #374151;
        font-size: 0.88rem;
      }}
      .setup-row p {{
        color: var(--muted);
        font-size: 0.84rem;
        margin: 0;
      }}
      @media (max-width: 760px) {{
        .header-inner {{
          align-items: flex-start;
          flex-direction: column;
        }}
        .header-actions {{ justify-content: flex-start; }}
        main {{ width: calc(100% - 32px); }}
        .two-col {{ grid-template-columns: 1fr; }}
        .setup-row {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <header>
      <div class="header-inner">
        <div>
          <h1>Lumenary Marketing Dashboard</h1>
          <p class="lead">Local GA4, Search Console, acquisition, and AEO reporting for thelumenary.org.</p>
          <p class="kicker">Localhost only</p>
        </div>
        <div class="header-actions">
          <span class="range-chip">28 days</span>
          <button class="update-button" data-update type="button">Collect Data</button>
          <span class="update-status {status_class}" data-update-status>{escape(status_text)}</span>
        </div>
      </div>
    </header>
    <main>
      <nav aria-label="Analytics navigation">{tab_html}</nav>
      {body}
    </main>
    <script>
      const updateButton = document.querySelector('[data-update]');
      const updateStatus = document.querySelector('[data-update-status]');
      updateButton?.addEventListener('click', async () => {{
        updateButton.disabled = true;
        updateButton.textContent = 'Updating...';
        updateStatus.textContent = 'Pulling GA4, Search Console, and AEO readiness data.';
        updateStatus.className = 'update-status idle';
        try {{
          const response = await fetch('/analytics/update', {{ method: 'POST' }});
          const data = await response.json();
          if (!response.ok || data.status === 'error') {{
            const failed = Object.values(data.steps || {{}})
              .filter(step => step.status !== 'complete')
              .map(step => step.label || 'step')
              .join(', ');
            throw new Error(failed ? `Update issue: ${{failed}}` : 'Update failed.');
          }}
          updateStatus.className = 'update-status ok';
          updateStatus.textContent = `Updated in ${{data.duration_seconds || 0}} seconds. Reloading.`;
          window.setTimeout(() => window.location.reload(), 700);
        }} catch (error) {{
          updateStatus.className = 'update-status error';
          updateStatus.textContent = error.message || 'Update failed.';
          updateButton.disabled = false;
          updateButton.textContent = 'Update';
        }}
      }});
    </script>
  </body>
</html>"""
    return html.encode("utf-8")


def overview_page():
    setup = read_json("data/analytics/setup-status.json", {})
    readiness = read_json("data/analytics/aeo-readiness.json", {"checks": []})
    queries = read_json("data/analytics/aeo-queries.json", [])
    ga4 = ga4_snapshot()
    gsc = gsc_snapshot()
    overview = ga4.get("overview", {})
    ideas = read_jsonl("hypotheses/ideas.jsonl")
    sources = read_jsonl("sources/sources_index.jsonl")
    gsc_rows = gsc.get("rows", [])
    sessions = metric_sum(overview, "sessions")
    users = metric_sum(overview, "totalUsers")
    views = metric_sum(overview, "screenPageViews")
    engagement = weighted_average(overview, "engagementRate", "sessions")
    avg_duration = weighted_average(overview, "averageSessionDuration", "sessions")
    search_clicks = sum(num(row.get("clicks")) for row in gsc_rows)
    search_impressions = sum(num(row.get("impressions")) for row in gsc_rows)
    body = '<div class="stack">'
    body += '<section class="score-grid">'
    body += card("Avg. time on site", fmt_duration(avg_duration), snapshot_meta(ga4, "GA4 snapshot has not been pulled yet."))
    body += card("Engagement rate", pct(engagement), "Weighted GA4 engagement.")
    body += card("Avg. pages / session", pages_per_session(views, sessions), f"{whole(views)} views from {whole(sessions)} sessions.")
    body += card("AI-engine sessions", whole(ga4_event_count(ga4, "aeo_referral_landing")), "Tracked answer-engine referral landings.")
    body += card("Search impressions", whole(search_impressions), f"{whole(search_clicks)} clicks from Search Console.")
    body += "</section>"

    body += '<div class="two-col">'
    body += panel("28-Day Traffic", traffic_chart(overview.get("rows", [])), "Sessions and users")
    landing_rows = []
    for row in ga4.get("landing_pages", {}).get("rows", [])[:10]:
        landing_rows.append(
            [
                f"<code>{escape(row.get('landingPage', '(not set)'))}</code>",
                whole(row.get("sessions")),
                whole(row.get("totalUsers")),
                whole(row.get("screenPageViews")),
            ]
        )
    body += panel(
        "Top Landing Pages",
        table(["Page", "Sessions", "Users", "Views"], landing_rows, "No GA4 landing page rows are available yet."),
        "GA4",
    )
    body += "</div>"

    if not overview.get("rows") and ga4.get("collected_at"):
        body += panel(
            "GA4 Data",
            "GA4 is connected and the report pull works, but the latest 28-day report has no traffic rows yet. Visit the site, wait for GA4 processing, then run npm run analytics:ga4.",
        )
    if not gsc_rows and gsc.get("collected_at"):
        body += panel(
            "Search Console Data",
            "Search Console is verified and the sitemap is submitted, but Google has not returned query data yet. This is normal immediately after verification.",
        )

    body += '<section class="score-grid">'
    body += card("Sessions", whole(sessions), "Total GA4 sessions.")
    body += card("Users", whole(users), "Total GA4 users.")
    body += card("Page views", whole(views), "Screen/page views.")
    body += card("GSC rows", whole(len(gsc_rows)), "Query/page rows returned.")
    body += card("Promoted claims", str(public_claim_count(ideas)), "Findings passing the public-claim gate.")
    body += card("Idea records", str(len(ideas)), "Structured observations in the corpus.")
    body += card("Source cards", str(len(sources)), "Grounding sources available to the loop.")
    body += card("AEO queries", str(len(queries)), "Starter citation questions.")
    body += "</section>"

    setup_rows = ""
    setup_items = [
        ("GA4", setup.get("ga4", {}).get("reporting_status", setup.get("ga4", {}).get("status", "waiting")), setup.get("ga4", {}).get("notes", "")),
        ("Search Console", setup.get("gsc", {}).get("reporting_status", setup.get("gsc", {}).get("status", "waiting")), setup.get("gsc", {}).get("notes", "")),
        ("AEO", setup.get("aeo", {}).get("status", "ready"), "Referral events, llms.txt, schema, sitemap, and query inventory are wired."),
        ("Sitemap", "ready", setup.get("gsc", {}).get("sitemap", "https://thelumenary.org/sitemap-index.xml")),
    ]
    for label, value, detail in setup_items:
        setup_rows += (
            '<div class="setup-row">'
            f"<strong>{escape(label)}</strong>"
            f"{badge(status_label(value), status_class(value))}"
            f"<p>{escape(detail)}</p>"
            "</div>"
        )
    body += panel("Analytics Setup", f'<div class="setup-list">{setup_rows}</div>')

    check_rows = ""
    for check in readiness.get("checks", []):
        check_rows += (
            '<div class="setup-row">'
            f"<strong>{escape(check.get('label', ''))}</strong>"
            f"{badge(check.get('status', ''), status_class(check.get('status', '')))}"
            f"<p>{escape(check.get('notes', ''))}<br><code>{escape(check.get('path', ''))}</code></p>"
            "</div>"
        )
    body += panel("AEO Setup Checks", f'<div class="setup-list">{check_rows}</div>')
    body += "</div>"
    return page_shell("Marketing Analytics", "Overview", body)


def acquisition_page():
    channels = read_json("data/analytics/acquisition-channels.json", [])
    ga4 = ga4_snapshot()
    gsc = gsc_snapshot()
    acquisition = ga4.get("acquisition", {}).get("rows", [])
    grouped = group_acquisition_rows(acquisition)
    total_sessions = sum(row["sessions"] for row in grouped)
    source_cards = '<section class="score-grid">'
    for row in grouped[:5]:
        share = (row["sessions"] / total_sessions) if total_sessions else 0
        source_cards += card(row["label"], whole(row["sessions"]), f"{pct(share)} of sessions, {whole(row['users'])} users")
    if not grouped:
        source_cards += card("No sources yet", "0", "Run Collect Data after traffic appears.")
    source_cards += "</section>"

    source_bars = bars(
        [(row["label"], row["sessions"], f"{whole(row['sessions'])} sessions, {whole(row['views'])} views") for row in grouped],
        "No GA4 acquisition rows are available yet.",
    )

    acquisition_rows = []
    for row in acquisition[:20]:
        source = source_label(row.get("sessionSource", "(none)"), row.get("sessionMedium", "(none)"))
        acquisition_rows.append(
            [
                escape(source_group(row)),
                escape(source),
                whole(row.get("sessions")),
                whole(row.get("totalUsers")),
                whole(row.get("screenPageViews")),
            ]
        )
    landing_rows = []
    for row in ga4.get("landing_pages", {}).get("rows", [])[:20]:
        landing_rows.append(
            [
                f"<code>{escape(row.get('landingPage', '(not set)'))}</code>",
                whole(row.get("sessions")),
                whole(row.get("totalUsers")),
                whole(row.get("engagedSessions")),
                whole(row.get("screenPageViews")),
            ]
        )
    gsc_rows = []
    for row in gsc.get("rows", [])[:20]:
        query = row.get("query") or "(query unavailable)"
        gsc_rows.append(
            [
                escape(query),
                whole(row.get("clicks")),
                whole(row.get("impressions")),
                pct(row.get("ctr")),
                f"{num(row.get('position')):.1f}",
                f"<code>{escape(row.get('page', ''))}</code>",
            ]
        )
    body = '<div class="stack">'
    body += source_cards
    body += panel("Traffic Sources", source_bars, snapshot_meta(ga4, "GA4 snapshot has not been pulled yet."))
    body += panel(
        "GA4 Source Detail",
        table(
            ["Channel", "Source / medium", "Sessions", "Users", "Views"],
            acquisition_rows,
            "GA4 reporting is connected, but no acquisition rows are available yet. Run Collect Data again after traffic appears.",
        ),
    )
    body += panel(
        "Landing Pages",
        table(
            ["Page", "Sessions", "Users", "Engaged", "Views"],
            landing_rows,
            "No GA4 landing-page rows are available yet.",
        ),
    )
    body += panel(
        "Search Console Queries",
        table(
            ["Query", "Clicks", "Impr", "CTR", "Pos", "Page"],
            gsc_rows,
            "Search Console reporting is connected, but no query rows are available yet. This is normal while Google begins crawling.",
        ),
        snapshot_meta(gsc, "GSC snapshot has not been pulled yet."),
    )
    source_rules = ""
    for channel in channels:
        source_rules += (
            '<div class="setup-row">'
            f"<strong>{escape(channel.get('channel', ''))}</strong>"
            f"<p>{escape(channel.get('source_rule', ''))}</p>"
            f"<p>{escape(channel.get('what_to_watch', ''))}<br><code>{escape(channel.get('first_action', ''))}</code></p>"
            "</div>"
        )
    body += panel("Source Rules", f'<div class="setup-list">{source_rules}</div>')
    body += "</div>"
    return page_shell("Acquisition", "Acquisition", body)


def aeo_page():
    setup = read_json("data/analytics/setup-status.json", {})
    readiness = read_json("data/analytics/aeo-readiness.json", {"checks": []})
    queries = read_json("data/analytics/aeo-queries.json", [])
    ga4 = ga4_snapshot()
    gsc = gsc_snapshot()
    engines = setup.get("aeo", {}).get("engines", [])
    aeo_referrals = ga4_event_count(ga4, "aeo_referral_landing")
    aeo_event_rows = []
    for row in ga4.get("events", {}).get("rows", []):
        event = row.get("eventName", "")
        if "aeo" in event or "referral" in event:
            aeo_event_rows.append(
                [
                    escape(event),
                    whole(row.get("eventCount")),
                    whole(row.get("totalUsers")),
                ]
            )
    body = '<div class="stack">'
    body += '<section class="score-grid">'
    body += card("Tracked engines", str(len(engines)), ", ".join(engines))
    body += card("Query inventory", str(len(queries)), "Questions mapped to expected pages.")
    body += card("Readiness checks", str(len(readiness.get("checks", []))), "Surfaces answer engines can parse.")
    body += card("AEO referrals", whole(aeo_referrals), snapshot_meta(ga4, "GA4 snapshot has not been pulled yet."))
    body += card("GSC query rows", whole(len(gsc.get("rows", []))), snapshot_meta(gsc, "GSC snapshot has not been pulled yet."))
    body += "</section>"

    body += panel(
        "AEO Events",
        table(
            ["Event", "Events", "Users"],
            aeo_event_rows,
            "No answer-engine referral events have been captured yet. The event is wired; it will appear after a visit arrives from a tracked answer engine.",
        ),
    )

    check_rows = ""
    for check in readiness.get("checks", []):
        check_rows += (
            '<div class="setup-row">'
            f"<strong>{escape(check.get('label', ''))}</strong>"
            f"{badge(check.get('status', ''), status_class(check.get('status', '')))}"
            f"<p>{escape(check.get('notes', ''))}<br><code>{escape(check.get('path', ''))}</code></p>"
            "</div>"
        )
    body += panel("Readiness Checks", f'<div class="setup-list">{check_rows}</div>', readiness.get("updated_at", ""))

    query_rows = []
    for query in queries:
        query_rows.append(
            [
                escape(query.get("query", "")),
                escape(query.get("intent", "")),
                escape(query.get("topic", "")),
                f"<code>{escape(query.get('expected_path', ''))}</code>",
            ]
        )
    body += panel(
        "Starter Questions",
        table(["Query", "Intent", "Topic", "Expected Page"], query_rows, "No AEO starter questions are defined yet."),
    )
    body += "</div>"
    return page_shell("AEO", "AEO", body)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: dict, status: int = 200, include_body: bool = True):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def send_dashboard(self, include_body=True):
        path = urlparse(self.path).path.rstrip("/") + "/"
        if path == "/analytics/":
            payload = overview_page()
        elif path == "/analytics/acquisition/":
            payload = acquisition_page()
        elif path == "/analytics/aeo/":
            payload = aeo_page()
        else:
            payload = b"Not found"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if include_body:
                self.wfile.write(payload)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def do_HEAD(self):
        self.send_dashboard(include_body=False)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") + "/"
        if path == "/analytics/update/status/":
            self.send_json(update_status())
        else:
            self.send_dashboard()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") + "/"
        if path == "/analytics/update/":
            payload = run_analytics_update()
            self.send_json(payload, status=200 if payload.get("status") == "complete" else 500)
            return
        self.send_json({"error": "Not found"}, status=404)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Local analytics dashboard: http://127.0.0.1:{PORT}/analytics/")
    print("Press Ctrl-C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
