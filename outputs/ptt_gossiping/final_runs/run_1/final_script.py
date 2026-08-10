import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    LOG.open("a").write(line)
    print(line, end="")

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        await page.goto("https://www.ptt.cc/bbs/Gossiping/index.html", wait_until="domcontentloaded")
        await asyncio.sleep(1)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_over18_page.png"))
        log(1, "載入八卦板首頁，觸發年齡驗證頁面")

        btn = page.locator("button:has-text('我同意')")
        await btn.first.click()
        await asyncio.sleep(2)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_article_list.png"))
        log(2, "點擊年齡驗證按鈕，進入文章列表")

        titles = await page.locator(".title a").all_text_contents()
        first_5 = titles[:5]
        print("前 5 筆標題：")
        for i, t in enumerate(first_5, 1):
            print(f"  {i}. {t}")

        with LOG.open("a") as f:
            f.write("\n前 5 筆標題：\n")
            for i, t in enumerate(first_5, 1):
                f.write(f"  {i}. {t}\n")

        await browser.close()

asyncio.run(main())
