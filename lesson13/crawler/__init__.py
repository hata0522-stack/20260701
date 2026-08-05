from playwright.sync_api import Playwright,Browser,BrowserContext,Page,Locator
import os,json
from datetime import datetime,timedelta


def crawl(p: Playwright, cookies_file: str, headless: bool = False,
          departure_station: str = "台北", arrival_station: str = "台中",
          departure_date: str | None = None, departure_time: str | None = None):
  browser: Browser = p.firefox.launch(headless=headless)
  try:
    context: BrowserContext = browser.new_context(viewport={"width": 1280, "height": 720})
    try:
      _load_cookies(context, cookies_file)

      page: Page = context.new_page()
      page.goto("https://www.thsrc.com.tw/", wait_until="domcontentloaded")

      _accept_cookies(page, context, cookies_file)
      _fill_search_form(page, departure_station, arrival_station,
                        departure_date, departure_time)
      _click_search(page)
      _wait_for_results(page)
      _print_schedule(page)
      _print_prices(page)
      _print_download_links(page)
      _print_complete()
    finally:
      context.close()
  finally:
    browser.close()


def _load_cookies(context: BrowserContext, cookies_file: str):
  if not os.path.exists(cookies_file):
    return
  with open(cookies_file, "r") as f:
    cookies = json.load(f)
    context.add_cookies(cookies)
  print("✓ 已載入保存的 cookies")


def _accept_cookies(page: Page, context: BrowserContext, cookies_file: str):
  try:
    agree_button: Locator = page.get_by_role("button", name="我同意")
    agree_button.click(timeout=3000)

    cookies = context.cookies()
    with open(cookies_file, "w") as f:
      json.dump(cookies, f)
    print("✓ 已保存 cookies 到檔案")
  except Exception:
    print("⚠ 沒有找到 cookies 對話框，可能已經同意過了")


def _fill_search_form(page: Page, departure_station: str, arrival_station: str,
                      departure_date: str | None = None,
                      departure_hour: str | None = None):
  print("正在等待頁面載入...")

  page.get_by_label("出發站").select_option(departure_station)
  page.get_by_label("到達站").select_option(arrival_station)
  print(f"✓ 已選擇 {departure_station} → {arrival_station}")

  if departure_date is None or departure_hour is None:
    now: datetime = datetime.now()
    auto_departure_time: datetime = now + timedelta(hours=1)
    departure_date = departure_date or auto_departure_time.strftime("%Y/%m/%d")
    departure_hour = departure_hour or auto_departure_time.strftime("%H:%M")
    print(f"\n✓ 自動設定出發時間為：{departure_date} {departure_hour}")
  else:
    print(f"\n✓ 使用指定出發時間：{departure_date} {departure_hour}")

  date_input = page.get_by_label("出發日期")
  date_input.click()
  date_input.fill("")
  date_input.fill(departure_date)
  print(f"✓ 已填入出發日期：{departure_date}")

  time_input = page.get_by_label("出發時間")
  time_input.click()
  time_input.fill("")
  time_input.fill(departure_hour)
  print(f"✓ 已填入出發時間：{departure_hour}")

  page.keyboard.press("Tab")

  filled_date = date_input.input_value()
  if filled_date != departure_date:
    raise ValueError(
      f"日期填寫失敗：網頁欄位顯示「{filled_date}」，"
      f"高鐵網站僅開放今天起 29 天內（含當日）的日期，請選擇更近的日期。"
    )


def _click_search(page: Page):
  search_button = page.get_by_role("button", name="查詢").first
  search_button.click()
  print("✓ 已點擊查詢按鈕")


def _wait_for_results(page: Page):
  page.wait_for_load_state("networkidle")
  print("正在等待查詢結果...")

  try:
    page.locator("a.tr-row").first.wait_for(state="visible", timeout=30000)
    print("✓ 查詢結果已載入\n")
  except Exception:
    print("⚠ 等待超時，但繼續嘗試抓取資料...\n")


def _print_schedule(page: Page):
  print("=" * 60)
  print("時刻表資料")
  print("=" * 60)

  train_rows: list[Locator] = page.locator("a.tr-row").all()

  if not train_rows:
    print("未找到車次資料")
    return

  print(f"{'出發時間':<10} {'行車時間':<10} {'抵達時間':<10} {'車次':<8} {'自由座車廂'}")
  print("-" * 60)

  for row in train_rows:
    cells = row.locator("> *").all()
    if len(cells) >= 5:
      print(f"{cells[0].inner_text():<10} {cells[1].inner_text():<10} {cells[2].inner_text():<10} {cells[3].inner_text():<8} {cells[4].inner_text()}")


def _print_prices(page: Page):
  print("\n" + "=" * 60)
  print("車廂票價參考")
  print("=" * 60)

  try:
    page.get_by_role("heading", name="車廂票價參考").wait_for(state="visible", timeout=10000)
  except Exception:
    print("⚠ 票價資料可能尚未載入...")

  price_data = []
  for row in page.locator("table tr").all():
    cells = row.locator("td, th").all()
    if cells:
      price_data.append([cell.inner_text().strip() for cell in cells])

  if price_data:
    for row in price_data:
      print(" | ".join(row))
  else:
    print("未找到票價資料")


def _print_download_links(page: Page):
  print("\n" + "=" * 60)
  print("時刻表下載")
  print("=" * 60)

  for link in page.locator('a[description*="時刻表.pdf"]').all():
    text = link.inner_text()
    href = link.get_attribute("href")
    if href:
      print(f"• {text}")
      print(f"  連結: https://www.thsrc.com.tw{href}")


def _print_complete():
  print("\n" + "=" * 60)
  print("✓ 完成！")
  print("=" * 60)
