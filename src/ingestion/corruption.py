from __future__ import annotations

from datetime import timedelta

import pandas as pd

from core.utils import compact_join, now_utc, write_json


def _truncate_title(title: str) -> str:
    cleaned = str(title).strip()
    if not cleaned:
        return "..."
    cutoff = min(max(12, len(cleaned) // 2), 48)
    return f"{cleaned[:cutoff].rstrip()}..."


def _rebuild_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    rebuilt = df.copy()
    rebuilt["authors_joined"] = rebuilt["authors"].apply(lambda value: compact_join(value if isinstance(value, list) else []))
    rebuilt["categories_joined"] = rebuilt["categories"].apply(
        lambda value: compact_join(value if isinstance(value, list) else [])
    )
    rebuilt["summary"] = rebuilt["summary"].fillna("").astype(str)
    rebuilt["title"] = rebuilt["title"].fillna("").astype(str)
    rebuilt["published"] = rebuilt["published"].fillna("").astype(str)
    rebuilt["comment"] = rebuilt["comment"].fillna("").astype(str)
    rebuilt["summary_chars"] = rebuilt["summary"].str.len().astype(int)

    run_timestamp = pd.Timestamp(now_utc()).tz_convert("UTC")
    published_at = pd.to_datetime(rebuilt["published"], errors="coerce", utc=True)
    rebuilt["age_days"] = (run_timestamp.normalize() - published_at.dt.normalize()).dt.days.fillna(9999).astype(int)

    rebuilt["text_for_embedding"] = rebuilt.apply(
        lambda row: "\n".join(
            part
            for part in [
                f"Title: {row['title']}",
                f"Summary: {row['summary']}",
                f"Authors: {row['authors_joined']}",
                f"Categories: {row['categories_joined']}",
                f"Published: {row['published']}",
                f"Venue: {row['comment']}" if row["comment"] else "",
            ]
            if part
        ),
        axis=1,
    )
    return rebuilt

def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    if df.empty:
        write_json(output_log_path, {"dropped_latest_count": 0, "duplicate_rows_added": 0, "operations": []})
        return df.copy()

    corrupted = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True).copy()
    dropped_latest_count = 2 if len(corrupted) >= 5 else 1
    dropped_latest_paper_ids = corrupted.head(dropped_latest_count)["paper_id"].astype(str).tolist()
    corrupted = corrupted.iloc[dropped_latest_count:].reset_index(drop=True)

    operations: list[dict[str, object]] = []

    if not corrupted.empty:
        corrupted.at[0, "summary"] = ""
        operations.append({"type": "blank_summary", "paper_id": str(corrupted.at[0, "paper_id"])})

    if len(corrupted) >= 2:
        corrupted.at[1, "summary"] = f"lorem xyz_noise lorem xyz_noise {corrupted.at[1, 'summary']}"
        operations.append({"type": "summary_noise", "paper_id": str(corrupted.at[1, "paper_id"])})

    if len(corrupted) >= 3:
        corrupted.at[2, "title"] = _truncate_title(str(corrupted.at[2, "title"]))
        operations.append({"type": "truncate_title", "paper_id": str(corrupted.at[2, "paper_id"])})

    if len(corrupted) >= 4:
        stale_date = (now_utc().date() - timedelta(days=400)).isoformat()
        corrupted.at[3, "published"] = stale_date
        corrupted.at[3, "updated"] = f"{stale_date}T00:00:00Z"
        operations.append({"type": "stale_publication_date", "paper_id": str(corrupted.at[3, "paper_id"])})

    duplicate_rows_added = 0
    if not corrupted.empty:
        corrupted = pd.concat([corrupted, corrupted.iloc[[0]].copy()], ignore_index=True)
        duplicate_rows_added = 1
        operations.append({"type": "duplicate_row", "paper_id": str(corrupted.iloc[-1]["paper_id"])})

    corrupted = _rebuild_derived_columns(corrupted)
    write_json(
        output_log_path,
        {
            "dropped_latest_count": dropped_latest_count,
            "dropped_latest_paper_ids": dropped_latest_paper_ids,
            "duplicate_rows_added": duplicate_rows_added,
            "final_row_count": int(len(corrupted)),
            "operations": operations,
        },
    )
    return corrupted
