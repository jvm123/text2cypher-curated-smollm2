import json

import pytest

from text2cypher.comparison import (
    build_comparison,
    discover_run_results,
    load_run_results,
    write_comparison_reports,
)


def _result(instance_id: str, exact_match: bool, token_f1: float) -> dict[str, object]:
    return {
        "instance_id": instance_id,
        "metrics": {
            "exact_match": exact_match,
            "token_precision": token_f1,
            "token_recall": token_f1,
            "token_f1": token_f1,
        },
        "error": None,
    }


def _write_run(tmp_path, name: str, results: list[dict[str, object]]):
    results_path = tmp_path / name / "evaluation" / "trained_results.jsonl"
    results_path.parent.mkdir(parents=True)
    results_path.write_text("\n".join(json.dumps(result) for result in results) + "\n")
    return results_path


def _write_baseline(tmp_path, name: str, results: list[dict[str, object]]):
    results_path = tmp_path / name / "evaluation" / "baseline_results.jsonl"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text("\n".join(json.dumps(result) for result in results) + "\n")
    return results_path


def test_comparison_discovers_all_runs_and_calculates_pairwise_changes(tmp_path) -> None:
    _write_run(tmp_path, "without_check", [_result("one", False, 0.2), _result("two", True, 1.0)])
    _write_run(tmp_path, "with_check", [_result("one", True, 0.8), _result("two", True, 1.0)])
    _write_run(tmp_path, "later", [_result("one", True, 0.9), _result("two", False, 0.3)])
    _write_baseline(tmp_path, "with_check", [_result("one", False, 0.1), _result("two", False, 0.2)])

    paths = discover_run_results(tmp_path)
    report = build_comparison({name: load_run_results(path) for name, path in paths.items()})

    assert set(report["runs"]) == {
        "later (trained)",
        "with_check (baseline)",
        "with_check (trained)",
        "without_check (trained)",
    }
    assert len(report["pairwise_comparisons"]) == 6
    comparison = next(
        item
        for item in report["pairwise_comparisons"]
        if item["left_run"] == "with_check (trained)"
        and item["right_run"] == "without_check (trained)"
    )
    assert comparison["exact_match_transitions"] == {
        "match_to_match": 1,
        "match_to_non_match": 1,
    }

    json_path, markdown_path = write_comparison_reports(report, tmp_path / "comparison")
    assert json.loads(json_path.read_text())["runs"]["with_check (baseline)"]["samples"] == 2
    assert "Pairwise changes" in markdown_path.read_text()


def test_comparison_requires_multiple_runs(tmp_path) -> None:
    _write_run(tmp_path, "only", [_result("one", True, 1.0)])

    with pytest.raises(ValueError, match="at least two"):
        discover_run_results(tmp_path)
