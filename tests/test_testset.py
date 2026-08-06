from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from evaluation.testset import build_test_set


class TestSetTests(unittest.TestCase):
    def test_build_test_set_creates_expected_question_types(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "paper_id": "p1",
                    "title": "Paper One",
                    "summary": "First sentence. Second sentence.",
                    "authors_joined": "Ada Lovelace, Alan Turing",
                    "categories_joined": "AI, Retrieval",
                    "published": "2026-08-01",
                },
                {
                    "paper_id": "p2",
                    "title": "Paper Two",
                    "summary": "Only sentence here.",
                    "authors_joined": "Grace Hopper",
                    "categories_joined": "",
                    "published": "2026-07-15",
                },
            ]
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_set.json"
            items = build_test_set(df, output_path)

            self.assertEqual(len(items), 7)
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), items)

        by_type = {}
        for item in items:
            by_type.setdefault(item["question_type"], []).append(item)
            self.assertIn("id", item)
            self.assertIn("question", item)
            self.assertIn("ground_truth", item)
            self.assertIn("ground_truth_doc_ids", item)
            self.assertEqual(len(item["ground_truth_doc_ids"]), 1)

        self.assertEqual(len(by_type["summary"]), 2)
        self.assertEqual(len(by_type["authors"]), 2)
        self.assertEqual(len(by_type["date"]), 2)
        self.assertEqual(len(by_type["categories"]), 1)

        summary_item = by_type["summary"][0]
        self.assertEqual(summary_item["ground_truth"], "First sentence.")
        self.assertIn("'Paper One'", summary_item["question"])

        authors_item = by_type["authors"][0]
        self.assertEqual(authors_item["ground_truth"], "Ada Lovelace, Alan Turing")
        self.assertIn("Who authored", authors_item["question"])

        date_item = by_type["date"][0]
        self.assertEqual(date_item["ground_truth"], "2026-08-01")
        self.assertIn("When was", date_item["question"])

        category_item = by_type["categories"][0]
        self.assertEqual(category_item["ground_truth"], "AI, Retrieval")
        self.assertIn("What categories", category_item["question"])

    def test_build_test_set_requires_at_least_one_document(self) -> None:
        df = pd.DataFrame(columns=["paper_id", "title", "summary", "authors_joined", "categories_joined", "published"])

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_set.json"
            with self.assertRaises(ValueError):
                build_test_set(df, output_path)


if __name__ == "__main__":
    unittest.main()
