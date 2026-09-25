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
    near = match.context or ""
    if name.lower() in near:
        near = near.replace(name.lower(), "", 1)
    near = " ".join(near.split())
    if len(near) > 60:
        near = near[:57].rstrip() + "..."
    return CandidateView(
        number=number,
        kind=KIND.get(match.role, "Elemento"),
        name=name[:60],
        near=near,
    )
