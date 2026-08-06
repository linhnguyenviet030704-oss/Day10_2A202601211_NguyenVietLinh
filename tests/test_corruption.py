from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

import pandas as pd

from ingestion.corruption import corrupt_clean_dataframe


def _sample_row(index: int) -> dict[str, object]:
    return {
        "paper_id": f"paper-{index}",
        "title": f"Paper Title {index} for Retrieval Testing",
        "summary": f"Detailed summary {index} with enough words to stay above the quality threshold for testing.",
        "authors": [f"Author {index}"],
        "categories": ["AI"],
        "primary_category": "AI",
        "published": f"2026-07-0{7 - index}",
        "updated": f"2026-07-0{7 - index}T00:00:00Z",
        "abs_url": f"https://example.com/{index}",
        "pdf_url": "",
        "comment": "Venue",
        "authors_joined": f"Author {index}",
        "categories_joined": "AI",
        "summary_chars": 84,
        "age_days": index,
        "text_for_embedding": f"Title: Paper Title {index}\nSummary: Detailed summary {index}",
    }


class CorruptionTests(unittest.TestCase):
    def test_corrupt_clean_dataframe_applies_all_requested_corruptions(self) -> None:
        df = pd.DataFrame([_sample_row(index) for index in range(6)])

        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "corruption_log.json"

            corrupted = corrupt_clean_dataframe(df, log_path)

            self.assertTrue(log_path.exists())
            log = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(log["dropped_latest_count"], 2)
            self.assertEqual(log["duplicate_rows_added"], 1)
            self.assertIn("paper-0", log["dropped_latest_paper_ids"])
            self.assertIn("paper-1", log["dropped_latest_paper_ids"])

            self.assertEqual(len(corrupted), 5)
            self.assertNotIn("paper-0", set(corrupted["paper_id"]))
            self.assertNotIn("paper-1", set(corrupted["paper_id"]))
            self.assertTrue((corrupted["summary"].astype(str).str.strip() == "").any())
            self.assertTrue(corrupted["summary"].astype(str).str.contains("lorem xyz_noise").any())
            self.assertTrue(corrupted["title"].astype(str).str.endswith("...").any())
            self.assertGreater(corrupted["paper_id"].value_counts().max(), 1)
            self.assertGreater(int(corrupted["age_days"].max()), 365)


if __name__ == "__main__":
    unittest.main()
