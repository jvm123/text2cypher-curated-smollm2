from datasets import Dataset, DatasetDict
import pytest

from text2cypher.data import (
    database_reference_counts,
    dataset_stats,
    filter_compilable_cypher,
    filter_database_reference_alias,
    load_text2cypher_dataset,
    tokenize_for_training,
)


class FakeTokenizer:
    eos_token = "<eos>"

    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert tokenize is False
        assert add_generation_prompt is True
        return "prompt:"

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": list(range(len(text)))}


def test_tokenization_masks_the_prompt() -> None:
    dataset = Dataset.from_dict(
        {"question": ["Question"], "schema": ["Schema"], "cypher": ["MATCH"]}
    )
    result = tokenize_for_training(dataset, FakeTokenizer())
    assert result[0]["labels"][:7] == [-100] * 7
    assert any(label != -100 for label in result[0]["labels"])


def test_tokenization_retains_the_complete_prompt_and_target() -> None:
    dataset = Dataset.from_dict(
        {"question": ["Question"], "schema": ["Schema"], "cypher": ["MATCH"]}
    )

    result = tokenize_for_training(dataset, FakeTokenizer())

    target_length = len("MATCH<eos>")
    assert len(result[0]["input_ids"]) == len("prompt:") + target_length
    assert result[0]["labels"] == [-100] * len("prompt:") + list(range(target_length))


def test_dataset_stats_reports_requested_splits() -> None:
    split = Dataset.from_dict({"question": ["q"]})
    stats = dataset_stats(DatasetDict({"train": split, "val": split, "test": split}))
    assert stats == {"train": 1, "val": 1, "test": 1}


def test_database_reference_counts_groups_unset_aliases() -> None:
    dataset = Dataset.from_dict(
        {"database_reference_alias": ["movies", None, "", "  ", "movies", "twitch"]}
    )

    assert database_reference_counts(dataset) == {"<unset>": 3, "movies": 2, "twitch": 1}


def test_dataset_validation_rejects_missing_split(monkeypatch) -> None:
    monkeypatch.setattr(
        "text2cypher.data.load_dataset",
        lambda *_args, **_kwargs: DatasetDict({"train": Dataset.from_dict({})}),
    )
    with pytest.raises(ValueError, match="missing required splits"):
        load_text2cypher_dataset("unused")


def test_alias_filter_selects_set_and_unset_examples() -> None:
    dataset = Dataset.from_dict(
        {"database_reference_alias": ["movies", None, "", "  "]}
    )
    assert len(filter_database_reference_alias(dataset, "any")) == 4
    assert len(filter_database_reference_alias(dataset, "set")) == 1
    assert len(filter_database_reference_alias(dataset, "unset")) == 3


def test_compilation_filter_retains_order_and_reports_rejections() -> None:
    dataset = Dataset.from_dict(
        {"instance_id": [1, 2, 3], "cypher": ["MATCH (a) RETURN a", "bad", "RETURN 1"]}
    )

    accepted, report = filter_compilable_cypher(
        dataset, lambda query: "Neo4jSyntaxError" if query == "bad" else None
    )

    assert accepted["instance_id"] == [1, 3]
    assert report.accepted == 2
    assert report.rejected == 1
    assert report.rejection_reasons == {"Neo4jSyntaxError": 1}


def test_compilation_filter_rejects_an_empty_dataset() -> None:
    dataset = Dataset.from_dict({"cypher": ["bad"]})

    with pytest.raises(ValueError, match="rejected every"):
        filter_compilable_cypher(dataset, lambda _query: "Neo4jSyntaxError")
