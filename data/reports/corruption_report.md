# Corruption Impact Report

## Comparison
| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Retrieval hit rate | 1.000 | 0.600 | 1.000 |
| Token F1 | 1.000 | 0.551 | 1.000 |
| Judge accuracy | 1.000 | 0.467 | 1.000 |
| Mean judge score | 5.000 | 2.933 | 5.000 |
| Data quality | pass | fail | pass |
| Freshness | fresh | stale | fresh |

## Verdict
Corrupted data reduced retrieval and answer quality, while repair recovered the dataset toward baseline.
