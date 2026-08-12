"""Yahoo 購物中心 —— DOM 列表分析模式。

Yahoo 商品卡片的文字混雜促銷標籤（"折"、"限時下殺"、"找相似"），
因此改以「逐行掃描 inner_text」的方式，過濾雜訊後找出真正的標題與價格。
"""

from playwright.async_api import Page

from base_platform import PagePlatform
from data_models import StoreInfo


class YahooPlatform(PagePlatform):
    name = "Yahoo購物中心"
    search_url = "https://tw.buy.yahoo.com/search/product?p={kw}"
    render_wait_ms = 1200

    CARD_SELECTOR = "a[href*='/gdsale/']"
    NOISE_LINES = {"比較", "找相似", "活動", "券", "限時下殺", "折扣"}

    async def parse(self, page: Page, info: StoreInfo) -> None:
        cards = page.locator(self.CARD_SELECTOR)
        if await cards.count() == 0:
            return

        card = cards.first
        href = await card.get_attribute("href")
        text = await card.inner_text()

        title, price = self._extract(text)
        if title:
            self.mark_success(info, title, price, href or "")

    def _extract(self, text: str) -> tuple[str, int]:
        """從卡片的多行文字中挑出標題與價格"""
        title = ""
        price = 0
        for line in (l.strip() for l in text.split("\n")):
            if not line:
                continue
            if "$" in line:
                if price == 0:
                    price = self.clean_price(line)
            elif not title and line not in self.NOISE_LINES:
                title = line
        return title, price
