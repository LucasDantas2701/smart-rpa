from typing import Callable

from playwright.sync_api import Page

from .loader import load_index_script
from .match import Match
from .scoring import score_element
from .tokenizer import (
    ACTION_WORDS_N,
    build_synonyms,
    extract_object_tokens,
    normalize_text,
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
        include_hidden: bool = False,
        context_selectors: list[str] | None = None,
        selector: str | None = None,
        synonyms: dict[str, str] | None = None,
    ):
        """
        context_selectors:
            Containers específicos de um site para o contexto
            (ex.: [".inventory_item"]). Opcional: o script já
            tem uma heurística genérica.

        selector:
            Seletor CSS fixo. Se informado, desliga a detecção
            automática do script (use só para depuração).

        synonyms:
            Vocabulário específico do site ou da automação salva
            (ex.: {"mochila": "backpack"}). Soma-se ao dicionário
            genérico, sem precisar alterar o constants.py.
        """

        self.page = page
        self.include_hidden = include_hidden
        self.context_selectors = context_selectors or []
        self.selector = selector
        self._script = load_index_script()
        self._records: list[dict] = []
        self._synonyms = build_synonyms(synonyms or {})

    def index(self, mode: str = "interactive") -> int:
        """
        Analisa a página e cria o índice de elementos.

        mode:
            "interactive": só elementos clicáveis/preenchíveis.
            "content": interativos + elementos com texto (extração).
        """

        self._records = self.page.evaluate(
            self._script,
            {
                "mode": mode,
                "selector": self.selector,
                "includeHidden": self.include_hidden,
                "contextSelectors": self.context_selectors,
            },
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

        # Reindexa a cada consulta: a página pode ter mudado
        # desde a última (navegação, re-render). Corrige o B2.
        self.index(
            "content" if action == "extract" else "interactive"
        )

        query = normalize_text(description).strip()

        query_tokens = tokenize(query)

        normalized_query_tokens = normalize_tokens(
            query_tokens,
            self._synonyms,
        )

        # Palavras de ação presentes na consulta.
        action_query_tokens = (
            normalized_query_tokens & ACTION_WORDS_N
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
                synonyms=self._synonyms,
                state=record.get("state"),
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
                type=record.get("type", ""),
                value=record.get("value", ""),
                hint=record.get("hint", ""),
                href=record.get("href", ""),
                state=record.get("state", {}),
                options=record.get("options", []),
                in_viewport=record.get("inViewport", True),
                obscured=record.get("obscured", False),
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