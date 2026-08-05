# 從 Playwright 的同步 API 匯入需要使用的類別。
# 同步 API 的程式碼由上到下執行，適合用來理解瀏覽器自動化流程。
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
import os


def crawl(p:Playwright):
  """開啟登入示範頁面，並自動填寫登入資料。"""

  # headless=False 代表顯示實際的 Chromium 視窗，方便觀察自動化過程。
  # 若要在背景執行測試，可改成 headless=True。
  browser:Browser = p.chromium.launch(headless=False)

  # 建立新的分頁；後續的 goto、fill、click 都會作用在這個 page 上。
  page:Page = browser.new_page()

  # __file__ 是目前 practice7.py 的完整路徑。
  # 先取得程式所在資料夾，能讓程式從任何工作目錄執行。
  current_dir:str = os.path.dirname(os.path.abspath(__file__))

  # login_demo.html 與本程式位於同一個 lesson10 資料夾。
  html_file:str = os.path.join(current_dir, "login_demo.html")

  # 使用 file:// 協定開啟本機 HTML 檔案，而不是連線到網際網路。
  page.goto(f"file://{html_file}")

  # get_by_label() 會依照 <label> 顯示的文字尋找對應輸入欄位。
  # fill() 會先清空欄位，再填入指定內容。
  page.get_by_label("用戶名").fill("admin")
  page.get_by_label("密碼").fill("password")

  # 依照按鈕的 ARIA role 與名稱定位登入按鈕，再模擬使用者點擊。
  # login_demo.html 的 JavaScript 會在點擊後檢查帳號與密碼。
  page.get_by_role("button", name="登入").click()


# 建立 Playwright 執行環境。
# with 區塊結束時會自動釋放 Playwright 相關資源。
with sync_playwright() as p:
  crawl(p)
