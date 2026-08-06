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


def main() -> None:
    settings = load_settings()

    # 1-2. Load or fetch raw records.
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)

    # 3-4. Clean data and persist clean CSV/JSON.
    run_date = now_utc()
    df = build_clean_dataframe(records, run_date)
    save_clean_dataframe(df, settings)

    # 5. Build the Chroma embedding index.
    index = LocalEmbeddingIndex.build(df, settings, embeddings_output_path=settings.paths.embeddings_json)

    # 6. Create or reuse the evaluation set.
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(df, settings.paths.eval_testset)

    # 7. Evaluate the baseline agent against the test set.
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 8. Data quality checks and freshness report.
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)

    # 9. Markdown report.
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(records),
        "clean_records": len(df),
        "embedding_model": settings.embedding_model,
        "collection_name": index.collection_name,
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    print("Phase 1 baseline pipeline complete.")
    print(f"Raw records: {len(records)} | Clean records: {len(df)}")
    print(f"Retrieval hit rate: {bundle.summary['retrieval_hit_rate']:.3f}")
    print(f"Mean token F1: {bundle.summary['mean_token_f1']:.3f}")
    print(f"Judge accuracy: {bundle.summary['judge_accuracy']:.3f}")
    print(f"Mean judge score: {bundle.summary['mean_judge_score']:.3f}")
    print(f"Data quality success: {quality['success']}")
    print(f"Freshness is_fresh: {freshness['is_fresh']}")
