from __future__ import annotations

from typing import Any, Callable, Optional

from playwright.sync_api import Page

from app.engine.disambiguation import (
    ChoiceRequest,
    Disambiguator,
    capture_click,
    clear_highlights,
    describe,
    highlight_candidates,
)
from app.engine.element_resolver import ElementResolver, Match

from .constants import (
    DEFAULT_AMBIGUITY_GAP,
    DEFAULT_K,
    DEFAULT_MIN_SCORE,
    RESOLVER_ACTION_MAP,
)
from .result import ActionResult


class ActionExecutor:
    """
    Orquestra ElementResolver + execução de ações no Playwright.

    Fluxo:

        descrição
            ↓
        ElementResolver
            ↓
        candidatos
            ↓
        score mínimo
            ↓
        verificação de ambiguidade
            ↓
        elemento selecionado
            ↓
        execução
            ↓
        ActionResult
    """

    def __init__(
        self,
        page: Page,
        resolver: Optional[ElementResolver] = None,
        min_score: float = DEFAULT_MIN_SCORE,
        ambiguity_gap: float = DEFAULT_AMBIGUITY_GAP,
        k: int = DEFAULT_K,
        disambiguator: Optional[Disambiguator] = None,
        can_point: bool = False,
        max_choices: int = 5,
        point_timeout_s: float = 120,
    ):
        """
        disambiguator:
            Quem pergunta ao usuário quando a heurística recusa
            (ambiguous / not_found). Sem ele, o Executor devolve a
            recusa, como antes.

        can_point:
            True quando o navegador está visível (headed): o usuário
            pode clicar direto no elemento.
        """
        self.page = page

        self.resolver = (
            resolver
            if resolver is not None
            else ElementResolver(page)
        )

        self.min_score = min_score
        self.ambiguity_gap = ambiguity_gap
        self.k = k
        self.disambiguator = disambiguator
        self.can_point = can_point
        self.max_choices = max_choices
        self.point_timeout_s = point_timeout_s

    def _resolve(
        self,
        description: str,
        resolver_action: str,
    ) -> tuple[
        str,
        Optional[Match],
        Optional[list[Match]],
    ]:

        matches = self.resolver.query(
            description,
            k=self.k,
            action=resolver_action,
        )

        if (
            not matches
            or matches[0].score < self.min_score
        ):
            return (
                "not_found",
                None,
                matches,
            )

        if len(matches) == 1:
            return (
                "success",
                matches[0],
                matches,
            )

        # Margem relativa ao score do 1º colocado (ver constants.py).
        gap = (
            matches[0].score
            - matches[1].score
        ) / matches[0].score

        if gap < self.ambiguity_gap:
            return (
                "ambiguous",
                None,
                matches,
            )

        return (
            "success",
            matches[0],
            matches,
        )

    def _run(
        self,
        description: str,
        action_name: str,
        fn: Callable[[Match], Any],
    ) -> ActionResult:

        resolver_action = RESOLVER_ACTION_MAP.get(
            action_name,
            action_name,
        )

        status, match, candidates = self._resolve(
            description,
            resolver_action,
        )

        resolved_by = "heuristic"

        if status in ("not_found", "ambiguous"):

            if self.disambiguator is None:
                return ActionResult(
                    status=status,
                    action=action_name,
                    description=description,
                    candidates=candidates,
                )

            match = self._ask_user(
                description, action_name, status, candidates or []
            )

            if match is None:
                return ActionResult(
                    status=status,
                    action=action_name,
                    description=description,
                    candidates=candidates,
                    resolved_by="user_skipped",
                )

            resolved_by = "user"

        assert match is not None

        try:
            value = fn(match)

        except Exception as exc:
            return ActionResult(
                status="error",
                action=action_name,
                description=description,
                selected_element=match,
                score=match.score,
                error=str(exc),
                resolved_by=resolved_by,
            )

        return ActionResult(
            status="success",
            action=action_name,
            description=description,
            selected_element=match,
            score=match.score,
            value=value,
            resolved_by=resolved_by,
        )

    def _ask_user(
        self,
        description: str,
        action_name: str,
        reason: str,
        candidates: list[Match],
    ) -> Optional[Match]:
        """Desempate: destaca os candidatos, pergunta e devolve a escolha."""

        shown = candidates[: self.max_choices]

        try:
            highlight_candidates(self.page, shown)
            screenshot = (
                None if self.can_point
                else self.page.screenshot(full_page=True)
            )
            choice = self.disambiguator.choose(ChoiceRequest(
                action=action_name,
                description=description,
                reason=reason,
                candidates=[describe(m, i) for i, m in enumerate(shown, 1)],
                screenshot=screenshot,
                can_point=self.can_point,
            ))
        finally:
            clear_highlights(self.page)

        if choice.kind == "candidate" and choice.number:
            return shown[choice.number - 1]

        if choice.kind == "point" and self.can_point:
            self.disambiguator.notify(
                "Clique no elemento na janela do navegador."
            )
            return capture_click(self.page, self.point_timeout_s)

        return None

    def click(
        self,
        description: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "click",
            lambda match: match.locator.click(
                **kwargs
            ),
        )

    def hover(
        self,
        description: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "hover",
            lambda match: match.locator.hover(
                **kwargs
            ),
        )

    def check(
        self,
        description: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "check",
            lambda match: match.locator.check(
                **kwargs
            ),
        )

    def uncheck(
        self,
        description: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "uncheck",
            lambda match: match.locator.uncheck(
                **kwargs
            ),
        )

    def press(
        self,
        description: str,
        key: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "press",
            lambda match: match.locator.press(
                key,
                **kwargs,
            ),
        )

    def fill(
        self,
        description: str,
        value: str,
        **kwargs,
    ) -> ActionResult:

        return self._run(
            description,
            "fill",
            lambda match: match.locator.fill(
                value,
                **kwargs,
            ),
        )

    def select(
        self,
        description: str,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        **kwargs,
    ) -> ActionResult:

        def _select(match: Match):

            if value is not None:
                return match.locator.select_option(
                    value=value,
                    **kwargs,
                )

            if label is not None:
                return match.locator.select_option(
                    label=label,
                    **kwargs,
                )

            if index is not None:
                return match.locator.select_option(
                    index=index,
                    **kwargs,
                )

            raise ValueError(
                "select() requer value, label ou index"
            )

        return self._run(
            description,
            "select",
            _select,
        )

    def extract_text(
        self,
        description: str,
    ) -> ActionResult:

        return self._run(
            description,
            "extract_text",
            lambda match: match.locator.inner_text(),
        )

    def extract_attribute(
        self,
        description: str,
        attribute: str,
    ) -> ActionResult:

        return self._run(
            description,
            "extract_attribute",
            lambda match: match.locator.get_attribute(
                attribute
            ),
        )

    def extract_value(
        self,
        description: str,
    ) -> ActionResult:

        return self._run(
            description,
            "extract_value",
            lambda match: match.locator.input_value(),
        )