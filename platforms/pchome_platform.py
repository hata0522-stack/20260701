from playwright.async_api import BrowserContext
from models.data_models import StoreInfo
from platforms.base_platform import BasePlatform
import urllib.parse

class PChomePlatform(BasePlatform):
    def __init__(self):
        super().__init__("PChome 24h")

    async def fetch(self, context: BrowserContext, keyword: str) -> StoreInfo:
        result = StoreInfo(platform=self.name)
        encoded_kw = urllib.parse.quote(keyword)
        api_url = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={encoded_kw}&page=1"

        try:
            response = await context.request.get(api_url, timeout=10000)
            if response.status == 200:
                data = await response.json()
                prods = data.get("prods", [])
                if prods:
                    item = prods[0]
                    result.title = item.get("name", "未知的商品標題")
                    result.price = self.clean_price(str(item.get("price", 0)))
                    result.url = f"https://24h.pchome.com.tw/prod/{item.get('Id', '')}"
                    result.status = "成功"
        except Exception as e:
            print(f"[PChome 24h] 抓取失敗: {e}")
        
        return result
