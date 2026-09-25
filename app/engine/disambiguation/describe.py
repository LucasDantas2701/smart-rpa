"""Descreve um Match para uma pessoa não-técnica."""

from app.engine.element_resolver import Match

from .types import CandidateView

KIND = {
    "button": "Botão", "link": "Link", "textbox": "Campo de texto", "searchbox": "Campo de busca",
    "checkbox": "Caixa de marcação", "radio": "Opção", "combobox": "Lista de opções",
    "listbox": "Lista de opções", "switch": "Chave liga/desliga", "tab": "Aba",
    "menuitem": "Item de menu", "option": "Opção", "slider": "Controle deslizante",
    "spinbutton": "Campo numérico", "clickable": "Área clicável",
}


def describe(match: Match, number: int) -> CandidateView:
    name = match.label or match.text or match.hint or match.value or "(sem texto)"
    near = " ".join((match.context or "").split())

    # Tira o próprio nome do elemento do "perto de" (sem diferenciar maiúsculas).
    start = near.lower().find(name.lower())
    if start >= 0:
        near = " ".join((near[:start] + near[start + len(name):]).split())
    if len(near) > 60:
        near = near[:57].rstrip() + "..."
    return CandidateView(
        number=number,
        kind=KIND.get(match.role, "Elemento"),
        name=name[:60],
        near=near,
    )
