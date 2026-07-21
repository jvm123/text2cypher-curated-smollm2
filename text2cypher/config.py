"""Runtime configuration from command-line defaults and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import DATASET_ID, MODEL_ID


def environment_int(name: str, default: int) -> int:
    """Return a positive integer environment setting."""
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be at least 1.")
    return value


@dataclass(frozen=True)
class RuntimeSettings:
    """Settings shared by training, evaluation, and the smoke test."""

    model_id: str = os.getenv("HF_MODEL_ID", MODEL_ID)
    dataset_id: str = os.getenv("HF_DATASET_ID", DATASET_ID)
    torch_threads: int = environment_int("TORCH_NUM_THREADS", 4)
    seed: int = environment_int("SEED", 42)
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    max_new_tokens: int = environment_int("MAX_NEW_TOKENS", 256)


def get_settings() -> RuntimeSettings:
    """Construct settings after validating environment-derived values."""
    return RuntimeSettings()
