from datetime import datetime
from playwright.sync_api import sync_playwright, Playwright, Browser, Page, TimeoutError as PwTimeout

WIKI_URL = "https://zh.wikipedia.org"


def crawl(p: Playwright) -> None:
    """爬取維基百科搜尋頁面，查詢關鍵字並顯示摘要"""
    # 啟動 Chromium 瀏覽器
    browser: Browser = p.chromium.launch()
    try:
        page: Page = browser.new_page()

        # 前往中文維基百科首頁
        page.goto(WIKI_URL)

        # 在搜尋框輸入關鍵字
        page.get_by_role("searchbox").first.fill("臺灣")

        # 截圖紀錄輸入後的畫面（檔名加時間戳記避免覆蓋）
        timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        page.screenshot(path=f"screenshot_{timestamp}.png")

        # 按下 Enter 進行搜尋
        page.keyboard.press("Enter")

        # 等待頁面載入完成（逾時 30 秒）
        page.wait_for_load_state("networkidle", timeout=30000)

        # 取得搜尋結果頁的標題
        first_heading: str = page.locator("#firstHeading").inner_text()
        print(f"搜尋主題:{first_heading}")

        # 取得第一段摘要內容（顯示前 100 字）
        content: str = page.locator("#mw-content-text p").first.inner_text()
        print(f"摘要: {content[:100]}")

        # 返回上一頁（首頁）
        page.go_back()
        page.wait_for_load_state("networkidle", timeout=30000)
        print(f"返回首頁:{page.title()}")

    except PwTimeout as e:
        print(f"操作逾時: {e}")
    except Exception as e:
        print(f"發生錯誤: {e}")
    finally:
        # 關閉瀏覽器
        browser.close()


with sync_playwright() as p:
    crawl(p)
