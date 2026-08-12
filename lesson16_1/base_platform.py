"""平台抓取基底類別（Template Method 樣板方法模式）。

    BasePlatform  → 統一 fetch() 的例外容錯與回傳型別，子類別只實作 _fetch()
    PagePlatform  → 再包一層：開分頁 / 導頁 / 等待 / 關分頁，子類別只實作 parse()

好處：新增一個賣場時，不用再重寫 try/except/finally 與 page.close() 樣板。
"""

import re
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Optional

from playwright.async_api import BrowserContext, Locator, Page

from data_models import STATUS_SUCCESS, StoreInfo


class BasePlatform(ABC):
    """所有賣場的共同介面"""

    name: str = "未命名賣場"
    timeout_ms: int = 15000

    async def fetch(self, context: BrowserContext, keyword: str) -> StoreInfo:
        """對外唯一入口：永遠回傳 StoreInfo，單一賣場失敗不會中斷併發任務。"""
        info = StoreInfo(platform=self.name)
        try:
            await self._fetch(context, keyword, info)
        except Exception as exc:
            print(f"[{self.name}] 抓取失敗: {exc}")
        return info

    @abstractmethod
    async def _fetch(self, context: BrowserContext, keyword: str, info: StoreInfo) -> None:
        """子類別在此填寫 info 的欄位；成功時請把 info.status 設為 STATUS_SUCCESS。"""

    @staticmethod
    def clean_price(price_text: Any) -> int:
        """價格字串清洗：'NT$ 1,090' -> 1090"""
        digits = re.sub(r"[^\d]", "", str(price_text))
        return int(digits) if digits else 0

    @staticmethod
    def encode(keyword: str) -> str:
        """中文關鍵字 URL 編碼，避免網址格式錯誤"""
        return urllib.parse.quote(keyword)


class PagePlatform(BasePlatform):
    """需要開啟瀏覽器分頁、解析 DOM 的賣場"""

    search_url: str = ""       # 例如 "https://.../search?q={kw}"
    render_wait_ms: int = 1000  # 給前端模板動態填入文字的緩衝時間

    async def _fetch(self, context: BrowserContext, keyword: str, info: StoreInfo) -> None:
        page = await context.new_page()
        try:
            url = self.search_url.format(kw=self.encode(keyword))
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            await page.wait_for_timeout(self.render_wait_ms)
            await self.parse(page, info)
        finally:
            # 關鍵！併發爬蟲中未關閉的 Page 會造成記憶體洩漏 (Memory Leak)
            await page.close()

    @abstractmethod
    async def parse(self, page: Page, info: StoreInfo) -> None:
        """解析搜尋結果頁，把資料寫進 info。"""

    def mark_success(self, info: StoreInfo, title: str, price: Any, url: str = "") -> None:
        info.title = title.strip()
        info.price = self.clean_price(price)
        info.url = url
        info.status = STATUS_SUCCESS

    @staticmethod
    async def first_text(scope: Locator, selector: str) -> str:
        """取得符合選擇器的第一個元素文字，找不到時回傳空字串"""
        loc = scope.locator(selector)
        if await loc.count() == 0:
            return ""
        return await loc.first.inner_text()

    @staticmethod
    async def first_attribute(scope: Locator, selector: str, attribute: str) -> Optional[str]:
        """取得符合選擇器的第一個元素屬性，找不到時回傳 None"""
        loc = scope.locator(selector)
        if await loc.count() == 0:
            return None
        return await loc.first.get_attribute(attribute)
