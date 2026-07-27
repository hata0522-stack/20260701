from playwright.sync_api import sync_playwright,Playwright,Browser,Page

def  element_location_demo(p:Playwright):
  browser:Browser = p.chromium.launch(headless=False)
  page:Page = browser.new_page()

  # 開啟 Saucedemo 網站
  page.goto("https://www.saucedemo.com/")
  page.wait_for_selector("#login-button")
  print("✓ 已開啟登入頁面")

  # 方法1：使用 get_by_placeholder() - 根據 placeholder 文字定位
  print("\n使用 get_by_placeholder() 定位輸入欄位...")
  page.get_by_placeholder("Username").fill("standard_user")
  print("✓ 已填入用戶名：standard_user")

  page.get_by_placeholder("Password").fill("secret_sauce")
  print("✓ 已填入密碼：secret_sauce")

  # 方法2：使用 get_by_role() 定位按鈕
  print("\n使用 get_by_role() 定位按鈕...")
  page.get_by_role("button", name="Login").click()
  print("✓ 已點擊登入按鈕")

  # 等待登入完成
  page.wait_for_selector(".inventory_list")
  print("✓ 登入成功，已進入商品頁面")

  print("\n程式執行完成，3 秒後關閉瀏覽器...")
  page.wait_for_timeout(3000)
  browser.close()

if __name__ == "__main__":
  print("=" * 60)
  print("Playwright 元素定位示範")
  print("=" * 60)
  with sync_playwright() as p:
    element_location_demo(p)
  print("\n" + "=" * 60)
  print("示範完成")
  print("=" * 60)
