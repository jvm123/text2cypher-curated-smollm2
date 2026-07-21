"""Test-set generation and required per-sample result artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import fmean
from typing import Any

from datasets import Dataset
from tqdm.auto import tqdm

from .execution import ExecutionEvaluator
from .metrics import evaluate_prediction
from .modeling import generate_cypher


def evaluate_dataset(
    model: object,
    tokenizer: object,
    dataset: Dataset,
    output_directory: Path,
    max_new_tokens: int,
    label: str,
    split: str,
    database_reference_alias: str,
    limit: int | None = None,
    execution_evaluator: ExecutionEvaluator | None = None,
) -> tuple[Path, Path]:
    """Generate predictions with progress and save JSONL results incrementally."""
    output_directory.mkdir(parents=True, exist_ok=True)
    results_path = output_directory / f"{label}_results.jsonl"
    summary_path = output_directory / f"{label}_summary.json"
    results: list[dict[str, Any]] = []
    selected_dataset = dataset.select(range(min(limit, len(dataset)))) if limit else dataset

    with results_path.open("w", encoding="utf-8") as file:
        for example in tqdm(selected_dataset, desc="Evaluating", unit="sample"):
            result: dict[str, Any] = {
                "instance_id": example["instance_id"],
                "question": example["question"],
                "schema": example["schema"],
                "reference_cypher": example["cypher"],
                "database_reference_alias": example.get("database_reference_alias"),
            }
            try:
                prediction = generate_cypher(
                    model, tokenizer, example["schema"], example["question"], max_new_tokens
                )
                result["predicted_cypher"] = prediction
                generated_metrics = evaluate_prediction(prediction, example["cypher"])
                generated_metrics["execution_match"] = None
                result["metrics"] = generated_metrics
                result["error"] = None
                if execution_evaluator is not None:
                    result["execution"] = execution_evaluator(
                        example.get("database_reference_alias"), example["cypher"], prediction
                    )
                    result["metrics"]["execution_match"] = result["execution"]["equivalent"]
            except Exception as error:
                result["predicted_cypher"] = ""
                generated_metrics = evaluate_prediction("", example["cypher"])
                generated_metrics["execution_match"] = None
                result["metrics"] = generated_metrics
                result["error"] = f"{type(error).__name__}: {error}"
                if execution_evaluator is not None:
                    result["execution"] = {
                        "status": "skipped",
                        "reason": "generation_error",
                        "equivalent": None,
                    }
            results.append(result)
            file.write(json.dumps(result, ensure_ascii=False) + "\n")
            file.flush()

    metric_names = ("exact_match", "token_precision", "token_recall", "token_f1")
    summary = {
        "label": label,
        "split": split,
        "database_reference_alias": database_reference_alias,
        "limit": limit,
        "num_samples": len(results),
        "generation": {"max_new_tokens": max_new_tokens, "do_sample": False},
        "metrics": {
            name: fmean(float(result["metrics"][name]) for result in results) if results else 0.0
            for name in metric_names
        },
        "failed_generations": sum(result["error"] is not None for result in results),
    }
    if execution_evaluator is not None:
        execution_results = [result["execution"] for result in results]
        evaluated = [
            result for result in execution_results if result["status"] in {"equivalent", "mismatch"}
        ]
        summary["execution"] = {
            "enabled": True,
            "eligible_samples": len(evaluated),
            "skipped_samples": sum(result["status"] == "skipped" for result in execution_results),
            "execution_errors": sum(
                result["status"] in {"reference_error", "prediction_error"}
                for result in execution_results
            ),
            "equivalent_samples": sum(result["equivalent"] is True for result in evaluated),
            "execution_accuracy": (
                fmean(float(result["equivalent"]) for result in evaluated) if evaluated else 0.0
            ),
            "status_counts": {
                status: sum(result["status"] == status for result in execution_results)
                for status in sorted({result["status"] for result in execution_results})
            },
        }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return results_path, summary_path
