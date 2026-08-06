# Phase 1 Baseline Report

## Source Summary
- Records: 24
- Loaded from cache: yes
- Clean rows: 22

## Evaluation Metrics
- samples: 15
- retrieval_hit_rate: 1.0
- mean_token_f1: 1.0
- judge_accuracy: 1.0
- mean_judge_score: 5
- ragas: {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}

## Data Quality
- report_name: baseline_quality
- total_rows: 22
- stale_rows: 0
- freshness_threshold_days: 180
- is_fresh: True
- passed: True
- checks: {'row_count_positive': {'passed': True, 'value': 22}, 'paper_id_unique': {'passed': True, 'value': 22}, 'title_present': {'passed': True, 'value': 22}, 'summary_present': {'passed': True, 'value': 22}, 'summary_length_reasonable': {'passed': True, 'value': 1777.5}}

## Freshness
- latest_published: 2026-08-01
- oldest_published: 2026-02-12
- stale_rows: 0
- total_rows: 22
- freshness_threshold_days: 180
- is_fresh: True
