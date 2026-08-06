from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def _load_or_fetch_records(settings):
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        return fetch_source_records(settings), False
    return load_raw_records(settings.paths.raw_records_json), True


def _ensure_test_set(df, settings) -> None:
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)


def main() -> None:
    settings = load_settings()
    records, loaded_from_cache = _load_or_fetch_records(settings)
    clean_df = build_clean_dataframe(records, now_utc())
    save_clean_dataframe(clean_df, settings)

    index = LocalEmbeddingIndex.build(clean_df, settings)
    _ensure_test_set(clean_df, settings)
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(clean_df, settings, report_name="baseline_quality")
    freshness = build_freshness_report(clean_df, settings, report_path=settings.paths.freshness_report)
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary={
            "records": len(records),
            "loaded_from_cache": loaded_from_cache,
            "clean_rows": len(clean_df),
        },
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )
