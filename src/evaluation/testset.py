from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, normalize_whitespace, write_json


def _build_samples_for_row(row: dict[str, Any], index: int) -> list[dict[str, Any]]:
    title = normalize_whitespace(str(row["title"]))
    paper_id = normalize_whitespace(str(row["paper_id"]))
    samples = [
        {
            "id": f"{paper_id}::summary::{index}",
            "question_type": "summary",
            "question": f"Summarize the paper '{title}'.",
            "ground_truth": first_sentence(str(row["summary"])),
            "ground_truth_doc_ids": [paper_id],
        },
        {
            "id": f"{paper_id}::authors::{index}",
            "question_type": "authors",
            "question": f"Who authored the paper '{title}'?",
            "ground_truth": normalize_whitespace(str(row["authors_joined"])),
            "ground_truth_doc_ids": [paper_id],
        },
        {
            "id": f"{paper_id}::date::{index}",
            "question_type": "date",
            "question": f"When was the paper '{title}' published?",
            "ground_truth": normalize_whitespace(str(row["published"])),
            "ground_truth_doc_ids": [paper_id],
        },
    ]

    categories = normalize_whitespace(str(row.get("categories_joined", "")))
    if categories:
        samples.append(
            {
                "id": f"{paper_id}::categories::{index}",
                "question_type": "categories",
                "question": f"What categories does the paper '{title}' belong to?",
                "ground_truth": categories,
                "ground_truth_doc_ids": [paper_id],
            }
        )
    return samples


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if df.empty:
        raise ValueError("Need at least one cleaned document to build a test set.")

    columns = {"paper_id", "title", "summary", "authors_joined", "categories_joined", "published"}
    missing = sorted(column for column in columns if column not in df.columns)
    if missing:
        raise ValueError(f"Missing required columns for test set: {', '.join(missing)}")

    candidates = (
        df.sort_values(["published", "summary_chars", "paper_id"], ascending=[False, False, True], na_position="last")
        if "summary_chars" in df.columns
        else df.sort_values(["published", "paper_id"], ascending=[False, True], na_position="last")
    )

    samples: list[dict[str, Any]] = []
    for index, row in enumerate(candidates.head(5).to_dict(orient="records"), start=1):
        samples.extend(_build_samples_for_row(row, index))

    write_json(output_path, samples)
    return samples
