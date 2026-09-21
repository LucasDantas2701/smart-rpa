from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from playwright.sync_api import Page

from app.engine.element_resolver import ElementResolver, Match


# Ação do Executor → ação correspondente passada para
# ElementResolver.query().
RESOLVER_ACTION_MAP = {
    "click": "click",
    "hover": "click",
    "check": "click",
    "uncheck": "click",
    "press": "click",
    "fill": "fill",
    "select": "fill",
    "extract_text": "extract",
    "extract_attribute": "extract",
    "extract_value": "extract",
}


# Score mínimo do melhor candidato para considerar
# a resolução confiável.
DEFAULT_MIN_SCORE = 0.20


# Diferença mínima entre o primeiro e o segundo candidato
# para considerar a escolha suficientemente clara.
#
# Exemplo:
#
# 0.79
# 0.74
#
# gap = 0.05
#
# Como 0.05 < 0.08, a ação será considerada ambígua.
DEFAULT_AMBIGUITY_GAP = 0.08


# Quantidade máxima de candidatos analisados pelo Executor.
DEFAULT_K = 5


@dataclass
class ActionResult:
    """
    Resultado estruturado de uma ação do ActionExecutor.

    status:

        success
            A ação foi executada com sucesso.

        ambiguous
            Existem candidatos com scores muito próximos.
            Nenhuma ação foi executada.

        not_found
            Nenhum candidato confiável foi encontrado.

        error
            Um candidato foi selecionado, mas a execução
            da ação falhou.
    """

    status: str
    action: str
    description: str

    selected_element: Optional[Match] = None
    score: Optional[float] = None
    value: Optional[Any] = None
    candidates: Optional[list[Match]] = None
    error: Optional[str] = None

    def __bool__(self) -> bool:
        """
        Permite utilizar:

            if result:
                ...

        O resultado só é considerado verdadeiro quando
        a ação foi executada com sucesso.
        """

        return self.status == "success"

    def raise_if_error(self) -> "ActionResult":
        """
        Levanta ActionExecutionError caso a ação
        não tenha sido executada com sucesso.
        """

        if self.status != "success":
            raise ActionExecutionError(self)

        return self

    def __repr__(self) -> str:

        if self.status == "success":

            element = self.selected_element

            label = (
                element.label or element.text
                if element
                else ""
            )

            return (
                f"ActionResult("
                f"status='success', "
                f"action='{self.action}', "
                f"score={self.score:.2f}, "
                f"element='{label}'"
                f")"
            )

        if self.status == "ambiguous":

            scores = ", ".join(
                f"{candidate.score:.2f}"
                for candidate in (self.candidates or [])[:3]
            )

            return (
                f"ActionResult("
                f"status='ambiguous', "
                f"action='{self.action}', "
                f"candidates=[{scores}]"
                f")"
            )

        if self.status == "error":

            return (
                f"ActionResult("
                f"status='error', "
                f"action='{self.action}', "
                f"error='{self.error}'"
                f")"
            )

        return (
            f"ActionResult("
            f"status='not_found', "
            f"action='{self.action}', "
            f"description='{self.description}'"
            f")"
        )


class ActionExecutionError(Exception):
    """
    Exceção levantada por ActionResult.raise_if_error().
    """

    def __init__(self, result: ActionResult):

        self.result = result

        super().__init__(repr(result))


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
    ):
        self.page = page

        self.resolver = (
            resolver
            if resolver is not None
            else ElementResolver(page)
        )

        self.min_score = min_score
        self.ambiguity_gap = ambiguity_gap
        self.k = k

    # ---------------------------------------------------------
    # Resolução
    # ---------------------------------------------------------

    def _resolve(
        self,
        description: str,
        resolver_action: str,
    ) -> tuple[
        str,
        Optional[Match],
        Optional[list[Match]],
    ]:
        """
        Consulta o ElementResolver e decide se existe
        um candidato seguro para executar.

        Retorna:

            (
                status,
                elemento_selecionado,
                candidatos
            )

        status pode ser:

            success
            ambiguous
            not_found
        """

        matches = self.resolver.query(
            description,
            k=self.k,
            action=resolver_action,
        )

        # Nenhum candidato ou score insuficiente.
        if (
            not matches
            or matches[0].score < self.min_score
        ):
            return (
                "not_found",
                None,
                matches,
            )

        # Apenas um candidato confiável.
        if len(matches) == 1:
            return (
                "success",
                matches[0],
                matches,
            )

        # Verifica a diferença entre o primeiro
        # e o segundo candidato.
        gap = (
            matches[0].score
            - matches[1].score
        )

        # Os candidatos estão próximos demais.
        if gap < self.ambiguity_gap:
            return (
                "ambiguous",
                None,
                matches,
            )

        # Primeiro candidato suficientemente acima
        # do segundo.
        return (
            "success",
            matches[0],
            matches,
        )

    # ---------------------------------------------------------
    # Execução genérica
    # ---------------------------------------------------------

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

        # -----------------------------------------------------
        # Elemento não encontrado
        # -----------------------------------------------------

        if status == "not_found":

            return ActionResult(
                status="not_found",
                action=action_name,
                description=description,
                candidates=candidates,
            )

        # -----------------------------------------------------
        # Elemento ambíguo
        # -----------------------------------------------------

        if status == "ambiguous":

            return ActionResult(
                status="ambiguous",
                action=action_name,
                description=description,
                candidates=candidates,
            )

        # -----------------------------------------------------
        # Execução
        # -----------------------------------------------------
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
            )

        # -----------------------------------------------------
        # Sucesso
        # -----------------------------------------------------

        return ActionResult(
            status="success",
            action=action_name,
            description=description,
            selected_element=match,
            score=match.score,
            value=value,
        )

    # ---------------------------------------------------------
    # Interação
    # ---------------------------------------------------------

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
        """
        Seleciona uma opção de um <select>.

        Pode receber:

            value="valor"

        ou:

            label="Texto"

        ou:

            index=0
        """

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

    # ---------------------------------------------------------
    # Extração
    # ---------------------------------------------------------

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