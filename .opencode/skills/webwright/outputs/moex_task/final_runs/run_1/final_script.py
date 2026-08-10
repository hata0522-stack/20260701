import asyncio
import os
import httpx
from pathlib import Path

from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    print(line, end="")

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        BASE_URL = "https://wwwq.moex.gov.tw/exam/wFrmExamQandASearch.aspx?y=2025&e=114100"

        # CP1: Open the page
        await page.goto(BASE_URL, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_page_loaded.png"))
        log(1, f"open page {BASE_URL}")

        title = await page.title()
        page_url = page.url
        print(f"Title: {title}")
        print(f"URL: {page_url}")
        with LOG.open("a") as f:
            f.write(f"Title: {title}\nURL: {page_url}\n")

        # Verify exam year and name
        year_select = page.locator("select[name$='ddlExamYear']").first
        selected_year = await year_select.input_value()
        print(f"Selected year: {selected_year}")

        exam_select = page.locator("select[name$='ddlExamCode']")
        selected_exam_value = await exam_select.input_value()
        selected_exam_text = await exam_select.locator("option:checked").inner_text()
        print(f"Selected exam: {selected_exam_value} - {selected_exam_text}")
        with LOG.open("a") as f:
            f.write(f"Selected exam: {selected_exam_value} - {selected_exam_text}\n")

        # CP2: Locate "生理學與生物化學" row
        subject_name = "生理學與生物化學"
        subject_checkbox = page.get_by_role("checkbox", name=subject_name).first
        await subject_checkbox.scroll_into_view_if_needed()
        await asyncio.sleep(0.5)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_subject_visible.png"))
        log(2, f"locate subject row: {subject_name}")

        is_visible = await subject_checkbox.is_visible()
        print(f"Subject checkbox visible: {is_visible}")
        with LOG.open("a") as f:
            f.write(f"Subject '{subject_name}' checkbox visible: {is_visible}\n")

        # Find the 試題 and 答案 links for subject code s=0103 (生理學與生物化學)
        q_links = await page.locator("a").evaluate_all(
            "els => els.map(e => ({text: e.innerText.trim(), href: e.getAttribute('href')}))"
            ".filter(l => l.href && l.href.includes('0103') && l.text === '試題')"
        )
        a_links = await page.locator("a").evaluate_all(
            "els => els.map(e => ({text: e.innerText.trim(), href: e.getAttribute('href')}))"
            ".filter(l => l.href && l.href.includes('0103') && l.text === '答案')"
        )

        q_href = q_links[0]['href'] if q_links else ""
        a_href = a_links[0]['href'] if a_links else ""
        print(f"Question link: {q_href}")
        print(f"Answer link: {a_href}")
        with LOG.open("a") as f:
            f.write(f"Question href: {q_href}\nAnswer href: {a_href}\n")

        # CP3 & CP4: Download PDFs
        base_domain = "https://wwwq.moex.gov.tw/exam/"
        q_url = base_domain + q_href if q_href.startswith("wHand") else q_href
        a_url = base_domain + a_href if a_href.startswith("wHand") else a_href

        download_dir = RUN_DIR / "downloads"
        download_dir.mkdir(exist_ok=True)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            log(3, f"download question PDF from {q_url}")
            q_resp = await client.get(q_url)
            q_filename = q_resp.headers.get("content-disposition", "")
            if "filename=" in q_filename:
                q_filename = q_filename.split("filename=")[-1].strip('"')
            else:
                q_filename = "exam_question.pdf"
            q_path = download_dir / q_filename
            q_path.write_bytes(q_resp.content)
            print(f"Question PDF saved: {q_path} ({len(q_resp.content)} bytes)")
            with LOG.open("a") as f:
                f.write(f"Question PDF: {q_filename}, {len(q_resp.content)} bytes\n")

            log(4, f"download answer PDF from {a_url}")
            a_resp = await client.get(a_url)
            a_filename = a_resp.headers.get("content-disposition", "")
            if "filename=" in a_filename:
                a_filename = a_filename.split("filename=")[-1].strip('"')
            else:
                a_filename = "exam_answer.pdf"
            a_path = download_dir / a_filename
            a_path.write_bytes(a_resp.content)
            print(f"Answer PDF saved: {a_path} ({len(a_resp.content)} bytes)")
            with LOG.open("a") as f:
                f.write(f"Answer PDF: {a_filename}, {len(a_resp.content)} bytes\n")

        # CP5: Verify PDFs
        q_valid = len(q_resp.content) > 1000 and q_resp.content[:4] == b'%PDF'
        a_valid = len(a_resp.content) > 1000 and a_resp.content[:4] == b'%PDF'

        final_msg = (
            f"FINAL_RESPONSE: 已下載「生理學與生物化學」科目資料\n"
            f"  試題: {q_filename} ({len(q_resp.content)} bytes) - {'有效' if q_valid else '無效'}\n"
            f"  答案: {a_filename} ({len(a_resp.content)} bytes) - {'有效' if a_valid else '無效'}\n"
        )
        print(final_msg)
        with LOG.open("a") as f:
            f.write(f"\n{final_msg}")

        await browser.close()

asyncio.run(main())
