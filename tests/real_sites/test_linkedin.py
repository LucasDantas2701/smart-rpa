import time

import pytest

from app.browser.browser import start_browser, close_browser
from app.engine.action_executor import ActionExecutor


@pytest.fixture
def linkedin_page():
    playwright, context = start_browser(
        "profiles/linkedin"
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        "https://www.linkedin.com/feed",
        wait_until="domcontentloaded",
        timeout=30000,
    )

    print("\nURL final:", page.url)
    print("Título:", page.title())

    yield page

    close_browser(playwright, context)

def test_find_linkedin_search(linkedin_page):

    executor = ActionExecutor(linkedin_page)

    result = executor.click(
        "campo de pesquisa"
    )

    print("\nResultado:")
    print(result)

    assert result.status == "success"


def test_debug_linkedin_search_click(linkedin_page):
    executor = ActionExecutor(linkedin_page)

    matches = executor.resolver.query(
        "campo de pesquisa",
        k=10,
        action="click",
    )

    print("\n=== CANDIDATOS PARA CLICK ===")
    for i, match in enumerate(matches, start=1):
        print(
            f"\n#{i}"
            f"\nscore:   {match.score:.2f}"
            f"\ntag:     {match.tag}"
            f"\nrole:    {match.role}"
            f"\nlabel:   {match.label}"
            f"\ntext:    {match.text}"
            f"\ncontent: {match.content}"
            f"\ncontext: {match.context}"
        )


def test_fill_linkedin_search(linkedin_page):

    executor = ActionExecutor(linkedin_page)

    result = executor.click(
        "perfil"
    )
    print("\nResultado:")
    print(result)
    time.sleep(10)
    assert result.status == "success"


def test_linkedin_search(linkedin_page):

    executor = ActionExecutor(linkedin_page)

    result = executor.fill(
        "campo de pesquisa",
        "Python"
    )

    assert result.status == "success"

    result = executor.press(
        "campo de pesquisa",
        "Enter"
    )

    assert result.status == "success"