#!/usr/bin/env python3
"""Refresh basic AEO readiness checks for the public site."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "analytics" / "aeo-readiness.json"
SITE = "https://thelumenary.org"


def check_path(path: str) -> str:
    try:
      request = Request(f"{SITE}{path}", headers={"user-agent": "LumenaryAEOReadiness/1.0"})
      with urlopen(request, timeout=15) as response:
          return "ready" if 200 <= response.status < 300 else "issue"
    except URLError:
      return "issue"


def main() -> None:
    checks = [
        {
            "label": "llms.txt",
            "status": check_path("/llms.txt"),
            "path": "/llms.txt",
            "notes": "Plain text summary for language models.",
        },
        {
            "label": "robots.txt",
            "status": check_path("/robots.txt"),
            "path": "/robots.txt",
            "notes": "Allows crawling and points to the sitemap.",
        },
        {
            "label": "sitemap",
            "status": check_path("/sitemap-index.xml"),
            "path": "/sitemap-index.xml",
            "notes": "Astro sitemap generated at build time.",
        },
        {
            "label": "structured data",
            "status": "ready",
            "path": "sitewide",
            "notes": "Home, Findings, Map, Method, Agent, and article pages emit schema.",
        },
        {
            "label": "answer-engine referrals",
            "status": "wired",
            "path": "GA4 event: aeo_referral_landing",
            "notes": "Triggered when the referrer is an answer engine such as ChatGPT, Perplexity, Gemini, Claude, Copilot, You.com, or Phind.",
        },
        {
            "label": "citation checks",
            "status": "inventory_ready",
            "path": "data/analytics/aeo-queries.json",
            "notes": "Starter questions and expected destination pages are defined.",
        },
    ]
    OUT.write_text(
        json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "checks": checks}, indent=2),
        encoding="utf-8",
    )
    print("wrote data/analytics/aeo-readiness.json")


if __name__ == "__main__":
    main()

