from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import tempfile
import unittest

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.crossref import PaperRecord


class CleaningTests(unittest.TestCase):
    def test_build_clean_dataframe_normalizes_filters_and_adds_embedding_text(self) -> None:
        run_date = datetime(2026, 8, 6, tzinfo=UTC)
        records = [
            PaperRecord(
                paper_id="10.1000/keep",
                title="  Agentic   RAG  ",
                summary="  A useful   summary about retrieval.  ",
                authors=[" Ada  Lovelace ", "Ada Lovelace", " Alan  Turing "],
                categories=[" AI ", "Retrieval", "AI"],
                primary_category=" AI ",
                published="2026-08-01",
                updated="2026-08-02T00:00:00Z",
                abs_url="https://doi.org/10.1000/keep",
                pdf_url="https://example.org/keep.pdf",
                comment=" Journal ",
            ),
            PaperRecord(
                paper_id="10.1000/drop-empty-summary",
                title="Has no summary",
                summary="   ",
                authors=["Nobody"],
                categories=["AI"],
                primary_category="AI",
                published="2026-07-01",
                updated="2026-07-02T00:00:00Z",
                abs_url="https://doi.org/10.1000/drop-empty-summary",
                pdf_url="",
                comment="",
            ),
            PaperRecord(
                paper_id="10.1000/drop-bad-date",
                title="Bad date",
                summary="This should drop.",
                authors=["Nobody"],
                categories=["AI"],
                primary_category="AI",
                published="not-a-date",
                updated="2026-07-02T00:00:00Z",
                abs_url="https://doi.org/10.1000/drop-bad-date",
                pdf_url="",
                comment="",
            ),
            PaperRecord(
                paper_id="10.1000/keep",
                title="Duplicate should drop",
                summary="Later duplicate should be removed.",
                authors=["Duplicate"],
                categories=["Duplicates"],
                primary_category="Duplicates",
                published="2026-07-15",
                updated="2026-07-16T00:00:00Z",
                abs_url="https://doi.org/10.1000/duplicate",
                pdf_url="",
                comment="",
            ),
        ]

        df = build_clean_dataframe(records, run_date)

        self.assertEqual(list(df["paper_id"]), ["10.1000/keep"])
        row = df.iloc[0].to_dict()
        self.assertEqual(row["title"], "Agentic RAG")
        self.assertEqual(row["summary"], "A useful summary about retrieval.")
        self.assertEqual(row["authors"], ["Ada Lovelace", "Alan Turing"])
        self.assertEqual(row["categories"], ["AI", "Retrieval"])
        self.assertEqual(row["primary_category"], "AI")
        self.assertEqual(row["authors_joined"], "Ada Lovelace, Alan Turing")
        self.assertEqual(row["categories_joined"], "AI, Retrieval")
        self.assertEqual(row["published"], "2026-08-01")
        self.assertEqual(row["age_days"], 5)
        self.assertEqual(row["summary_chars"], len("A useful summary about retrieval."))
        self.assertIn("Title: Agentic RAG", row["text_for_embedding"])
        self.assertIn("Summary: A useful summary about retrieval.", row["text_for_embedding"])
        self.assertIn("Authors: Ada Lovelace, Alan Turing", row["text_for_embedding"])
        self.assertIn("Categories: AI, Retrieval", row["text_for_embedding"])

    def test_save_clean_dataframe_writes_csv_and_json(self) -> None:
        run_date = datetime(2026, 8, 6, tzinfo=UTC)
        records = [
            PaperRecord(
                paper_id="10.1000/save",
                title="Save Me",
                summary="Persist cleaned output.",
                authors=["Save Author"],
                categories=["Pipelines"],
                primary_category="Pipelines",
                published="2026-08-05",
                updated="2026-08-05T00:00:00Z",
                abs_url="https://doi.org/10.1000/save",
                pdf_url="",
                comment="",
            )
        ]
        df = build_clean_dataframe(records, run_date)

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = load_settings()
            root = Path(tmp_dir)
            settings = settings.__class__(
                **{
                    **settings.__dict__,
                    "paths": settings.paths.__class__(
                        **{
                            **settings.paths.__dict__,
                            "clean_csv": root / "data" / "clean" / "papers_clean.csv",
                            "clean_json": root / "data" / "clean" / "papers_clean.json",
                        }
                    ),
                }
            )

            save_clean_dataframe(df, settings)

            self.assertTrue(settings.paths.clean_csv.exists())
            self.assertTrue(settings.paths.clean_json.exists())
            payload = json.loads(settings.paths.clean_json.read_text(encoding="utf-8"))
            self.assertEqual(payload[0]["paper_id"], "10.1000/save")
            self.assertEqual(payload[0]["age_days"], 1)


if __name__ == "__main__":
    unittest.main()
