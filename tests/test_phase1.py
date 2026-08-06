from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from core.config import load_settings
from ingestion.crossref import PaperRecord
from pipelines.phase1 import main


class Phase1PipelineTests(unittest.TestCase):
    def test_main_reuses_existing_artifacts_and_runs_baseline_flow(self) -> None:
        base_settings = load_settings()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            settings = replace(
                base_settings,
                refresh_source=False,
                refresh_test_set=False,
                paths=replace(
                    base_settings.paths,
                    raw_records_json=tmp_path / "raw" / "crossref_records.json",
                    clean_csv=tmp_path / "clean" / "papers_clean.csv",
                    clean_json=tmp_path / "clean" / "papers_clean.json",
                    chroma_dir=tmp_path / "chroma",
                    embeddings_json=tmp_path / "embeddings" / "papers_embeddings.json",
                    eval_testset=tmp_path / "eval" / "test_set.json",
                    baseline_metrics=tmp_path / "results" / "baseline_metrics.json",
                    baseline_answers=tmp_path / "results" / "baseline_answers.json",
                    quality_dir=tmp_path / "quality",
                    freshness_report=tmp_path / "quality" / "freshness_report.json",
                    baseline_report=tmp_path / "reports" / "phase1_report.md",
                ),
            )
            settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.raw_records_json.write_text("[]\n", encoding="utf-8")
            settings.paths.eval_testset.parent.mkdir(parents=True, exist_ok=True)
            settings.paths.eval_testset.write_text("[]\n", encoding="utf-8")

            records = [
                PaperRecord(
                    paper_id="p1",
                    title="Paper One",
                    summary="Summary one.",
                    authors=["Ada"],
                    categories=["AI"],
                    primary_category="AI",
                    published="2026-07-01",
                    updated="2026-07-02T00:00:00Z",
                    abs_url="https://example.com/p1",
                    pdf_url="",
                    comment="Venue",
                )
            ]
            df = pd.DataFrame(
                [
                    {
                        "paper_id": "p1",
                        "title": "Paper One",
                        "summary": "Summary one.",
                        "authors_joined": "Ada",
                        "categories_joined": "AI",
                        "published": "2026-07-01",
                        "age_days": 10,
                        "text_for_embedding": "paper one context",
                    }
                ]
            )
            index = object()
            evaluation_bundle = type("Bundle", (), {"summary": {"retrieval_hit_rate": 1.0}, "answers": []})()

            with (
                patch("pipelines.phase1.load_settings", return_value=settings),
                patch("pipelines.phase1.load_raw_records", return_value=records) as load_raw_records,
                patch("pipelines.phase1.fetch_source_records") as fetch_source_records,
                patch("pipelines.phase1.build_clean_dataframe", return_value=df) as build_clean_dataframe,
                patch("pipelines.phase1.save_clean_dataframe") as save_clean_dataframe,
                patch("pipelines.phase1.LocalEmbeddingIndex.build", return_value=index) as build_index,
                patch("pipelines.phase1.build_test_set") as build_test_set,
                patch("pipelines.phase1.evaluate_pipeline", return_value=evaluation_bundle) as evaluate_pipeline,
                patch("pipelines.phase1.run_data_quality_checks", return_value={"passed": True}) as run_quality,
                patch("pipelines.phase1.build_freshness_report", return_value={"is_fresh": True}) as build_freshness,
                patch("pipelines.phase1.generate_phase1_report") as generate_report,
            ):
                main()

            load_raw_records.assert_called_once_with(settings.paths.raw_records_json)
            fetch_source_records.assert_not_called()
            build_clean_dataframe.assert_called_once()
            save_clean_dataframe.assert_called_once_with(df, settings)
            build_index.assert_called_once_with(df, settings)
            build_test_set.assert_not_called()
            evaluate_pipeline.assert_called_once_with(
                settings=settings,
                index=index,
                test_set_path=settings.paths.eval_testset,
                metrics_output_path=settings.paths.baseline_metrics,
                answers_output_path=settings.paths.baseline_answers,
            )
            run_quality.assert_called_once_with(df, settings, report_name="baseline_quality")
            build_freshness.assert_called_once_with(df, settings, report_path=settings.paths.freshness_report)
            generate_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
