# Task

撰寫一段 Python Playwright 腳本，爬取櫃買中心「等價成交系統價格行情」頁面
(https://www.tpex.org.tw/zh-tw/mainboard/trading/info/pricing.html) 的
即時/每日行情表格資料，取得股票代號、股票名稱、成交價、漲跌、開盤價、
最高價、最低價及成交量等欄位，轉為 Pandas DataFrame 並匯出
`tpex_pricing.csv`（編碼 utf-8-sig）。

# Critical Points

- [x] CP1: 目標頁面成功載入（正確 URL、頁面標題、表格容器存在）。
      — 證據: log step 1「開啟目標頁面完成 -> URL: .../pricing.html | TITLE: 上櫃股票行情 - 證券櫃檯買賣中心」
- [x] CP2: 表格資料透過等待機制（wait_for_selector / wait_for_response）等待後完整載入，擷取到非空資料列。
      — 證據: log step 2「wait_for_selector，目前表格資料列數: 10」+「expect_response: ...dailyQuotes | date=20260805 | stat=ok」；API 回傳 10252 列
- [x] CP3: 每列資料正確對應 8 個欄位：股票代號、股票名稱、成交價、漲跌、開盤價、最高價、最低價、成交量。
      — 證據: log step 3 欄位對照（股票代號<-代號; 股票名稱<-名稱; 成交價<-收盤; ...; 成交量<-成交股數）；CSV 欄位=[股票代號,股票名稱,成交價,漲跌,開盤價,最高價,最低價,成交量]；DOM 首頁 10 列與 API JSON 相符 10/10
- [x] CP4: 擷取文字去除前後空白與多餘換行符號。
      — 證據: 驗證腳本 text-clean issues=0；9962 漲跌原始 '-0.01 ' 清理後 '-0.01'
- [x] CP5: 以 Pandas DataFrame 匯出 `tpex_pricing.csv`，編碼 utf-8-sig，檔案存在且含資料列。
      — 證據: log step 5「已匯出 CSV ... | 列數=10252 | utf-8-sig BOM=True」+ 讀回 shape=(10252, 8)
- [x] CP6: 程式碼含 try-except 異常處理與明確錯誤訊息。
      — 證據: final_script.py 含 try-except (wait_for_selector / expect_response 逾時處理) 與「錯誤: ...」訊息
- [x] CP7: 程式碼採用 async/await 非同步寫法與清晰註解。
      — 證據: final_script.py 使用 async def main / async with async_playwright / await，並附中文註解
- [x] CP8: 記錄最終資料量（列數）與一筆範例列資料（含成交價）於 log。
      — 證據: FINAL_RESPONSE: 日期=20260805 上櫃家數=890 資料筆數=10252 範例列={股票代號:006201, 股票名稱:元大富櫃50, 成交價:42.42, ...}
