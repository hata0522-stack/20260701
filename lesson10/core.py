"""核心自動化模組：分離 Playwright 操作邏輯，提供結構化回傳。"""
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

from playwright.sync_api import Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


# 目標網址
TARGET_URL = "https://www.selenium.dev/selenium/web/web-form.html"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass
class FormData:
    """表單輸入資料結構"""
    name: str = "王小明"
    password: str = "practice-only"
    notes: str = "這是 Playwright 表單自動化練習。"
    dropdown_value: str = "2"
    checkbox_checked: bool = True
    radio_checked: bool = True


@dataclass
class ExecutionResult:
    """執行結果結構"""
    success: bool = False
    final_url: str = ""
    received_message: str = ""
    elapsed_ms: float = 0.0
    screenshot_path: str = ""
    error_message: str = ""
    steps: list[str] = field(default_factory=list)


def _ensure_output_dir() -> Path:
    """確保輸出目錄存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def _take_screenshot(page: Any, filename: str) -> str:
    """截圖並返回路徑"""
    output_dir = _ensure_output_dir()
    screenshot_path = output_dir / filename
    page.screenshot(path=screenshot_path, full_page=True)
    return str(screenshot_path)


def _friendly_error(exc: Exception) -> str:
    """將例外轉換為人類可讀的錯誤訊息"""
    if isinstance(exc, PlaywrightTimeoutError):
        return "操作超時，請提高 timeout 值或檢查網路狀態"
    if isinstance(exc, PlaywrightError):
        return f"瀏覽器錯誤：{str(exc).splitlines()[0]}"
    return f"未預期錯誤：{str(exc)}"


def run_automation(
    playwright: Playwright,
    form_data: FormData,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> ExecutionResult:
    """
    執行表單自動化操作。

    參數:
        playwright: Playwright 實例
        form_data: 表單資料
        headless: 是否以無頭模式執行
        timeout_ms: 導航超時（毫秒）

    回傳:
        ExecutionResult 結構化結果
    """
    result = ExecutionResult()
    browser = None

    try:
        # 步驟 1: 啟動瀏覽器
        result.steps.append("啟動瀏覽器...")
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()

        # 步驟 2: 導航到目標頁面
        result.steps.append("導航到目標頁面...")
        page.goto(TARGET_URL, wait_until="domcontentloaded", timeout=timeout_ms)

        # 步驟 3: 填寫文字輸入
        result.steps.append("填寫文字輸入欄位...")
        page.get_by_label("Text input").fill(form_data.name)

        # 步驟 4: 填寫密碼
        result.steps.append("填寫密碼欄位...")
        page.get_by_label("Password").fill(form_data.password)

        # 步驟 5: 填寫文字區域
        result.steps.append("填寫備註欄位...")
        page.get_by_label("Textarea").fill(form_data.notes)

        # 步驟 6: 選擇下拉選項
        result.steps.append("選擇下拉選項...")
        page.get_by_label("Dropdown (select)").select_option(form_data.dropdown_value)

        # 步驟 7: 勾選核取方塊
        result.steps.append("設定核取方塊...")
        checkbox = page.get_by_label("Default checkbox")
        if form_data.checkbox_checked and not checkbox.is_checked():
            checkbox.check()
        elif not form_data.checkbox_checked and checkbox.is_checked():
            checkbox.uncheck()

        # 步驟 8: 勾選單選按鈕
        result.steps.append("設定單選按鈕...")
        if form_data.radio_checked:
            page.get_by_label("Default radio").check()

        # 步驟 9: 截圖（送出前）
        result.steps.append("截圖（送出前）...")
        result.screenshot_path = _take_screenshot(page, "before_submit.png")

        # 步驟 10: 點擊送出按鈕
        result.steps.append("點擊送出按鈕...")
        page.get_by_role("button", name="Submit").click()

        # 步驟 11: 等待頁面跳轉
        result.steps.append("等待頁面跳轉...")
        page.wait_for_url("**/submitted-form.html**", timeout=timeout_ms)

        # 步驟 12: 驗證成功訊息
        result.steps.append("驗證成功訊息...")
        message = page.get_by_text("Received!", exact=True)
        message.wait_for(state="visible", timeout=timeout_ms)
        result.received_message = message.inner_text()

        # 步驟 13: 截圖（送出後）
        result.steps.append("截圖（送出後）...")
        result.screenshot_path = _take_screenshot(page, "after_submit.png")

        # 收集結果
        result.final_url = page.url
        result.success = True
        result.steps.append("執行完成！")

    except Exception as exc:
        result.error_message = _friendly_error(exc)
        result.steps.append(f"執行失敗：{result.error_message}")

        # 失敗時也截圖
        try:
            if browser:
                pages = browser.pages
                if pages:
                    result.screenshot_path = _take_screenshot(pages[0], "error.png")
        except Exception:
            pass

    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass

    return result


def execute_automation(
    name: str,
    password: str,
    notes: str,
    dropdown_value: str,
    checkbox_checked: bool,
    radio_checked: bool,
    headless: bool = True,
    timeout_ms: int = 30000,
) -> dict[str, Any]:
    """
    執行自動化並返回字典格式結果（供 Gradio 使用）。

    參數:
        name: 姓名
        password: 練習用密碼
        notes: 備註
        dropdown_value: 下拉選項值
        checkbox_checked: 核取方塊狀態
        radio_checked: 單選按鈕狀態
        headless: 是否無頭模式
        timeout_ms: 超時毫秒數

    回傳:
        結構化字典結果
    """
    form_data = FormData(
        name=name,
        password=password,
        notes=notes,
        dropdown_value=dropdown_value,
        checkbox_checked=checkbox_checked,
        radio_checked=radio_checked,
    )

    start_time = perf_counter()

    with sync_playwright() as playwright:
        result = run_automation(playwright, form_data, headless, timeout_ms)

    elapsed_ms = (perf_counter() - start_time) * 1000

    return {
        "success": result.success,
        "final_url": result.final_url,
        "received_message": result.received_message,
        "elapsed_ms": round(elapsed_ms, 1),
        "screenshot_path": result.screenshot_path,
        "error_message": result.error_message,
        "steps": result.steps,
    }


# 供 practice6.py 直接呼叫的函式
def run_form_automation(playwright: Playwright) -> None:
    """
    執行預設表單自動化（保留原本 practice6.py 的功能）。

    參數:
        playwright: Playwright 實例
    """
    form_data = FormData()
    result = run_automation(playwright, form_data, headless=True)
    print(f"送出後網址: {result.final_url}")
    print(f"驗收訊息: {result.received_message}")
