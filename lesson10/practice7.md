# Practice 7：使用 Playwright 自動完成本機登入表單

## 練習目標

本練習使用 Playwright 開啟同一個資料夾中的 `login_demo.html`，自動完成下列操作：

1. 啟動 Chromium 瀏覽器。
2. 開啟本機 HTML 登入頁面。
3. 填入用戶名與密碼。
4. 找到並點擊「登入」按鈕。

這個範例的重點是學習如何使用具可讀性的元素定位方式，讓自動化程式能根據表單標籤和按鈕名稱操作頁面。

## 檔案關係

```text
lesson10/
├── login_demo.html   # 被自動操作的本機登入頁面
├── practice7.py      # Playwright 自動化程式
└── practice7.md      # 本說明文件
```

`practice7.py` 與 `login_demo.html` 必須放在同一個資料夾。程式會透過目前 Python 檔案的位置組合 HTML 路徑，因此不必依賴執行指令時所在的工作目錄。

## 程式流程說明

### 1. 匯入 Playwright 類別

```python
from playwright.sync_api import sync_playwright, Playwright, Browser, Page
import os
```

- `sync_playwright`：啟動 Playwright 的同步執行環境。
- `Playwright`、`Browser`、`Page`：提供型別註記，讓程式的用途更容易閱讀，也能協助編輯器提供提示。
- `os`：處理檔案路徑，避免直接手寫不同作業系統的路徑分隔符號。

### 2. 建立自動化函式

```python
def crawl(p: Playwright):
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
```

`crawl()` 負責執行一次完整的登入流程。

- `p.chromium.launch()`：啟動 Chromium。
- `headless=False`：顯示瀏覽器視窗，適合上課示範和除錯。
- `new_page()`：建立一個新的瀏覽器分頁。

正式測試或批次執行時，可以改成：

```python
browser = p.chromium.launch(headless=True)
```

這樣瀏覽器會在背景執行，不會顯示視窗。

### 3. 組合本機 HTML 路徑

```python
current_dir = os.path.dirname(os.path.abspath(__file__))
html_file = os.path.join(current_dir, "login_demo.html")
page.goto(f"file://{html_file}")
```

`__file__` 代表目前執行中的 Python 檔案。透過 `abspath()` 和 `dirname()` 可以取得 `practice7.py` 所在的資料夾，再用 `os.path.join()` 找到同資料夾中的 `login_demo.html`。

這種寫法比直接使用相對路徑更穩定。例如，即使在專案根目錄執行：

```bash
uv run lesson10/practice7.py
```

程式仍然能找到 HTML 檔案。

### 4. 使用標籤定位輸入欄位

```python
page.get_by_label("用戶名").fill("admin")
page.get_by_label("密碼").fill("password")
```

`get_by_label()` 會尋找與 `<label>` 文字關聯的表單元素。在 `login_demo.html` 中：

```html
<label for="username">用戶名</label>
<input id="username" ...>
```

因此，`get_by_label("用戶名")` 能找到 `id="username"` 的輸入框。

`fill()` 會清空原本內容，再填入新的文字，適合輸入帳號、密碼、搜尋文字等內容。

### 5. 使用角色與名稱定位按鈕

```python
page.get_by_role("button", name="登入").click()
```

- `get_by_role("button")`：尋找按鈕角色的元素。
- `name="登入"`：進一步限定按鈕的可存取名稱。
- `click()`：模擬使用者點擊。

相較於依賴 CSS class 或元素順序，`get_by_role()` 和 `get_by_label()` 通常更容易閱讀，也比較不容易因為頁面樣式調整而失效。

## 執行前準備

如果尚未安裝 Playwright 或 Chromium，請在專案根目錄執行：

```bash
uv sync
uv run playwright install chromium
```

接著執行程式：

```bash
uv run lesson10/practice7.py
```

也可以先切換到 `lesson10` 資料夾，再執行：

```bash
cd lesson10
uv run practice7.py
```

## 預期結果

執行後會看到 Chromium 視窗，程式會自動：

1. 開啟登入頁面。
2. 在用戶名欄位填入 `admin`。
3. 在密碼欄位填入 `password`。
4. 點擊「登入」。
5. 頁面顯示「登入成功！歡迎回來，admin」。

這個登入頁面只是前端示範，帳號和密碼寫在 `login_demo.html` 的 JavaScript 中，並不是真正連接後端的登入系統。

## 建議改進

### 1. 驗證登入成功

目前程式點擊按鈕後就結束，建議加入成功訊息驗證：

```python
success_message = page.get_by_text("登入成功！歡迎回來，admin")
success_message.wait_for(state="visible")
print("登入測試成功")
```

也可以使用更寬鬆的文字定位：

```python
page.get_by_text("登入成功！").wait_for(state="visible")
```

自動化測試不只要「執行操作」，也應該確認操作後的結果符合預期。

### 2. 關閉瀏覽器

目前使用 `headless=False` 時，瀏覽器視窗會保持開啟，方便觀察結果。若要讓程式完整釋放資源，可以在流程結束時加入：

```python
browser.close()
```

若在測試中使用例外處理，建議將關閉瀏覽器放在 `finally` 區塊，確保發生錯誤時也會執行。

### 3. 使用變數集中管理測試資料

```python
username = "admin"
password = "password"

page.get_by_label("用戶名").fill(username)
page.get_by_label("密碼").fill(password)
```

之後若要測試其他帳號，只需修改變數，不必在多個地方尋找字串。

### 4. 加入錯誤帳密測試

可以改用錯誤密碼，並驗證頁面是否跳出警告：

```python
def handle_dialog(dialog):
    print(f"收到提示：{dialog.message}")
    dialog.accept()

page.get_by_label("用戶名").fill("admin")
page.get_by_label("密碼").fill("wrong-password")
page.once("dialog", handle_dialog)
page.get_by_role("button", name="登入").click()
```

實際撰寫時，應在點擊前先註冊 dialog handler，才能穩定處理 JavaScript 的 `alert()`。這可作為進一步練習。

### 5. 擷取畫面協助除錯

```python
page.screenshot(path="login_result.png", full_page=True)
```

當元素找不到、畫面沒有如預期更新時，保存截圖可以協助確認實際頁面狀態。

## 常見問題

### 找不到「用戶名」或「密碼」欄位

請確認：

- `login_demo.html` 確實存在於 `practice7.py` 同一個資料夾。
- `<label>` 的文字仍然是「用戶名」和「密碼」。
- HTML 中的 `label for` 與 `input id` 仍然正確對應。

### 找不到「登入」按鈕

請確認按鈕文字是否變更。若按鈕文字已改成其他內容，必須同步修改：

```python
page.get_by_role("button", name="新的按鈕文字").click()
```

### 瀏覽器沒有啟動

請確認 Chromium 已安裝：

```bash
uv run playwright install chromium
```

### 執行後程式立即結束

這是因為目前程式只執行填寫和點擊，沒有等待成功訊息或其他驗證步驟。可以加入 `wait_for()` 或 `expect()`，讓測試明確檢查結果。

## 延伸練習

1. 將 `headless=False` 改成 `headless=True`，比較兩種模式的差異。
2. 加入登入成功訊息驗證，並印出結果。
3. 測試錯誤帳號和錯誤密碼。
4. 為登入成功與失敗的情況各保存一張截圖。
5. 將登入流程改寫成 `pytest` 測試函式。
6. 將帳號和密碼改由函式參數傳入。
7. 為 `browser.close()` 加入例外安全的資源清理流程。

## 參考資源

- [Playwright Python 官方文件](https://playwright.dev/python/)
- [Playwright Locator 定位器](https://playwright.dev/python/docs/locators)
- [Playwright Input 輸入操作](https://playwright.dev/python/docs/input)
