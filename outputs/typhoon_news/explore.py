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

        print("\n--- URL ---")
        print(page.url)

        print("\n--- Page Title ---")
        print(await page.title())

        print("\n--- Aria Snapshot (Excerpt) ---")
        try:
            snapshot = await page.aria_snapshot()
            print(snapshot[:1000] + "...")
        except Exception as e:
            print(f"Snapshot failed: {e}")

        await page.screenshot(path="outputs/typhoon_news/explore_1_google_news.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(explore())
