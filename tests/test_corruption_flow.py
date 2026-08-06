from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from core.config import load_settings
from pipelines.corruption_flow import main


class CorruptionFlowTests(unittest.TestCase):
    def test_main_runs_corrupt_evaluate_repair_compare_pipeline(self) -> None:
        base_settings = load_settings()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = replace(
                base_settings,
                paths=replace(
                    base_settings.paths,
                    clean_json=tmp_path / "clean" / "papers_clean.json",
                    clean_csv=tmp_path / "clean" / "papers_clean.csv",
                    raw_records_json=tmp_path / "raw" / "crossref_records.json",
                    eval_testset=tmp_path / "eval" / "test_set.json",
                    corrupted_clean_csv=tmp_path / "clean" / "papers_clean_corrupted.csv",
                    corrupted_clean_json=tmp_path / "clean" / "papers_clean_corrupted.json",
                    repaired_clean_csv=tmp_path / "clean" / "papers_clean_repaired.csv",
                    repaired_clean_json=tmp_path / "clean" / "papers_clean_repaired.json",
                    corrupted_embeddings_json=tmp_path / "embeddings" / "papers_embeddings_corrupted.json",
                    repaired_embeddings_json=tmp_path / "embeddings" / "papers_embeddings_repaired.json",
                    baseline_metrics=tmp_path / "results" / "baseline_metrics.json",
                    corrupted_metrics=tmp_path / "results" / "corrupted_metrics.json",
                    corrupted_answers=tmp_path / "results" / "corrupted_answers.json",
                    repaired_metrics=tmp_path / "results" / "repaired_metrics.json",
                    repaired_answers=tmp_path / "results" / "repaired_answers.json",
                    quality_dir=tmp_path / "quality",
                    corruption_log=tmp_path / "results" / "corruption_log.json",
                    comparison_report=tmp_path / "reports" / "corruption_report.md",
                ),
            )

            baseline_df = pd.DataFrame(
                [
                    {
                        "paper_id": "paper-1",
                        "title": "Paper One",
                        "summary": "Summary one with enough detail for testing.",
                        "authors": ["Ada"],
                        "categories": ["AI"],
                        "primary_category": "AI",
                        "published": "2026-08-01",
                        "updated": "2026-08-02T00:00:00Z",
                        "abs_url": "https://example.com/p1",
                        "pdf_url": "",
                        "comment": "Venue",
                        "authors_joined": "Ada",
                        "categories_joined": "AI",
                        "summary_chars": 42,
                        "age_days": 5,
                        "text_for_embedding": "paper one context",
                    }
                ]
            )
            corrupted_df = baseline_df.copy()
            repaired_df = baseline_df.copy()

            settings.paths.clean_json.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.clean_json.write_text(baseline_df.to_json(orient="records", indent=2), encoding="utf-8")
            settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.raw_records_json.write_text("[]\n", encoding="utf-8")
            settings.paths.eval_testset.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.eval_testset.write_text("[]\n", encoding="utf-8")
            settings.paths.baseline_metrics.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.baseline_metrics.write_text(
                json.dumps(
                    {
                        "retrieval_hit_rate": 1.0,
                        "mean_token_f1": 1.0,
                        "judge_accuracy": 1.0,
                        "mean_judge_score": 5.0,
                    }
                ),
                encoding="utf-8",
            )

            with (
                patch("pipelines.corruption_flow.load_settings", return_value=settings),
                patch("pipelines.corruption_flow.corrupt_clean_dataframe", return_value=corrupted_df) as corrupt_df,
                patch("pipelines.corruption_flow.LocalEmbeddingIndex.build", side_effect=[object(), object()]) as build_index,
                patch(
                    "pipelines.corruption_flow.evaluate_pipeline",
                    side_effect=[
                        type("Bundle", (), {"summary": {"retrieval_hit_rate": 0.5}, "answers": []})(),
                        type("Bundle", (), {"summary": {"retrieval_hit_rate": 0.9}, "answers": []})(),
                    ],
                ) as evaluate_pipeline,
                patch("pipelines.corruption_flow.run_data_quality_checks", side_effect=[{"passed": True}, {"passed": False}, {"passed": True}]) as run_quality,
                patch(
                    "pipelines.corruption_flow.build_freshness_report",
                    side_effect=[{"is_fresh": True}, {"is_fresh": False}, {"is_fresh": True}],
                ) as build_freshness,
                patch("pipelines.corruption_flow.load_raw_records", return_value=[]) as load_raw_records,
                patch("pipelines.corruption_flow.build_clean_dataframe", return_value=repaired_df) as build_clean_dataframe,
                patch("pipelines.corruption_flow.generate_corruption_report") as generate_report,
            ):
                main()

            corrupt_df.assert_called_once()
            self.assertEqual(build_index.call_count, 2)
            self.assertEqual(evaluate_pipeline.call_count, 2)
            self.assertEqual(run_quality.call_count, 3)
            self.assertEqual(build_freshness.call_count, 3)
            load_raw_records.assert_called_once_with(settings.paths.raw_records_json)
            build_clean_dataframe.assert_called_once()
            generate_report.assert_called_once()
            self.assertTrue(settings.paths.corrupted_clean_json.exists())
            self.assertTrue(settings.paths.repaired_clean_json.exists())


if __name__ == "__main__":
    unittest.main()
