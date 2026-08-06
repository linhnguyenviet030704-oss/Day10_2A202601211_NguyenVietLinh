from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from observability.reporting import generate_corruption_report, generate_phase1_report


class ReportingTests(unittest.TestCase):
    def test_generate_phase1_report_writes_expected_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "phase1_report.md"

            generate_phase1_report(
                report_path=report_path,
                source_summary={"records": 12, "loaded_from_cache": True},
                metrics={"retrieval_hit_rate": 0.75, "mean_token_f1": 0.5, "judge_accuracy": 0.5},
                quality={"passed": True, "stale_rows": 1},
                freshness={"is_fresh": False, "latest_published": "2026-07-01"},
            )

            content = report_path.read_text(encoding="utf-8")
            self.assertIn("# Phase 1 Baseline Report", content)
            self.assertIn("- Records: 12", content)
            self.assertIn("- Loaded from cache: yes", content)
            self.assertIn("- retrieval_hit_rate: 0.75", content)
            self.assertIn("- passed: True", content)
            self.assertIn("- latest_published: 2026-07-01", content)

    def test_generate_corruption_report_writes_comparison_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "corruption_report.md"

            generate_corruption_report(
                report_path=report_path,
                baseline_metrics={
                    "retrieval_hit_rate": 1.0,
                    "mean_token_f1": 1.0,
                    "judge_accuracy": 1.0,
                    "mean_judge_score": 5.0,
                },
                corrupted_metrics={
                    "retrieval_hit_rate": 0.4,
                    "mean_token_f1": 0.5,
                    "judge_accuracy": 0.4,
                    "mean_judge_score": 2.2,
                },
                repaired_metrics={
                    "retrieval_hit_rate": 0.9,
                    "mean_token_f1": 0.95,
                    "judge_accuracy": 0.9,
                    "mean_judge_score": 4.7,
                },
                baseline_quality={"passed": True},
                corrupted_quality={"passed": False},
                repaired_quality={"passed": True},
                baseline_freshness={"is_fresh": True},
                corrupted_freshness={"is_fresh": False},
                repaired_freshness={"is_fresh": True},
            )

            content = report_path.read_text(encoding="utf-8")
            self.assertIn("# Corruption Impact Report", content)
            self.assertIn("| Retrieval hit rate | 1.000 | 0.400 | 0.900 |", content)
            self.assertIn("| Data quality | pass | fail | pass |", content)
            self.assertIn("| Freshness | fresh | stale | fresh |", content)
            self.assertIn("Corrupted data reduced retrieval and answer quality", content)


if __name__ == "__main__":
    unittest.main()
