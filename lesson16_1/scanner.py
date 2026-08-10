"""非同步掃描核心：串起各賣場 platform 類別與併發編排。

供 console 與 PySide6 UI 共用：
- run_monitoring(): 依設定檔執行「品類 x 品牌 x 賣場」全量監控
- run_keyword_scan(): 單一關鍵字跨賣場即時查價
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from threading import Event
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from playwright.async_api import async_playwright, BrowserContext

from base_platform import BasePlatform
from data_models import CategoryScan, ProductScan, StoreInfo
from momo_platform import MomoPlatform
from pchome_platform import PChomePlatform
from yahoo_platform import YahooPlatform

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

# 抓取器註冊表：新增賣場只需在此註冊，並於設定檔 platforms 加入對應 id
PLATFORMS: Dict[str, BasePlatform] = {
    "pchome": PChomePlatform(),
    "momo": MomoPlatform(),
    "yahoo": YahooPlatform(),
}

LogCallback = Optional[Callable[[str], None]]


def _safe_print(msg: str) -> None:
    """console 無法編碼（如 cp950 遇到 emoji）時降級輸出。"""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def _default_log(msg: str) -> None:
    _safe_print(msg)


def resolve_platform_ids(config_data: Dict[str, Any]) -> List[str]:
    """從設定檔過濾出已註冊的賣場 id。"""
    return [p["id"] for p in config_data.get("platforms", []) if p.get("id") in PLATFORMS]


def _collect_valid(results: Sequence[Any]) -> List[Any]:
    """過濾 asyncio.gather(return_exceptions=True) 回傳中的失敗例外。"""
    return [r for r in results if not isinstance(r, Exception)]


@asynccontextmanager
async def browser_context():
    """啟動 headless 瀏覽器並在結束時自動清理 context / browser。"""
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=USER_AGENT,
        )
        try:
            yield context
        finally:
            await context.close()
            await browser.close()


async def _scan_keyword(context: BrowserContext, keyword: str, platform_ids: Sequence[str]) -> List[StoreInfo]:
    """單一關鍵字在指定賣場上的併發查價。"""
    tasks = [PLATFORMS[pid].fetch(context, keyword) for pid in platform_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return _collect_valid(results)


async def _gather_with_stop(tasks: Sequence[Any], stop_event: Optional[Event] = None) -> List[Any]:
    """等待全部任務完成；若 stop_event 被設定則取消未完成任務並回傳已完成結果。"""
    pending = set(tasks)
    done = set()
    while pending:
        if stop_event is not None and stop_event.is_set():
            for t in pending:
                t.cancel()
            done |= pending
            break
        finished, pending = await asyncio.wait(
            pending, timeout=0.3, return_when=asyncio.FIRST_COMPLETED
        )
        done |= finished

    results = []
    for t in done:
        try:
            results.append(t.result())
        except (asyncio.CancelledError, Exception):
            pass
    return _collect_valid(results)


async def fetch_item_across_platforms(
    context: BrowserContext,
    brand: str,
    name: str,
    keyword: str,
    platform_ids: Sequence[str],
) -> ProductScan:
    """單一商品跨多賣場併發，回傳 ProductScan。"""
    stores = await _scan_keyword(context, keyword, platform_ids)
    return ProductScan(brand=brand, name=name, keyword=keyword, stores=stores)


async def monitor_category_async(
    context: BrowserContext,
    category_item: Dict[str, Any],
    platform_ids: Sequence[str],
    log: LogCallback = None,
) -> CategoryScan:
    """單一品類：毛寶本家 + 競品跨賣場併發。"""
    log = log or _default_log
    category_name = category_item["category"]
    maobao_cfg = category_item.get("maobao_product")
    competitors_cfg = category_item.get("competitors", [])

    log(f"🚀 開始平行併發查詢品類：【{category_name}】跨賣場數據...")

    tasks = []
    if maobao_cfg:
        tasks.append(
            fetch_item_across_platforms(
                context, "毛寶", maobao_cfg["name"], maobao_cfg["keyword"], platform_ids
            )
        )
    for comp in competitors_cfg:
        tasks.append(
            fetch_item_across_platforms(
                context, comp["brand"], comp["name"], comp["keyword"], platform_ids
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)
    products = _collect_valid(results)

    if maobao_cfg:
        return CategoryScan(
            category=category_name,
            maobao_product=products[0] if products else None,
            competitors=products[1:],
        )
    return CategoryScan(
        category=category_name,
        maobao_product=None,
        competitors=products,
    )


async def run_monitoring(
    config_data: Dict[str, Any],
    stop_event: Optional[Event] = None,
    log: LogCallback = None,
) -> Tuple[List[CategoryScan], float]:
    """依設定檔執行全量監控，回傳 (品類掃描結果, 耗時秒數)。"""
    log = log or _default_log
    categories = config_data.get("monitor_products", [])
    platform_ids = resolve_platform_ids(config_data)
    start = datetime.now()

    async with browser_context() as context:
        tasks = [
            asyncio.create_task(monitor_category_async(context, cat, platform_ids, log))
            for cat in categories
        ]
        scans = await _gather_with_stop(tasks, stop_event)

    elapsed = (datetime.now() - start).total_seconds()
    return scans, elapsed


async def run_keyword_scan(
    config_data: Dict[str, Any],
    keyword: str,
    log: LogCallback = None,
) -> Tuple[List[StoreInfo], float]:
    """單一關鍵字跨賣場即時查價，回傳 (賣場結果, 耗時秒數)。"""
    log = log or _default_log
    platform_ids = resolve_platform_ids(config_data)
    log(f"🔎 開始查價關鍵字：{keyword} ...")
    start = datetime.now()

    async with browser_context() as context:
        stores = await _scan_keyword(context, keyword, platform_ids)

    elapsed = (datetime.now() - start).total_seconds()
    log(f"✓ 查價完成，耗時 {elapsed:.2f} 秒，共 {len(stores)} 個賣場回傳")
    return stores, elapsed
