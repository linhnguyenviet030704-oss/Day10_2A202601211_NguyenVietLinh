# Corruption & Repair Comparison Report

Generated at: 2026-08-06T04:58:38.676772+00:00

## Metrics Comparison

| Metric | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| retrieval_hit_rate | 1.0000 | 0.4000 | 1.0000 |
| mean_token_f1 | 1.0000 | 0.2947 | 1.0000 |
| judge_accuracy | 1.0000 | 0.2667 | 1.0000 |
| mean_judge_score | 5 | 2.5333 | 5 |

## Data Quality Comparison

| State | Success | Row Count |
| --- | --- | --- |
| Corrupted | False | 21 |
| Repaired | True | 22 |

## Freshness Comparison

| State | Is Fresh | Stale Rows | Total Rows |
| --- | --- | --- | --- |
| Corrupted | False | 3 | 21 |
| Repaired | True | 0 | 22 |

## Analysis

- Retrieval hit rate dropped by 0.6000 from baseline to corrupted data.
- Retrieval hit rate recovered by 0.6000 after repair.
- Mean token F1 dropped by 0.7053 from baseline to corrupted data.
- Mean token F1 recovered by 0.7053 after repair.

