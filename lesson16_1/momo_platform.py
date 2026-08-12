"""momo 購物網 —— DOM 動態解析模式。

momo 是動態渲染網頁，需開啟分頁等待前端填值後再以 locator 精準定位。
多重選擇器（以逗號分隔）可適應 momo 不定期變更的 CSS class。
"""

import urllib.parse

from playwright.async_api import Page

from base_platform import PagePlatform
from data_models import StoreInfo


class MomoPlatform(PagePlatform):
    name = "momo購物網"
    search_url = "https://www.momoshop.com.tw/search/searchShop.jsp?keyword={kw}"
    render_wait_ms = 1000

    BASE_URL = "https://www.momoshop.com.tw"
    CARD_SELECTOR = "div.listArea ul li, .prdListArea ul li"
    TITLE_SELECTOR = ".prdName, h3, .goodsName"
    PRICE_SELECTOR = ".price, .money, .prdPrice"
    LINK_SELECTOR = "a.goods-img-url, a.prdName, a"

    async def parse(self, page: Page, info: StoreInfo) -> None:
        cards = page.locator(self.CARD_SELECTOR)
        if await cards.count() == 0:
            return

        card = cards.first
        title = await self.first_text(card, self.TITLE_SELECTOR)
        if not title.strip():
            return

        price_text = await self.first_text(card, self.PRICE_SELECTOR)
        href = await self.first_attribute(card, self.LINK_SELECTOR, "href")
        # 補全相對路徑 URL
        url = urllib.parse.urljoin(self.BASE_URL, href) if href else ""

        self.mark_success(info, title, price_text, url)
