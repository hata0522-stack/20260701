"""毛寶企業 多賣場產品與競品價格每日監控系統 [Playwright Async 版] —— CLI 進入點。

執行方式：python clawler.py

架構分層：
    config.py      → 讀取 products_config.json
    scraper.py     → 瀏覽器生命週期 + 三層非同步併發
    *_platform.py  → 各賣場的抓取策略
    reporting.py   → 終端機 / JSON / Markdown 報表輸出
"""

import asyncio
from datetime import datetime
from pathlib import Path

from config import AppConfig
from reporting import (
    build_json_payload,
    build_markdown_report,
    print_console_report,
    save_json,
    save_text,
)
from scraper import PriceScraper, browser_context

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "products_config.json"  # 商品與賣場組態設定檔
REPORT_JSON = BASE_DIR / "price_report.json"     # 詳細數據 JSON 報表
REPORT_MD = BASE_DIR / "price_report.md"         # GFM Markdown 競品日報


async def main() -> None:
    print("=" * 80)
    print("毛寶企業 (Maobao) 多賣場產品與競品價格每日監控系統 [Playwright Async版]")
    print("=" * 80)

    try:
        config = AppConfig.load(CONFIG_FILE)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return

    print(
        f"📦 載入設定完成！監控 {len(config.categories)} 大品類，"
        f"跨賣場：{', '.join(config.platform_names)}...\n"
    )

    # 1. 啟動瀏覽器並執行超大規模平行併發抓取
    start_time = datetime.now()
    scraper = PriceScraper()
    async with browser_context(browser_name="firefox", headless=True) as context:
        all_results = await scraper.scan_all(context, config.categories)
    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 80)
    print(f"✓ 所有品類跨賣場抓取完成！總耗時僅：{elapsed:.2f} 秒 (非同步併發加速)")
    print("=" * 80)

    # 2. 終端機報表
    print_console_report(all_results)

    # 3. JSON 詳細數據（供系統整合）
    save_json(REPORT_JSON, build_json_payload(all_results, config.platform_names, elapsed))
    print(f"\n✓ 已匯出 JSON 詳細數據：{REPORT_JSON.name}")

    # 4. Markdown 分析報告（供 PM 閱讀）
    save_text(REPORT_MD, build_markdown_report(all_results, config.platform_names, elapsed))
    print(f"✓ 已匯出 Markdown 分析報告：{REPORT_MD.name}")


if __name__ == "__main__":
    asyncio.run(main())
