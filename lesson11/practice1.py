import re
from datetime import datetime
from playwright.sync_api import sync_playwright,Playwright,Browser,Page


def launch_browser(p:Playwright) -> Browser:
  """啟動 Chromium 瀏覽器實例"""
  return p.chromium.launch()


def search_wikipedia(page:Page, keyword:str) -> None:
  """在維基百科搜尋指定關鍵字"""
  page.goto("https://zh.wikipedia.org")
  search_input = page.locator("#searchInput")
  search_input.fill(keyword)
  page.screenshot(path=f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
  search_input.press("Enter")
  page.wait_for_selector("#firstHeading")


def get_search_result(page:Page) -> dict[str, str]:
  """擷取搜尋結果頁面的標題與摘要"""
  heading:str = page.locator("#firstHeading").inner_text()
  # 過濾空段落(中文維基文章的第一個 <p> 常是空段落或座標資訊)
  paragraphs = page.locator("#mw-content-text p").filter(has_text=re.compile(r"\S"))
  content:str = paragraphs.first.inner_text() if paragraphs.count() > 0 else ""
  return {"heading": heading, "content": content[:100]}


def crawl(p:Playwright) -> None:
  """爬蟲主流程:啟動瀏覽器、搜尋、擷取結果、返回首頁"""
  browser:Browser = launch_browser(p)
  try:
    page:Page = browser.new_page()
    search_wikipedia(page, "臺灣")

    result:dict[str, str] = get_search_result(page)
    print(f"搜尋主題: {result['heading']}")
    print(f"摘要: {result['content']}")

    page.go_back()
    page.wait_for_selector("#searchInput")
    print(f"返回首頁: {page.title()}")
  except Exception as e:
    print(f"爬蟲執行失敗: {e}")
    raise
  finally:
    browser.close()


if __name__ == "__main__":
  with sync_playwright() as p:
    crawl(p)
