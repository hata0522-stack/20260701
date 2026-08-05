# 線上表單自動化助理

使用 Playwright 與 Gradio 建立的互動式表單自動化工具，可自動填寫 Selenium 官方測試表單。

## 專案結構

```
lesson10/
├── app.py              # Gradio UI 介面
├── core.py             # 核心自動化邏輯（分離 UI）
├── practice6.py        # 原始腳本版本（仍可獨立執行）
├── practice6.md        # 練習說明文件
├── output/             # 截圖輸出目錄
└── README.md           # 本文件
```

## 功能特色

- ✅ 自動填寫文字輸入、密碼、文字區域
- ✅ 自動選擇下拉選項
- ✅ 自動勾選核取方塊與單選按鈕
- ✅ 送出表單並驗證結果
- ✅ 成功與失敗時自動截圖
- ✅ 即時步驟指示與執行結果
- ✅ 支援無頭/有頭模式切換
- ✅ 可調整超時時間
- ✅ 示範資料載入與表單清除

## 安裝與執行

### 1. 安裝依賴套件

```bash
# 使用 uv（推薦）
uv sync

# 或使用 pip
pip install gradio playwright
```

### 2. 安裝 Playwright 瀏覽器

```bash
uv run playwright install chromium
```

### 3. 執行 Gradio UI

```bash
uv run app.py
```

開啟瀏覽器訪問 `http://localhost:7860`

### 4. 執行原始腳本

```bash
uv run practice6.py
```

## 使用說明

### Gradio 介面操作

1. **載入示範資料**：點擊「📋 載入示範資料」按鈕，自動填入預設值
2. **自訂表單**：修改姓名、密碼、備註等欄位
3. **執行自動化**：點擊「🚀 執行自動化」按鈕
4. **查看結果**：右側顯示執行步驟、結果訊息與截圖預覽
5. **下載截圖**：成功或失敗時可下載截圖記錄

### 表單欄位說明

| 欄位 | 說明 | 預設值 |
|------|------|--------|
| 姓名 | 文字輸入欄位 | 王小明 |
| 練習用密碼 | 密碼欄位（隱藏顯示） | practice-only |
| 備註 | 文字區域 | 這是 Playwright 表單自動化練習。 |
| 下拉選項 | 選擇 1-5 | 2 |
| 核取方塊 | 預設勾選 | ✓ |
| 單選按鈕 | 預設選取 | ● |
| 無頭模式 | 不顯示瀏覽器視窗 | ✓ |
| 超時時間 | 操作超時毫秒數 | 30000 |

## 程式架構

### 核心模組 (core.py)

- `FormData`：表單資料結構
- `ExecutionResult`：執行結果結構
- `run_automation()`：執行 Playwright 自動化
- `execute_automation()`：供 Gradio 呼叫的包裝函式

### UI 介面 (app.py)

- 使用 `gr.Blocks` 建立自訂佈局
- 左側表單區、右側結果區
- 自訂 CSS 樣式
- 事件處理與狀態管理

### 設計原則

1. **關注點分離**：UI 與核心邏輯完全分離
2. **結構化回傳**：核心層回傳 dict，UI 只負責顯示
3. **不保存敏感資訊**：密碼不寫入 log，僅保留本次 session 截圖
4. **錯誤處理**：完整的例外處理與人類可讀錯誤訊息

## API 使用

Gradio 介面提供 REST API，可透過程式碼呼叫：

```python
import gradio as gr

# 呼叫自動化 API
result = gr.Interface.load(
    name="http://localhost:7860/",
    api_name="execute",
).predict(
    name="王小明",
    password="practice-only",
    notes="測試備註",
    dropdown_value="2",
    checkbox_checked=True,
    radio_checked=True,
    headless=True,
    timeout_ms=30000,
)
```

## 常見問題

### Q1: 找不到瀏覽器程式

執行以下指令安裝瀏覽器：

```bash
uv run playwright install chromium
```

### Q2: 超時錯誤

提高 timeout 值，或檢查網路連線狀態。

### Q3: 元素找不到

目標頁面可能已更新，請檢查 Selenium 官方測試表單的 HTML 結構。

## 學習資源

- [Playwright 官方文檔](https://playwright.dev/python/)
- [Gradio 官方文檔](https://www.gradio.app/docs/)
- [Selenium 官方測試表單](https://www.selenium.dev/selenium/web/web-form.html)

## 授權條款

本專案僅供學習用途。
