"""Analyze lexical and static success/failure patterns in evaluation JSONL results."""

from __future__ import annotations

import argparse
from pathlib import Path

from text2cypher.analysis import build_analysis, load_evaluation_results, write_analysis_reports


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="Path to an evaluation results JSONL artifact.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for JSON and Markdown reports; defaults to the results directory.",
    )
    parser.add_argument(
        "--prefix",
        help="Report filename prefix; defaults to the input filename without '_results'.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=5,
        help="Maximum representative examples per report group (default: 5).",
    )
    args = parser.parse_args()
    if args.max_examples < 1:
        parser.error("--max-examples must be at least 1.")
    return args


def default_prefix(results_path: Path) -> str:
    """Derive a display-safe report prefix from the standard evaluation artifact name."""
    stem = results_path.stem
    return stem.removesuffix("_results") or stem


def main() -> None:
    args = parse_args()
    results = load_evaluation_results(args.results)
    report = build_analysis(results, args.results, args.max_examples)
    output_directory = args.output_dir or args.results.parent
    prefix = args.prefix or default_prefix(args.results)
    json_path, markdown_path = write_analysis_reports(report, output_directory, prefix)
    outcomes = report["outcomes"]
    exact_matches = outcomes.get("exact_lexical_match", {}).get("count", 0)
    print(f"Analyzed {len(results)} evaluation results.")
    print(f"Exact lexical matches: {exact_matches}/{len(results)}")
    print(f"JSON analysis: {json_path}")
    print(f"Markdown analysis: {markdown_path}")


if __name__ == "__main__":
    main()
