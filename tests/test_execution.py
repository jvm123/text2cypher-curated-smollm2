from collections import Counter

from text2cypher.execution import (
    canonical_rows,
    graph_matches_alias,
    is_read_only_cypher,
    results_equivalent,
)


def test_read_only_cypher_rejects_write_and_procedure_clauses() -> None:
    assert is_read_only_cypher("MATCH (n) RETURN n")
    assert is_read_only_cypher("OPTIONAL MATCH (n) WITH n RETURN n")
    assert not is_read_only_cypher("MATCH (n)")
    assert not is_read_only_cypher("MATCH (n) SET n.name = 'changed' RETURN n")
    assert not is_read_only_cypher("CALL db.labels()")
    assert not is_read_only_cypher("MATCH (n) RETURN n;")


def test_results_equivalent_preserves_duplicates_and_order() -> None:
    reference = [{"value": 1}, {"value": 1}, {"value": 2}]
    reordered = [{"value": 2}, {"value": 1}, {"value": 1}]
    missing_duplicate = [{"value": 1}, {"value": 2}]

    assert results_equivalent(reference, reordered, ordered=False)
    assert not results_equivalent(reference, reordered, ordered=True)
    assert not results_equivalent(reference, missing_duplicate, ordered=False)
    assert Counter(canonical_rows(reference))[canonical_rows(reference)[0]] == 2


def test_graph_aliases_only_accept_the_selected_snapshot() -> None:
    assert graph_matches_alias("movies", "neo4jlabs_demo_db_movies")
    assert graph_matches_alias("twitter", "neo4jlabs_demo_db_twitter_v2")
    assert not graph_matches_alias("movies", "neo4jlabs_demo_db_fincen")
    assert not graph_matches_alias("movies", None)