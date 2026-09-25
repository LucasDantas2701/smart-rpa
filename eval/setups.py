"""
Passos de preparação de cada site antes dos casos (login, navegação...).
Referenciados pelo campo "setup" dos arquivos em eval/cases/.
"""

from playwright.sync_api import Page


def saucedemo_login(page: Page) -> None:
    page.locator('[data-test="username"]').fill("standard_user")
    page.locator('[data-test="password"]').fill("secret_sauce")
    page.locator('[data-test="login-button"]').click()
    page.locator(".inventory_list").wait_for(state="visible")


SETUPS = {
    "saucedemo_login": saucedemo_login,
}
