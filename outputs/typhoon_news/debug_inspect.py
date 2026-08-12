import asyncio
from playwright.async_api import async_playwright

async def explore():
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        print("Visiting Google News...")
        await page.goto("https://news.google.com/search?q=颱風&hl=zh-TW&gl=TW&ceid=TW:zh-TW")
        await page.wait_for_load_state("networkidle")

        print("\n--- Aria Snapshot ---")
        snapshot = await page.aria_snapshot()
        print(snapshot)

        await page.screenshot(path="outputs/typhoon_news/debug_inspect.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explore())
