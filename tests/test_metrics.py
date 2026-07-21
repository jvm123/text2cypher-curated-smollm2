from text2cypher.metrics import evaluate_prediction, normalize_cypher, token_prf


def test_normalize_cypher_ignores_whitespace_and_terminal_semicolon() -> None:
    assert normalize_cypher(" MATCH (n) RETURN n; ") == "MATCH (n) RETURN n"


def test_exact_match_uses_normalized_cypher() -> None:
    metrics = evaluate_prediction("MATCH (n) RETURN n;", "MATCH (n)   RETURN n")
    assert metrics["exact_match"] is True
    assert metrics["token_f1"] == 1.0


def test_token_prf_reports_partial_overlap() -> None:
    metrics = token_prf("MATCH (n) RETURN n", "MATCH (n) RETURN n.name")
    assert metrics["token_precision"] == 1.0
    assert 0.0 < metrics["token_recall"] < 1.0
    assert 0.0 < metrics["token_f1"] < 1.0
