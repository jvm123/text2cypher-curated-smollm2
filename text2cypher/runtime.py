"""CPU and reproducibility setup."""

from __future__ import annotations

import torch
from transformers import set_seed


def configure_cpu(threads: int, seed: int) -> None:
    """Limit PyTorch CPU parallelism and initialize deterministic random seeds."""
    torch.set_num_threads(threads)
    set_seed(seed)
