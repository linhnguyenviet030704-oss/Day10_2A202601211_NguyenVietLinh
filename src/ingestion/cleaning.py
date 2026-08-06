from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import compact_join, normalize_whitespace, write_csv, write_json
from ingestion.crossref import PaperRecord


def _normalize_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        cleaned = normalize_whitespace(value)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def _normalize_record(record: PaperRecord) -> dict[str, Any]:
    authors = _normalize_list(record.authors)
    categories = _normalize_list(record.categories)
    primary_category = normalize_whitespace(record.primary_category) or (categories[0] if categories else "")

    return {
        "paper_id": normalize_whitespace(record.paper_id),
        "title": normalize_whitespace(record.title),
        "summary": normalize_whitespace(record.summary),
        "authors": authors,
        "categories": categories,
        "primary_category": primary_category,
        "published": normalize_whitespace(record.published),
        "updated": normalize_whitespace(record.updated),
        "abs_url": normalize_whitespace(record.abs_url),
        "pdf_url": normalize_whitespace(record.pdf_url),
        "comment": normalize_whitespace(record.comment),
    }


def _build_embedding_text(row: pd.Series) -> str:
    parts = [
        f"Title: {row['title']}",
        f"Summary: {row['summary']}",
        f"Authors: {row['authors_joined']}",
        f"Categories: {row['categories_joined']}",
        f"Published: {row['published']}",
    ]
    if row["comment"]:
        parts.append(f"Venue: {row['comment']}")
    return "\n".join(part for part in parts if not part.endswith(": "))


def _empty_clean_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "paper_id",
            "title",
            "summary",
            "authors",
            "categories",
            "primary_category",
            "published",
            "updated",
            "abs_url",
            "pdf_url",
            "comment",
            "authors_joined",
            "categories_joined",
            "summary_chars",
            "age_days",
            "text_for_embedding",
        ]
    )


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if not records:
        return _empty_clean_dataframe()

    df = pd.DataFrame(_normalize_record(record) for record in records)
    if df.empty:
        return _empty_clean_dataframe()

    df["published_at"] = pd.to_datetime(df["published"], errors="coerce", utc=True)
    df["updated_at"] = pd.to_datetime(df["updated"], errors="coerce", utc=True)
    df = df[
        (df["paper_id"] != "")
        & (df["title"] != "")
        & (df["summary"] != "")
        & df["published_at"].notna()
    ].copy()
    if df.empty:
        return _empty_clean_dataframe()

    df = df.sort_values(["published_at", "paper_id"], ascending=[False, True]).drop_duplicates("paper_id", keep="first")
    df["published"] = df["published_at"].dt.strftime("%Y-%m-%d")
    df["updated"] = df["updated_at"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").fillna("")
    df["authors_joined"] = df["authors"].apply(compact_join)
    df["categories_joined"] = df["categories"].apply(compact_join)
    df["summary_chars"] = df["summary"].str.len().astype(int)
    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")
    df["age_days"] = (run_timestamp.normalize() - df["published_at"].dt.normalize()).dt.days.astype(int)
    df["text_for_embedding"] = df.apply(_build_embedding_text, axis=1)
    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df[_empty_clean_dataframe().columns.tolist()]


def save_clean_dataframe(df: pd.DataFrame, settings: Settings) -> None:
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
