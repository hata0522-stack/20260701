from playwright.async_api import BrowserContext
from data_models import StoreInfo
from base_platform import BasePlatform
import urllib.parse
import re

class YahooPlatform(BasePlatform):
    def __init__(self):
        super().__init__("Yahoo購物中心")

    async def fetch(self, context: BrowserContext, keyword: str) -> StoreInfo:
        result = StoreInfo(platform=self.name)
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://tw.buy.yahoo.com/search/product?p={encoded_kw}"
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1200)
            cards = page.locator("a[href*='/gdsale/']")

            if await cards.count() > 0:
                card = cards.first
                href = await card.get_attribute("href")
                txt = await card.inner_text()
                lines = [l.strip() for l in txt.split("\n") if l.strip()]

                title = ""
                price = 0
                for l in lines:
                    if "$" in l and price == 0:
                        digits = re.sub(r"[^\d]", "", l)
                        if digits:
                            price = int(digits)
                    elif l not in ["比較", "找相似", "活動", "券", "限時下殺", "折扣"] and "$" not in l and not title:
                        title = l

                if title:
                    result.title = title
                    result.price = price
                    result.url = href or ""
                    result.status = "成功"
        except Exception as e:
            print(f"[Yahoo購物中心] 抓取失敗: {e}")
        finally:
            await page.close()

        return result
