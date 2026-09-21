from .constants import (
    ACTION_CONTENT_BONUS,
    ACTION_MISMATCH_DAMPING,
    ACTION_ROLE_WEIGHTS,
)
from .tokenizer import (
    normalize_tokens,
    tokenize,
)


def score_element(
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

        if object_coverage == 0.0:
            score *= 0.50

        else:
            score += object_coverage * 0.35

            if object_coverage == 1.0:
                score += 0.20

    # -------------------------------------------------
    # 4.6. Correspondência direta do objeto no próprio
    # elemento.
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

        score += (
            text_coverage
            * 0.30
        )

        normalized_text = " ".join(
            sorted(normalized_text_tokens)
        )

        normalized_query = " ".join(
            sorted(normalized_query_tokens)
        )

        if normalized_text == normalized_query:
            score += 0.35

        if text and query:

            text_normalized = " ".join(
                tokenize(text)
            )

            query_normalized = " ".join(
                tokenize(query)
            )

            if text_normalized == query_normalized:
                score += 0.25

    return max(0.0, score)