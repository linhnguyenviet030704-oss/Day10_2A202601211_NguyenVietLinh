# Phase 1 - Baseline Report

Generated at: 2026-08-06T04:57:19.685956+00:00

## Data Source

- **source_api**: Crossref REST API
- **source_query**: agentic retrieval augmented generation large language model
- **source_filter**: from-pub-date:2026-02-07,has-abstract:true
- **raw_records**: 24
- **clean_records**: 22
- **embedding_model**: sentence-transformers/all-MiniLM-L6-v2
- **collection_name**: papers-baseline

## Evaluation Metrics

| Metric | Value |
| --- | --- |
| samples | 15 |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 1.0000 |
| judge_accuracy | 1.0000 |
| mean_judge_score | 5 |

### Ragas

- **skipped**: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## Data Quality

- **success**: True
- **row_count**: 22

  - [PASS] `row_count_positive` — row_count=22
  - [PASS] `paper_id_not_null` — missing=0/22
  - [PASS] `paper_id_unique` — unique=22/22
  - [PASS] `title_not_null` — missing=0/22
  - [PASS] `title_min_length` — threshold=15 chars, failing=0/22
  - [PASS] `summary_min_length` — threshold=20 chars, failing=0/22
  - [PASS] `freshness_age_days` — threshold_days=180, stale_rows=0/22

## Freshness

- **latest_published**: 2026-08-01
- **oldest_published**: 2026-02-12
- **stale_rows**: 0
- **total_rows**: 22
- **is_fresh**: True

