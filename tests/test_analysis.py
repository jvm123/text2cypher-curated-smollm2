import json

import pytest

from text2cypher.analysis import (
    build_analysis,
    classify_result,
    load_evaluation_results,
    query_features,
    write_analysis_reports,
)


def _result(
    instance_id: str,
    prediction: str,
    *,
    reference: str = "MATCH (p:Person)-[:ACTED_IN]->(m:Movie) WHERE p.name = 'Ada' RETURN m",
    exact_match: bool = False,
    token_f1: float = 0.0,
    execution_match: bool | None = None,
    error: str | None = None,
    alias: str | None = None,
) -> dict[str, object]:
    return {
        "instance_id": instance_id,
        "question": "Which movies did Ada act in?",
        "schema": "Person {name}; Movie",
        "reference_cypher": reference,
        "predicted_cypher": prediction,
        "database_reference_alias": alias,
        "metrics": {
            "exact_match": exact_match,
            "token_precision": token_f1,
            "token_recall": token_f1,
            "token_f1": token_f1,
            "execution_match": execution_match,
        },
        "error": error,
    }


def _write_results(tmp_path, *results: dict[str, object]):
    path = tmp_path / "results.jsonl"
    path.write_text("\n".join(json.dumps(result) for result in results) + "\n", encoding="utf-8")
    return path


def test_load_and_classify_evaluation_results(tmp_path) -> None:
    path = _write_results(
        tmp_path,
        _result("exact", "MATCH (n) RETURN n", reference="MATCH (n) RETURN n", exact_match=True, token_f1=1.0),
        _result("empty", ""),
        _result("sql", "Here is a query: SELECT * FROM movies", token_f1=0.1),
        _result("prose", "The answer depends on the graph."),
        _result("cypher", "MATCH (p:Person) RETURN p", token_f1=0.7),
        _result("error", "", error="RuntimeError: unavailable"),
    )

    classified = [classify_result(result) for result in load_evaluation_results(path)]

    assert [item.outcome for item in classified] == [
        "exact_lexical_match",
        "empty_output",
        "sql_shaped_output",
        "prose_or_markdown_output",
        "cypher_shaped_non_match",
        "generation_error",
    ]
    assert classified[4].lexical_overlap == "high_overlap"
    assert classified[2].has_sql_keywords is True
    assert classified[3].has_prose_prefix is True


def test_loader_rejects_malformed_json_and_missing_metrics(tmp_path) -> None:
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed JSON.*line 1"):
        load_evaluation_results(malformed)

    missing = tmp_path / "missing.jsonl"
    missing.write_text(json.dumps({"instance_id": "one"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required field"):
        load_evaluation_results(missing)


def test_query_features_identify_common_cypher_constructs() -> None:
    query = (
        "OPTIONAL MATCH (n:Person)-[:KNOWS]->(m) WHERE n.name = 'Ada' "
        "WITH DISTINCT m, count(n) AS total RETURN m ORDER BY total DESC LIMIT 3"
    )

    assert set(query_features(query)) == {
        "aggregation",
        "distinct",
        "match",
        "node_label",
        "optional_match",
        "ordering",
        "pagination",
        "property_filter",
        "relationship_pattern",
        "return",
        "where",
        "with",
    }


def test_analysis_aggregates_features_aliases_and_deterministic_examples(tmp_path) -> None:
    reference = "MATCH (p:Person)-[:ACTED_IN]->(m:Movie) WHERE p.name = 'Ada' RETURN m"
    path = _write_results(
        tmp_path,
        _result("exact-simple", "MATCH (n) RETURN n", reference="MATCH (n) RETURN n", exact_match=True, token_f1=1.0),
        _result("exact-complex", reference, reference=reference, exact_match=True, token_f1=1.0, alias="movies"),
        _result("partial", "MATCH (p:Person) RETURN p", reference=reference, token_f1=0.6, alias="movies"),
        _result("error", "", reference=reference, error="ValueError: bad generation"),
        _result("true-positive", "MATCH (n) RETURN n", reference="MATCH (n) RETURN n", exact_match=True, token_f1=1.0, execution_match=True),
        _result("true-negative", "MATCH (p) RETURN p", reference="MATCH (n) RETURN n", token_f1=0.5, execution_match=False),
        _result("false-positive", "MATCH (n) RETURN n", reference="MATCH (n) RETURN n", exact_match=True, token_f1=1.0, execution_match=False),
        _result("false-negative", "MATCH (p) RETURN p", reference="MATCH (n) RETURN n", token_f1=0.5, execution_match=True),
    )

    report = build_analysis(load_evaluation_results(path), path, max_examples=1)

    assert report["outcomes"]["exact_lexical_match"]["count"] == 4
    assert report["by_database_reference_alias"]["movies"]["samples"] == 2
    assert report["reference_feature_success"]["relationship_pattern"]["samples"] == 3
    assert report["static_feature_gaps"]["omitted_reference_features"]["relationship_pattern"] == 1
    assert report["examples"]["complex_exact_matches"][0]["instance_id"] == "exact-complex"
    assert report["error_types"] == {"ValueError": 1}
    confusion_matrix = report["execution_confusion_matrix"]
    assert confusion_matrix["samples"] == 8
    assert confusion_matrix["execution_evaluated_samples"] == 4
    assert confusion_matrix["categories"]["true_positives"]["count"] == 5
    assert confusion_matrix["categories"]["true_negatives"]["count"] == 3
    assert confusion_matrix["categories"]["false_positives"]["examples"] == []
    assert confusion_matrix["categories"]["false_negatives"]["examples"] == []

    json_path, markdown_path = write_analysis_reports(report, tmp_path / "reports", "baseline")
    stored = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert stored["metadata"]["num_samples"] == 8
    assert "# Evaluation Result Analysis" in markdown
    assert "## Execution-match confusion matrix" in markdown
    assert "## Limitations" in markdown
