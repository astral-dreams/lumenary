#!/usr/bin/env python3
"""Local-only analytics dashboard for The Lumenary.

This intentionally does not live under src/pages or public. Run it on the
local machine when you want the private marketing dashboard.
"""

from __future__ import annotations

import json
import os
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
PORT = int(os.environ.get("LUMENARY_ANALYTICS_PORT", "8789"))


def read_json(relative_path: str, fallback):
    path = ROOT / relative_path
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


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
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>{escape(title)} | Lumenary Local Analytics</title>
    <style>
      :root {{
        color-scheme: dark;
        --bg: #101512;
        --panel: #17201b;
        --line: #35483c;
        --text: #f1efe7;
        --muted: #b4c1b8;
        --accent: #d9bd76;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        line-height: 1.5;
      }}
      main {{
        width: min(1120px, calc(100% - 32px));
        margin: 0 auto;
        padding: 42px 0 64px;
      }}
      .kicker {{
        color: var(--accent);
        font-size: 0.76rem;
        letter-spacing: 0.08em;
        margin: 0 0 10px;
        text-transform: uppercase;
      }}
      h1 {{
        font-family: Georgia, "Times New Roman", serif;
        font-size: clamp(2.4rem, 8vw, 5.5rem);
        line-height: 0.94;
        margin: 0;
      }}
      .lead {{
        color: var(--muted);
        font-size: 1.1rem;
        max-width: 720px;
        margin: 18px 0 24px;
      }}
      nav {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 0 0 34px;
      }}
      nav a {{
        border: 1px solid var(--line);
        color: var(--text);
        padding: 9px 12px;
        text-decoration: none;
      }}
      nav a.active {{
        background: var(--accent);
        border-color: var(--accent);
        color: #17130a;
      }}
      .grid {{
        display: grid;
        gap: 14px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin: 0 0 18px;
      }}
      .card, .panel {{
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 18px;
      }}
      .card span, .row span {{
        color: var(--muted);
        display: block;
        font-size: 0.86rem;
      }}
      .card strong {{
        display: block;
        font-size: 2.1rem;
        line-height: 1;
        margin: 8px 0;
      }}
      .card p, .row p {{
        color: var(--muted);
        margin: 0;
      }}
      h2 {{
        font-size: 1.35rem;
        margin: 0 0 14px;
      }}
      .row {{
        border-top: 1px solid var(--line);
        display: grid;
        gap: 8px;
        grid-template-columns: minmax(160px, 0.7fr) minmax(180px, 1fr) minmax(260px, 1.4fr);
        padding: 14px 0;
      }}
      .row:first-of-type {{ border-top: 0; }}
      code {{
        color: #f5dfa5;
        overflow-wrap: anywhere;
      }}
      a {{ color: #f5dfa5; }}
      @media (max-width: 760px) {{
        .row {{ grid-template-columns: 1fr; }}
      }}
    </style>
  </head>
  <body>
    <main>
      <p class="kicker">Localhost only</p>
      <h1>{escape(title)}</h1>
      <p class="lead">Private analytics control room for setup status, acquisition rules, and answer-engine visibility. This dashboard is not part of the public Cloudflare Pages build.</p>
      <nav aria-label="Analytics navigation">{tab_html}</nav>
      {body}
    </main>
  </body>
</html>"""
    return html.encode("utf-8")


def overview_page():
    setup = read_json("data/analytics/setup-status.json", {})
    readiness = read_json("data/analytics/aeo-readiness.json", {"checks": []})
    queries = read_json("data/analytics/aeo-queries.json", [])
    ideas = read_jsonl("hypotheses/ideas.jsonl")
    sources = read_jsonl("sources/sources_index.jsonl")
    cards = [
        ("GA4", status_label(setup.get("ga4", {}).get("status", "waiting")), setup.get("ga4", {}).get("notes", "")),
        ("Search Console", status_label(setup.get("gsc", {}).get("status", "waiting")), setup.get("gsc", {}).get("notes", "")),
        ("AEO", status_label(setup.get("aeo", {}).get("status", "ready")), "Referral events, llms.txt, schema, sitemap, and query inventory are wired."),
        ("Sitemap", "Ready", setup.get("gsc", {}).get("sitemap", "https://thelumenary.org/sitemap-index.xml")),
        ("Idea Records", str(len(ideas)), "Structured observations in the research corpus."),
        ("Promoted Claims", str(public_claim_count(ideas)), "Findings that currently pass the public-claim gate."),
        ("Source Cards", str(len(sources)), "Grounding sources available to the loop."),
        ("AEO Queries", str(len(queries)), "Starter questions for citation checks."),
    ]
    body = '<section class="grid">'
    for label, value, detail in cards:
        body += f'<article class="card"><span>{escape(label)}</span><strong>{escape(value)}</strong><p>{escape(detail)}</p></article>'
    body += '</section><section class="panel"><h2>AEO Setup Checks</h2>'
    for check in readiness.get("checks", []):
        body += (
            '<div class="row">'
            f"<strong>{escape(check.get('label', ''))}</strong>"
            f"<span>{escape(check.get('status', ''))}</span>"
            f"<p>{escape(check.get('notes', ''))}<br><code>{escape(check.get('path', ''))}</code></p>"
            "</div>"
        )
    body += "</section>"
    return page_shell("Marketing Analytics", "Overview", body)


def acquisition_page():
    channels = read_json("data/analytics/acquisition-channels.json", [])
    body = '<section class="panel"><h2>Source Rules</h2>'
    for channel in channels:
        body += (
            '<div class="row">'
            f"<strong>{escape(channel.get('channel', ''))}</strong>"
            f"<span>{escape(channel.get('source_rule', ''))}</span>"
            f"<p>{escape(channel.get('what_to_watch', ''))}<br><code>{escape(channel.get('first_action', ''))}</code></p>"
            "</div>"
        )
    body += "</section>"
    body += (
        '<section class="panel" style="margin-top:18px"><h2>Next Metrics</h2>'
        '<div class="row"><strong>GA4</strong><span>Sessions, users, engagement, landing pages</span><p>Requires a GA4 property ID and Google credentials for local report pulls.</p></div>'
        '<div class="row"><strong>Search Console</strong><span>Queries, impressions, clicks, pages</span><p>Requires verified domain property and Google credentials for local report pulls.</p></div>'
        '<div class="row"><strong>AEO</strong><span>AI referrals and citation checks</span><p>Requires GA4 events plus manual or authenticated answer-engine visibility checks.</p></div>'
        "</section>"
    )
    return page_shell("Acquisition", "Acquisition", body)


def aeo_page():
    setup = read_json("data/analytics/setup-status.json", {})
    readiness = read_json("data/analytics/aeo-readiness.json", {"checks": []})
    queries = read_json("data/analytics/aeo-queries.json", [])
    engines = setup.get("aeo", {}).get("engines", [])
    body = '<section class="grid">'
    body += f'<article class="card"><span>Tracked Engines</span><strong>{len(engines)}</strong><p>{escape(", ".join(engines))}</p></article>'
    body += f'<article class="card"><span>Query Inventory</span><strong>{len(queries)}</strong><p>Questions mapped to expected Lumenary pages.</p></article>'
    body += f'<article class="card"><span>Readiness Checks</span><strong>{len(readiness.get("checks", []))}</strong><p>Surfaces that help answer engines parse the site.</p></article>'
    body += '</section><section class="panel"><h2>Starter Questions</h2>'
    for query in queries:
        body += (
            '<div class="row">'
            f"<strong>{escape(query.get('query', ''))}</strong>"
            f"<span>{escape(query.get('intent', ''))} / {escape(query.get('topic', ''))}</span>"
            f"<p>Expected page:<br><code>{escape(query.get('expected_path', ''))}</code></p>"
            "</div>"
        )
    body += "</section>"
    return page_shell("AEO", "AEO", body)


class Handler(BaseHTTPRequestHandler):
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
        self.send_dashboard()

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Local analytics dashboard: http://127.0.0.1:{PORT}/analytics/")
    print("Press Ctrl-C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
