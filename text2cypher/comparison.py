"""Aggregate and pairwise comparison of completed evaluation runs."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Any

METRIC_NAMES = ("exact_match", "token_precision", "token_recall", "token_f1")


def load_run_results(results_path: Path) -> list[dict[str, Any]]:
    """Load evaluation JSONL and validate the fields used for run comparison."""
    try:
        lines = results_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Unable to read evaluation results at {results_path}: {error}") from error

    results: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            result = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Malformed JSON in {results_path} on line {line_number}.") from error
        if not isinstance(result, dict) or "instance_id" not in result or "metrics" not in result:
            raise ValueError(f"Missing comparison fields in {results_path} on line {line_number}.")
        if not isinstance(result["metrics"], dict) or any(
            name not in result["metrics"] for name in METRIC_NAMES
        ):
            raise ValueError(f"Missing metrics in {results_path} on line {line_number}.")
        results.append(result)
    if not results:
        raise ValueError(f"No evaluation results found at {results_path}.")
    return results


def discover_run_results(runs_directory: Path) -> dict[str, Path]:
    """Find baseline and trained evaluation artifacts for each named run."""
    discovered = {}
    for results_path in sorted(runs_directory.glob("*/evaluation/*_results.jsonl")):
        label = results_path.stem.removesuffix("_results")
        if label not in {"baseline", "trained"}:
            continue
        run_name = results_path.parent.parent.name
        discovered[f"{run_name} ({label})"] = results_path
    if len(discovered) < 2:
        raise ValueError(f"Expected at least two completed runs below {runs_directory}.")
    return discovered


def build_comparison(run_results: dict[str, list[dict[str, Any]]]) -> dict[str, object]:
    """Build aggregate metrics and every pairwise comparison across named runs."""
    runs = {
        name: _aggregate_run(results)
        for name, results in sorted(run_results.items())
    }
    comparisons = [
        _compare_pair(left_name, run_results[left_name], right_name, run_results[right_name])
        for index, left_name in enumerate(sorted(run_results))
        for right_name in sorted(run_results)[index + 1 :]
    ]
    return {"runs": runs, "pairwise_comparisons": comparisons}


def write_comparison_reports(
    report: dict[str, object], output_directory: Path, prefix: str = "all_runs"
) -> tuple[Path, Path]:
    """Write machine-readable and Markdown reports for all discovered runs."""
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / f"{prefix}_comparison.json"
    markdown_path = output_directory / f"{prefix}_comparison.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, markdown_path


def _aggregate_run(results: list[dict[str, Any]]) -> dict[str, object]:
    return {
        "samples": len(results),
        "failed_generations": sum(result.get("error") is not None for result in results),
        "metrics": {
            name: fmean(float(result["metrics"][name]) for result in results)
            for name in METRIC_NAMES
        },
    }


def _compare_pair(
    left_name: str,
    left_results: list[dict[str, Any]],
    right_name: str,
    right_results: list[dict[str, Any]],
) -> dict[str, object]:
    left_by_id = {str(result["instance_id"]): result for result in left_results}
    right_by_id = {str(result["instance_id"]): result for result in right_results}
    shared_ids = sorted(left_by_id.keys() & right_by_id.keys())
    if not shared_ids:
        raise ValueError(f"Runs '{left_name}' and '{right_name}' have no shared instance IDs.")

    metric_deltas = {
        name: fmean(
            float(right_by_id[instance_id]["metrics"][name])
            - float(left_by_id[instance_id]["metrics"][name])
            for instance_id in shared_ids
        )
        for name in METRIC_NAMES
    }
    exact_match_changes = Counter(
        _exact_match_transition(left_by_id[instance_id], right_by_id[instance_id])
        for instance_id in shared_ids
    )
    return {
        "left_run": left_name,
        "right_run": right_name,
        "shared_samples": len(shared_ids),
        "only_left_samples": len(left_by_id.keys() - right_by_id.keys()),
        "only_right_samples": len(right_by_id.keys() - left_by_id.keys()),
        "right_minus_left_metrics": metric_deltas,
        "exact_match_transitions": dict(sorted(exact_match_changes.items())),
    }


def _exact_match_transition(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_match = bool(left["metrics"]["exact_match"])
    right_match = bool(right["metrics"]["exact_match"])
    return f"{'match' if left_match else 'non_match'}_to_{'match' if right_match else 'non_match'}"


def _render_markdown(report: dict[str, object]) -> str:
    runs = report["runs"]
    comparisons = report["pairwise_comparisons"]
    lines = [
        "# Evaluation Run Comparison",
        "",
        "## Aggregate metrics",
        "",
        "| Run | Samples | Exact match | Token precision | Token recall | Token F1 | Failed generations |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, summary in runs.items():
        metrics = summary["metrics"]
        lines.append(
            f"| {name} | {summary['samples']} | {metrics['exact_match']:.4f} | "
            f"{metrics['token_precision']:.4f} | {metrics['token_recall']:.4f} | "
            f"{metrics['token_f1']:.4f} | {summary['failed_generations']} |"
        )
    lines.extend(["", "## Pairwise changes", ""])
    for comparison in comparisons:
        deltas = comparison["right_minus_left_metrics"]
        transitions = comparison["exact_match_transitions"]
        lines.extend(
            [
                f"### {comparison['right_run']} minus {comparison['left_run']}",
                "",
                f"Shared samples: {comparison['shared_samples']}",
                "",
                "| Exact-match change | Token F1 change | New matches | Lost matches |",
                "| ---: | ---: | ---: | ---: |",
                f"| {deltas['exact_match']:+.4f} | {deltas['token_f1']:+.4f} | "
                f"{transitions.get('non_match_to_match', 0)} | {transitions.get('match_to_non_match', 0)} |",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitation",
            "",
            "These comparisons measure lexical metrics. A lexical gain does not by itself establish execution or semantic equivalence.",
            "",
        ]
    )
    return "\n".join(lines)
