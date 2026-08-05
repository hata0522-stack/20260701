"""
專案 01：開啟真實網頁，檢查標題並留下截圖。

本範例展示如何使用 Playwright 開啟指定網頁、
檢查頁面標題與內容，並儲存完整頁面截圖。
支援三種瀏覽器引擎：chromium、firefox、webkit。
"""

import argparse
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


# 目標網址
URL = "https://example.com/"
# 輸出截圖的資料夾（與此腳本同目錄下的 output/）
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")
MIN_TIMEOUT_MS = 100
MAX_TIMEOUT_MS = 300_000


@dataclass
class CheckResult:
    """網站檢查結果的資料容器"""

    url: str
    browser: str
    success: bool = False
    http_status: int | None = None
    page_title: str = ""
    main_heading: str = ""
    final_url: str = ""
    response_time_ms: float = 0.0
    screenshot_path: str | None = None
    error_message: str = ""
    warnings: list[str] = field(default_factory=list)


def validate_url(url: str) -> str:
    """驗證並整理 HTTP(S) 網址，失敗時提供適合顯示給使用者的訊息。"""
    cleaned_url = url.strip()
    if not cleaned_url:
        raise ValueError("請輸入要檢查的網址，例如：https://example.com/")

    parsed = urlparse(cleaned_url)
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("網址必須以 http:// 或 https:// 開頭。")
    if not parsed.netloc or any(char.isspace() for char in parsed.netloc):
        raise ValueError("網址格式不完整，請確認主機名稱是否正確。")
    return cleaned_url


def validate_timeout(timeout_ms: int | str) -> int:
    """驗證逾時毫秒數，並回傳可供 Playwright 使用的整數。"""
    try:
        value = int(timeout_ms)
    except (TypeError, ValueError) as exc:
        raise ValueError("Timeout 必須是整數毫秒，例如：30000。") from exc

    if not MIN_TIMEOUT_MS <= value <= MAX_TIMEOUT_MS:
        raise ValueError(
            f"Timeout 必須介於 {MIN_TIMEOUT_MS} 到 {MAX_TIMEOUT_MS} 毫秒之間。"
        )
    return value


def _friendly_error_message(exc: Exception) -> str:
    """把常見 Playwright 例外轉成學生看得懂、可採取行動的說明。"""
    detail = str(exc).strip().splitlines()[0] if str(exc).strip() else "未知錯誤"
    if isinstance(exc, PlaywrightTimeoutError):
        return "網站在指定時間內沒有完成載入，請提高 Timeout 或確認網路狀態。"
    if isinstance(exc, PlaywrightError) and "Executable doesn't exist" in str(exc):
        return "找不到瀏覽器程式，請先執行：uv run playwright install"
    if isinstance(exc, PlaywrightError):
        return f"瀏覽器無法完成檢查：{detail}"
    return f"檢查時發生未預期的錯誤：{detail}"


def check_website_core(
    url: str,
    browser_name: str = "chromium",
    headless: bool = True,
    timeout_ms: int = 30000,
    heading_selector: str | None = None,
    output_dir: Path | str = OUTPUT_DIR,
) -> CheckResult:
    """
    核心檢查函式：開啟瀏覽器、導航、收集頁面資訊、儲存截圖。

    參數:
        url: 目標網址
        browser_name: 瀏覽器名稱 (chromium/firefox/webkit)
        headless: 是否以無頭模式執行
        timeout_ms: 導航超時（毫秒）
        heading_selector: 選擇器，用於定位主標題；若為 None 則自動找第一個 h1

    回傳:
        CheckResult 物件，包含所有檢查結果
    """
    result = CheckResult(url=url.strip(), browser=browser_name)
    browser = None

    try:
        checked_url = validate_url(url)
        checked_timeout = validate_timeout(timeout_ms)
        if browser_name not in SUPPORTED_BROWSERS:
            raise ValueError(
                "不支援的瀏覽器，請選擇 chromium、firefox 或 webkit。"
            )

        screenshot_dir = Path(output_dir)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser_type = getattr(playwright, browser_name)
            browser = browser_type.launch(headless=headless)
            page = browser.new_page(viewport={"width": 1280, "height": 720})

            start = time.perf_counter()
            response = page.goto(
                checked_url,
                wait_until="domcontentloaded",
                timeout=checked_timeout,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            result.response_time_ms = round(elapsed_ms, 1)

            result.http_status = response.status if response else None
            result.page_title = page.title()
            result.final_url = page.url

            if heading_selector:
                heading_el = page.query_selector(heading_selector)
                result.main_heading = heading_el.inner_text() if heading_el else ""
            else:
                h1 = page.query_selector("h1")
                result.main_heading = h1.inner_text() if h1 else ""

            screenshot_filename = f"check_{browser_name}_{time.time_ns()}.png"
            screenshot_path = screenshot_dir / screenshot_filename
            page.screenshot(path=screenshot_path, full_page=True)
            result.screenshot_path = str(screenshot_path)

            result.success = True
            browser.close()
            browser = None

    except Exception as e:
        result.success = False
        result.error_message = _friendly_error_message(e)
        result.warnings.append(f"{type(e).__name__}: {e}")
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass

    return result


def check_website(browser_name: str = "chromium") -> None:
    """
    使用指定的瀏覽器開啟目標網頁，檢查 HTTP 狀態、頁面標題與主標題，
    最後將頁面截圖儲存至 OUTPUT_DIR（保留原本 CLI 行為）。

    參數:
        browser_name (str): 瀏覽器名稱，可為 "chromium"、"firefox" 或 "webkit"。
    """
    result = check_website_core(
        url=URL,
        browser_name=browser_name,
        headless=True,
    )
    print(f"瀏覽器: {result.browser}")
    print(f"HTTP 狀態: {result.http_status if result.http_status else '無回應'}")
    print(f"頁面標題: {result.page_title}")
    print(f"主標題: {result.main_heading}")
    print(f"截圖: {result.screenshot_path}")
    if not result.success:
        print(f"錯誤: {result.error_message}")


# 當此腳本被直接執行時（非被 import）
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="使用 Playwright 檢查網頁並擷取截圖"
    )
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="選擇瀏覽器引擎 (預設: chromium)",
    )
    args = parser.parse_args()
    check_website(args.browser)
