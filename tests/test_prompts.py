from text2cypher.prompts import SYSTEM_MESSAGE, messages_for, user_message


def test_user_message_contains_schema_and_question() -> None:
    message = user_message("Movie {title}", "Which movies exist?")
    assert "Schema:\nMovie {title}" in message
    assert "Question:\nWhich movies exist?" in message


def test_messages_include_system_instruction() -> None:
    messages = messages_for("Movie {title}", "Which movies exist?")
    assert messages[0] == {"role": "system", "content": SYSTEM_MESSAGE}
    assert messages[1]["role"] == "user"


def test_system_instruction_requires_cypher_only_output() -> None:
    assert "first token must be a Cypher clause" in SYSTEM_MESSAGE
    assert "SQL, SELECT, or FROM" in SYSTEM_MESSAGE
