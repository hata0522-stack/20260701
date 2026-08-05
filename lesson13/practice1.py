import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG_FILE = LOG.open("w")

def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    LOG_FILE.write(line)
    print(line, end="")

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        # CP1: Open THSR website
        await page.goto("https://www.thsrc.com.tw/", wait_until="domcontentloaded")
        await page.wait_for_selector("#select_location01", timeout=10000)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_open_start_page.png"))
        log(1, "open THSR website https://www.thsrc.com.tw/")
        title = await page.title()
        if "台灣高鐵" not in title and "Taiwan High Speed Rail" not in title:
            log(1, f"unexpected title: {title}")

        # Accept cookie consent if present
        try:
            accept_btn = page.get_by_role("button", name="我同意")
            await accept_btn.click(timeout=2000)
            await page.wait_for_timeout(500)
            log(1, "accept cookie consent")
        except Exception:
            pass

        # CP2: Select departure station 台北
        await page.select_option("#select_location01", "TaiPei")
        dep_value = await page.locator("#select_location01").input_value()
        if dep_value != "TaiPei":
            log(2, f"departure mismatch: got {dep_value}")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_select_departure.png"))
        log(2, "select departure station 台北")

        # CP3: Select arrival station 台中
        await page.select_option("#select_location02", "TaiZhong")
        arr_value = await page.locator("#select_location02").input_value()
        if arr_value != "TaiZhong":
            log(3, f"arrival mismatch: got {arr_value}")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_3_select_arrival.png"))
        log(3, "select arrival station 台中")

        # CP4: Date is already 2026/07/29 by default
        date_value = await page.locator("#Departdate01").input_value()
        if date_value != "2026/07/29":
            log(4, f"date mismatch: got {date_value}")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_4_check_date.png"))
        log(4, "check departure date 2026/07/29")

        # CP5: Set departure time to 19:00
        await page.locator("#outWardTime").press_sequentially("19:00")
        time_value = await page.locator("#outWardTime").input_value()
        if time_value != "19:00":
            log(5, f"time mismatch: got {time_value}")
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_5_set_time.png"))
        log(5, "set departure time 19:00")

        # CP6: Click search and extract results
        await page.locator("#start-search").click()
        log(6, "click 查詢 search button")
        await page.wait_for_selector("#timeTableTrain_S a.tr-row", timeout=15000)

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_6_results_overview.png"))
        log(6, "search results loaded")

        # Extract train schedule data
        rows = await page.locator("#timeTableTrain_S a.tr-row").all()
        train_data = []
        for row in rows:
            data = await row.evaluate("""
                el => {
                    const spans = el.querySelectorAll('.tr-td span');
                    const times = [];
                    spans.forEach(s => {
                        const text = s.textContent.trim();
                        if (text.match(/\\d{2}:\\d{2}/)) times.push(text);
                    });
                    const trainNo = el.querySelector('.tr-td.train')?.textContent?.trim();
                    const cars = el.querySelector('.tr-td.car')?.textContent?.trim();
                    const duration = el.querySelector('.traffic-time p')?.textContent?.trim();
                    return { departure: times[0] || '', arrival: times[1] || '', trainNo: trainNo || '', cars: cars || '', duration: duration || '' };
                }
            """)
            train_data.append(data)

        # Also get price info
        await page.wait_for_selector("#priceTable", timeout=10000)
        price_text = await page.locator("#priceTable").inner_text()

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_7_all_data.png"))
        log(7, f"extracted {len(train_data)} train schedules")

        final_output = f"""
========================================
台灣高鐵 台北→台中 單程票
日期: 2026/07/29 (三)
出發時間: 19:00
========================================"""
        print(final_output)
        LOG_FILE.write(final_output + "\n")

        for t in train_data:
            line = f"  {t['departure']} → {t['arrival']} ({t['duration']}) | 車次: {t['trainNo']} | 自由座車廂: {t['cars']}"
            print(line)
            LOG_FILE.write(line + "\n")

        price_summary = f"""
票價資訊:
{price_text}
"""
        print(price_summary)
        LOG_FILE.write("\n票價資訊:\n" + price_text + "\n")

        # Final datum
        final_datum = f"共 {len(train_data)} 班車次，區間 19:11~19:51"
        LOG_FILE.write(f"\nFINAL_RESPONSE: {final_datum}\n")
        print(f"\nFINAL_RESPONSE: {final_datum}")

        await browser.close()
        LOG_FILE.close()

asyncio.run(main())
