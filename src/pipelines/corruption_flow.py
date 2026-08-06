from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def _save_dataframe(df: pd.DataFrame, csv_path, json_path) -> None:
    write_csv(df, csv_path)
    write_json(json_path, df.to_dict(orient="records"))


def _load_baseline_dataframe(settings) -> pd.DataFrame:
    if settings.paths.clean_json.exists():
        return pd.DataFrame(read_json(settings.paths.clean_json))
    records = load_raw_records(settings.paths.raw_records_json)
    baseline_df = build_clean_dataframe(records, now_utc())
    _save_dataframe(baseline_df, settings.paths.clean_csv, settings.paths.clean_json)
    return baseline_df


def _load_or_build_baseline_metrics(settings, baseline_df: pd.DataFrame) -> dict:
    if settings.paths.baseline_metrics.exists():
        return read_json(settings.paths.baseline_metrics)
    if not settings.paths.eval_testset.exists():
        build_test_set(baseline_df, settings.paths.eval_testset)
    baseline_index = LocalEmbeddingIndex.build(baseline_df, settings)
    return evaluate_pipeline(
        settings=settings,
        index=baseline_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    ).summary


def main() -> None:
    settings = load_settings()
    baseline_df = _load_baseline_dataframe(settings)
    if not settings.paths.eval_testset.exists():
        build_test_set(baseline_df, settings.paths.eval_testset)
    baseline_metrics = _load_or_build_baseline_metrics(settings, baseline_df)
    baseline_quality = run_data_quality_checks(baseline_df, settings, report_name="baseline_quality")
    baseline_freshness = build_freshness_report(baseline_df, settings, report_path=settings.paths.freshness_report)

    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    _save_dataframe(corrupted_df, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_metrics = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    ).summary
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, report_name="corrupted_quality")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        report_path=settings.paths.quality_dir / "corrupted_freshness_report.json",
    )

    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    _save_dataframe(repaired_df, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_metrics = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    ).summary
    repaired_quality = run_data_quality_checks(repaired_df, settings, report_name="repaired_quality")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        report_path=settings.paths.quality_dir / "repaired_freshness_report.json",
    )

    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        baseline_quality=baseline_quality,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        baseline_freshness=baseline_freshness,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )
