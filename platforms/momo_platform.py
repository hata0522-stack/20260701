from playwright.async_api import BrowserContext
from models.data_models import StoreInfo
from platforms.base_platform import BasePlatform
import urllib.parse
import re

class MomoPlatform(BasePlatform):
    def __init__(self):
        super().__init__("momo購物網")

    async def fetch(self, context: BrowserContext, keyword: str) -> StoreInfo:
        result = StoreInfo(platform=self.name)
        encoded_kw = urllib.parse.quote(keyword)
        url = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={encoded_kw}"

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1000)

            cards = page.locator("div.listArea ul li, .prdListArea ul li")

            if await cards.count() > 0:
                card = cards.first
                title_loc = card.locator(".prdName, h3, .goodsName")
                price_loc = card.locator(".price, .money, .prdPrice")
                link_loc = card.locator("a.goods-img-url, a.prdName, a").first

                title = await title_loc.first.inner_text() if await title_loc.count() > 0 else ""
                price_text = await price_loc.first.inner_text() if await price_loc.count() > 0 else ""
                href = await link_loc.get_attribute("href") if await link_loc.count() > 0 else ""

                result.title = title.strip()
                result.price = self.clean_price(price_text)
                if href:
                    result.url = urllib.parse.urljoin("https://www.momoshop.com.tw", href)
                result.status = "成功"
        except Exception as e:
            print(f"[momo購物網] 抓取失敗: {e}")
        finally:
            await page.close()

        return result
