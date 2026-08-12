"""抓取引擎：負責瀏覽器生命週期與多層非同步併發。

併發三層結構：
    scan_all      → 跨品類併發   (品類 A、品類 B、品類 C ... 同時跑)
      scan_category → 跨品牌併發 (毛寶、競品1、競品2 ... 同時跑)
        scan_target   → 跨賣場併發 (PChome、momo、Yahoo 同時跑)

總耗時取決於「最慢的那一個請求」，而不是所有請求相加。
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Callable, List, Optional, Sequence

from playwright.async_api import BrowserContext, async_playwright

from base_platform import BasePlatform
from config import CategoryConfig
from data_models import CategoryScan, ProductScan, ProductTarget, StoreInfo
from momo_platform import MomoPlatform
from pchome_platform import PChomePlatform
from yahoo_platform import YahooPlatform

# 預設賣場順序：PChome 走 API 最快，放第一個
PLATFORM_CLASSES = [PChomePlatform, MomoPlatform, YahooPlatform]

VIEWPORT = {"width": 1280, "height": 720}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)


def build_platforms() -> List[BasePlatform]:
    """建立全部賣場抓取器實例"""
    return [cls() for cls in PLATFORM_CLASSES]


@asynccontextmanager
async def browser_context(browser_name: str = "firefox", headless: bool = True):
    """統一管理 Playwright / Browser / Context 的建立與釋放。

    以 async context manager 包裝，確保就算中途發生例外也一定會關閉瀏覽器。
    headless=False 可以觀察自動化操作過程。
    """
    async with async_playwright() as p:
        browser = await getattr(p, browser_name).launch(headless=headless)
        context = await browser.new_context(viewport=VIEWPORT, user_agent=USER_AGENT)
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


class PriceScraper:
    """價格抓取引擎。log 可替換成 GUI 的訊號發送函式。"""

    def __init__(
        self,
        platforms: Optional[Sequence[BasePlatform]] = None,
        log: Callable[[str], None] = print,
    ):
        self.platforms = list(platforms) if platforms else build_platforms()
        self.log = log

    async def scan_target(self, context: BrowserContext, target: ProductTarget) -> ProductScan:
        """【併發層級 3】單一商品跨所有賣場同時查詢"""
        results = await asyncio.gather(
            *(platform.fetch(context, target.keyword) for platform in self.platforms),
            return_exceptions=True,
        )
        stores = [r for r in results if isinstance(r, StoreInfo)]
        return ProductScan(
            brand=target.brand, name=target.name, keyword=target.keyword, stores=stores
        )

    async def scan_category(
        self, context: BrowserContext, category: CategoryConfig
    ) -> CategoryScan:
        """【併發層級 2】單一品類中，毛寶本家與所有競品同時查詢"""
        self.log(f"🚀 開始平行併發查詢品類：【{category.category}】跨賣場數據...")

        targets = category.targets
        results = await asyncio.gather(
            *(self.scan_target(context, t) for t in targets), return_exceptions=True
        )

        # 與 targets 對齊：失敗的目標補上空白結果，避免後續索引錯位
        scans = []
        for target, result in zip(targets, results):
            if isinstance(result, ProductScan):
                scans.append(result)
            else:
                self.log(f"⚠️ [{target.brand}] {target.name} 抓取失敗: {result}")
                scans.append(ProductScan.empty(target))

        return CategoryScan(
            category=category.category,
            maobao_product=scans[0],
            competitors=scans[1:],
        )

    async def scan_all(
        self, context: BrowserContext, categories: Sequence[CategoryConfig]
    ) -> List[CategoryScan]:
        """【併發層級 1】所有品類同時查詢"""
        results = await asyncio.gather(
            *(self.scan_category(context, cat) for cat in categories),
            return_exceptions=True,
        )

        scans = []
        for category, result in zip(categories, results):
            if isinstance(result, CategoryScan):
                scans.append(result)
            else:
                self.log(f"⚠️ 品類【{category.category}】抓取失敗: {result}")
        return scans

    async def find_first(self, context: BrowserContext, keyword: str) -> Optional[StoreInfo]:
        """依序嘗試各賣場，回傳第一個「有價格」的結果（GUI 單筆查詢用）。"""
        for platform in self.platforms:
            info = await platform.fetch(context, keyword)
            if info.found:
                return info
        return None
