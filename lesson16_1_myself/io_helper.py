import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

from data_models import CategoryScan, ProductScan, StoreInfo


@dataclass
class AppConfig:
    project_name: str
    version: str
    platforms: List[Dict[str, str]]
    monitor_products: List[Dict[str, Any]]


def load_config(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"找不到設定檔：{file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_report(file_path: str, data: Dict[str, Any]) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_report_data(
    scans: List[CategoryScan],
    elapsed: float,
    platform_names: List[str],
) -> Dict[str, Any]:
    """組裝 JSON 報表結構（與 console / Markdown 共用）。"""
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 2),
        "platforms": platform_names,
        "note": "單位與包裝規格不同，無輸出價差比較與優劣分析",
        "data": [asdict(c) for c in scans],
    }


def format_console_report(all_results: List[CategoryScan]) -> None:
    """終端機報表輸出。

    商業倫理說明：各商品包裝規格（如 1000g vs 300gX12盒）不同，
    僅列出客觀售價，不直接進行相減計算優劣。
    """
    print("\n📊 【毛寶 vs 競品 多賣場即時價格監控報表】")
    print("註：因各商品包裝規格與單位不同，本報表僅呈現原始監控售價，不進行價差比較與優勢計算")
    print("-" * 90)
    print(f"{'品類':<12} {'品牌':<8} {'賣場':<12} {'搜尋商品標題':<32} {'售價'}")
    print("-" * 90)

    for cat_data in all_results:
        all_prods = [p for p in ([cat_data.maobao_product] + cat_data.competitors) if p is not None]
        for prod_idx, prod in enumerate(all_prods):
            brand_label = f"[{prod.brand}]"
            is_first_store = True
            for store in prod.stores:
                title_short = (store.title[:30] + "..") if len(store.title) > 30 else store.title
                price_str = f"${store.price}" if store.price > 0 else "未找到"

                cat_disp = cat_data.category if (prod_idx == 0 and is_first_store) else ""
                brand_disp = brand_label if is_first_store else ""

                print(f"{cat_disp:<12} {brand_disp:<8} {store.platform:<12} {title_short:<32} {price_str}")
                is_first_store = False
        print("-" * 90)


def format_markdown_report(all_results: List[CategoryScan], platforms_names: List[str], elapsed: float) -> str:
    """產出 GFM Markdown 分析報告內容 (供 PM 報告)。"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = (
        "# 毛寶企業 產品與競品多賣場價格監控日報\n\n"
        f"- **監控時間**：{timestamp}\n"
        f"- **總耗時**：{elapsed:.2f} 秒 (Playwright Async 多賣場平行併發)\n"
        f"- **監控賣場**：{', '.join(platforms_names)}\n"
        "- **說明**：*因各品牌商品與包裝規格單位不一，本報告僅呈現各平台即時監控價格與標題，不進行價差比較。*\n\n"
        "## 📊 跨賣場價格一覽表\n\n"
        "| 品類 | 品牌 | 賣場平台 | 搜尋商品標題 | 售價 (TWD) | 商品連結 |\n"
        "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    )
    for cat_data in all_results:
        all_prods = [p for p in ([cat_data.maobao_product] + cat_data.competitors) if p is not None]
        for prod in all_prods:
            brand_label = f"**{prod.brand}**" if prod.brand == "毛寶" else prod.brand
            for store in prod.stores:
                price_disp = f"**${store.price}**" if store.price > 0 else "N/A"
                url_disp = f"[商品連結]({store.url})" if store.url else "N/A"
                md += f"| {cat_data.category} | {brand_label} | {store.platform} | {store.title} | {price_disp} | {url_disp} |\n"
    return md
