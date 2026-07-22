# Code Review: practice1.py

## 檔案說明
使用 Playwright 爬取中文維基百科，搜尋「臺灣」並顯示搜尋結果的標題與摘要。

---

## 建議事項

### 1. 使用 `with` 管理瀏覽器生命週期
**問題**：若 `page` 操作發生例外，`browser.close()` 不會被执行。

**建議**：
```python
browser: Browser = p.chromium.launch()
with browser:
    page: Page = browser.new_page()
    # ... 操作
```

### 2. 使用常數管理 URL
**問題**：URL 硬寫在程式碼中，不易維護。

**建議**：
```python
WIKI_URL = "https://zh.wikipedia.org"
page.goto(WIKI_URL)
```

### 3. 選擇器改用 `get_by_role`
**問題**：`input.cdx-text-input__input` 依賴 CSS class，維基百科改版後容易失效。

**建議**：
```python
page.get_by_role("searchbox").first.fill("臺灣")
```

### 4. 補充錯誤處理
**問題**：網路逾時或頁面結構變動時，程式會直接崩潰。

**建議**：加入 `try-except` 或使用 Playwright 的 `expect` 等待機制。

### 5. 補充 `timeout` 參數
**問題**：`wait_for_timeout` 與 `wait_for_load_state` 未明確設定逾時時間。

**建議**：
```python
page.wait_for_load_state("networkidle", timeout=30000)
```

### 6. 截圖檔名加入時間戳記
**問題**：多次執行會覆蓋同一個 `screenshot.png`。

**建議**：
```python
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
page.screenshot(path=f"screenshot_{timestamp}.png")
```

---

## 程式碼風格

| 項目 | 狀態 |
|------|------|
| PEP 8 縮排 (4 空格) | ✓ |
| 類型提示 | ✓ |
| 函式 docstring | ✓ |
| 行註解 | ✓ |
