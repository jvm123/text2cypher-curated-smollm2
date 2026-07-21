import json

from datasets import Dataset

from text2cypher.evaluation import evaluate_dataset


def test_evaluation_limits_samples_and_writes_summary(tmp_path, monkeypatch) -> None:
    dataset = Dataset.from_dict(
        {
            "instance_id": [1, 2],
            "question": ["First", "Second"],
            "schema": ["Node {name}", "Node {name}"],
            "cypher": ["MATCH (n) RETURN n", "MATCH (n) RETURN n.name"],
            "database_reference_alias": [None, "movies"],
        }
    )
    monkeypatch.setattr(
        "text2cypher.evaluation.generate_cypher",
        lambda *_args, **_kwargs: "MATCH (n) RETURN n",
    )

    results_path, summary_path = evaluate_dataset(
        model=object(),
        tokenizer=object(),
        dataset=dataset,
        output_directory=tmp_path,
        max_new_tokens=16,
        label="smoke",
        split="test",
        database_reference_alias="any",
        limit=1,
    )

    results = [json.loads(line) for line in results_path.read_text().splitlines()]
    summary = json.loads(summary_path.read_text())
    assert len(results) == 1
    assert results[0]["instance_id"] == 1
    assert results[0]["metrics"]["exact_match"] is True
    assert results[0]["metrics"]["execution_match"] is None
    assert "comparisons" not in results[0]
    assert "generation" not in results[0]
    assert summary["num_samples"] == 1
    assert summary["limit"] == 1
    assert summary["split"] == "test"
    assert summary["metrics"]["exact_match"] == 1.0


def test_evaluation_records_opt_in_execution_results(tmp_path, monkeypatch) -> None:
    dataset = Dataset.from_dict(
        {
            "instance_id": [1, 2],
            "question": ["First", "Second"],
            "schema": ["Node {name}", "Node {name}"],
            "cypher": ["MATCH (n) RETURN n", "MATCH (n) RETURN n"],
            "database_reference_alias": ["neo4jlabs_demo_db_movies", None],
        }
    )
    monkeypatch.setattr(
        "text2cypher.evaluation.generate_cypher", lambda *_args, **_kwargs: "MATCH (n) RETURN n"
    )

    def execution_evaluator(alias, _reference, _prediction):
        if alias is None:
            return {"status": "skipped", "reason": "alias_mismatch", "equivalent": None}
        return {"status": "equivalent", "reason": None, "equivalent": True}

    results_path, summary_path = evaluate_dataset(
        model=object(),
        tokenizer=object(),
        dataset=dataset,
        output_directory=tmp_path,
        max_new_tokens=16,
        label="execution",
        split="test",
        database_reference_alias="any",
        execution_evaluator=execution_evaluator,
    )

    results = [json.loads(line) for line in results_path.read_text().splitlines()]
    summary = json.loads(summary_path.read_text())
    assert results[0]["execution"]["equivalent"] is True
    assert results[0]["metrics"]["execution_match"] is True
    assert results[1]["execution"]["status"] == "skipped"
    assert results[1]["metrics"]["execution_match"] is None
    assert summary["execution"]["eligible_samples"] == 1
    assert summary["execution"]["execution_accuracy"] == 1.0
