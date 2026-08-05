"""專案 02：自動完成 Selenium 官方測試表單。"""
from playwright.sync_api import sync_playwright
from playwright.sync_api import Playwright, Browser, Page, Locator

from core import run_form_automation


URL = "https://www.selenium.dev/selenium/web/web-form.html"


def run(playwright: Playwright) -> None:
    """執行預設表單自動化操作。"""
    run_form_automation(playwright)


with sync_playwright() as playwright:
    run(playwright)
