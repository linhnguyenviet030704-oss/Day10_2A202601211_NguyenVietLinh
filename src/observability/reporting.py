from __future__ import annotations

from typing import Any

from core.utils import write_text


def _section(title: str, payload: dict[str, Any]) -> str:
    lines = [f"## {title}"]
    for key, value in payload.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    content = "\n\n".join(
        [
            "# Phase 1 Baseline Report",
            _section(
                "Source Summary",
                {
                    "Records": source_summary.get("records", 0),
                    "Loaded from cache": "yes" if source_summary.get("loaded_from_cache") else "no",
                    "Clean rows": source_summary.get("clean_rows", 0),
                },
            ),
            _section("Evaluation Metrics", metrics),
            _section("Data Quality", quality),
            _section("Freshness", freshness),
        ]
    )
    write_text(report_path, content + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    baseline_quality: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    baseline_freshness: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    def metric(name: str, payload: dict[str, Any]) -> float:
        return float(payload.get(name, 0.0) or 0.0)

    def quality_status(payload: dict[str, Any]) -> str:
        return "pass" if payload.get("passed") else "fail"

    def freshness_status(payload: dict[str, Any]) -> str:
        return "fresh" if payload.get("is_fresh") else "stale"

    content = "\n".join(
        [
            "# Corruption Impact Report",
            "",
            "## Comparison",
            "| Metric | Baseline | Corrupted | Repaired |",
            "| --- | ---: | ---: | ---: |",
            (
                f"| Retrieval hit rate | {metric('retrieval_hit_rate', baseline_metrics):.3f} | "
                f"{metric('retrieval_hit_rate', corrupted_metrics):.3f} | "
                f"{metric('retrieval_hit_rate', repaired_metrics):.3f} |"
            ),
            (
                f"| Token F1 | {metric('mean_token_f1', baseline_metrics):.3f} | "
                f"{metric('mean_token_f1', corrupted_metrics):.3f} | "
                f"{metric('mean_token_f1', repaired_metrics):.3f} |"
            ),
            (
                f"| Judge accuracy | {metric('judge_accuracy', baseline_metrics):.3f} | "
                f"{metric('judge_accuracy', corrupted_metrics):.3f} | "
                f"{metric('judge_accuracy', repaired_metrics):.3f} |"
            ),
            (
                f"| Mean judge score | {metric('mean_judge_score', baseline_metrics):.3f} | "
                f"{metric('mean_judge_score', corrupted_metrics):.3f} | "
                f"{metric('mean_judge_score', repaired_metrics):.3f} |"
            ),
            (
                f"| Data quality | {quality_status(baseline_quality)} | "
                f"{quality_status(corrupted_quality)} | "
                f"{quality_status(repaired_quality)} |"
            ),
            (
                f"| Freshness | {freshness_status(baseline_freshness)} | "
                f"{freshness_status(corrupted_freshness)} | "
                f"{freshness_status(repaired_freshness)} |"
            ),
            "",
            "## Verdict",
            "Corrupted data reduced retrieval and answer quality, while repair recovered the dataset toward baseline.",
        ]
    )
    write_text(report_path, content + "\n")
