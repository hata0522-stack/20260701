from playwright.sync_api import sync_playwright
from playwright.sync_api import Browser, Page

def main():
  with sync_playwright() as p:
    browser: Browser = p.chromium.launch(headless=False)
    page: Page= browser.new_page()
    page.goto("https://www.google.com")
    print(page.title())
    browser.close()

if __name__ == "__main__":
  main()
