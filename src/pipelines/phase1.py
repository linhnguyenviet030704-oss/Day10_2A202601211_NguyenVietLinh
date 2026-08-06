from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, read_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Baseline pipeline: ingest -> clean -> index -> evaluate -> observe -> report."""
    settings = load_settings()
    paths = settings.paths
    run_date = now_utc()

    # 1-2. Load or fetch raw records.
    if settings.refresh_source or not paths.raw_records_json.exists():
        print("[phase1] fetching raw records from source ...")
        records = fetch_source_records(settings)
    else:
        print("[phase1] loading cached raw records ...")
        records = load_raw_records(paths.raw_records_json)
    print(f"[phase1] raw records: {len(records)}")

    # 3-4. Clean and persist.
    df = build_clean_dataframe(records, run_date=run_date)
    save_clean_dataframe(df, settings)
    print(f"[phase1] clean rows: {len(df)}")
    if df.empty:
        raise RuntimeError("No clean rows produced; cannot continue baseline pipeline.")

    # 5. Build embedding index (ChromaDB).
    print("[phase1] building embedding index ...")
    index = LocalEmbeddingIndex.build(df, settings)

    # 6. Create or load evaluation set.
    if settings.refresh_test_set or not paths.eval_testset.exists():
        print("[phase1] building evaluation test set ...")
        test_set = build_test_set(df, paths.eval_testset)
    else:
        print("[phase1] loading existing evaluation test set ...")
        test_set = read_json(paths.eval_testset)
    print(f"[phase1] test samples: {len(test_set)}")

    # 7. Evaluate.
    print("[phase1] evaluating pipeline (this calls the LLM judge) ...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.baseline_metrics,
        answers_output_path=paths.baseline_answers,
    )

    # 8. Data quality + freshness.
    print("[phase1] running data quality checks ...")
    quality = run_data_quality_checks(df, settings, report_name="baseline")
    freshness = build_freshness_report(df, settings, paths.freshness_report)

    # 9. Baseline markdown report.
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(records),
        "clean_rows": int(len(df)),
        "run_date": run_date.date().isoformat(),
    }
    generate_phase1_report(
        report_path=paths.baseline_report,
        source_summary=source_summary,
        metrics=bundle.summary,
        quality=quality,
        freshness=freshness,
    )

    # Console summary.
    print("\n[phase1] === baseline summary ===")
    for key in ["samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]:
        if key in bundle.summary:
            print(f"  {key}: {bundle.summary[key]}")
    print(f"  data_quality: {'PASS' if quality['success'] else 'FAIL'} "
          f"(failed: {quality['failed_checks'] or 'none'})")
    print(f"  freshness: {'FRESH' if freshness['is_fresh'] else 'STALE'} "
          f"({freshness['stale_rows']} stale / {freshness['total_rows']} rows)")
    print(f"  report: {paths.baseline_report}")


if __name__ == "__main__":
    main()
