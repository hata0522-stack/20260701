import asyncio
from playwright.async_api import async_playwright

async def run_task():
    """
    Searches for recent typhoon news on Google News and logs the results.

    Args:
        None
    """
    workspace_dir = "outputs/typhoon_news"
    run_dir = f"{workspace_dir}/final_runs/run_1"
    log_path = f"{run_dir}/final_script_log.txt"
    screenshot_dir = f"{run_dir}/screenshots"

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # Initialize log
        with open(log_path, "w", encoding="utf-8") as log:
            log.write("Starting typhoon news search task...\n")

        try:
            # Step 1: Navigate to Google News Search
            print("Step 1: Navigating to Google News...")
            await page.goto("https://news.google.com/search?q=颱風&hl=zh-TW&gl=TW&ceid=TW:zh-TW")
            await page.wait_for_load_state("networkidle")

            with open(log_path, "a", encoding="utf-8") as log:
                log.write("step 1 action: Navigated to Google News search results for '颱風'\n")

            # Capture screenshot for CP1
            await page.screenshot(path=f"{screenshot_dir}/final_execution_1_navigated.png")

            # Step 2: Extract news headlines and URLs
            print("Step 2: Extracting headlines...")
            # Google News search results are often contained in <li> or <article> with specific classes/roles
            # Using a broader approach for better reliability
            articles = await page.query_selector_all("article")

            news_items = []
            for article in articles:
                # Find title text and link inside the article
                title_el = await article.query_selector("h3, h4, a") 
                if not title_el:
                    continue

                title_text = await title_el.inner_text()
                link_el = await article.query_selector("a")
                if not link_el:
                    continue
                
                href = await link_el.get_attribute("href")
                if href and href.startswith("/"):
                    href = "https://news.google.com" + href

                if title_text.strip():
                    news_items.append({"title": title_text.strip(), "url": href})

            # Filter for uniqueness (sometimes Google News has duplicates)
            unique_news = []
            seen_titles = set()
            for item in news_items:
                if item["title"] not in seen_titles and len(item["title"]) > 5: # filter very short/useless ones
                    unique_news.append(item)
                    seen_titles.add(item["title"])

            final_list = unique_news[:10]

            with open(log_path, "a", encoding="utf-8") as log:
                log.write("step 2 action: Extracted news headlines and URLs\n")

            # Screenshot for CP2 verification (after extraction)
            await page.screenshot(path=f"{screenshot_dir}/final_execution_2_extracted.png")

            print("\n--- Found News ---")
            for item in final_list:
                print(f"- {item['title']} ({item['url']})")

            with open(log_path, "a", encoding="utf-8") as log:
                log.write("--- Final Results ---\n")
                total = len(final_list)
                log.write(f"Found {total} recent news articles.\n")
                for item in final_list:
                    log.write(f"{item['title']} | {item['url']}\n")
                if total > 0:
                    log.write(f"LATEST_NEWS_TITLE: {final_list[0]['title']}\n")

            print(f"\nSuccess! Found {total} articles.")

        except Exception as e:
            print(f"An error occurred: {e}")
            with open(log_path, "a", encoding="utf-8") as log:
                log.write(f"ERROR: {str(e)}\n")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_task())
