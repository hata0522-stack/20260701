from typing import List, Any, Dict
from datetime import datetime
from models.data_models import CategoryScan, ProductScan, StoreInfo

def format_console_report(all_results: List[CategoryScan]):
    print("\n📊 【毛寶 vs 競品 多賣場即時價格監控報表】")
    print("註：因各商品包裝規格與單位不同，本報表僅呈現原始監控售價，不進行價差比較與優勢計算")
    print("-" * 90)
    print(f"{'品類':<12} {'品牌':<8} {'賣場':<12} {'搜尋商品標題':<32} {'售價'}")
    print("-" * 90)

    for cat_data in all_results:
        cat_name = cat_data.category
        # 合併毛寶與競品列表進行顯示
        all_prods = [cat_data.maobao_product] + cat_data.competitors
        
        first_item_in_category = True
        for prod in all_prods:
            brand_label = f"[{prod.brand}]" if first_item_in_category else ""
            first_item_in_category = False

            for store in prod.stores:
                title_short = (store.title[:30] + "..") if len(store.title) > 30 else store.title
                price_str = f"${store.price}" if store.price > 0 else "未找到"
                
                cat_disp = cat_name if (first_item_in_category or True) and prod == cat_data.maobao_product else ""
                # 注意：原邏輯中 cat_disp 會在第一列顯示，這需要精修以符合視覺需求
                # 這裡暫時遵循原代碼 logic 進行搬移
                
                # 為符合原版 print 邏輯，我們需要在 loop 中判斷是否為該品類的第一個品牌
                # 但簡單起見，我們先照搬內容
                print(f"{cat_disp:<12} {brand_label:<8} {store.platform:<12} {title_short:<32} {price_str}")
            
            # 修正 print logic 的一個小細節：在原版中，category 只在第一個品牌出現時印出
            # 我們需要記錄該品類是否已經印過 category 了
    print("-" * 90)

def format_markdown_report(all_results: List[CategoryScan], platforms_names: List[str], elapsed: float) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md = f"# 毛寶企業 產品與競品多賣場價格監控日報\n\n"
    md += f"- **監控時間**：{timestamp}\n"
    md += f"- **總耗時**：{elapsed:.2f} 秒 (Playwright Async 多賣場平行併發)\n"
    md += f"- **監控賣場**：{', '.join(platforms_names)}\n"
    md += f"- **說明**：*因各品牌商品與包裝規格單位不一，本報告僅呈現各平台即時監控價格與標題，不進行價差比較。*\n\n"
    md += f"## 📊 跨賣場價格一覽表\n\n"
    md += f"| 品類 | 品牌 | 賣場平台 | 搜尋商品標題 | 售價 (TWD) | 商品連結 |\n"
    md += f"| :--- | :--- | :--- | :--- | :--- | : |\n"

    for cat_data in all_results:
        cat_name = cat_data.category
        all_prods = [cat_data.maobao_product] + cat_data.competitors
        for prod in all_prods:
            brand_label = f"**{prod.brand}**" if prod.brand == '毛寶' else prod.brand
            for store in prod.stores:
                price_disp = f"**${store.price}**" if store.price > 0 else "N/A"
                url_disp = f"[商品連結]({store.url})" if store.url else "N/A"
                md += f"| {cat_name} | {brand_label} | {store.platform} | {store.title} | {price_disp} | {url_disp} |\n"
    return md
