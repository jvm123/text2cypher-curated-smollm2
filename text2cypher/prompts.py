"""Prompt construction for Text-to-Cypher generation."""

from __future__ import annotations

SYSTEM_MESSAGE = (
    "You are a text-to-Cypher engine for Neo4j. Given a graph schema and a "
    "natural language question, output one valid Cypher query that answers the "
    "question. Use only labels, relationship types, and properties in the schema. "
    "Your first token must be a Cypher clause such as MATCH, CALL, WITH, UNWIND, "
    "CREATE, MERGE, or RETURN. Output only the Cypher query, without explanation, "
    "comments, Markdown fences, SQL, SELECT, or FROM."
)


def user_message(schema: str, question: str) -> str:
    """Create the user turn for a dataset example."""
    return f"Schema:\n{schema}\n\nQuestion:\n{question}"


def messages_for(schema: str, question: str) -> list[dict[str, str]]:
    """Create the chat messages supplied to the model tokenizer."""
    return [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": user_message(schema, question)},
    ]


def generation_prompt(tokenizer: object, schema: str, question: str) -> str:
    """Render the model-native prompt ending with an assistant turn."""
    return tokenizer.apply_chat_template(
        messages_for(schema, question),
        tokenize=False,
        add_generation_prompt=True,
    )
