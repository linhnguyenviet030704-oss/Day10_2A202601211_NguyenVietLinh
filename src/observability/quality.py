from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


# Minimum acceptable characters for a usable summary/abstract.
MIN_SUMMARY_CHARS = 40


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run a small battery of data quality checks over a cleaned dataframe.

    Produces a structured result (one entry per check) and persists it under
    ``data/quality/`` so the health of each dataset state (baseline, corrupted,
    repaired) can be compared later.
    """
    total_rows = int(len(df))
    threshold = settings.freshness_threshold_days
    checks: list[dict[str, Any]] = []

    def add(name: str, success: bool, detail: str, **extra: Any) -> None:
        checks.append({"name": name, "success": bool(success), "detail": detail, **extra})

    # 1. Row count.
    add(
        "row_count_positive",
        total_rows > 0,
        f"{total_rows} row(s) present.",
        total_rows=total_rows,
    )

    if total_rows == 0:
        result = {
            "report_name": report_name,
            "total_rows": 0,
            "checks": checks,
            "failed_checks": [c["name"] for c in checks if not c["success"]],
            "success": False,
        }
        write_json(settings.paths.quality_dir / f"{safe_slug(report_name)}_quality.json", result)
        return result

    paper_id = df["paper_id"].fillna("").astype(str).str.strip()
    title = df["title"].fillna("").astype(str).str.strip()
    summary_chars = (
        df["summary_chars"]
        if "summary_chars" in df.columns
        else df["summary"].fillna("").astype(str).str.len()
    ).astype(int)

    # 2. paper_id not null and unique.
    empty_ids = int((paper_id == "").sum())
    add("paper_id_not_null", empty_ids == 0, f"{empty_ids} empty paper_id value(s).", empty=empty_ids)
    duplicate_ids = int(paper_id[paper_id != ""].duplicated().sum())
    add("paper_id_unique", duplicate_ids == 0, f"{duplicate_ids} duplicate paper_id value(s).", duplicates=duplicate_ids)

    # 3. title not null.
    empty_titles = int((title == "").sum())
    add("title_not_null", empty_titles == 0, f"{empty_titles} empty title value(s).", empty=empty_titles)

    # 4. summary length.
    short_summaries = int((summary_chars < MIN_SUMMARY_CHARS).sum())
    add(
        "summary_min_length",
        short_summaries == 0,
        f"{short_summaries} summary(ies) shorter than {MIN_SUMMARY_CHARS} chars.",
        threshold_chars=MIN_SUMMARY_CHARS,
        short=short_summaries,
    )

    # 5. freshness via age_days.
    if "age_days" in df.columns:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
        stale_rows = int((age_days > threshold).sum())
        fresh_rows = int((age_days <= threshold).sum())
    else:
        stale_rows = total_rows
        fresh_rows = 0
    add(
        "freshness_has_recent_rows",
        fresh_rows > 0,
        f"{fresh_rows} row(s) within {threshold} days, {stale_rows} stale.",
        threshold_days=threshold,
        fresh_rows=fresh_rows,
        stale_rows=stale_rows,
    )

    failed = [c["name"] for c in checks if not c["success"]]
    result = {
        "report_name": report_name,
        "total_rows": total_rows,
        "checks": checks,
        "failed_checks": failed,
        "success": len(failed) == 0,
    }
    write_json(settings.paths.quality_dir / f"{safe_slug(report_name)}_quality.json", result)
    return result


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Summarize how fresh the dataset is and persist a JSON freshness report."""
    threshold = settings.freshness_threshold_days
    total_rows = int(len(df))

    if total_rows == 0 or "published" not in df.columns:
        payload = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": 0,
            "fresh_rows": 0,
            "total_rows": total_rows,
            "threshold_days": threshold,
            "is_fresh": False,
        }
        write_json(report_path, payload)
        return payload

    published = df["published"].fillna("").astype(str)
    non_empty = published[published != ""]
    latest_published = non_empty.max() if not non_empty.empty else None
    oldest_published = non_empty.min() if not non_empty.empty else None

    if "age_days" in df.columns:
        age_days = pd.to_numeric(df["age_days"], errors="coerce")
        stale_rows = int((age_days > threshold).sum())
        fresh_rows = int((age_days <= threshold).sum())
        max_age = int(age_days.max()) if age_days.notna().any() else None
        min_age = int(age_days.min()) if age_days.notna().any() else None
    else:
        stale_rows, fresh_rows, max_age, min_age = total_rows, 0, None, None

    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "fresh_rows": fresh_rows,
        "total_rows": total_rows,
        "threshold_days": threshold,
        "max_age_days": max_age,
        "min_age_days": min_age,
        "is_fresh": stale_rows == 0 and fresh_rows > 0,
    }
    write_json(report_path, payload)
    return payload
