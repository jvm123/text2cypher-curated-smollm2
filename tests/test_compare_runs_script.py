from scripts.compare_runs import format_metrics_table


def test_format_metrics_table_lists_every_run() -> None:
    report = {
        "runs": {
            "with-syntax-check": {
                "metrics": {
                    "exact_match": 0.44,
                    "token_precision": 0.91,
                    "token_recall": 0.92,
                    "token_f1": 0.91,
                }
            },
            "without-syntax-check": {
                "metrics": {
                    "exact_match": 0.28,
                    "token_precision": 0.85,
                    "token_recall": 0.84,
                    "token_f1": 0.83,
                }
            },
        }
    }

    table = format_metrics_table(report)

    assert "Run" in table
    assert "Exact match" in table
    assert "with-syntax-check" in table
    assert "without-syntax-check" in table
    assert "0.4400" in table
    rows = table.splitlines()
    assert rows[2].index("0.4400") == rows[3].index("0.2800")