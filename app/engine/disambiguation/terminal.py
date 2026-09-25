"""Desempate pelo terminal (interface provisória, até existir o frontend)."""

from __future__ import annotations

import os
import sys
import tempfile
import webbrowser

from .types import ChoiceRequest, UserChoice

_ACTIONS = {
    "click": "clicar", "hover": "passar o mouse", "check": "marcar", "uncheck": "desmarcar",
    "press": "pressionar uma tecla em", "fill": "preencher", "select": "escolher uma opção em",
    "extract_text": "ler o texto de", "extract_attribute": "ler", "extract_value": "ler o valor de",
}


class TerminalDisambiguator:
    def __init__(self, open_screenshot: bool = True, input_fn=input, output=print):
        self.open_screenshot = open_screenshot
        self._input = input_fn
        self._print = output

    def notify(self, message: str) -> None:
        self._print(f"\n>>> {message}")

    def choose(self, request: ChoiceRequest) -> UserChoice:
        p = self._print
        verb = _ACTIONS.get(request.action, request.action)
        p("")
        p("=" * 64)
        if request.reason == "ambiguous":
            p(f"Encontrei mais de um elemento possível para: \"{request.description}\"")
        else:
            p(f"Não tenho certeza de onde {verb}: \"{request.description}\"")
        p("=" * 64)

        if request.candidates:
            where = "na janela do navegador" if request.can_point else "na imagem"
            p(f"Os candidatos estão numerados {where}:")
            for c in request.candidates:
                near = f"  (perto de: {c.near})" if c.near else ""
                p(f"  [{c.number}] {c.kind} \"{c.name}\"{near}")

        if request.screenshot and self.open_screenshot:
            self._show(request.screenshot)

        options = []
        if request.candidates:
            options.append(f"número de 1 a {len(request.candidates)}")
        if request.can_point:
            options.append("C para clicar você mesmo no navegador")
        options.append("P para pular este passo")
        prompt = "Digite " + ", ".join(options) + ": "

        while True:
            answer = self._input(prompt).strip().lower()
            if answer == "p":
                return UserChoice("skip")
            if answer == "c" and request.can_point:
                return UserChoice("point")
            if answer.isdigit() and 1 <= int(answer) <= len(request.candidates):
                return UserChoice("candidate", int(answer))
            p("Resposta não reconhecida, tente de novo.")

    def _show(self, png: bytes) -> None:
        fd, path = tempfile.mkstemp(suffix=".png", prefix="desempate_")
        with os.fdopen(fd, "wb") as f:
            f.write(png)
        self._print(f"(imagem salva em {path})")
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                webbrowser.open(f"file://{path}")
        except Exception:
            pass
