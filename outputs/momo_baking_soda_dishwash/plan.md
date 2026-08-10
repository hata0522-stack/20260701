# Task

使用 Playwright 開啟 momo 購物網（https://www.momoshop.com.tw）：
1. 在搜尋框中輸入『毛寶 小蘇打洗碗精 無香精』並進行搜尋，先記錄我方產品的促銷價格與規格。
2. 接著重新搜尋『小蘇打洗碗精』，尋找其他競爭品牌（橘子工坊、茶籽堂、淨毒五郎等）的類似產品。
3. 收集前 5 筆競品商品的『品牌名稱』、『商品名稱』、『容量』與『促銷價格』。
4. 將我方產品與這 5 筆競品交叉對比，整理成 Markdown 比較表格，並針對我方產品價格競爭力提供簡單對比建議。

# Critical Points

- [x] CP1: 成功開啟 momoshop.com.tw 首頁 — log step1 (URL=main/Main.jsp, title=momo購物網), final_execution_1_open_home.png
- [x] CP2: 搜尋「毛寶 小蘇打洗碗精 無香精」並提交搜尋 — log step2 (URL 含 %E6%AF%9B%E5%AF%B6%20%E5%B0%8F%E8%98%87...), final_execution_2_ourproduct_search.png
- [x] CP3: 記錄我方產品（毛寶）的促銷價格與規格 — log step3 (【毛寶】小蘇打洗碗精-無香精(2800gX4入), 價格639, 容量2800gX4入), final_execution_3_ourproduct_detail.png
- [x] CP4: 重新搜尋「小蘇打洗碗精」 — log step4 (URL 含 %E5%B0%8F%E8%98%87%E6%89%93%E6%B4%97%E7%A2%97%E7%B2%BE), final_execution_4_competitors_search.png
- [x] CP5: 收集前 5 筆競品的品牌、商品名稱、容量、促銷價格 — log step5 (5 筆競品 JSON, idx 0-4), final_execution_5_competitors_list.png + 5 張詳情頁截圖
- [x] CP6: 輸出我方 vs 5 競品的 Markdown 比較表格與價格競爭力建議 — final_runs/run_1/final_comparison.md + log FINAL_RESPONSE
