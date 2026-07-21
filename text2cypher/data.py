"""Dataset loading, validation, and completion-only tokenization."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable

from datasets import Dataset, DatasetDict, load_dataset

from .prompts import generation_prompt

REQUIRED_COLUMNS = frozenset({"question", "schema", "cypher", "instance_id"})
REQUIRED_SPLITS = frozenset({"train", "val", "test"})
CypherValidator = Callable[[str], str | None]


@dataclass(frozen=True)
class CypherValidationReport:
    """Counts produced while removing Cypher targets Neo4j cannot compile."""

    accepted: int
    rejected: int
    rejection_reasons: dict[str, int]


def load_text2cypher_dataset(dataset_id: str) -> DatasetDict:
    """Load and validate all curated Text-to-Cypher splits."""
    dataset = load_dataset(dataset_id, trust_remote_code=False)
    missing_splits = REQUIRED_SPLITS - set(dataset)
    if missing_splits:
        raise ValueError(f"Dataset is missing required splits: {sorted(missing_splits)}")
    for split in REQUIRED_SPLITS:
        missing_columns = REQUIRED_COLUMNS - set(dataset[split].column_names)
        if missing_columns:
            raise ValueError(
                f"Dataset split '{split}' is missing required columns: "
                f"{sorted(missing_columns)}"
            )
    return dataset


def tokenize_for_training(dataset: Dataset, tokenizer: object) -> Dataset:
    """Build causal-LM examples with labels masked over prompt tokens."""
    eos_token = tokenizer.eos_token or ""

    def tokenize_example(example: dict[str, str]) -> dict[str, list[int]]:
        prompt = generation_prompt(tokenizer, example["schema"], example["question"])
        prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
        target_ids = tokenizer(example["cypher"] + eos_token, add_special_tokens=False)["input_ids"]
        input_ids = prompt_ids + target_ids
        labels = [-100] * len(prompt_ids) + target_ids
        return {"input_ids": input_ids, "attention_mask": [1] * len(input_ids), "labels": labels}

    tokenized = dataset.map(tokenize_example, remove_columns=dataset.column_names)
    return tokenized.filter(lambda example: any(label != -100 for label in example["labels"]))


def filter_compilable_cypher(
    dataset: Dataset, validator: CypherValidator
) -> tuple[Dataset, CypherValidationReport]:
    """Retain only examples whose reference Cypher compiles through Neo4j."""
    if "cypher" not in dataset.column_names:
        raise ValueError("Dataset has no 'cypher' column to validate.")

    accepted_indices: list[int] = []
    rejection_reasons: Counter[str] = Counter()
    for index, query in enumerate(dataset["cypher"]):
        reason = validator(query)
        if reason is None:
            accepted_indices.append(index)
        else:
            rejection_reasons[reason] += 1

    if not accepted_indices:
        raise ValueError("Neo4j rejected every Cypher training example.")
    accepted = dataset.select(accepted_indices)
    report = CypherValidationReport(
        accepted=len(accepted),
        rejected=len(dataset) - len(accepted),
        rejection_reasons=dict(sorted(rejection_reasons.items())),
    )
    return accepted, report


def dataset_stats(dataset: DatasetDict, splits: Iterable[str] = REQUIRED_SPLITS) -> dict[str, int]:
    """Return the number of samples in each requested split."""
    return {split: len(dataset[split]) for split in splits}


def database_reference_counts(dataset: Dataset) -> dict[str, int]:
    """Return sorted sample counts by database reference alias."""
    if "database_reference_alias" not in dataset.column_names:
        raise ValueError("Dataset has no 'database_reference_alias' column to count.")

    aliases = (
        alias.strip()
        if isinstance(alias, str) and alias.strip()
        else "<unset>"
        for alias in dataset["database_reference_alias"]
    )
    return dict(sorted(Counter(aliases).items()))


def filter_database_reference_alias(dataset: Dataset, state: str) -> Dataset:
    """Select examples with any, set, or unset database reference aliases."""
    if state == "any":
        return dataset
    if state not in {"set", "unset"}:
        raise ValueError("Alias state must be one of: any, set, unset.")
    if "database_reference_alias" not in dataset.column_names:
        raise ValueError("Dataset has no 'database_reference_alias' column to filter.")

    def has_alias(example: dict[str, object]) -> bool:
        alias = example["database_reference_alias"]
        return isinstance(alias, str) and bool(alias.strip())

    return dataset.filter(lambda example: has_alias(example) == (state == "set"))
