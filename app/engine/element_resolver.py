from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from playwright.sync_api import Locator, Page


DEFAULT_SELECTOR = ",".join([
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a[href]",
    "button",
    "input",
    "select",
    "textarea",
    "[role]",
    "[contenteditable]",
    "[tabindex]",
    "[data-testid]",
    "[data-test]",
    "[data-qa]",
    "summary",
    "label",
])


TOKEN_RE = re.compile(r"[^a-z0-9à-ÿ]+")


# Normalização inicial para testes multilíngues.
# A ideia é permitir que uma descrição em português
# encontre informações em inglês presentes na página.
SYNONYMS = {
    "botão": "button",
    "botoes": "button",
    "botões": "button",
    "adicionar": "add",
    "adicione": "add",
    "carrinho": "cart",
    "mochila": "backpack",
    "bicicleta": "bike",
    "luz": "light",
    "camisa": "shirt",
    "jaqueta": "jacket",
    "macacão": "onesie",
    # Verbos genéricos de ação (não específicos de nenhum site).
    # Mapeiam para a mesma palavra em inglês que normalmente aparece
    # no texto/atributos de botões e links em páginas reais.
    "comprar": "buy",
    "remover": "remove",
    "excluir": "delete",
    "apagar": "delete",
    "selecionar": "select",
    "escolher": "choose",
    "buscar": "search",
    "pesquisar": "search",
    "continuar": "continue",
    "voltar": "back",
    "enviar": "send",
    "confirmar": "confirm",
    "cancelar": "cancel",
    "salvar": "save",
    "atualizar": "update",
    "filtrar": "filter",
    "ordenar": "sort",
    "abrir": "open",
    "fechar": "close",
    "entrar": "login",
    "sair": "logout",
}


# Palavras que indicam uma *ação* (verbo), em oposição a palavras que
# descrevem o *objeto/contexto* da consulta (ex: "mochila", "carrinho").
# Usadas para separar "o elemento que executa a ação" de elementos que
# apenas compartilham o mesmo objeto/contexto. Deliberadamente genérico:
# nenhuma dessas palavras é específica de um site.
ACTION_WORDS = {
    "add", "remove", "delete", "buy", "purchase", "submit", "save",
    "cancel", "confirm", "open", "close", "select", "choose", "click",
    "edit", "update", "search", "login", "logout", "signup", "subscribe",
    "upload", "download", "send", "apply", "filter", "sort", "checkout",
    "increase", "decrease", "view", "continue", "next", "back", "clear",
}
STOPWORDS = {
    "a",
    "o",
    "as",
    "os",
    "um",
    "uma",
    "uns",
    "umas",
    "de",
    "do",
    "da",
    "dos",
    "das",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "por",
    "com",
    "sem",
    "ao",
    "aos",
    "à",
    "às",
}

STRUCTURAL_WORDS = {
    "button",
    "link",
    "input",
    "textbox",
    "field",
    "campo",
    "element",
    "elemento",
}


# Quanto um match entre os verbos da consulta e o CONTEÚDO PRÓPRIO do
# elemento (não o contexto) pesa a favor dele. Isso é o que separa
# "Add to cart" (contém "add") de "Sauce Labs Backpack" (não contém).
ACTION_CONTENT_BONUS = 0.30

# Quando a consulta tem verbo de ação mas o elemento não tem nenhuma
# palavra de ação no seu próprio conteúdo, o score acumulado até ali
# (frase/tokens/semântica/contexto) é multiplicado por este fator.
# Isso evita que um elemento só "relacionado ao contexto" (ex: o nome
# do produto, ou um ícone de carrinho) fique empatado com o elemento
# que realmente executa a ação.
ACTION_MISMATCH_DAMPING = 0.55

# Quanto uma correspondência do objeto da consulta
# dentro do contexto do elemento pesa.
OBJECT_CONTEXT_BONUS = 0.30

# Quando a consulta possui um objeto específico e o contexto
# do candidato não contém nenhuma evidência desse objeto.
OBJECT_MISMATCH_DAMPING = 0.70

# Para extração de texto, privilegia elementos cujo próprio
# texto contém a entidade procurada.
EXTRACT_TEXT_BONUS = 0.15


# Peso adicional baseado no tipo de ação desejada.
#
# Isso permite que a mesma descrição seja interpretada
# de maneira diferente dependendo da operação.
ACTION_ROLE_WEIGHTS = {
    "click": {
        "button": 0.15,
        "link": 0.12,
        "checkbox": 0.10,
        "radio": 0.10,
        "combobox": 0.08,
        "div": -0.05,
        "span": -0.05,
        "p": -0.05,
    },
    "fill": {
        "textbox": 0.15,
        "input": 0.15,
        "textarea": 0.15,
        "combobox": 0.10,
        "button": -0.10,
        "link": -0.10,
    },
    "extract": {
        "button": 0.0,
        "link": 0.0,
    },
}


def tokenize(text: str) -> set[str]:
    """
    Divide um texto em palavras normalizadas.
    """

    return {
        token
        for token in TOKEN_RE.split(text.lower())
        if token
    }


def normalize_tokens(tokens: set[str]) -> set[str]:
    """
    Normaliza tokens utilizando o dicionário de sinônimos.
    """

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
    Extrai os tokens semanticamente relevantes da consulta.
    """

    structural_words = {
        "button",
        "link",
        "input",
        "textbox",
        "field",
        "element",
        "elemento",
    }

    stopwords = {
        "a",
        "o",
        "as",
        "os",
        "um",
        "uma",
        "uns",
        "umas",
        "de",
        "do",
        "da",
        "dos",
        "das",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "para",
        "por",
        "com",
        "sem",
        "ao",
        "aos",
        "à",
        "às",
    }

    return (
        normalized_query_tokens
        - action_query_tokens
        - structural_words
        - stopwords
    )

@dataclass
class Match:
    """
    Representa um elemento encontrado pelo ElementResolver.
    """

    id: str
    tag: str
    role: str
    label: str
    text: str
    content: str
    context: str
    rect: dict
    score: float
    page: Page = field(repr=False)

    @property
    def locator(self) -> Locator:
        """
        Retorna um Locator do elemento encontrado.
        """

        return self.page.locator(
            f'[data-er-id="{self.id}"]'
        )

    def click(self, **kwargs) -> None:
        """
        Clica no elemento encontrado.
        """

        self.locator.click(**kwargs)

    def fill(self, value: str, **kwargs) -> None:
        """
        Preenche um campo encontrado.
        """

        self.locator.fill(value, **kwargs)

    def __repr__(self) -> str:
        return (
            f"Match("
            f"score={self.score:.2f}, "
            f"role='{self.role}', "
            f"text='{self.text}', "
            f"context='{self.context}'"
            f")"
        )


_INDEX_JS = """
(args) => {
    const [selector, includeHidden] = args;

    function isVisible(el) {
        const rect = el.getBoundingClientRect();

        if (rect.width === 0 && rect.height === 0) {
            return false;
        }

        const style = getComputedStyle(el);

        if (style.visibility === "hidden") {
            return false;
        }

        if (style.display === "none") {
            return false;
        }

        if (parseFloat(style.opacity) === 0) {
            return false;
        }

        return true;
    }

    function accessibleLabel(el) {
        const aria = el.getAttribute("aria-label");

        if (aria) {
            return aria.trim();
        }

        const labelledBy = el.getAttribute("aria-labelledby");

        if (labelledBy) {
            const joined = labelledBy
                .split(/\\s+/)
                .map((id) => {
                    const element = document.getElementById(id);

                    return element
                        ? (element.innerText || element.textContent)
                        : "";
                })
                .filter(Boolean)
                .join(" ");

            if (joined) {
                return joined.trim();
            }
        }

        if (el.labels && el.labels.length) {
            return Array
                .from(el.labels)
                .map((label) => label.innerText)
                .join(" ")
                .trim();
        }

        return "";
    }

    function ownText(el) {
        const raw =
            el.innerText !== undefined
                ? el.innerText
                : el.textContent;

        return (raw || "")
            .trim()
            .replace(/\\s+/g, " ")
            .slice(0, 200);
    }

    function contextText(el) {
        /*
         * Procura um contexto próximo do elemento.
         *
         * A ideia é evitar pegar o texto da página inteira.
         * Primeiro tentamos encontrar um container próximo
         * que represente um componente/card.
         */

        const preferredSelectors = [
            ".inventory_item",
            "[data-testid='inventory-item']",
            "[data-test='inventory-item']",
            "article",
            "[role='article']",
            "li"
        ];

        for (const selector of preferredSelectors) {
            const container = el.closest(selector);

            if (container) {
                return ownText(container);
            }
        }

        /*
         * Fallback genérico:
         * sobe alguns níveis na árvore procurando um
         * container com uma quantidade razoável de texto.
         */

        let parent = el.parentElement;

        for (let i = 0; i < 4 && parent; i++) {
            const text = ownText(parent);

            if (
                text &&
                text.length >= 10 &&
                text.length <= 500
            ) {
                return text;
            }

            parent = parent.parentElement;
        }

        return "";
    }

    const implicitRoles = {
        a: "link",
        button: "button",
        input: "input",
        select: "listbox",
        textarea: "textbox",
        summary: "button",
        label: "label"
    };

    const nodes = Array.from(
        document.querySelectorAll(selector)
    );

    const records = [];

    let index = 0;

    for (const el of nodes) {

        if (!includeHidden && !isVisible(el)) {
            continue;
        }

        const id = "el-" + index++;

        el.setAttribute("data-er-id", id);

        const tag = el.tagName.toLowerCase();

        const role =
            el.getAttribute("role")
            || implicitRoles[tag]
            || tag;

        const label = accessibleLabel(el);

        const text = ownText(el);

        const value =
            "value" in el
                ? String(el.value || "")
                : "";

        const placeholder =
            el.getAttribute("placeholder")
            || "";

        const title =
            el.getAttribute("title")
            || "";

        const testId =
            el.getAttribute("data-testid")
            || el.getAttribute("data-test")
            || el.getAttribute("data-qa")
            || "";

        const context = contextText(el);

        const rect = el.getBoundingClientRect();

        const content = [
            label,
            text,
            value,
            placeholder,
            title,
            testId,
            el.id,
            tag,
            role
        ]
        .filter(Boolean)
        .join(" ");

        records.push({
            id,
            tag,
            role,
            label,
            text,
            context: context.toLowerCase(),
            content: content.toLowerCase(),
            rect: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            }
        });
    }

    return records;
}
"""


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

        self._records = self.page.evaluate(
            _INDEX_JS,
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

        # Palavras de ação presentes na consulta (ex: "add", vindo de
        # "adicionar"). Vazio se a consulta não menciona nenhum verbo
        # reconhecido — nesse caso o comportamento de ranking não muda.
        action_query_tokens = (
            normalized_query_tokens & ACTION_WORDS
            if action
            else set()
        )
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

            score = self._score(
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

    @staticmethod
    def _score(
        content: str,
        context: str,
        text: str,
        query: str,
        query_tokens: set[str],
        normalized_query_tokens: set[str],
        action_query_tokens: set[str],
        object_query_tokens: set[str],
        role: str,
        tag: str,
        action: str | None = None,
    ) -> float:
        """
        Calcula a relevância de um elemento
        em relação à descrição.
        """

        if not content or not query:
            return 0.0

        score = 0.0

        content_tokens = tokenize(content)
        context_tokens = tokenize(context)

        normalized_content_tokens = normalize_tokens(
            content_tokens
        )

        normalized_context_tokens = normalize_tokens(
            context_tokens
        )

        # -------------------------------------------------
        # 1. Correspondência da frase completa.
        # -------------------------------------------------

        if query in content:
            score += 0.35

        # -------------------------------------------------
        # 2. Correspondência direta das palavras no elemento.
        # -------------------------------------------------

        if query_tokens:

            hits = 0.0

            for token in query_tokens:

                if token in content_tokens:
                    hits += 1.0

                elif token in content:
                    hits += 0.5

            score += (
                hits / len(query_tokens)
            ) * 0.25

        # -------------------------------------------------
        # 3. Correspondência semântica no elemento.
        # -------------------------------------------------

        if normalized_query_tokens:

            normalized_hits = (
                normalized_query_tokens
                & normalized_content_tokens
            )

            score += (
                len(normalized_hits)
                / len(normalized_query_tokens)
            ) * 0.20

        # -------------------------------------------------
        # 4. Correspondência contextual.
        # -------------------------------------------------

        if normalized_query_tokens:

            context_hits = (
                normalized_query_tokens
                & normalized_context_tokens
            )

            score += (
                len(context_hits)
                / len(normalized_query_tokens)
            ) * 0.15

        # -------------------------------------------------
        # 4.5. Objeto/contexto.
        #
        # O objeto é mais importante que palavras genéricas
        # como "button", "add", "cart".
        # -------------------------------------------------

# -------------------------------------------------
# 4.5. Correspondência do objeto no contexto.
#
# Para ações, o objeto é o principal discriminador
# entre elementos semelhantes.
# -------------------------------------------------

        if object_query_tokens and action:

            object_hits = (
                object_query_tokens
                & normalized_context_tokens
            )

            object_coverage = (
                len(object_hits)
                / len(object_query_tokens)
            )

            # Se o candidato não pertence ao objeto procurado,
            # ele perde bastante relevância.
            if object_coverage == 0.0:
                score *= 0.50

            else:
                # O contexto correto recebe um peso forte.
                score += object_coverage * 0.35

                # Se todos os objetos da consulta aparecem no
                # contexto, recebe um bônus adicional.
                if object_coverage == 1.0:
                    score += 0.20
        # -------------------------------------------------
        # 4.6. Correspondência direta do objeto no próprio
        # elemento.
        #
        # Se o objeto aparece no próprio elemento, isso é
        # ainda mais forte do que aparecer apenas no contexto.
        # -------------------------------------------------

        if object_query_tokens:

            direct_object_hits = (
                object_query_tokens
                & normalized_content_tokens
            )

            if direct_object_hits:

                direct_object_coverage = (
                    len(direct_object_hits)
                    / len(object_query_tokens)
                )

                score += (
                    direct_object_coverage
                    * 0.20
                )

        # -------------------------------------------------
        # 5. Correspondência do tipo de elemento.
        # -------------------------------------------------

        if role in normalized_query_tokens:
            score += 0.05

        elif tag in normalized_query_tokens:
            score += 0.05

        # -------------------------------------------------
        # 6. Preferência por elementos interativos.
        # -------------------------------------------------

        interactive_roles = {
            "button",
            "link",
            "textbox",
            "checkbox",
            "radio",
            "combobox",
            "listbox",
        }

        if role in interactive_roles:
            score += 0.10

        elif tag in {
            "button",
            "a",
            "input",
            "select",
            "textarea",
        }:
            score += 0.10

        elif tag in {
            "div",
            "span",
            "p",
        }:
            score -= 0.05

        # -------------------------------------------------
        # 7. Alinhamento da ação com o conteúdo.
        # -------------------------------------------------

        if action_query_tokens:

            action_hits = (
                action_query_tokens
                & normalized_content_tokens
            )

            action_coverage = (
                len(action_hits)
                / len(action_query_tokens)
            )

            score += (
                action_coverage
                * ACTION_CONTENT_BONUS
            )

            if action_coverage == 0.0:
                score *= ACTION_MISMATCH_DAMPING

        # -------------------------------------------------
        # 8. Peso baseado no tipo de ação.
        # -------------------------------------------------

        if action:

            action_weights = ACTION_ROLE_WEIGHTS.get(
                action,
                {}
            )

            if role in action_weights:
                score += action_weights[role]

            elif tag in action_weights:
                score += action_weights[tag]

        # -------------------------------------------------
        # 9. Extração de texto.
        #
        # Aqui não queremos simplesmente somar pontos.
        # Queremos diferenciar:
        #
        #   <div> ... Backpack ... muitos elementos ... </div>
        #
        # de:
        #
        #   <div>Backpack</div>
        #
        # -------------------------------------------------

        if action == "extract" and normalized_query_tokens:

            normalized_text_tokens = normalize_tokens(
                tokenize(text)
            )

            text_hits = (
                normalized_query_tokens
                & normalized_text_tokens
            )

            text_coverage = (
                len(text_hits)
                / len(normalized_query_tokens)
            )

            # O texto próprio do elemento é muito importante
            # para operações de extração.
            score += (
                text_coverage
                * 0.30
            )

            # Se o texto próprio corresponde exatamente
            # à consulta, trata como um forte sinal de que
            # este é o elemento que deve ser extraído.
            normalized_text = " ".join(
                sorted(normalized_text_tokens)
            )

            normalized_query = " ".join(
                sorted(normalized_query_tokens)
            )

            if normalized_text == normalized_query:
                score += 0.35

            # Elementos com muito texto adicional são menos
            # específicos para uma operação de extração.
            if text and query:

                text_normalized = " ".join(
                    tokenize(text)
                )

                query_normalized = " ".join(
                    tokenize(query)
                )

                if text_normalized == query_normalized:
                    score += 0.25

        return max(0.0,score)