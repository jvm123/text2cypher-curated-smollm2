import pytest

from text2cypher.execution import Neo4jCypherValidator, NotificationMinimumSeverity


class FakeResult:
    def consume(self) -> None:
        return None


class FakeSession:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.queries: list[object] = []

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def run(self, query):
        self.queries.append(query)
        if self.should_fail:
            raise SyntaxError("invalid Cypher")
        return FakeResult()


class FakeDriver:
    def __init__(self, should_fail: bool = False) -> None:
        self.session_instance = FakeSession(should_fail)
        self.connected = False
        self.closed = False

    def verify_connectivity(self) -> None:
        self.connected = True

    def session(self) -> FakeSession:
        return self.session_instance

    def close(self) -> None:
        self.closed = True


def test_validator_compiles_with_explain_without_executing(monkeypatch) -> None:
    driver = FakeDriver()
    driver_config = {}

    def create_driver(*_args, **kwargs):
        driver_config.update(kwargs)
        return driver

    monkeypatch.setattr("text2cypher.execution.GraphDatabase.driver", create_driver)

    validator = Neo4jCypherValidator("bolt://test", "neo4j", "password", 5.0)

    assert validator.validate("CREATE (:Example)") is None
    assert driver.connected is True
    assert driver_config["notifications_min_severity"] is NotificationMinimumSeverity.OFF
    assert str(driver.session_instance.queries[0]) == "EXPLAIN CREATE (:Example)"
    validator.close()
    assert driver.closed is True


def test_validator_reports_compilation_errors_without_exposing_query(monkeypatch) -> None:
    driver = FakeDriver(should_fail=True)
    monkeypatch.setattr("text2cypher.execution.GraphDatabase.driver", lambda *_args, **_kwargs: driver)
    validator = Neo4jCypherValidator("bolt://test", "neo4j", "password", 5.0)

    assert validator.validate("MATCH (broken") == "SyntaxError"


def test_validator_rejects_non_positive_timeouts() -> None:
    with pytest.raises(ValueError, match="positive"):
        Neo4jCypherValidator("bolt://test", "neo4j", "password", 0)


def test_validator_fails_fast_and_closes_on_connectivity_error(monkeypatch) -> None:
    driver = FakeDriver()

    def fail_connectivity() -> None:
        raise RuntimeError("database unavailable")

    driver.verify_connectivity = fail_connectivity
    monkeypatch.setattr("text2cypher.execution.GraphDatabase.driver", lambda *_args, **_kwargs: driver)

    with pytest.raises(RuntimeError, match="database unavailable"):
        Neo4jCypherValidator("bolt://test", "neo4j", "password", 5.0)
    assert driver.closed is True