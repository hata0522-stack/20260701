"""專案 01：開啟真實網頁，檢查標題並留下截圖。"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


# 網頁 URL
URL = "https://example.com/"
# 截圖輸出目錄（與此腳本同層的 output 資料夾）
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def check_website(browser_name: str = "chromium") -> None:
    """開啟指定瀏覽器，瀏覽目標網頁，驗證標題並截圖。"""
    # 若 output 目錄不存在則建立
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 啟動 Playwright 上下文管理器
    with sync_playwright() as playwright:
        # 根據瀏覽器名稱取得對應的瀏覽器類型（chromium / firefox / webkit）
        browser_type = getattr(playwright, browser_name)
        # 啟動瀏覽器（headless=True 表示無 GUI 模式，適合伺服器環境）
        browser = browser_type.launch(headless=True)
        # 建立新分頁並設定視窗大小
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        # 前往目標網頁，等待 DOM 內容載入完成
        response = page.goto(URL, wait_until="domcontentloaded")
        # 取得頁面中名為 "Example Domain" 的標題文字
        heading = page.get_by_role("heading", name="Example Domain").inner_text()
        # 組合截圖檔案路徑（含瀏覽器名稱）
        screenshot = OUTPUT_DIR / f"homepage_{browser_name}.png"
        # 進行全頁面截圖並儲存
        page.screenshot(path=screenshot, full_page=True)

        # 輸出檢查結果
        print(f"瀏覽器: {browser_name}")
        print(f"HTTP 狀態: {response.status if response else '無回應'}")
        print(f"頁面標題: {page.title()}")
        print(f"主標題: {heading}")
        print(f"截圖: {screenshot}")
        # 關閉瀏覽器釋放資源
        browser.close()


if __name__ == "__main__":
    # 建立命令列參數解析器
    parser = argparse.ArgumentParser()
    # --browser 參數：選擇瀏覽器，支援 chromium / firefox / webkit，預設 chromium
    parser.add_argument(
        "--browser", choices=["chromium", "firefox", "webkit"], default="chromium"
    )
    args = parser.parse_args()
    # 執行檢查網站功能
    check_website(args.browser)
