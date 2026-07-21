"""Dependency-free lexical metrics for generated Cypher queries."""

from __future__ import annotations

import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?|<=|>=|<>|!=|[-+*/=<>(),.:{}\[\]]")


def normalize_cypher(query: str) -> str:
    """Normalize whitespace and terminal semicolons for exact-match comparison."""
    return " ".join(query.strip().rstrip(";").split())


def cypher_tokens(query: str) -> list[str]:
    """Tokenize Cypher conservatively for a transparent lexical metric."""
    return [token.lower() for token in TOKEN_PATTERN.findall(normalize_cypher(query))]


def token_prf(prediction: str, reference: str) -> dict[str, float]:
    """Compute multiset token precision, recall, and F1."""
    predicted = Counter(cypher_tokens(prediction))
    expected = Counter(cypher_tokens(reference))
    overlap = sum((predicted & expected).values())
    predicted_count = sum(predicted.values())
    expected_count = sum(expected.values())
    precision = overlap / predicted_count if predicted_count else 0.0
    recall = overlap / expected_count if expected_count else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"token_precision": precision, "token_recall": recall, "token_f1": f1}


def evaluate_prediction(prediction: str, reference: str) -> dict[str, bool | float]:
    """Return per-example lexical metrics."""
    return {
        "exact_match": normalize_cypher(prediction) == normalize_cypher(reference),
        **token_prf(prediction, reference),
    }
