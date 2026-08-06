from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from core.config import load_settings
from observability.quality import build_freshness_report, run_data_quality_checks


class QualityTests(unittest.TestCase):
    def test_quality_and_freshness_reports_are_written(self) -> None:
        df = pd.DataFrame(
            [
                {
                    "paper_id": "p1",
                    "title": "Fresh Paper",
                    "summary": "Useful summary.",
                    "age_days": 30,
                    "published": "2026-07-01",
                },
                {
                    "paper_id": "p2",
                    "title": "Older Paper",
                    "summary": "Another useful summary.",
                    "age_days": 240,
                    "published": "2025-12-10",
                },
            ]
        )

        base_settings = load_settings()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = replace(
                base_settings,
                paths=replace(
                    base_settings.paths,
                    quality_dir=tmp_path / "quality",
                    freshness_report=tmp_path / "quality" / "freshness_report.json",
                ),
            )

            quality = run_data_quality_checks(df, settings, report_name="baseline_quality")
            freshness = build_freshness_report(df, settings, report_path=settings.paths.freshness_report)

            quality_path = settings.paths.quality_dir / "baseline_quality.json"
            self.assertTrue(quality_path.exists())
            self.assertEqual(json.loads(quality_path.read_text(encoding="utf-8")), quality)
            self.assertEqual(quality["total_rows"], 2)
            self.assertEqual(quality["stale_rows"], 1)
            self.assertTrue(quality["checks"]["paper_id_unique"]["passed"])
            self.assertTrue(quality["checks"]["summary_present"]["passed"])
            self.assertFalse(quality["is_fresh"])

            self.assertTrue(settings.paths.freshness_report.exists())
            self.assertEqual(json.loads(settings.paths.freshness_report.read_text(encoding="utf-8")), freshness)
            self.assertEqual(freshness["latest_published"], "2026-07-01")
            self.assertEqual(freshness["oldest_published"], "2025-12-10")
            self.assertEqual(freshness["stale_rows"], 1)
            self.assertFalse(freshness["is_fresh"])


if __name__ == "__main__":
    unittest.main()
