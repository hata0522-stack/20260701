# Practice 6：自動完成 Selenium 官方測試表單

## 練習目標

學習使用 Playwright 自動化填寫網頁表單，包括文字輸入、密碼欄位、文字區域、下拉選單、核取方塊與單選按鈕，並驗證表單送出後的結果。

## 程式碼逐行解釋

### 1. 匯入與設定

```python
from playwright.sync_api import sync_playwright
from playwright.sync_api import Playwright, Browser, Page, Locator

URL = "https://www.selenium.dev/selenium/web/web-form.html"
```

- 使用 `sync_playwright` 提供同步 API，適合初學者
- 匯入類型提示類別，提升程式碼可讀性
- 指定目標網址為 Selenium 官方測試表單

### 2. 主要執行函式

```python
def run(playwright: Playwright) -> None:
    browser: Browser = playwright.chromium.launch(headless=True)
    page: Page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded")
```

- `headless=True`：無頭模式執行，不顯示瀏覽器視窗
- `wait_until="domcontentloaded"`：等待 DOM 元素載入完成即可開始操作

### 3. 表單欄位操作

#### 文字輸入欄位
```python
page.get_by_label("Text input").fill("王小明")
```
- `get_by_label()`：透過關聯標籤定位表單元素
- `fill()`：清空欄位並填入新值

#### 密碼欄位
```python
page.get_by_label("Password").fill("practice-only")
```
- 密碼欄位同樣使用 `fill()` 方法

#### 文字區域
```python
page.get_by_label("Textarea").fill("這是 Playwright 表單自動化練習。")
```
- 文字區域（`<textarea>`）也使用相同方法

#### 下拉選單
```python
page.get_by_label("Dropdown (select)").select_option("2")
```
- `select_option()`：選擇下拉選單中的選項
- 參數可為選項的值（value）、標籤文字或索引

### 4. 核取方塊與單選按鈕

```python
checkbox: Locator = page.get_by_label("Default checkbox")
if not checkbox.is_checked():
    checkbox.check()
page.get_by_label("Default radio").check()
```
- `is_checked()`：檢查是否已勾選
- `check()`：勾選元素（若已勾選則不會重複操作）
- 核取方塊可以取消勾選，單選按鈕通常只能勾選

### 5. 送出表單與驗證

```python
page.get_by_role("button", name="Submit").click()
page.wait_for_url("**/submitted-form.html**")
message: Locator = page.get_by_text("Received!", exact=True)
message.wait_for(state="visible")
```
- `get_by_role()`：透過 ARIA 角色定位元素
- `wait_for_url()`：等待網址符合指定模式
- `get_by_text()`：透過文字內容定位元素
- `wait_for(state="visible")`：等待元素可見

### 6. 結果輸出

```python
print(f"送出後網址: {page.url}")
print(f"驗收訊息: {message.inner_text()}")
browser.close()
```
- 確認頁面跳轉正確
- 驗證成功訊息是否正確顯示

## 重要概念

### 元素定位策略

| 方法 | 適用情境 | 範例 |
|------|----------|------|
| `get_by_label()` | 有標籤的表單元素 | `get_by_label("Email")` |
| `get_by_role()` | 按鈕、連結等互動元素 | `get_by_role("button", name="Submit")` |
| `get_by_text()` | 透過顯示文字定位 | `get_by_text("Submit")` |
| `get_by_placeholder()` | 透過 placeholder 定位 | `get_by_placeholder("Enter email")` |

### 表單操作方法

| 方法 | 功能 | 使用場景 |
|------|------|----------|
| `fill()` | 填入文字 | 文字輸入、密碼、文字區域 |
| `check()` | 勾選 | 核取方塊、單選按鈕 |
| `select_option()` | 選擇選項 | 下拉選單 |
| `click()` | 點擊 | 按鈕、連結 |

### 等待策略

- `wait_for_url()`：等待頁面跳轉
- `wait_for(state="visible")`：等待元素可見
- `wait_for_load_state()`：等待頁面載入狀態

## 執行方式

```bash
uv run practice6.py
```

## 預期輸出

```
送出後網址: https://www.selenium.dev/selenium/web/submitted-form.html
驗收訊息: Received!
```

## 建議與擴展練習

### 1. 錯誤處理增強

```python
try:
    page.get_by_role("button", name="Submit").click()
    page.wait_for_url("**/submitted-form.html**", timeout=10000)
except PlaywrightTimeoutError:
    print("表單送出超時，請檢查網路狀態")
    page.screenshot(path="error_screenshot.png")
```

### 2. 使用不同瀏覽器引擎

```python
def run(playwright: Playwright, browser_name: str = "chromium") -> None:
    browser_type = getattr(playwright, browser_name)
    browser = browser_type.launch(headless=False)  # 顯示瀏覽器視窗
    # ... 其餘程式碼
```

### 3. 參數化測試資料

```python
test_data = {
    "text_input": "李大華",
    "password": "secure_password_123",
    "textarea": "這是自動化測試填入的內容",
    "dropdown": "3"
}

page.get_by_label("Text input").fill(test_data["text_input"])
page.get_by_label("Password").fill(test_data["password"])
```

### 4. 截圖記錄

```python
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

page.screenshot(path=OUTPUT_DIR / "form_filled.png", full_page=True)
```

### 5. 表單欄位驗證

```python
# 填入表單前，先驗證欄位存在
text_input = page.get_by_label("Text input")
assert text_input.is_visible(), "文字輸入欄位不可見"

# 填入後驗證值
text_input.fill("測試內容")
assert text_input.input_value() == "測試內容", "欄位值驗證失敗"
```

### 6. 處理動態載入的元素

```python
# 等待特定元素出現後再操作
page.wait_for_selector("#dynamic_element")
dynamic_element = page.locator("#dynamic_element")
dynamic_element.click()
```

## 常見問題與解決方案

### Q1: 找不到元素怎麼辦？

**解決方案：**
- 使用 `page.pause()` 開啟 Playwright Inspector 檢查元素
- 嘗試不同的定位策略（label、role、text）
- 檢查元素是否在 iframe 中

### Q2: 表單送出後沒有跳轉？

**解決方案：**
- 增加等待時間：`page.wait_for_url(timeout=30000)`
- 檢查是否有 JavaScript 驗證阻止送出
- 使用 `page.wait_for_load_state("networkidle")`

### Q3: 如何處理隱藏的表單元素？

**解決方案：**
- 使用 `force=True` 參數強制操作：`checkbox.check(force=True)`
- 先使用 JavaScript 顯示元素

## 學習重點

1. **元素定位優先順序**：優先使用 `get_by_label()` 和 `get_by_role()`，這是最穩固的定位方式
2. **等待策略**：永遠不要使用 `time.sleep()`，改用 Playwright 的等待方法
3. **無頭模式**：在自動化測試中使用 `headless=True` 提升執行速度
4. **錯誤處理**：加入適當的例外處理，讓測試更加穩健

## 參考資源

- [Playwright 官方文檔 - 表單操作](https://playwright.dev/docs/input)
- [Playwright 官方文檔 - 元素定位](https://playwright.dev/docs/locators)
- [Selenium 官方測試表單](https://www.selenium.dev/selenium/web/web-form.html)
