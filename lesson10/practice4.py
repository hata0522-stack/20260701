from playwright.sync_api import sync_playwright,Browser,Page
import os

def basic_operations():
    with sync_playwright() as p:
        # 啟動瀏覽器（有頭模式）
        browser:Browser = p.chromium.launch(headless=False, slow_mo=500)
        page:Page = browser.new_page()

        # 取得當前檔案的絕對路徑
        current_dir:str = os.path.dirname(os.path.abspath(__file__))
        html_file:str = os.path.join(current_dir, "form_demo.html")

        # 訪問本地 HTML 檔案
        page.goto(f"file://{html_file}")

        # 填寫表單
        page.fill("input#name", "張三")
        page.fill("input#email", "zhang@example.com")
        page.select_option("select#country", "Taiwan")
        page.check("input#subscribe")

        # 點擊提交按鈕
        page.click("button#submit")

        # 等待導航完成
        page.wait_for_load_state("networkidle")

        # 等待一下讓使用者看到結果
        page.wait_for_timeout(2000)

        # 關閉瀏覽器
        browser.close()

if __name__ == "__main__":
    basic_operations()
