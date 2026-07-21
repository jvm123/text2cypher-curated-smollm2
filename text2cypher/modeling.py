"""Model loading and deterministic Text-to-Cypher generation."""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .prompts import generation_prompt


def load_tokenizer(model_id: str):
    """Load a tokenizer and ensure it supports batched causal-LM padding."""
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def load_model(model_id: str):
    """Load a causal language model in CPU-compatible float32 precision."""
    return AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float32)


def generate_cypher(
    model: object,
    tokenizer: object,
    schema: str,
    question: str,
    max_new_tokens: int,
) -> str:
    """Generate a deterministic assistant completion and return only new tokens."""
    prompt = generation_prompt(tokenizer, schema, question)
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    device = next(model.parameters()).device
    inputs = {name: value.to(device) for name, value in inputs.items()}
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    completion_ids = generated[0, inputs["input_ids"].shape[1] :]
    return tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
