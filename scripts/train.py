"""Fine-tune SmolLM2 on the curated Text-to-Cypher training split."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from text2cypher.config import get_settings
from text2cypher.data import filter_compilable_cypher, load_text2cypher_dataset
from text2cypher.execution import Neo4jCypherValidator
from text2cypher.modeling import load_model, load_tokenizer
from text2cypher.runtime import configure_cpu
from text2cypher.training import TrainingConfig, resolve_use_cpu, train_model


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=settings.output_dir / "model")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Training device; auto uses CUDA when PyTorch reports it is available.",
    )
    parser.add_argument(
        "--validation-uri",
        default=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        help="Bolt URI used to compile every training and validation Cypher target.",
    )
    parser.add_argument(
        "--validation-user",
        default=os.getenv("NEO4J_USER", "neo4j"),
        help="Neo4j user used for mandatory Cypher compilation validation.",
    )
    parser.add_argument(
        "--validation-password",
        default=os.getenv("NEO4J_PASSWORD", "password"),
        help="Neo4j password used for mandatory Cypher compilation validation.",
    )
    parser.add_argument(
        "--validation-timeout",
        type=float,
        default=float(os.getenv("NEO4J_VALIDATION_TIMEOUT", "10")),
        help="Positive per-query Neo4j compilation timeout in seconds.",
    )
    parser.add_argument(
        "--syntax-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Compile Cypher targets with Neo4j before training (default: enabled).",
    )
    args = parser.parse_args()
    if args.validation_timeout <= 0:
        parser.error("--validation-timeout must be positive.")
    return args


def write_run_config(
    output_directory: Path,
    args: argparse.Namespace,
    settings: object,
    validation: dict[str, object],
) -> Path:
    """Persist reproducible, non-sensitive parameters with a trained model."""
    output_directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "training": {
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "gradient_accumulation_steps": args.gradient_accumulation_steps,
            "learning_rate": args.learning_rate,
            "max_steps": args.max_steps,
            "device": args.device,
            "syntax_check": args.syntax_check,
        },
        "runtime": {
            "model_id": settings.model_id,
            "dataset_id": settings.dataset_id,
            "torch_threads": settings.torch_threads,
            "seed": settings.seed,
        },
        "cypher_validation": validation,
    }
    config_path = output_directory / "run_config.json"
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path


def main() -> None:
    args = parse_args()
    settings = get_settings()
    configure_cpu(settings.torch_threads, settings.seed)
    dataset = load_text2cypher_dataset(settings.dataset_id)
    validation: dict[str, object] = {"enabled": args.syntax_check}
    if args.syntax_check:
        validator = Neo4jCypherValidator(
            args.validation_uri,
            args.validation_user,
            args.validation_password,
            args.validation_timeout,
        )
        try:
            train_dataset, train_report = filter_compilable_cypher(
                dataset["train"], validator.validate
            )
            val_dataset, val_report = filter_compilable_cypher(dataset["val"], validator.validate)
        finally:
            validator.close()
        validation.update(
            {
                "timeout_seconds": args.validation_timeout,
                "uri": args.validation_uri,
                "user": args.validation_user,
                "train": {
                    "accepted": train_report.accepted,
                    "rejected": train_report.rejected,
                    "rejection_reasons": train_report.rejection_reasons,
                },
                "val": {
                    "accepted": val_report.accepted,
                    "rejected": val_report.rejected,
                    "rejection_reasons": val_report.rejection_reasons,
                },
            }
        )
        print(
            "Cypher validation: "
            f"train accepted={train_report.accepted}, rejected={train_report.rejected}; "
            f"val accepted={val_report.accepted}, rejected={val_report.rejected}."
        )
    else:
        train_dataset, val_dataset = dataset["train"], dataset["val"]
        print("Cypher validation: disabled.")
    config_path = write_run_config(args.output_dir, args, settings, validation)
    tokenizer = load_tokenizer(settings.model_id)
    model = load_model(settings.model_id)
    use_cpu = resolve_use_cpu(args.device)
    config = TrainingConfig(
        output_dir=args.output_dir,
        epochs=args.epochs,
        train_batch_size=args.batch_size,
        eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        max_steps=args.max_steps,
        use_cpu=use_cpu,
    )
    print(f"Training device: {'CPU' if use_cpu else 'CUDA'}")
    trainer = train_model(model, tokenizer, train_dataset, val_dataset, config)
    print(f"Training complete. Best checkpoint: {trainer.state.best_model_checkpoint}")
    print(f"Final model saved to: {args.output_dir}")
    print(f"Run parameters: {config_path}")
    print(f"Loss curve: {args.output_dir / 'loss_curve.png'}")


if __name__ == "__main__":
    main()
