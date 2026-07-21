"""Compare every completed baseline and trained evaluation below a runs directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from text2cypher.comparison import (
    build_comparison,
    discover_run_results,
    load_run_results,
    write_comparison_reports,
)


def format_metrics_table(report: dict[str, object]) -> str:
    """Render aggregate lexical metrics for all discovered runs as a CLI table."""
    rows = [
        (
            name,
            f"{summary['metrics']['exact_match']:.4f}",
            f"{summary['metrics']['token_precision']:.4f}",
            f"{summary['metrics']['token_recall']:.4f}",
            f"{summary['metrics']['token_f1']:.4f}",
        )
        for name, summary in report["runs"].items()
    ]
    headers = ("Run", "Exact match", "Precision", "Recall", "F1")
    widths = tuple(
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    )
    separator = "  ".join("-" * width for width in widths)
    lines = [
        "  ".join(
            header.ljust(width) if index == 0 else header.rjust(width)
            for index, (header, width) in enumerate(zip(headers, widths, strict=True))
        ),
        separator,
    ]
    for row in rows:
        lines.append(
            "  ".join(
                value.ljust(width) if index == 0 else value.rjust(width)
                for index, (value, width) in enumerate(zip(row, widths, strict=True))
            )
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("outputs/runs"),
        help="Directory whose immediate children are named training runs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for comparison reports; defaults to <runs-dir>/comparisons.",
    )
    parser.add_argument("--prefix", default="all_runs", help="Comparison report filename prefix.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result_paths = discover_run_results(args.runs_dir)
    report = build_comparison(
        {name: load_run_results(results_path) for name, results_path in result_paths.items()}
    )
    output_directory = args.output_dir or args.runs_dir / "comparisons"
    json_path, markdown_path = write_comparison_reports(report, output_directory, args.prefix)
    print(f"Compared {len(result_paths)} runs.")
    print(format_metrics_table(report))
    print(f"JSON comparison: {json_path}")
    print(f"Markdown comparison: {markdown_path}")


if __name__ == "__main__":
    main()
