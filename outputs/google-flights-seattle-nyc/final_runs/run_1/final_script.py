import asyncio
import re
from pathlib import Path

from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

URL = "https://www.google.com/travel/flights"


def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    print(line, end="")


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # CP1: 成功開啟 Google Flights 頁面
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_open_page.png"))
        log(1, "開啟 Google Flights 頁面")
        assert "google.com/travel/flights" in page.url

        # CP2: 設定出發地為西雅圖
        where_from = page.get_by_role("combobox", name="Where from?")
        await where_from.click()
        await page.wait_for_timeout(500)
        await page.keyboard.press("Meta+a")
        await page.keyboard.type("Seattle", delay=80)
        await page.wait_for_timeout(2000)
        await page.get_by_role("option", name="Seattle, Washington, USA").first.click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_origin_seattle.png"))
        log(2, "設定出發地為 Seattle")

        # CP3: 設定目的地為紐約
        where_to = page.get_by_role("combobox", name="Where to?")
        await where_to.click()
        await page.wait_for_timeout(500)
        await page.keyboard.type("New York", delay=80)
        await page.wait_for_timeout(2000)
        await page.get_by_role("option", name="New York, USA").first.click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_3_dest_newyork.png"))
        log(3, "設定目的地為 New York")

        # CP4: 設定日期為 8/15
        dep = page.get_by_role("textbox", name="Departure")
        await dep.click()
        await page.wait_for_timeout(1500)
        aug15_btn = page.get_by_role("button", name="Saturday, August 15, 2026").first
        await aug15_btn.click()
        await page.wait_for_timeout(1500)
        done_btn = page.get_by_role("button", name="Done").first
        await done_btn.click()
        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_4_date_aug15.png"))
        log(4, "設定出發日期為 2026/08/15")

        # CP5: 點擊搜尋顯示日期價格格線，擷取 8/15 最低票價
        search_btn = page.get_by_role("button", name="Search")
        await search_btn.click()
        await page.wait_for_timeout(5000)

        # Extract price from the gridcell for Aug 15
        snapshot = await page.locator("body").aria_snapshot()
        price_match = re.search(
            r"Saturday, August 15, 2026.*?(\d+)\s*New Taiwan dollars",
            snapshot,
        )
        if price_match:
            cheapest_price = price_match.group(1)
        else:
            # Fallback: find line with "August 15, 2026" and extract price
            lines = snapshot.split("\n")
            cheapest_price = "N/A"
            for line in lines:
                if "August 15, 2026" in line and "New Taiwan dollars" in line:
                    nums = re.findall(r"\b(\d{4,})\b", line)
                    if nums:
                        # The largest number is usually the price
                        cheapest_price = max(nums, key=int)
                    break

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_5_price_grid.png"))
        log(5, f"8/15 最低票價: NT${cheapest_price}")

        # CP6: 記錄最終結果
        final_value = f"8/15 西雅圖→紐約最低票價: NT${cheapest_price}"
        with LOG.open("a") as f:
            f.write(f"\nFINAL_RESPONSE: {final_value}\n")
        log(6, f"最終結果: {final_value}")

        print(f"\n=== FINAL RESULT ===")
        print(final_value)

        await browser.close()


asyncio.run(main())
