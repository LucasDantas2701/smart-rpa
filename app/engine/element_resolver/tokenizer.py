from .constants import (
    ACTION_WORDS,
    STOPWORDS,
    STRUCTURAL_WORDS,
    SYNONYMS,
    TOKEN_RE,
)


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.split(text.lower())
        if token
    }


def normalize_tokens(tokens: set[str]) -> set[str]:
    normalized = set()

    for token in tokens:
        normalized.add(
            SYNONYMS.get(token, token)
        )

    return normalized


def extract_object_tokens(
    normalized_query_tokens: set[str],
    action_query_tokens: set[str],
) -> set[str]:
    """
    Extrai os tokens semanticamente relevantes
    da consulta.
    """

    return (
        normalized_query_tokens
        - action_query_tokens
        - STRUCTURAL_WORDS
        - STOPWORDS
    )