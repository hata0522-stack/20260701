from playwright.sync_api import sync_playwright,Browser,Page

with sync_playwright() as p:
    # 啟動瀏覽器
    browser:Browser = p.chromium.launch()
    page:Page = browser.new_page()
    browser.close()
