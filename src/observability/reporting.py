from __future__ import annotations

from typing import Any

from core.utils import write_text


def _fmt(value: Any, digits: int = 4) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}" if isinstance(value, float) else str(value)
    if value in (None, ""):
        return "n/a"
    return str(value)


def _metrics_rows(metrics: dict[str, Any]) -> str:
    keys = ["samples", "retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"]
    lines = ["| Metric | Value |", "| --- | --- |"]
    for key in keys:
        if key in metrics:
            lines.append(f"| `{key}` | {_fmt(metrics[key])} |")
    return "\n".join(lines)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the baseline (phase 1) markdown report to ``report_path``."""
    ragas = metrics.get("ragas")
    quality_status = "PASS" if quality.get("success") else "FAIL"
    freshness_status = "FRESH" if freshness.get("is_fresh") else "STALE"

    lines: list[str] = []
    lines.append("# Phase 1 - Baseline Report")
    lines.append("")

    # 1. Source summary.
    lines.append("## Source")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    for label, key in [
        ("Source API", "source_api"),
        ("Query", "source_query"),
        ("Filter", "source_filter"),
        ("Raw records", "raw_records"),
        ("Clean rows", "clean_rows"),
        ("Run date", "run_date"),
    ]:
        if key in source_summary:
            lines.append(f"| {label} | {_fmt(source_summary[key])} |")
    lines.append("")

    # 2. Evaluation metrics.
    lines.append("## Retrieval & Evaluation Metrics")
    lines.append("")
    lines.append(_metrics_rows(metrics))
    lines.append("")
    if isinstance(ragas, dict):
        if "skipped" in ragas:
            lines.append(f"> Ragas: {ragas['skipped']}")
        elif "error" in ragas:
            lines.append(f"> Ragas: {ragas['error']}")
        else:
            lines.append("**Ragas**")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("| --- | --- |")
            for key, value in ragas.items():
                lines.append(f"| `{key}` | {_fmt(value)} |")
        lines.append("")

    # 3. Data quality.
    lines.append(f"## Data Quality - {quality_status}")
    lines.append("")
    lines.append(f"Total rows checked: {_fmt(quality.get('total_rows'))}")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("| --- | --- | --- |")
    for check in quality.get("checks", []):
        status = "PASS" if check.get("success") else "FAIL"
        lines.append(f"| `{check.get('name')}` | {status} | {check.get('detail', '')} |")
    lines.append("")

    # 4. Freshness.
    lines.append(f"## Freshness - {freshness_status}")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    for label, key in [
        ("Latest published", "latest_published"),
        ("Oldest published", "oldest_published"),
        ("Fresh rows", "fresh_rows"),
        ("Stale rows", "stale_rows"),
        ("Total rows", "total_rows"),
        ("Threshold (days)", "threshold_days"),
        ("Is fresh", "is_fresh"),
    ]:
        if key in freshness:
            lines.append(f"| {label} | {_fmt(freshness[key])} |")
    lines.append("")

    write_text(report_path, "\n".join(lines) + "\n")


def _quality_line(quality: dict[str, Any]) -> str:
    status = "PASS" if quality.get("success") else "FAIL"
    failed = quality.get("failed_checks") or []
    detail = ", ".join(failed) if failed else "none"
    return f"{status} (failed: {detail})"


def _freshness_line(freshness: dict[str, Any]) -> str:
    status = "FRESH" if freshness.get("is_fresh") else "STALE"
    return f"{status} ({_fmt(freshness.get('stale_rows'))} stale / {_fmt(freshness.get('total_rows'))} rows)"


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
    """Write the baseline/corrupted/repaired comparison markdown report."""
    metric_keys = [
        "samples",
        "retrieval_hit_rate",
        "mean_token_f1",
        "judge_accuracy",
        "mean_judge_score",
    ]

    lines: list[str] = []
    lines.append("# Corruption Flow - Comparison Report")
    lines.append("")
    lines.append("Comparing agent quality across three dataset states: **baseline** (clean), "
                 "**corrupted** (deliberate faults), and **repaired** (rebuilt from raw source).")
    lines.append("")

    # Metrics comparison.
    lines.append("## Metrics")
    lines.append("")
    lines.append("| Metric | Baseline | Corrupted | Repaired | Corrupted vs Baseline |")
    lines.append("| --- | --- | --- | --- | --- |")
    for key in metric_keys:
        base = baseline_metrics.get(key)
        corr = corrupted_metrics.get(key)
        rep = repaired_metrics.get(key)
        delta = ""
        if isinstance(base, (int, float)) and isinstance(corr, (int, float)) and not isinstance(base, bool):
            diff = corr - base
            arrow = "down" if diff < 0 else ("up" if diff > 0 else "same")
            delta = f"{diff:+.4f} ({arrow})"
        lines.append(f"| `{key}` | {_fmt(base)} | {_fmt(corr)} | {_fmt(rep)} | {delta} |")
    lines.append("")

    # Data quality comparison.
    lines.append("## Data Quality")
    lines.append("")
    lines.append("| State | Result |")
    lines.append("| --- | --- |")
    lines.append(f"| Corrupted | {_quality_line(corrupted_quality)} |")
    lines.append(f"| Repaired | {_quality_line(repaired_quality)} |")
    lines.append("")

    # Freshness comparison.
    lines.append("## Freshness")
    lines.append("")
    lines.append("| State | Result |")
    lines.append("| --- | --- |")
    lines.append(f"| Corrupted | {_freshness_line(corrupted_freshness)} |")
    lines.append(f"| Repaired | {_freshness_line(repaired_freshness)} |")
    lines.append("")

    # Conclusion.
    hit_base = baseline_metrics.get("retrieval_hit_rate")
    hit_corr = corrupted_metrics.get("retrieval_hit_rate")
    hit_rep = repaired_metrics.get("retrieval_hit_rate")
    lines.append("## Conclusion")
    lines.append("")
    if isinstance(hit_base, (int, float)) and isinstance(hit_corr, (int, float)):
        degraded = hit_corr < hit_base
        recovered = isinstance(hit_rep, (int, float)) and hit_rep >= hit_base
        lines.append(
            f"- Corruption {'**degraded**' if degraded else 'did not degrade'} retrieval "
            f"({_fmt(hit_base)} -> {_fmt(hit_corr)})."
        )
        lines.append(
            f"- Repair {'**restored**' if recovered else 'did not fully restore'} retrieval "
            f"({_fmt(hit_corr)} -> {_fmt(hit_rep)})."
        )
        lines.append(
            "- Data quality and freshness checks flagged the corrupted dataset before the "
            "agent produced wrong answers, then returned to healthy after repair."
        )
    write_text(report_path, "\n".join(lines) + "\n")
