# Code Review: practice1.py

## 檔案概述

維基百科搜尋爬蟲腳本，使用 Playwright 瀏覽器自動化框架搜尋「臺灣」關鍵字並擷取頁面資訊。

---

## 優點

- 使用型別提示（Type Hint）標註回傳值與變數，提高可讀性
- 邏輯流程清晰，步驟明確
- 使用 `networkidle` 等待頁面完整載入，確保資料完整性

---

## 問題與建議

### 1. 錯字問題（Bug）

```python
# 第 19 行
print(f"返品首頁:{page.title()}")
```

「返品」為日文用法，中文應為「返回」或「回到」。

**修正建議：**

```python
print(f"返回首頁:{page.title()}")
```

### 2. 缺少錯誤處理

目前程式沒有任何例外處理機制，若網路斷線、頁面結構改變或元素找不到，程式會直接崩潰。

**建議加上 try-except：**

```python
def crawl(p: Playwright) -> None:
    browser = p.chromium.launch()
    try:
        page = browser.new_page()
        page.goto("https://zh.wikipedia.org", timeout=30000)
        # ... 其餘邏輯
    except Exception as e:
        print(f"爬蟲執行失敗: {e}")
    finally:
        browser.close()
```

### 3. 瀏覽器未確保關閉

若中途發生例外，`browser.close()` 不會被執行，可能導致瀏覽器程序殘留。

**建議使用 context manager 或 finally 區塊確保關閉。**

### 4. 截圖路徑硬編碼

```python
page.screenshot(path="screenshot.png")
```

路徑硬編碼且無自動檔名管理，多次執行會覆蓋舊檔。

**建議使用動態檔名或時間戳：**

```python
from datetime import datetime
filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
page.screenshot(path=filename)
```

### 5. 搜尋結果內容可能為空

```python
content: str = page.locator("#mw-content-text p").first.inner_text()
print(f"摘要: {content[:100]}")
```

若搜尋結果頁面結構不同（例如導向 disambiguation 頁面），第一個 `<p>` 可能不是預期內容。

**建議加上空值檢查：**

```python
elements = page.locator("#mw-content-text p")
if elements.count() > 0:
    content = elements.first.inner_text()
    print(f"摘要: {content[:100]}")
else:
    print("未找到摘要內容")
```

### 6. 未使用 `headless` 參數說明

`p.chromium.launch()` 預設以 headless 模式執行，這在爬蟲情境下是合理的，但若要除錯可改為：

```python
browser = p.chromium.launch(headless=False)
```

建議在註解或文件中說明此選項。

### 7. 函式職責過重

`crawl()` 函式同時負責瀏覽器管理、頁面操作、資料擷取與輸出。

**建議拆分職責：**

```python
def launch_browser(p: Playwright) -> Browser:
    """啟動瀏覽器"""
    return p.chromium.launch()

def search_wikipedia(page: Page, keyword: str) -> None:
    """在維基百科搜尋指定關鍵字"""
    page.goto("https://zh.wikipedia.org")
    page.locator("#searchInput").fill(keyword)
    page.keyboard.press("Enter")
    page.wait_for_load_state("networkidle")

def get_search_result(page: Page) -> dict:
    """擷取搜尋結果頁面資訊"""
    heading = page.locator("#firstHeading").inner_text()
    elements = page.locator("#mw-content-text p")
    content = elements.first.inner_text() if elements.count() > 0 else ""
    return {"heading": heading, "content": content[:100]}
```

---

## 總結

| 類別 | 狀態 |
|------|------|
| 功能正確性 | 基本可用，有錯字需修正 |
| 穩定性 | 缺少錯誤處理，建議加強 |
| 可維護性 | 可考慮拆分函式 |
| 可讀性 | 良好，型別提示完整 |
