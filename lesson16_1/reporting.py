"""報表輸出層：終端機報表、JSON 詳細數據、GFM Markdown 日報。

⚠️ 商業倫理說明：各商品包裝規格（如 1000g vs 300g x 12 盒）不同，
   本模組僅列出客觀售價，不進行價差相減或優劣計算。
"""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Union

from data_models import CategoryScan

NOTE = "單位與包裝規格不同，無輸出價差比較與優劣分析"
CONSOLE_WIDTH = 90
TITLE_MAX_LEN = 30


def _short_title(title: str) -> str:
    return (title[:TITLE_MAX_LEN] + "..") if len(title) > TITLE_MAX_LEN else title


def print_console_report(all_results: Sequence[CategoryScan]) -> None:
    """終端機表格報表：品類與品牌只在該群組第一列顯示，避免視覺重複。"""
    print("\n📊 【毛寶 vs 競品 多賣場即時價格監控報表】")
    print("註：因各商品包裝規格與單位不同，本報表僅呈現原始監控售價，不進行價差比較與優勢計算")
    print("-" * CONSOLE_WIDTH)
    print(f"{'品類':<12} {'品牌':<8} {'賣場':<12} {'搜尋商品標題':<32} {'售價'}")
    print("-" * CONSOLE_WIDTH)

    for cat_data in all_results:
        is_first_row_of_category = True

        for product in cat_data.products:
            is_first_row_of_product = True

            for store in product.stores:
                cat_disp = cat_data.category if is_first_row_of_category else ""
                brand_disp = f"[{product.brand}]" if is_first_row_of_product else ""
                price_str = f"${store.price}" if store.price > 0 else "未找到"

                print(
                    f"{cat_disp:<12} {brand_disp:<8} {store.platform:<12} "
                    f"{_short_title(store.title):<32} {price_str}"
                )
                is_first_row_of_category = False
                is_first_row_of_product = False

        print("-" * CONSOLE_WIDTH)


def build_json_payload(
    all_results: Sequence[CategoryScan], platform_names: Sequence[str], elapsed: float
) -> Dict[str, Any]:
    """組出可供其他系統整合的 JSON 結構（dataclass 自動轉巢狀 dict）"""
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_seconds": round(elapsed, 2),
        "platforms": list(platform_names),
        "note": NOTE,
        "data": [asdict(cat) for cat in all_results],
    }


def build_markdown_report(
    all_results: Sequence[CategoryScan], platform_names: Sequence[str], elapsed: float
) -> str:
    """組出給 PM 閱讀的 GFM Markdown 日報"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = [
        "# 毛寶企業 產品與競品多賣場價格監控日報",
        "",
        f"- **監控時間**：{timestamp}",
        f"- **總耗時**：{elapsed:.2f} 秒 (Playwright Async 多賣場平行併發)",
        f"- **監控賣場**：{', '.join(platform_names)}",
        "- **說明**：*因各品牌商品與包裝規格單位不一，本報告僅呈現各平台即時監控價格與標題，不進行價差比較。*",
        "",
        "## 📊 跨賣場價格一覽表",
        "",
        "| 品類 | 品牌 | 賣場平台 | 搜尋商品標題 | 售價 (TWD) | 商品連結 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for cat_data in all_results:
        for product in cat_data.products:
            brand_label = f"**{product.brand}**" if product.brand == "毛寶" else product.brand
            for store in product.stores:
                price_disp = f"**${store.price}**" if store.price > 0 else "N/A"
                url_disp = f"[商品連結]({store.url})" if store.url else "N/A"
                lines.append(
                    f"| {cat_data.category} | {brand_label} | {store.platform} | "
                    f"{store.title} | {price_disp} | {url_disp} |"
                )

    return "\n".join(lines) + "\n"


def save_json(file_path: Union[str, Path], data: Dict[str, Any]) -> None:
    with Path(file_path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_text(file_path: Union[str, Path], content: str) -> None:
    with Path(file_path).open("w", encoding="utf-8") as f:
        f.write(content)
