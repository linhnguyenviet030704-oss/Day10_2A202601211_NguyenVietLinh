from __future__ import annotations

from typing import Any

from core.utils import now_utc, write_text


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _quality_section(quality: dict[str, Any]) -> list[str]:
    lines = [
        f"- **success**: {quality.get('success')}",
        f"- **row_count**: {quality.get('row_count')}",
        "",
    ]
    for check in quality.get("checks", []):
        status = "PASS" if check.get("success") else "FAIL"
        lines.append(f"  - [{status}] `{check.get('name')}` — {check.get('details')}")
    return lines


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    lines: list[str] = []
    lines.append("# Phase 1 - Baseline Report")
    lines.append("")
    lines.append(f"Generated at: {now_utc().isoformat()}")
    lines.append("")

    lines.append("## Data Source")
    lines.append("")
    for key, value in source_summary.items():
        lines.append(f"- **{key}**: {_fmt(value)}")
    lines.append("")

    lines.append("## Evaluation Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    for key in ("samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        if key in metrics:
            lines.append(f"| {key} | {_fmt(metrics[key])} |")
    lines.append("")

    ragas = metrics.get("ragas")
    if isinstance(ragas, dict):
        lines.append("### Ragas")
        lines.append("")
        for key, value in ragas.items():
            lines.append(f"- **{key}**: {_fmt(value)}")
        lines.append("")

    lines.append("## Data Quality")
    lines.append("")
    lines.extend(_quality_section(quality))
    lines.append("")

    lines.append("## Freshness")
    lines.append("")
    for key, value in freshness.items():
        lines.append(f"- **{key}**: {_fmt(value)}")
    lines.append("")

    write_text(report_path, "\n".join(lines) + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    lines: list[str] = []
    lines.append("# Corruption & Repair Comparison Report")
    lines.append("")
    lines.append(f"Generated at: {now_utc().isoformat()}")
    lines.append("")

    lines.append("## Metrics Comparison")
    lines.append("")
    lines.append("| Metric | Baseline | Corrupted | Repaired |")
    lines.append("| --- | --- | --- | --- |")
    for key in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        b = baseline_metrics.get(key)
        c = corrupted_metrics.get(key)
        r = repaired_metrics.get(key)
        lines.append(f"| {key} | {_fmt(b)} | {_fmt(c)} | {_fmt(r)} |")
    lines.append("")

    lines.append("## Data Quality Comparison")
    lines.append("")
    lines.append("| State | Success | Row Count |")
    lines.append("| --- | --- | --- |")
    lines.append(f"| Corrupted | {corrupted_quality.get('success')} | {corrupted_quality.get('row_count')} |")
    lines.append(f"| Repaired | {repaired_quality.get('success')} | {repaired_quality.get('row_count')} |")
    lines.append("")

    lines.append("## Freshness Comparison")
    lines.append("")
    lines.append("| State | Is Fresh | Stale Rows | Total Rows |")
    lines.append("| --- | --- | --- | --- |")
    lines.append(
        f"| Corrupted | {corrupted_freshness.get('is_fresh')} | {corrupted_freshness.get('stale_rows')} "
        f"| {corrupted_freshness.get('total_rows')} |"
    )
    lines.append(
        f"| Repaired | {repaired_freshness.get('is_fresh')} | {repaired_freshness.get('stale_rows')} "
        f"| {repaired_freshness.get('total_rows')} |"
    )
    lines.append("")

    lines.append("## Analysis")
    lines.append("")
    hit_b = baseline_metrics.get("retrieval_hit_rate")
    hit_c = corrupted_metrics.get("retrieval_hit_rate")
    hit_r = repaired_metrics.get("retrieval_hit_rate")
    if isinstance(hit_b, (int, float)) and isinstance(hit_c, (int, float)):
        lines.append(f"- Retrieval hit rate dropped by {hit_b - hit_c:.4f} from baseline to corrupted data.")
    if isinstance(hit_r, (int, float)) and isinstance(hit_c, (int, float)):
        lines.append(f"- Retrieval hit rate recovered by {hit_r - hit_c:.4f} after repair.")
    f1_b = baseline_metrics.get("mean_token_f1")
    f1_c = corrupted_metrics.get("mean_token_f1")
    f1_r = repaired_metrics.get("mean_token_f1")
    if isinstance(f1_b, (int, float)) and isinstance(f1_c, (int, float)):
        lines.append(f"- Mean token F1 dropped by {f1_b - f1_c:.4f} from baseline to corrupted data.")
    if isinstance(f1_r, (int, float)) and isinstance(f1_c, (int, float)):
        lines.append(f"- Mean token F1 recovered by {f1_r - f1_c:.4f} after repair.")
    lines.append("")

    write_text(report_path, "\n".join(lines) + "\n")
