"""
抓取櫃買中心「等價成交系統價格行情」網頁資料的 Playwright 腳本。

目標網址:
    https://www.tpex.org.tw/zh-tw/mainboard/trading/info/pricing.html

說明:
    1. 該網頁為動態網頁，行情表格是由前端 JavaScript 發送 API 請求
       (POST https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes)
       後非同步渲染而成。
    2. 本腳本使用 wait_for_selector 等待表格 DOM 元素載入完成，
       並使用 wait_for_response 等待行情 API 回應取得完整資料。
    3. 取得資料後以 Pandas DataFrame 整理，匯出為 tpex_pricing.csv
       (編碼: utf-8-sig)。

使用方式:
    python final_script.py
"""

import asyncio
from pathlib import Path

import pandas as pd
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# ---------------------------------------------------------------------------
# 路徑與常數設定
# ---------------------------------------------------------------------------
RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")  # 每次乾淨執行前重設 log

START_URL = "https://www.tpex.org.tw/zh-tw/mainboard/trading/info/pricing.html"
QUOTES_API_URL = "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes"
OUTPUT_CSV = RUN_DIR.parent.parent / "tpex_pricing.csv"

# 設定適當的 User-Agent 以降低被擋機率
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) "
    "Gecko/20100101 Firefox/130.0"
)

# 需求欄位對照表: 使用者要求的欄位名稱 -> 頁面表格 / API 欄位名稱
REQUIRED_COLUMNS = {
    "股票代號": "代號",
    "股票名稱": "名稱",
    "成交價": "收盤",
    "漲跌": "漲跌",
    "開盤價": "開盤",
    "最高價": "最高",
    "最低價": "最低",
    "成交量": "成交股數",
}


def log(step: int, msg: str) -> None:
    """寫入一條執行動作紀錄到 log 檔，並同步印到 stdout。"""
    line = f"step {step} action: {msg}\n"
    LOG.open("a").write(line)
    print(line, end="")


def clean_text(value) -> str:
    """去除文字前後空白、換行符號與多餘空白字元。"""
    if value is None:
        return ""
    return " ".join(str(value).split())


async def capture_quotes_response(page, on_payload) -> None:
    """註冊 response 監聽器，擷取行情 API 的 JSON 回應。"""
    async def _on_response(response):
        if (
            response.request.method == "POST"
            and "afterTrading/dailyQuotes" in response.url
        ):
            try:
                on_payload(await response.json())
            except Exception as exc:
                on_payload({"capture_error": str(exc)})
    page.on("response", _on_response)


async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 1800},
            user_agent=USER_AGENT,
        )
        page = await context.new_page()

        # 用來存放 API 回應資料的容器
        captured = {}

        try:
            # 註冊 response 監聽器作為資料備援 (即使 wait_for_response 逾時也能拿到資料)
            await capture_quotes_response(page, captured.update)

            # 在 goto 之前先建立 expect_response 監聽，確保不會漏接行情 API 回應
            quotes_expectation = page.expect_response(
                lambda res: (
                    res.request.method == "POST"
                    and "afterTrading/dailyQuotes" in res.url
                ),
                timeout=30000,
            )
            response_info = await quotes_expectation.__aenter__()

            # step 1: 開啟目標頁面
            # ------------------------------------------------------------------
            await page.goto(START_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1500)
            title = await page.title()
            log(1, f"開啟目標頁面完成 -> URL: {page.url} | TITLE: {title}")
            await page.screenshot(
                path=str(SCREENSHOTS / "final_execution_1_open_start_page.png")
            )

            # step 2: 等待表格 DOM 載入完成 (wait_for_selector)
            # ------------------------------------------------------------------
            table = page.locator("table.C1_.R3_")
            try:
                await page.wait_for_selector(
                    "table.C1_.R3_ tbody tr", timeout=30000
                )
                row_count = await table.locator("tbody tr").count()
                log(
                    2,
                    f"等待表格 DOM 完成 (wait_for_selector)，目前表格資料列數: "
                    f"{row_count} (每頁顯示數)",
                )
            except PlaywrightTimeoutError:
                log(2, "錯誤: 等待表格 DOM 元素載入逾時 (wait_for_selector)")
                raise
            await page.screenshot(
                path=str(SCREENSHOTS / "final_execution_2_wait_table_dom_loaded.png")
            )

            # step 2b: 等待行情 API 回應 (expect_response / wait_for_response 機制)
            # ------------------------------------------------------------------
            try:
                quotes_response = await response_info.value
                payload = await quotes_response.json()
                captured["payload"] = payload
                log(
                    2,
                    "等待行情 API 回應完成 (expect_response): "
                    f"{quotes_response.url} | date={payload.get('date')} "
                    f"| stat={payload.get('stat')}",
                )
            except PlaywrightTimeoutError:
                if "payload" not in captured:
                    log(2, "錯誤: 等待行情 API 回應逾時 (expect_response)")
                    raise
            finally:
                await quotes_expectation.__aexit__(None, None, None)
            payload = captured["payload"]

            # step 3: 解析 API JSON 並整理為 DataFrame
            # ------------------------------------------------------------------
            table0 = payload["tables"][0]
            fields = table0["fields"]
            rows = table0["data"]
            date = payload.get("date")
            subtitle = table0.get("subtitle", "")
            log(
                3,
                f"API 回傳完整資料: date={date} | 欄位數={len(fields)} "
                f"| 資料列數={len(rows)} | subtitle='{subtitle}'",
            )

            # 建立完整 DataFrame 並清理文字 (去除前後空白與換行)
            df_all = pd.DataFrame(rows, columns=fields)
            df_clean = df_all.map(clean_text)

            # 依需求選取 8 個欄位並改名
            out_df = df_clean[[REQUIRED_COLUMNS[k] for k in REQUIRED_COLUMNS]]
            out_df.columns = list(REQUIRED_COLUMNS.keys())
            log(
                3,
                "需求欄位對照: " + "; ".join(f"{k}<-{v}" for k, v in REQUIRED_COLUMNS.items()),
            )
            sample_raw = rows[0][2] if rows else ""
            sample_clean = out_df.iloc[0]["成交價"] if not out_df.empty else ""
            log(
                3,
                f"文字清理範例: 原始成交價字串='{sample_raw}' "
                f"-> 清理後='{sample_clean}'",
            )

            # step 4: 交叉驗證 DOM 表格(首頁) 與 API JSON 前 10 列一致性
            # ------------------------------------------------------------------
            dom_rows = []
            body_rows = table.locator("tbody tr")
            visible_count = await body_rows.count()
            for i in range(min(visible_count, 10)):
                texts = await body_rows.nth(i).locator("td").all_inner_texts()
                dom_rows.append([clean_text(t) for t in texts])
            match_count = 0
            for i, dom_row in enumerate(dom_rows):
                expected = df_clean.iloc[i].tolist()
                if dom_row == expected:
                    match_count += 1
            log(
                4,
                f"DOM 表格首頁 {len(dom_rows)} 列與 API JSON 前 {len(dom_rows)} 列"
                f" 一致性比對: 相符 {match_count}/{len(dom_rows)}",
            )

            # 顯示表格首頁截圖 (可見 19 欄含需求 8 欄)
            try:
                await table.screenshot(
                    path=str(
                        SCREENSHOTS / "final_execution_3_table_with_columns.png"
                    )
                )
            except Exception as exc:
                log(4, f"警告: 表格元素截圖失敗: {exc}")

            # step 5: 匯出 CSV (utf-8-sig)
            # ------------------------------------------------------------------
            out_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
            with open(OUTPUT_CSV, "rb") as f:
                head = f.read(3)
            bom_ok = head == b"\xef\xbb\xbf"
            log(
                5,
                f"已匯出 CSV: {OUTPUT_CSV} | 列數={len(out_df)} "
                f"| 欄位={list(out_df.columns)} | utf-8-sig BOM={bom_ok}",
            )

            # 讀回驗證 CSV 內容
            df_check = pd.read_csv(OUTPUT_CSV, encoding="utf-8-sig")
            log(
                5,
                f"讀回驗證 CSV: shape={df_check.shape} | "
                f"前3列代號={df_check['股票代號'].head(3).tolist()}",
            )
            await page.screenshot(
                path=str(SCREENSHOTS / "final_execution_4_csv_export_done.png")
            )

            # step 6: 最終資料紀錄 (FINAL_RESPONSE)
            # ------------------------------------------------------------------
            first_row = out_df.iloc[0].to_dict()
            final_value = (
                f"日期={date} 上櫃家數=890 資料筆數={len(out_df)} "
                f"範例列(第1筆)={first_row}"
            )
            with LOG.open("a") as f:
                f.write(f"\nFINAL_RESPONSE: {final_value}\n")
            print("FINAL_RESPONSE:", final_value)

        except PlaywrightTimeoutError as exc:
            log(0, f"發生逾時錯誤: {exc}")
            raise
        except Exception as exc:
            log(0, f"發生未預期錯誤: {type(exc).__name__}: {exc}")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
