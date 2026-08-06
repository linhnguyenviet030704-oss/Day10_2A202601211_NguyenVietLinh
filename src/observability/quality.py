from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json

MIN_SUMMARY_CHARS = 20
MIN_TITLE_CHARS = 15


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add_check(name: str, success: bool, details: str) -> None:
        checks.append({"name": name, "success": bool(success), "details": details})

    row_count = len(df)
    add_check("row_count_positive", row_count > 0, f"row_count={row_count}")

    if "paper_id" in df.columns and row_count:
        non_null_ids = df["paper_id"].notna() & (df["paper_id"].astype(str).str.strip() != "")
        add_check(
            "paper_id_not_null",
            bool(non_null_ids.all()),
            f"missing={int((~non_null_ids).sum())}/{row_count}",
        )
        unique_count = df["paper_id"].nunique(dropna=True)
        add_check(
            "paper_id_unique",
            unique_count == row_count,
            f"unique={unique_count}/{row_count}",
        )
    else:
        add_check("paper_id_not_null", False, "column missing or dataset empty")
        add_check("paper_id_unique", False, "column missing or dataset empty")

    if "title" in df.columns and row_count:
        non_null_titles = df["title"].notna() & (df["title"].astype(str).str.strip() != "")
        add_check(
            "title_not_null",
            bool(non_null_titles.all()),
            f"missing={int((~non_null_titles).sum())}/{row_count}",
        )
    else:
        add_check("title_not_null", False, "column missing or dataset empty")

    if "title" in df.columns and row_count:
        title_lengths = df["title"].astype(str).str.len()
        valid_title_length = title_lengths >= MIN_TITLE_CHARS
        add_check(
            "title_min_length",
            bool(valid_title_length.all()),
            f"threshold={MIN_TITLE_CHARS} chars, failing={int((~valid_title_length).sum())}/{row_count}",
        )
    else:
        add_check("title_min_length", False, "column missing or dataset empty")

    if "summary" in df.columns and row_count:
        summary_lengths = df["summary"].astype(str).str.len()
        valid_summary = summary_lengths >= MIN_SUMMARY_CHARS
        add_check(
            "summary_min_length",
            bool(valid_summary.all()),
            f"threshold={MIN_SUMMARY_CHARS} chars, failing={int((~valid_summary).sum())}/{row_count}",
        )
    else:
        add_check("summary_min_length", False, "column missing or dataset empty")

    if "age_days" in df.columns and row_count:
        stale_mask = df["age_days"] > settings.freshness_threshold_days
        stale_count = int(stale_mask.sum())
        add_check(
            "freshness_age_days",
            stale_count == 0,
            f"threshold_days={settings.freshness_threshold_days}, stale_rows={stale_count}/{row_count}",
        )
    else:
        add_check("freshness_age_days", False, "column missing or dataset empty")

    success = all(check["success"] for check in checks)
    report = {
        "report_name": report_name,
        "generated_at": now_utc().isoformat(),
        "row_count": row_count,
        "success": success,
        "checks": checks,
    }

    output_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(output_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    total_rows = len(df)

    if total_rows == 0 or "published" not in df.columns:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "total_rows": total_rows,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    published_dates = pd.to_datetime(df["published"], errors="coerce", utc=True)
    has_dates = published_dates.notna().any()

    if "age_days" in df.columns:
        stale_mask = df["age_days"] > settings.freshness_threshold_days
    else:
        stale_mask = pd.Series([False] * total_rows)
    stale_rows = int(stale_mask.sum())

    payload = {
        "latest_published": published_dates.max().strftime("%Y-%m-%d") if has_dates else None,
        "oldest_published": published_dates.min().strftime("%Y-%m-%d") if has_dates else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": stale_rows == 0,
    }
    write_json(report_path, payload)
    return payload
