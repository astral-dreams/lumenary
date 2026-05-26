#!/usr/bin/env python3
"""Pull a small Google Search Console snapshot into data/analytics/."""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import google.auth
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "analytics"
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _credentials():
    creds, _ = google.auth.default(scopes=SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return creds


def _rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in response.get("rows", []):
        keys = row.get("keys", [])
        rows.append(
            {
                "query": keys[0] if len(keys) > 0 else "",
                "page": keys[1] if len(keys) > 1 else "",
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "ctr": row.get("ctr", 0),
                "position": row.get("position", 0),
            }
        )
    return rows


def main() -> None:
    site_url = os.environ.get("GSC_SITE_URL", "sc-domain:thelumenary.org").strip()
    end = date.today() - timedelta(days=2)
    start = end - timedelta(days=28)
    service = build("searchconsole", "v1", credentials=_credentials(), cache_discovery=False)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query", "page"],
        "rowLimit": 250,
      }
    response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "site_url": site_url,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "rows": _rows(response),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "gsc-snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print("wrote data/analytics/gsc-snapshot.json")


if __name__ == "__main__":
    main()

