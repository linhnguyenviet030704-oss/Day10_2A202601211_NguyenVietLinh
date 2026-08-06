from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    total_rows = int(len(df))
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else total_rows
    checks = {
        "row_count_positive": {"passed": total_rows > 0, "value": total_rows},
        "paper_id_unique": {
            "passed": "paper_id" in df.columns
            and bool(df["paper_id"].notna().all())
            and bool((df["paper_id"].astype(str).str.strip() != "").all())
            and bool(df["paper_id"].is_unique),
            "value": int(df["paper_id"].nunique()) if "paper_id" in df.columns else 0,
        },
        "title_present": {
            "passed": "title" in df.columns and bool((df["title"].astype(str).str.strip() != "").all()),
            "value": int((df["title"].astype(str).str.strip() != "").sum()) if "title" in df.columns else 0,
        },
        "summary_present": {
            "passed": "summary" in df.columns and bool((df["summary"].astype(str).str.strip() != "").all()),
            "value": int((df["summary"].astype(str).str.strip() != "").sum()) if "summary" in df.columns else 0,
        },
        "summary_length_reasonable": {
            "passed": "summary" in df.columns and bool((df["summary"].astype(str).str.len() >= 40).all()),
            "value": float(df["summary"].astype(str).str.len().mean()) if "summary" in df.columns and total_rows else 0.0,
        },
    }
    payload = {
        "report_name": report_name,
        "total_rows": total_rows,
        "stale_rows": stale_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": total_rows > 0 and stale_rows == 0,
        "passed": all(check["passed"] for check in checks.values()),
        "checks": checks,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    total_rows = int(len(df))
    published = (
        df["published"].dropna().astype(str).sort_values(ascending=False).tolist()
        if "published" in df.columns
        else []
    )
    stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum()) if "age_days" in df.columns else total_rows
    payload = {
        "latest_published": published[0] if published else "",
        "oldest_published": published[-1] if published else "",
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": total_rows > 0 and stale_rows == 0,
    }
    write_json(report_path, payload)
    return payload
