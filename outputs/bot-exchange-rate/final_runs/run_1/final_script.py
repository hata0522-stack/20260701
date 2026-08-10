import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

URL = "https://rate.bot.com.tw/xrt?Lang=zh-TW"


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

        # CP1: 成功開啟臺灣銀行牌告匯率官網
        await page.goto(URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_open_page.png"))
        log(1, f"開啟臺灣銀行牌告匯率官網: {page.url}")
        assert "rate.bot.com.tw" in page.url

        # Locate the exchange rate table
        table = page.get_by_role("table").first

        # Find the USD row - contains "美金 (USD)"
        usd_row = table.get_by_role("row").filter(has_text="美金 (USD)")
        cells = await usd_row.get_by_role("cell").all()

        # Cell 1 (index 0) = currency name, Cell 2 (index 1) = 本行買入/現金, Cell 3 (index 2) = 本行賣出/現金
        cash_buying = (await cells[1].inner_text()).strip()
        cash_selling = (await cells[2].inner_text()).strip()

        # CP2: 擷取美金現鈔買入匯率
        await page.screenshot(
            path=str(SCREENSHOTS / "final_execution_2_usd_cash_buying.png")
        )
        log(2, f"美金現鈔買入匯率 (USD Cash Buying Rate): {cash_buying}")

        # CP3: 擷取美金現鈔賣出匯率
        await page.screenshot(
            path=str(SCREENSHOTS / "final_execution_3_usd_cash_selling.png")
        )
        log(3, f"美金現鈔賣出匯率 (USD Cash Selling Rate): {cash_selling}")

        # CP4: 記錄最終結果
        final_value = f"美金現鈔買入: {cash_buying}, 美金現鈔賣出: {cash_selling}"
        with LOG.open("a") as f:
            f.write(f"\nFINAL_RESPONSE: {final_value}\n")
        log(4, f"最終結果: {final_value}")

        print(f"\n=== FINAL RESULT ===")
        print(final_value)

        await browser.close()


asyncio.run(main())
