# Phase 1 - Baseline Report

## Source

| Field | Value |
| --- | --- |
| Source API | Crossref REST API |
| Query | agentic retrieval augmented generation large language model |
| Filter | from-pub-date:2026-02-07,has-abstract:true |
| Raw records | 24 |
| Clean rows | 22 |
| Run date | 2026-08-06 |

## Retrieval & Evaluation Metrics

| Metric | Value |
| --- | --- |
| `samples` | 15 |
| `retrieval_hit_rate` | 1.0000 |
| `mean_token_f1` | 1.0000 |
| `judge_accuracy` | 1.0000 |
| `mean_judge_score` | 5 |

> Ragas: Set RUN_RAGAS=1 to enable the slower Ragas pass.

## Data Quality - PASS

Total rows checked: 22

| Check | Status | Detail |
| --- | --- | --- |
| `row_count_positive` | PASS | 22 row(s) present. |
| `paper_id_not_null` | PASS | 0 empty paper_id value(s). |
| `paper_id_unique` | PASS | 0 duplicate paper_id value(s). |
| `title_not_null` | PASS | 0 empty title value(s). |
| `summary_min_length` | PASS | 0 summary(ies) shorter than 40 chars. |
| `freshness_has_recent_rows` | PASS | 22 row(s) within 180 days, 0 stale. |

## Freshness - FRESH

| Field | Value |
| --- | --- |
| Latest published | 2026-08-01 |
| Oldest published | 2026-02-12 |
| Fresh rows | 22 |
| Stale rows | 0 |
| Total rows | 22 |
| Threshold (days) | 180 |
| Is fresh | yes |

