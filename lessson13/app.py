from playwright.sync_api import Locator, sync_playwright

import crawler
COOKIES_FILE = "thsrc_cookies.json"
if __name__ == "__main__":
  with sync_playwright() as p:
    crawler.crawl(p=p,cookies_file=COOKIES_FILE)
