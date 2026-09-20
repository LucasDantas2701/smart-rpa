from app.browser.browser import start_browser, close_browser
from app.browser.session import is_logged_in, wait_for_login
from app.automation.saucedemo import run_saucedemo


PROFILE_PATH = "./profiles/user_001"
URL = "https://www.saucedemo.com/"

LOGGED_IN_SELECTOR = ".inventory_list"


def main():

    playwright, context = start_browser(PROFILE_PATH)

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(URL)

    if is_logged_in(page, LOGGED_IN_SELECTOR):
        print("Usuário já está logado.")

    else:
        wait_for_login(
            page,
            LOGGED_IN_SELECTOR
        )

    print("Iniciando automação...")

    run_saucedemo(page)

    input("Pressione ENTER para encerrar...")

    close_browser(
        playwright,
        context
    )


if __name__ == "__main__":
    main()