"""Full CPU fine-tuning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib
import torch
from transformers import DataCollatorForTokenClassification, Trainer, TrainingArguments

from .data import tokenize_for_training

matplotlib.use("Agg")


def save_loss_curve(trainer: Trainer, output_dir: Path) -> Path:
    """Save training and validation loss from the Trainer log history as a PNG."""
    import matplotlib.pyplot as plt

    train_points = [
        (entry["step"], entry["loss"])
        for entry in trainer.state.log_history
        if "loss" in entry and "step" in entry
    ]
    validation_points = [
        (entry["step"], entry["eval_loss"])
        for entry in trainer.state.log_history
        if "eval_loss" in entry and "step" in entry
    ]
    if not train_points and not validation_points:
        raise ValueError("Trainer history does not contain loss values.")

    figure, axes = plt.subplots(figsize=(8, 5))
    if train_points:
        steps, losses = zip(*train_points, strict=True)
        axes.plot(steps, losses, label="Training loss")
    if validation_points:
        steps, losses = zip(*validation_points, strict=True)
        axes.plot(steps, losses, marker="o", label="Validation loss")
    axes.set(xlabel="Optimizer step", ylabel="Cross-entropy loss", title="Training loss")
    axes.grid(alpha=0.3)
    axes.legend()
    figure.tight_layout()
    curve_path = output_dir / "loss_curve.png"
    figure.savefig(curve_path, dpi=160)
    plt.close(figure)
    return curve_path


@dataclass(frozen=True)
class TrainingConfig:
    """CPU-friendly full fine-tuning hyperparameters."""

    output_dir: Path
    epochs: float = 3.0
    train_batch_size: int = 1
    eval_batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 5e-5
    max_steps: int = -1
    use_cpu: bool = True


def resolve_use_cpu(device: str) -> bool:
    """Resolve a requested training device and reject unavailable CUDA explicitly."""
    if device == "cpu":
        return True
    if device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "CUDA was requested but is unavailable. Install a PyTorch CUDA build "
                "compatible with the installed NVIDIA driver, or use --device cpu."
            )
        return False
    if device == "auto":
        return not torch.cuda.is_available()
    raise ValueError("Device must be one of: auto, cpu, cuda.")


def train_model(model: object, tokenizer: object, train_dataset: object, val_dataset: object, config: TrainingConfig) -> Trainer:
    """Fine-tune every model parameter and persist the selected best checkpoint."""
    output_dir = str(config.output_dir)
    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=config.epochs,
        max_steps=config.max_steps,
        per_device_train_batch_size=config.train_batch_size,
        per_device_eval_batch_size=config.eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        save_total_limit=2,
        report_to="none",
        use_cpu=config.use_cpu,
        fp16=False,
        bf16=False,
        dataloader_num_workers=0,
    )
    collator = DataCollatorForTokenClassification(tokenizer=tokenizer, label_pad_token_id=-100)
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenize_for_training(train_dataset, tokenizer),
        eval_dataset=tokenize_for_training(val_dataset, tokenizer),
        data_collator=collator,
    )
    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    trainer.save_state()
    save_loss_curve(trainer, config.output_dir)
    return trainer
