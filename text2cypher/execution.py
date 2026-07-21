"""Safe, opt-in execution equivalence checks for compatible Neo4j snapshots."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from neo4j import GraphDatabase, NotificationMinimumSeverity, Query, READ_ACCESS
from neo4j.exceptions import ServiceUnavailable, SessionExpired

GRAPH_ALIASES = {
    "movies": frozenset({"neo4jlabs_demo_db_movies"}),
    "twitter": frozenset(
        {"neo4jlabs_demo_db_twitter", "neo4jlabs_demo_db_twitter_v2"}
    ),
    "fincen": frozenset({"neo4jlabs_demo_db_fincen"}),
    "stackoverflow": frozenset({"neo4jlabs_demo_db_stackoverflow"}),
    "twitch": frozenset({"neo4jlabs_demo_db_twitch"}),
}
READ_START_PATTERN = re.compile(r"^\s*(?:OPTIONAL\s+MATCH|MATCH|WITH|UNWIND|RETURN)\b", re.IGNORECASE)
RETURN_PATTERN = re.compile(r"\bRETURN\b", re.IGNORECASE)
ORDER_BY_PATTERN = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)
FORBIDDEN_PATTERN = re.compile(
    r"\b(?:CALL|CREATE|MERGE|DELETE|SET|REMOVE|FOREACH|LOAD\s+CSV|DROP|ALTER|GRANT|DENY|REVOKE)\b",
    re.IGNORECASE,
)
COMMENT_OR_STRING_PATTERN = re.compile(
    r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|//[^\n]*|/\*.*?\*/",
    re.DOTALL,
)


def graph_matches_alias(graph: str, database_reference_alias: object) -> bool:
    """Return whether an example belongs to the selected imported graph."""
    return isinstance(database_reference_alias, str) and database_reference_alias in GRAPH_ALIASES[graph]


def is_read_only_cypher(query: str) -> bool:
    """Conservatively accept only a single read-only Cypher statement."""
    if not isinstance(query, str) or not query.strip() or ";" in query or "```" in query:
        return False
    sanitized = COMMENT_OR_STRING_PATTERN.sub(" ", query)
    return (
        bool(READ_START_PATTERN.search(sanitized))
        and bool(RETURN_PATTERN.search(sanitized))
        and not FORBIDDEN_PATTERN.search(sanitized)
    )


def has_order_by(query: str) -> bool:
    """Return whether a query declares result ordering."""
    return bool(ORDER_BY_PATTERN.search(COMMENT_OR_STRING_PATTERN.sub(" ", query)))


def canonical_value(value: Any) -> object:
    """Serialize Neo4j values deterministically without exposing internal identities."""
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {"__float__": repr(value)}
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if hasattr(value, "labels") and hasattr(value, "items"):
        return {
            "__node__": {
                "labels": sorted(str(label) for label in value.labels),
                "properties": canonical_value(dict(value.items())),
            }
        }
    if hasattr(value, "type") and hasattr(value, "items"):
        return {
            "__relationship__": {
                "type": str(value.type),
                "properties": canonical_value(dict(value.items())),
            }
        }
    if hasattr(value, "nodes") and hasattr(value, "relationships"):
        return {
            "__path__": {
                "nodes": canonical_value(list(value.nodes)),
                "relationships": canonical_value(list(value.relationships)),
            }
        }
    if isinstance(value, Mapping):
        return {str(key): canonical_value(item) for key, item in sorted(value.items())}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonical_value(item) for item in value]
    if hasattr(value, "isoformat"):
        return {"__temporal__": value.isoformat()}
    raise TypeError(f"Unsupported Neo4j result value: {type(value).__name__}")


def canonical_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return stable JSON representations of result rows."""
    return [json.dumps(canonical_value(dict(row)), sort_keys=True, separators=(",", ":")) for row in rows]


def results_equivalent(reference_rows: Sequence[Mapping[str, Any]], prediction_rows: Sequence[Mapping[str, Any]], ordered: bool) -> bool:
    """Compare results as ordered rows or duplicate-preserving unordered multisets."""
    reference = canonical_rows(reference_rows)
    prediction = canonical_rows(prediction_rows)
    return reference == prediction if ordered else Counter(reference) == Counter(prediction)


def result_fingerprint(rows: Sequence[Mapping[str, Any]], ordered: bool) -> str:
    """Return a compact deterministic fingerprint for diagnostic result artifacts."""
    canonical = canonical_rows(rows)
    if not ordered:
        canonical.sort()
    return hashlib.sha256("\n".join(canonical).encode("utf-8")).hexdigest()


@dataclass
class Neo4jExecutionEvaluator:
    """Execute compatible graph queries through a dedicated read access session."""

    uri: str
    user: str
    password: str
    graph: str
    timeout_seconds: float
    max_records: int = 10_000

    def __post_init__(self) -> None:
        if self.graph not in GRAPH_ALIASES:
            raise ValueError(f"Unsupported execution graph: {self.graph}")
        if self.timeout_seconds <= 0:
            raise ValueError("Execution timeout must be positive.")
        self._driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            notifications_min_severity=NotificationMinimumSeverity.OFF,
        )

    def close(self) -> None:
        """Close the database driver."""
        self._driver.close()

    def evaluate(self, database_reference_alias: object, reference: str, prediction: str) -> dict[str, object]:
        """Compare one generated query with its reference on the selected graph."""
        if not graph_matches_alias(self.graph, database_reference_alias):
            return {"status": "skipped", "reason": "alias_mismatch", "equivalent": None}
        if not is_read_only_cypher(reference):
            return {"status": "skipped", "reason": "unsafe_reference", "equivalent": None}
        if not is_read_only_cypher(prediction):
            return {"status": "skipped", "reason": "unsafe_prediction", "equivalent": None}

        ordered = has_order_by(reference)
        try:
            reference_rows = self._run(reference)
        except Exception as error:
            return self._error("reference_error", error, ordered)
        try:
            prediction_rows = self._run(prediction)
        except Exception as error:
            return self._error("prediction_error", error, ordered)

        equivalent = results_equivalent(reference_rows, prediction_rows, ordered)
        return {
            "status": "equivalent" if equivalent else "mismatch",
            "reason": None,
            "equivalent": equivalent,
            "ordered": ordered,
            "reference_row_count": len(reference_rows),
            "prediction_row_count": len(prediction_rows),
            "reference_fingerprint": result_fingerprint(reference_rows, ordered),
            "prediction_fingerprint": result_fingerprint(prediction_rows, ordered),
        }

    def _run(self, query: str) -> list[dict[str, Any]]:
        with self._driver.session(default_access_mode=READ_ACCESS) as session:
            result = session.run(Query(query, timeout=self.timeout_seconds))
            rows: list[dict[str, Any]] = []
            for record in result:
                rows.append(dict(record.data()))
                if len(rows) > self.max_records:
                    raise RuntimeError(f"Query returned more than {self.max_records} records.")
            return rows

    @staticmethod
    def _error(status: str, error: Exception, ordered: bool) -> dict[str, object]:
        return {
            "status": status,
            "reason": f"{type(error).__name__}: {error}",
            "equivalent": None,
            "ordered": ordered,
        }


@dataclass
class Neo4jCypherValidator:
    """Validate Cypher compilation through Neo4j without executing it."""

    uri: str
    user: str
    password: str
    timeout_seconds: float

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("Validation timeout must be positive.")
        self._driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            notifications_min_severity=NotificationMinimumSeverity.OFF,
        )
        try:
            self._driver.verify_connectivity()
        except Exception:
            self._driver.close()
            raise

    def close(self) -> None:
        """Close the database driver."""
        self._driver.close()

    def validate(self, query: str) -> str | None:
        """Return an error class when Neo4j cannot compile a query, otherwise None."""
        if not isinstance(query, str) or not query.strip():
            return "EmptyCypher"
        try:
            with self._driver.session() as session:
                session.run(Query(f"EXPLAIN {query}", timeout=self.timeout_seconds)).consume()
        except (ServiceUnavailable, SessionExpired):
            raise
        except Exception as error:
            return type(error).__name__
        return None


ExecutionEvaluator = Callable[[object, str, str], dict[str, object]]
