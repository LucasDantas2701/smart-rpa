"""
Demonstração do desempate pelo usuário, com o navegador visível.

Rodar na raiz do projeto:

    python -m examples.desempate

Passo 1 é ambíguo (dois botões "Add to cart" parecidos): o terminal
pergunta qual deles, e os números aparecem na janela do navegador.
Passo 2 não é encontrado pela heurística: digite C e clique no
coração da cafeteira na janela do navegador.
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

from app.engine.action_executor import ActionExecutor
from app.engine.disambiguation import TerminalDisambiguator

PAGE = Path(__file__).resolve().parent.parent / "eval" / "fixtures" / "loja.html"

STEPS = [
    ("click", "adicionar ao carrinho"),
    ("click", "marcar a cafeteira como favorita"),
]


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(PAGE.as_uri())

        executor = ActionExecutor(
            page,
            disambiguator=TerminalDisambiguator(),
            can_point=True,
        )

        for action, description in STEPS:
            result = getattr(executor, action)(description)
            print(f"\nResultado: {result}")

        input("\nEnter para fechar o navegador...")
        browser.close()


if __name__ == "__main__":
    main()
