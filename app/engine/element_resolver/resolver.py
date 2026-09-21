from typing import Callable

from playwright.sync_api import Page

from .constants import ACTION_WORDS, DEFAULT_SELECTOR
from .loader import load_index_script
from .match import Match
from .scoring import score_element
from .tokenizer import (
    extract_object_tokens,
    normalize_tokens,
    tokenize,
)


class ElementResolver:
    """
    Localiza elementos de uma página utilizando
    descrição em linguagem natural.

    Fluxo:

        página
          ↓
        index()
          ↓
        candidatos
          ↓
        contexto
          ↓
        query()
          ↓
        ranking
          ↓
        Match
    """

    def __init__(
        self,
        page: Page,
        selector: str = DEFAULT_SELECTOR,
        include_hidden: bool = False,
    ):
        self.page = page
        self.selector = selector
        self.include_hidden = include_hidden
        self._records: list[dict] = []

    def index(self) -> int:
        """
        Analisa a página e cria o índice de elementos.
        """

        index_script = load_index_script()

        self._records = self.page.evaluate(
            index_script,
            [
                self.selector,
                self.include_hidden,
            ],
        )

        return len(self._records)

    def query(
        self,
        description: str,
        k: int = 5,
        threshold: float = 0.0,
        action: str | None = None,
        filter: Callable[[Match], bool] | None = None,
    ) -> list[Match]:
        """
        Procura elementos relacionados à descrição
        e retorna os melhores candidatos.

        action:
            click
            fill
            extract

        filter:
            Função opcional para filtrar candidatos.
        """

        if not self._records:
            self.index()

        query = description.lower().strip()

        query_tokens = tokenize(query)

        normalized_query_tokens = normalize_tokens(
            query_tokens
        )

        # Palavras de ação presentes na consulta.
        action_query_tokens = (
            normalized_query_tokens & ACTION_WORDS
            if action
            else set()
        )

        # Objetos relevantes da consulta.
        object_query_tokens = (
            extract_object_tokens(
                normalized_query_tokens,
                action_query_tokens,
            )
            if action
            else normalized_query_tokens
        )

        matches = []

        for record in self._records:

            score = score_element(
                content=record["content"],
                context=record["context"],
                query=query,
                query_tokens=query_tokens,
                normalized_query_tokens=normalized_query_tokens,
                action_query_tokens=action_query_tokens,
                object_query_tokens=object_query_tokens,
                role=record["role"],
                tag=record["tag"],
                action=action,
                text=record["text"],
            )

            match = Match(
                id=record["id"],
                tag=record["tag"],
                role=record["role"],
                label=record["label"],
                text=record["text"],
                content=record["content"],
                context=record["context"],
                rect=record["rect"],
                score=score,
                page=self.page,
            )

            matches.append(match)

        if filter:
            matches = [
                match
                for match in matches
                if filter(match)
            ]

        matches = [
            match
            for match in matches
            if match.score >= threshold
        ]

        matches.sort(
            key=lambda match: match.score,
            reverse=True,
        )

        return matches[:k]