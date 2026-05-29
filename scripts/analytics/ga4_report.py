#!/usr/bin/env python3
"""Pull a small GA4 snapshot into data/analytics/.

Required env:
  GA4_PROPERTY_ID

Auth:
  Uses Google Application Default Credentials. Run
  `gcloud auth application-default login` if local credentials are stale.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "analytics"


def _metric_value(row: Any, index: int) -> str:
    try:
        return row.metric_values[index].value
    except Exception:
        return "0"


def _dimension_value(row: Any, index: int) -> str:
    try:
        return row.dimension_values[index].value
    except Exception:
        return ""


def _run_report(
    client: BetaAnalyticsDataClient,
    property_id: str,
    dimensions: list[str],
    metrics: list[str],
    start_date: str,
    end_date: str,
):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=name) for name in dimensions],
        metrics=[Metric(name=name) for name in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=100,
      )
    response = client.run_report(request)
    rows = []
    for row in response.rows:
        item = {name: _dimension_value(row, index) for index, name in enumerate(dimensions)}
        item.update({name: _metric_value(row, index) for index, name in enumerate(metrics)})
        rows.append(item)
    return {
        "dimensions": dimensions,
        "metrics": metrics,
        "row_count": response.row_count,
        "rows": rows,
    }


def main() -> None:
    property_id = os.environ.get("GA4_PROPERTY_ID", "").strip()
    if not property_id:
        raise SystemExit("GA4_PROPERTY_ID is required.")

    client = BetaAnalyticsDataClient()
    start_date = "28daysAgo"
    end_date = "yesterday"
    snapshot = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "property_id": property_id,
        "start_date": start_date,
        "end_date": end_date,
        "overview": _run_report(
            client,
            property_id,
            ["date"],
            ["sessions", "totalUsers", "screenPageViews", "averageSessionDuration", "engagementRate"],
            start_date,
            end_date,
        ),
        "acquisition": _run_report(
            client,
            property_id,
            ["sessionDefaultChannelGroup", "sessionSource", "sessionMedium"],
            ["sessions", "totalUsers", "engagedSessions", "screenPageViews"],
            start_date,
            end_date,
        ),
        "landing_pages": _run_report(
            client,
            property_id,
            ["landingPage"],
            ["sessions", "totalUsers", "engagedSessions", "screenPageViews"],
            start_date,
            end_date,
        ),
        "first_visit_pages": _run_report(
            client,
            property_id,
            ["landingPage", "eventName"],
            ["eventCount", "totalUsers"],
            start_date,
            end_date,
        ),
        "events": _run_report(
            client,
            property_id,
            ["eventName"],
            ["eventCount", "totalUsers"],
            start_date,
            end_date,
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "ga4-snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print("wrote data/analytics/ga4-snapshot.json")


if __name__ == "__main__":
    main()
