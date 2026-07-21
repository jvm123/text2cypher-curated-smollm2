"""Validate the configured Text-to-Cypher model, dataset, and Neo4j service."""

from __future__ import annotations

import argparse
import os
import sys

from neo4j import GraphDatabase

from text2cypher.config import get_settings
from text2cypher.data import (
    database_reference_counts,
    dataset_stats,
    load_text2cypher_dataset,
)
from text2cypher.metrics import evaluate_prediction
from text2cypher.modeling import generate_cypher, load_model, load_tokenizer
from text2cypher.runtime import configure_cpu

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
SMOKE_SPLIT = os.getenv("HF_SMOKE_SPLIT", "test")
SMOKE_INDEX = int(os.getenv("HF_SMOKE_INDEX", "0"))


def parse_args() -> argparse.Namespace:
    """Parse optional model selection for base-model or checkpoint smoke tests."""
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default=settings.model_id,
        help="Hugging Face model ID or local checkpoint directory.",
    )
    return parser.parse_args()


def heading(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def verify_generation(model_id: str) -> None:
    settings = get_settings()
    configure_cpu(settings.torch_threads, settings.seed)
    heading("Model and dataset")
    dataset = load_text2cypher_dataset(settings.dataset_id)
    if SMOKE_SPLIT not in dataset:
        raise ValueError(f"HF_SMOKE_SPLIT must name a dataset split; received '{SMOKE_SPLIT}'.")
    if not 0 <= SMOKE_INDEX < len(dataset[SMOKE_SPLIT]):
        raise IndexError(f"HF_SMOKE_INDEX {SMOKE_INDEX} is outside split '{SMOKE_SPLIT}'.")
    example = dataset[SMOKE_SPLIT][SMOKE_INDEX]
    tokenizer = load_tokenizer(model_id)
    model = load_model(model_id)
    prediction = generate_cypher(
        model,
        tokenizer,
        example["schema"],
        example["question"],
        settings.max_new_tokens,
    )
    print(f"Model: {model_id}")
    print(f"Dataset: {settings.dataset_id}")
    print(f"Split sizes: {dataset_stats(dataset)}")
    print("Test-set database reference aliases:")
    for alias, sample_count in database_reference_counts(dataset["test"]).items():
        print(f"  {alias}: {sample_count}")
    print(f"Sample: {SMOKE_SPLIT}[{SMOKE_INDEX}]: {example}")
    print(f"Question: {example['question']}")
    print(f"Reference Cypher: {example['cypher']}")
    print(f"Generated Cypher: {prediction}")
    print(
        "Evaluation of ground truth vs. ground truth: "
        f"{evaluate_prediction(example['cypher'], example['cypher'])}"
    )
    print(
        "Evaluation of generated Cypher vs. ground truth: "
        f"{evaluate_prediction(prediction, example['cypher'])}"
    )


def verify_neo4j() -> None:
    heading("Neo4j")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            record = session.run("RETURN 1 AS connection_check").single(strict=True)
        print(f"Neo4j URI: {NEO4J_URI}")
        print(f"Connection query result: {record['connection_check']}")
    finally:
        driver.close()


def main() -> None:
    args = parse_args()
    try:
        verify_generation(args.model)
        verify_neo4j()
    except Exception as error:
        print(f"Smoke test failed ({type(error).__name__}): {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print("\nSmoke test completed successfully.")


if __name__ == "__main__":
    main()
