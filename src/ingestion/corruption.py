from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from core.utils import compact_join, now_utc, write_json

STALE_PUBLISHED_DATE = "2015-01-01"
NOISE_SUFFIX = " ##CORRUPTED_NOISE_TOKEN_lorem_ipsum_9f3x##"


def _rebuild_embedding_text(row: pd.Series) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Summary: {row['summary']}",
        f"Authors: {row['authors_joined']}",
        f"Categories: {row['categories_joined']}",
        f"Published: {row['published']}",
    ]
    if row.get("comment"):
        parts.append(f"Venue: {row['comment']}")
    return "\n".join(part for part in parts if not part.endswith(": "))


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    log: dict[str, Any] = {"generated_at": now_utc().isoformat(), "actions": []}
    corrupted = df.reset_index(drop=True).copy()
    original_count = len(corrupted)

    if original_count == 0:
        write_json(output_log_path, log)
        return corrupted

    # 1. Drop some of the most recent records (simulate a missed ingestion window).
    n_drop = max(1, original_count // 6)
    sorted_by_date = corrupted.sort_values("published", ascending=False)
    dropped_ids = sorted_by_date.head(n_drop)["paper_id"].tolist()
    corrupted = corrupted[~corrupted["paper_id"].isin(dropped_ids)].reset_index(drop=True)
    log["actions"].append({"action": "drop_latest_records", "paper_ids": dropped_ids, "count": len(dropped_ids)})

    row_count = len(corrupted)
    if row_count == 0:
        log["original_row_count"] = original_count
        log["final_row_count"] = 0
        write_json(output_log_path, log)
        return corrupted

    n_blank = max(1, row_count // 5)
    n_noise = max(1, row_count // 5)
    n_truncate = max(1, row_count // 5)
    n_stale = max(1, row_count // 5)

    # 2. Blank out summaries on a slice of rows.
    blank_idx = corrupted.index[:n_blank]
    blanked_ids = corrupted.loc[blank_idx, "paper_id"].tolist()
    corrupted.loc[blank_idx, "summary"] = ""
    log["actions"].append({"action": "blank_summary", "paper_ids": blanked_ids, "count": len(blanked_ids)})

    # 3. Inject noise text into another slice of summaries.
    noise_idx = corrupted.index[n_blank : n_blank + n_noise]
    noisy_ids = corrupted.loc[noise_idx, "paper_id"].tolist()
    corrupted.loc[noise_idx, "summary"] = corrupted.loc[noise_idx, "summary"].astype(str) + NOISE_SUFFIX
    log["actions"].append({"action": "inject_summary_noise", "paper_ids": noisy_ids, "count": len(noisy_ids)})

    # 4. Truncate titles on another slice.
    truncate_idx = corrupted.index[n_blank + n_noise : n_blank + n_noise + n_truncate]
    truncated_ids = corrupted.loc[truncate_idx, "paper_id"].tolist()
    corrupted.loc[truncate_idx, "title"] = corrupted.loc[truncate_idx, "title"].astype(str).str[:8]
    log["actions"].append({"action": "truncate_title", "paper_ids": truncated_ids, "count": len(truncated_ids)})

    # 5. Push publication dates far into the past (stale data).
    stale_idx = corrupted.index[-n_stale:]
    stale_ids = corrupted.loc[stale_idx, "paper_id"].tolist()
    stale_age_days = (now_utc() - datetime.fromisoformat(STALE_PUBLISHED_DATE).replace(tzinfo=UTC)).days
    corrupted.loc[stale_idx, "published"] = STALE_PUBLISHED_DATE
    if "age_days" in corrupted.columns:
        corrupted.loc[stale_idx, "age_days"] = stale_age_days
    log["actions"].append(
        {
            "action": "stale_published_date",
            "paper_ids": stale_ids,
            "count": len(stale_ids),
            "new_published": STALE_PUBLISHED_DATE,
        }
    )

    # 6. Duplicate a couple of rows.
    n_dup = min(2, row_count)
    duplicates = corrupted.head(n_dup).copy()
    dup_ids = duplicates["paper_id"].tolist()
    corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
    log["actions"].append({"action": "duplicate_rows", "paper_ids": dup_ids, "count": len(dup_ids)})

    # 7. Rebuild fields that depend on the corrupted columns.
    if "authors" in corrupted.columns:
        corrupted["authors_joined"] = corrupted["authors"].apply(compact_join)
    if "categories" in corrupted.columns:
        corrupted["categories_joined"] = corrupted["categories"].apply(compact_join)
    corrupted["summary_chars"] = corrupted["summary"].astype(str).str.len().astype(int)
    corrupted["text_for_embedding"] = corrupted.apply(_rebuild_embedding_text, axis=1)

    log["original_row_count"] = original_count
    log["final_row_count"] = len(corrupted)
    write_json(output_log_path, log)
    return corrupted
