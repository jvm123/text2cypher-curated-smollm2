"""Offline lexical and static analysis for evaluation JSONL artifacts."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metrics import cypher_tokens, normalize_cypher

CYPHER_CLAUSES = (
    "OPTIONAL MATCH",
    "MATCH",
    "WHERE",
    "WITH",
    "RETURN",
    "ORDER BY",
    "LIMIT",
    "SKIP",
    "UNION",
    "CALL",
    "CREATE",
    "MERGE",
    "SET",
    "DELETE",
    "REMOVE",
    "DETACH DELETE",
)
WRITE_CLAUSES = ("CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DETACH DELETE")
SQL_KEYWORDS = ("SELECT", "FROM", "JOIN", "GROUP BY", "HAVING", "INSERT", "UPDATE", "DROP TABLE")
AGGREGATIONS = ("COUNT", "SUM", "AVG", "MIN", "MAX", "COLLECT")
CYPHER_KEYWORDS = frozenset(
    token.lower()
    for clause in CYPHER_CLAUSES
    for token in clause.split()
) | frozenset({"as", "distinct", "and", "or", "not", "in", "is", "null", "true", "false", "case", "when", "then", "else", "end", "exists", "yield", "on"})


@dataclass(frozen=True)
class EvaluationResult:
    """A validated evaluation result loaded from one JSONL line."""

    source_line: int
    instance_id: str
    question: str
    schema: str
    reference_cypher: str
    predicted_cypher: str
    database_reference_alias: str | None
    exact_match: bool
    token_precision: float
    token_recall: float
    token_f1: float
    execution_match: bool | None
    error: str | None


@dataclass(frozen=True)
class ClassifiedResult:
    """Static and lexical classification of one evaluation result."""

    result: EvaluationResult
    outcome: str
    lexical_overlap: str | None
    first_cypher_clause: str | None
    has_markdown_fence: bool
    has_prose_prefix: bool
    has_sql_keywords: bool
    has_write_clause: bool
    reference_features: tuple[str, ...]
    predicted_features: tuple[str, ...]
    omitted_reference_features: tuple[str, ...]
    introduced_features: tuple[str, ...]
    identifier_overlap: dict[str, float | int]


def load_evaluation_results(results_path: Path) -> list[EvaluationResult]:
    """Load and validate evaluation results from a JSONL artifact."""
    results: list[EvaluationResult] = []
    try:
        lines = results_path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ValueError(f"Unable to read evaluation results at {results_path}: {error}") from error

    for source_line, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Malformed JSON in {results_path} on line {source_line}: {error.msg}"
            ) from error
        if not isinstance(payload, dict):
            raise ValueError(f"Expected an object in {results_path} on line {source_line}.")
        results.append(_parse_result(payload, results_path, source_line))
    return results


def _parse_result(payload: dict[str, Any], results_path: Path, source_line: int) -> EvaluationResult:
    required_strings = ("instance_id", "question", "schema", "reference_cypher", "predicted_cypher")
    missing = [field for field in required_strings if field not in payload]
    if missing:
        raise ValueError(
            f"Missing required field(s) {', '.join(missing)} in {results_path} on line {source_line}."
        )
    if not all(isinstance(payload[field], str) for field in required_strings):
        raise ValueError(f"Expected string result fields in {results_path} on line {source_line}.")

    metrics = payload.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError(f"Missing metrics object in {results_path} on line {source_line}.")
    metric_names = ("exact_match", "token_precision", "token_recall", "token_f1")
    missing_metrics = [name for name in metric_names if name not in metrics]
    if missing_metrics:
        raise ValueError(
            f"Missing metric(s) {', '.join(missing_metrics)} in {results_path} on line {source_line}."
        )

    alias = payload.get("database_reference_alias")
    error = payload.get("error")
    execution_match = metrics.get("execution_match")
    if alias is not None and not isinstance(alias, str):
        raise ValueError(f"Expected a string or null alias in {results_path} on line {source_line}.")
    if error is not None and not isinstance(error, str):
        raise ValueError(f"Expected a string or null error in {results_path} on line {source_line}.")
    if not isinstance(metrics["exact_match"], bool):
        raise ValueError(f"Expected boolean exact_match in {results_path} on line {source_line}.")
    if execution_match is not None and not isinstance(execution_match, bool):
        raise ValueError(
            f"Expected boolean or null execution_match in {results_path} on line {source_line}."
        )
    try:
        token_precision = float(metrics["token_precision"])
        token_recall = float(metrics["token_recall"])
        token_f1 = float(metrics["token_f1"])
    except (TypeError, ValueError) as metric_error:
        raise ValueError(
            f"Expected numeric token metrics in {results_path} on line {source_line}."
        ) from metric_error

    return EvaluationResult(
        source_line=source_line,
        instance_id=payload["instance_id"],
        question=payload["question"],
        schema=payload["schema"],
        reference_cypher=payload["reference_cypher"],
        predicted_cypher=payload["predicted_cypher"],
        database_reference_alias=alias or None,
        exact_match=metrics["exact_match"],
        token_precision=token_precision,
        token_recall=token_recall,
        token_f1=token_f1,
        execution_match=execution_match,
        error=error,
    )


def classify_result(result: EvaluationResult) -> ClassifiedResult:
    """Classify a result without attempting Cypher parsing or execution."""
    prediction = result.predicted_cypher
    prediction_features = query_features(prediction)
    reference_features = query_features(result.reference_cypher)
    has_sql_keywords = _has_any_phrase(prediction, SQL_KEYWORDS)
    has_markdown_fence = "```" in prediction
    first_clause = first_cypher_clause(prediction)
    has_prose_prefix = _has_prose_prefix(prediction, first_clause)
    has_write_clause = bool(set(prediction_features) & {"write_clause"})

    if result.error is not None:
        outcome = "generation_error"
    elif not normalize_cypher(prediction):
        outcome = "empty_output"
    elif result.exact_match:
        outcome = "exact_lexical_match"
    elif has_sql_keywords and not _starts_with_cypher_clause(prediction):
        outcome = "sql_shaped_output"
    elif first_clause is not None or prediction_features:
        outcome = "cypher_shaped_non_match"
    elif has_markdown_fence or has_prose_prefix:
        outcome = "prose_or_markdown_output"
    else:
        outcome = "unclassified_non_cypher_output"

    lexical_overlap = None if result.exact_match else lexical_overlap_band(result.token_f1)
    omitted = tuple(sorted(set(reference_features) - set(prediction_features)))
    introduced = tuple(sorted(set(prediction_features) - set(reference_features)))
    return ClassifiedResult(
        result=result,
        outcome=outcome,
        lexical_overlap=lexical_overlap,
        first_cypher_clause=first_clause,
        has_markdown_fence=has_markdown_fence,
        has_prose_prefix=has_prose_prefix,
        has_sql_keywords=has_sql_keywords,
        has_write_clause=has_write_clause,
        reference_features=reference_features,
        predicted_features=prediction_features,
        omitted_reference_features=omitted,
        introduced_features=introduced,
        identifier_overlap=identifier_overlap(result.reference_cypher, prediction),
    )


def lexical_overlap_band(token_f1: float) -> str:
    """Return a transparent lexical-overlap band for a non-exact prediction."""
    if token_f1 == 0:
        return "no_overlap"
    if token_f1 < 0.5:
        return "low_overlap"
    return "high_overlap"


def first_cypher_clause(query: str) -> str | None:
    """Return the first recognized Cypher clause in textual order."""
    matches: list[tuple[int, str]] = []
    for clause in CYPHER_CLAUSES:
        match = re.search(rf"\b{re.escape(clause)}\b", query, flags=re.IGNORECASE)
        if match:
            matches.append((match.start(), clause))
    return min(matches, default=(0, None), key=lambda item: item[0])[1]


def query_features(query: str) -> tuple[str, ...]:
    """Extract a conservative, static set of common Cypher query features."""
    normalized = normalize_cypher(query)
    features: set[str] = set()
    if _has_phrase(normalized, "MATCH"):
        features.add("match")
    if _has_phrase(normalized, "OPTIONAL MATCH"):
        features.add("optional_match")
    if _has_phrase(normalized, "WHERE"):
        features.add("where")
    if _has_phrase(normalized, "WITH"):
        features.add("with")
    if _has_phrase(normalized, "RETURN"):
        features.add("return")
    if re.search(r"(?:<-|-)\s*\[[^\]]*\]\s*(?:->|-)", normalized):
        features.add("relationship_pattern")
    if re.search(r"\([^)]*:[A-Za-z_][A-Za-z0-9_]*", normalized):
        features.add("node_label")
    if re.search(r"\.[A-Za-z_][A-Za-z0-9_]*\s*(?:=|<>|!=|<=|>=|<|>|IN\b|IS\b)", normalized, re.I) or re.search(r"\{\s*[A-Za-z_][A-Za-z0-9_]*\s*:", normalized):
        features.add("property_filter")
    if any(_has_phrase(normalized, f"{name}(") for name in AGGREGATIONS):
        features.add("aggregation")
    if _has_phrase(normalized, "DISTINCT"):
        features.add("distinct")
    if _has_phrase(normalized, "ORDER BY"):
        features.add("ordering")
    if _has_phrase(normalized, "LIMIT") or _has_phrase(normalized, "SKIP"):
        features.add("pagination")
    if _has_phrase(normalized, "UNION"):
        features.add("union")
    if re.search(r"\bCALL\s*\{", normalized, re.I):
        features.add("subquery")
    if _has_any_phrase(normalized, WRITE_CLAUSES):
        features.add("write_clause")
    return tuple(sorted(features))


def identifier_overlap(reference: str, prediction: str) -> dict[str, float | int]:
    """Measure static identifier-token overlap after excluding Cypher keywords."""
    reference_identifiers = {
        token for token in cypher_tokens(reference) if token not in CYPHER_KEYWORDS and not token.isdecimal()
    }
    predicted_identifiers = {
        token for token in cypher_tokens(prediction) if token not in CYPHER_KEYWORDS and not token.isdecimal()
    }
    overlap = len(reference_identifiers & predicted_identifiers)
    precision = overlap / len(predicted_identifiers) if predicted_identifiers else 0.0
    recall = overlap / len(reference_identifiers) if reference_identifiers else 0.0
    return {"precision": precision, "recall": recall, "shared": overlap}


def build_analysis(
    results: list[EvaluationResult], source_path: Path, max_examples: int = 5
) -> dict[str, Any]:
    """Build a JSON-serializable lexical and static analysis report."""
    if max_examples < 1:
        raise ValueError("max_examples must be at least 1.")
    classified = [classify_result(result) for result in results]
    report = {
        "metadata": {
            "source_results": str(source_path),
            "num_samples": len(classified),
            "analysis_scope": "offline lexical and static analysis; no Cypher parsing or execution equivalence",
        },
        "outcomes": _count_rate_table(classified, lambda item: item.outcome),
        "lexical_overlap": _count_rate_table(
            [item for item in classified if item.lexical_overlap is not None],
            lambda item: item.lexical_overlap or "",
        ),
        "error_types": _error_types(classified),
        "by_database_reference_alias": _alias_breakdown(classified),
        "by_reference_complexity": _complexity_breakdown(classified),
        "reference_feature_success": _feature_success(classified),
        "static_feature_gaps": _feature_gaps(classified),
        "execution_confusion_matrix": _execution_confusion_matrix(classified, max_examples),
        "examples": _select_examples(classified, max_examples),
        "limitations": [
            "Exact match and token overlap are lexical metrics, not semantic or execution equivalence.",
            "Feature extraction uses conservative regular-expression rules, not a Cypher parser.",
            "A non-exact result can still be semantically valid; this report does not determine that.",
        ],
    }
    return report


def write_analysis_reports(report: dict[str, Any], output_directory: Path, prefix: str) -> tuple[Path, Path]:
    """Write stable JSON and Markdown analysis artifacts."""
    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / f"{prefix}_analysis.json"
    markdown_path = output_directory / f"{prefix}_analysis.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown_report(report), encoding="utf-8")
    return json_path, markdown_path


def render_markdown_report(report: dict[str, Any]) -> str:
    """Render a human-reviewable Markdown report from analysis data."""
    metadata = report["metadata"]
    lines = [
        "# Evaluation Result Analysis",
        "",
        "## Scope",
        "",
        f"- Source: `{metadata['source_results']}`",
        f"- Samples: {metadata['num_samples']}",
        f"- Interpretation: {metadata['analysis_scope']}",
        "",
        "## Outcome distribution",
        "",
        _render_table(report["outcomes"], ("Outcome", "Count", "Rate")),
        "",
        "## Lexical overlap among non-exact outputs",
        "",
        _render_table(report["lexical_overlap"], ("Band", "Count", "Rate")),
        "",
        "## Reference query features: lexical exact-match rate",
        "",
        _render_feature_table(report["reference_feature_success"]),
        "",
        "## Static feature gaps in Cypher-shaped non-matches",
        "",
        _render_gap_table(report["static_feature_gaps"]),
        "",
        "## Execution-match confusion matrix",
        "",
        _render_execution_confusion_matrix(report["execution_confusion_matrix"]),
        "",
        "## Database-alias breakdown",
        "",
        _render_alias_table(report["by_database_reference_alias"]),
        "",
        "## Reference-complexity breakdown",
        "",
        _render_complexity_table(report["by_reference_complexity"]),
        "",
        "## Generation errors",
        "",
    ]
    error_types = report["error_types"]
    if error_types:
        lines.extend(f"- `{name}`: {count}" for name, count in error_types.items())
    else:
        lines.append("- None")
    lines.extend(["", "## Representative examples", ""])
    for group, examples in report["examples"].items():
        lines.extend([f"### {group.replace('_', ' ').title()}", ""])
        if not examples:
            lines.extend(["No examples.", ""])
            continue
        for example in examples:
            lines.extend(
                [
                    f"#### {example['instance_id']} — {example['outcome']}",
                    "",
                    f"- Token F1: {example['token_f1']:.3f}",
                    f"- Reference features: {', '.join(example['reference_features']) or 'none'}",
                    f"- Predicted features: {', '.join(example['predicted_features']) or 'none'}",
                    f"- Omitted reference features: {', '.join(example['omitted_reference_features']) or 'none'}",
                    f"- Introduced features: {', '.join(example['introduced_features']) or 'none'}",
                    "",
                    "Question:",
                    "",
                    example["question"],
                    "",
                    "Reference Cypher:",
                    "",
                    "````cypher",
                    example["reference_cypher"],
                    "````",
                    "",
                    "Generated output:",
                    "",
                    "````text",
                    example["predicted_cypher"] or "<empty>",
                    "````",
                    "",
                ]
            )
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in report["limitations"])
    return "\n".join(lines) + "\n"


def _has_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE))


def _has_any_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    return any(_has_phrase(text, phrase) for phrase in phrases)


def _starts_with_cypher_clause(query: str) -> bool:
    stripped = query.lstrip()
    return any(re.match(rf"{re.escape(clause)}\b", stripped, flags=re.IGNORECASE) for clause in CYPHER_CLAUSES)


def _has_prose_prefix(query: str, first_clause: str | None) -> bool:
    if not query.strip():
        return False
    if first_clause is None:
        return bool(re.search(r"[A-Za-z]{3}", query))
    if _starts_with_cypher_clause(query):
        return False
    match = re.search(rf"\b{re.escape(first_clause)}\b", query, flags=re.IGNORECASE)
    return bool(match and query[: match.start()].strip())


def _count_rate_table(items: list[ClassifiedResult], key: Any) -> dict[str, dict[str, float | int]]:
    counts = Counter(key(item) for item in items)
    total = len(items)
    return {
        name: {"count": count, "rate": count / total if total else 0.0}
        for name, count in sorted(counts.items())
    }


def _error_types(items: list[ClassifiedResult]) -> dict[str, int]:
    counts = Counter(
        item.result.error.split(":", maxsplit=1)[0]
        for item in items
        if item.result.error is not None
    )
    return dict(sorted(counts.items()))


def _alias_breakdown(items: list[ClassifiedResult]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[ClassifiedResult]] = defaultdict(list)
    for item in items:
        groups[item.result.database_reference_alias or "<unset>"].append(item)
    return {
        alias: _subset_summary(group)
        for alias, group in sorted(groups.items())
    }


def _complexity_breakdown(items: list[ClassifiedResult]) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[ClassifiedResult]] = defaultdict(list)
    for item in items:
        groups[str(len(item.reference_features))].append(item)
    return {complexity: _subset_summary(group) for complexity, group in sorted(groups.items(), key=lambda pair: int(pair[0]))}


def _subset_summary(items: list[ClassifiedResult]) -> dict[str, Any]:
    exact_matches = sum(item.outcome == "exact_lexical_match" for item in items)
    return {
        "samples": len(items),
        "exact_lexical_matches": exact_matches,
        "exact_lexical_match_rate": exact_matches / len(items) if items else 0.0,
        "outcomes": _count_rate_table(items, lambda item: item.outcome),
    }


def _feature_success(items: list[ClassifiedResult]) -> dict[str, dict[str, float | int]]:
    all_features = sorted({feature for item in items for feature in item.reference_features})
    report: dict[str, dict[str, float | int]] = {}
    for feature in all_features:
        cohort = [item for item in items if feature in item.reference_features]
        exact_matches = sum(item.outcome == "exact_lexical_match" for item in cohort)
        report[feature] = {
            "samples": len(cohort),
            "exact_lexical_matches": exact_matches,
            "exact_lexical_match_rate": exact_matches / len(cohort) if cohort else 0.0,
        }
    return report


def _feature_gaps(items: list[ClassifiedResult]) -> dict[str, dict[str, int]]:
    cohort = [item for item in items if item.outcome == "cypher_shaped_non_match"]
    omitted = Counter(feature for item in cohort for feature in item.omitted_reference_features)
    introduced = Counter(feature for item in cohort for feature in item.introduced_features)
    return {
        "cypher_shaped_non_matches": len(cohort),
        "omitted_reference_features": dict(sorted(omitted.items())),
        "introduced_features": dict(sorted(introduced.items())),
    }


def _execution_confusion_matrix(
    items: list[ClassifiedResult], max_examples: int
) -> dict[str, Any]:
    execution_evaluated = [item for item in items if item.result.execution_match is not None]
    categories = {
        "true_positives": [
            item for item in items if item.result.exact_match or item.result.execution_match
        ],
        "true_negatives": [
            item for item in items if not item.result.exact_match and not item.result.execution_match
        ],
        "false_positives": [],
        "false_negatives": [],
    }
    return {
        "samples": len(items),
        "execution_evaluated_samples": len(execution_evaluated),
        "definition": (
            "True positives are lexical exact matches or execution matches. True negatives are "
            "non-exact lexical matches without an execution match. False positives and false "
            "negatives are unavailable because the artifact has no independent ground-truth "
            "semantic-equivalence label. A null execution_match is treated as not execution-matched."
        ),
        "categories": {
            name: {
                "count": len(group),
                "examples": [
                    _example_payload(item)
                    for item in sorted(
                        group, key=lambda item: (-item.result.token_f1, item.result.instance_id)
                    )[:max_examples]
                ],
            }
            for name, group in categories.items()
        },
    }


def _select_examples(items: list[ClassifiedResult], max_examples: int) -> dict[str, list[dict[str, Any]]]:
    exact = [item for item in items if item.outcome == "exact_lexical_match"]
    partial = [item for item in items if item.outcome == "cypher_shaped_non_match"]
    failures: dict[str, list[ClassifiedResult]] = defaultdict(list)
    for item in items:
        if item.outcome not in {"exact_lexical_match", "cypher_shaped_non_match"}:
            failures[item.outcome].append(item)
    selected = {
        "complex_exact_matches": sorted(
            exact, key=lambda item: (-len(item.reference_features), item.result.instance_id)
        )[:max_examples],
        "closest_cypher_non_matches": sorted(
            partial,
            key=lambda item: (-item.result.token_f1, -len(item.reference_features), item.result.instance_id),
        )[:max_examples],
    }
    for outcome, group in sorted(failures.items()):
        selected[f"{outcome}_examples"] = sorted(
            group, key=lambda item: (-item.result.token_f1, item.result.instance_id)
        )[:max_examples]
    return {name: [_example_payload(item) for item in group] for name, group in selected.items()}


def _example_payload(item: ClassifiedResult) -> dict[str, Any]:
    result = item.result
    return {
        "instance_id": result.instance_id,
        "question": result.question,
        "reference_cypher": result.reference_cypher,
        "predicted_cypher": result.predicted_cypher,
        "database_reference_alias": result.database_reference_alias,
        "error": result.error,
        "outcome": item.outcome,
        "lexical_overlap": item.lexical_overlap,
        "token_f1": result.token_f1,
        "execution_match": result.execution_match,
        "reference_features": list(item.reference_features),
        "predicted_features": list(item.predicted_features),
        "omitted_reference_features": list(item.omitted_reference_features),
        "introduced_features": list(item.introduced_features),
        "identifier_overlap": item.identifier_overlap,
        "static_signals": {
            "first_cypher_clause": item.first_cypher_clause,
            "has_markdown_fence": item.has_markdown_fence,
            "has_prose_prefix": item.has_prose_prefix,
            "has_sql_keywords": item.has_sql_keywords,
            "has_write_clause": item.has_write_clause,
        },
    }


def _render_table(table: dict[str, dict[str, float | int]], headers: tuple[str, str, str]) -> str:
    lines = [f"| {' | '.join(headers)} |", "|---|---:|---:|"]
    lines.extend(f"| {name} | {values['count']} | {values['rate']:.1%} |" for name, values in table.items())
    return "\n".join(lines)


def _render_feature_table(table: dict[str, dict[str, float | int]]) -> str:
    lines = ["| Feature | Samples | Exact matches | Exact-match rate |", "|---|---:|---:|---:|"]
    lines.extend(
        f"| {feature} | {values['samples']} | {values['exact_lexical_matches']} | {values['exact_lexical_match_rate']:.1%} |"
        for feature, values in table.items()
    )
    return "\n".join(lines)


def _render_gap_table(table: dict[str, Any]) -> str:
    lines = [f"Cypher-shaped non-matches: {table['cypher_shaped_non_matches']}", "", "| Gap type | Feature | Count |", "|---|---|---:|"]
    lines.extend(f"| Omitted reference feature | {feature} | {count} |" for feature, count in table["omitted_reference_features"].items())
    lines.extend(f"| Introduced feature | {feature} | {count} |" for feature, count in table["introduced_features"].items())
    return "\n".join(lines)


def _render_execution_confusion_matrix(table: dict[str, Any]) -> str:
    lines = [
        f"- Samples: {table['samples']}",
        f"- Execution-evaluated samples: {table['execution_evaluated_samples']}",
        f"- Definition: {table['definition']}",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {category.replace('_', ' ')} | {values['count']} |"
        for category, values in table["categories"].items()
    )
    for category, values in table["categories"].items():
        lines.extend(["", f"### {category.replace('_', ' ').title()} examples", ""])
        examples = values["examples"]
        if not examples:
            lines.append("No examples.")
            continue
        for example in examples:
            lines.extend(
                [
                    f"#### {example['instance_id']}",
                    "",
                    f"- Execution match: {example['execution_match']}",
                    f"- Token F1: {example['token_f1']:.3f}",
                    "",
                    "Question:",
                    "",
                    example["question"],
                    "",
                    "Reference Cypher:",
                    "",
                    "````cypher",
                    example["reference_cypher"],
                    "````",
                    "",
                    "Generated output:",
                    "",
                    "````text",
                    example["predicted_cypher"] or "<empty>",
                    "````",
                ]
            )
    return "\n".join(lines)


def _render_alias_table(table: dict[str, dict[str, Any]]) -> str:
    lines = ["| Alias | Samples | Exact lexical matches | Exact-match rate |", "|---|---:|---:|---:|"]
    lines.extend(
        f"| {alias} | {values['samples']} | {values['exact_lexical_matches']} | {values['exact_lexical_match_rate']:.1%} |"
        for alias, values in table.items()
    )
    return "\n".join(lines)


def _render_complexity_table(table: dict[str, dict[str, Any]]) -> str:
    lines = ["| Recognized reference features | Samples | Exact lexical matches | Exact-match rate |", "|---:|---:|---:|---:|"]
    lines.extend(
        f"| {complexity} | {values['samples']} | {values['exact_lexical_matches']} | {values['exact_lexical_match_rate']:.1%} |"
        for complexity, values in table.items()
    )
    return "\n".join(lines)
