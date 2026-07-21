"""Evaluate a base or fine-tuned Text-to-Cypher model on the test split."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from text2cypher.config import get_settings
from text2cypher.data import filter_database_reference_alias, load_text2cypher_dataset
from text2cypher.evaluation import evaluate_dataset
from text2cypher.execution import GRAPH_ALIASES, Neo4jExecutionEvaluator
from text2cypher.modeling import load_model, load_tokenizer
from text2cypher.runtime import configure_cpu


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=settings.model_id, help="Model ID or local checkpoint path.")
    parser.add_argument("--output-dir", type=Path, default=settings.output_dir / "evaluation")
    parser.add_argument("--label", default="test")
    parser.add_argument(
        "--split",
        choices=("train", "val", "test"),
        default="test",
        help="Dataset split to evaluate.",
    )
    parser.add_argument(
        "--database-reference-alias",
        choices=("any", "set", "unset"),
        default="any",
        help="Filter examples by whether database_reference_alias is populated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Evaluate at most this many filtered examples; intended for smoke tests.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Compare safe read-only queries on the selected locally imported graph.",
    )
    parser.add_argument(
        "--execution-graph",
        choices=tuple(GRAPH_ALIASES),
        help="Graph currently loaded by make neo4j-import GRAPH=<graph>; required with --execute.",
    )
    parser.add_argument(
        "--execution-uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Bolt URI for opt-in execution evaluation.",
    )
    parser.add_argument(
        "--execution-user",
        default=os.getenv("NEO4J_USER", "neo4j"),
        help="Neo4j user for opt-in execution evaluation.",
    )
    parser.add_argument(
        "--execution-password",
        default=os.getenv("NEO4J_PASSWORD", "password"),
        help="Neo4j password for opt-in execution evaluation.",
    )
    parser.add_argument(
        "--execution-timeout",
        type=float,
        default=10.0,
        help="Per-query Neo4j timeout in seconds when --execute is set.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1.")
    if args.execute != (args.execution_graph is not None):
        parser.error("--execute and --execution-graph must be supplied together.")
    if args.execution_timeout <= 0:
        parser.error("--execution-timeout must be positive.")
    return args


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_cpu(settings.torch_threads, settings.seed)
    dataset = load_text2cypher_dataset(settings.dataset_id)
    selected_dataset = filter_database_reference_alias(
        dataset[args.split], args.database_reference_alias
    )
    tokenizer = load_tokenizer(args.model)
    model = load_model(args.model)
    evaluator = None
    if args.execute:
        evaluator = Neo4jExecutionEvaluator(
            args.execution_uri,
            args.execution_user,
            args.execution_password,
            args.execution_graph,
            args.execution_timeout,
        )
    try:
        results_path, summary_path = evaluate_dataset(
            model,
            tokenizer,
            selected_dataset,
            args.output_dir,
            settings.max_new_tokens,
            args.label,
            args.split,
            args.database_reference_alias,
            args.limit,
            evaluator.evaluate if evaluator else None,
        )
    finally:
        if evaluator is not None:
            evaluator.close()
    print(
        f"Evaluated {len(selected_dataset)} examples from {args.split} "
        f"with database_reference_alias={args.database_reference_alias}."
    )
    print(f"Per-sample results: {results_path}")
    print(f"Aggregate summary: {summary_path}")


if __name__ == "__main__":
    main()
