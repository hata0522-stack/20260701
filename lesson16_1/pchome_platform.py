"""PChome 24h 購物 —— API 直連模式。

PChome 搜尋頁底層採用開放 API，不必啟動分頁渲染 HTML，
直接用 context.request.get() 取得 JSON，速度極快且省資源。
"""

from playwright.async_api import BrowserContext

from base_platform import BasePlatform
from data_models import STATUS_SUCCESS, StoreInfo


class PChomePlatform(BasePlatform):
    name = "PChome 24h"
    timeout_ms = 10000

    API_URL = "https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={kw}&page=1"
    PRODUCT_URL = "https://24h.pchome.com.tw/prod/{pid}"

    async def _fetch(self, context: BrowserContext, keyword: str, info: StoreInfo) -> None:
        response = await context.request.get(
            self.API_URL.format(kw=self.encode(keyword)), timeout=self.timeout_ms
        )
        if response.status != 200:
            return

        prods = (await response.json()).get("prods", [])
        if not prods:
            return

        item = prods[0]  # 取搜尋結果第一筆
        info.title = item.get("name") or "未知的商品標題"
        info.price = self.clean_price(item.get("price", 0))
        info.url = self.PRODUCT_URL.format(pid=item.get("Id", ""))
        info.status = STATUS_SUCCESS
