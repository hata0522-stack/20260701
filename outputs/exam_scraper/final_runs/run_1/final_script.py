import asyncio
import os
import re
import subprocess
from pathlib import Path

import httpx
from playwright.async_api import async_playwright

RUN_DIR = Path(__file__).parent
SCREENSHOTS = RUN_DIR / "screenshots"
SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "final_script_log.txt"
LOG.write_text("")

BASE_URL = "https://wwwq.moex.gov.tw/exam"
EXAM_URL = f"{BASE_URL}/wFrmExamQandASearch.aspx?y=2025&e=114100"
EXAM_CODE = "114100"
CATEGORY = "101"
SUBJECT = "0101"
SUBJECT_NAME = "膳食療養學"
CATEGORY_NAME = "營養師"

def log(step: int, msg: str) -> None:
    line = f"step {step} action: {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    print(line, end="")

async def download_pdf(client: httpx.AsyncClient, url: str, path: Path) -> None:
    resp = await client.get(url, follow_redirects=True, timeout=30)
    resp.raise_for_status()
    path.write_bytes(resp.content)

def extract_text_from_pdf(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

def parse_answers(answer_text: str) -> dict[int, str]:
    answers: dict[int, str] = {}
    lines = answer_text.split("\n")
    blocks = re.split(r"題號\s*", answer_text)
    for block in blocks[1:]:
        part_lines = block.split("\n")
        q_lines = []
        a_lines = []
        mode = "q"
        for line in part_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("答案"):
                mode = "a"
                stripped = stripped[2:].strip()
                if stripped:
                    a_lines.append(stripped)
                continue
            if stripped.startswith("備") or stripped.startswith("題號"):
                break
            if mode == "q":
                q_lines.append(stripped)
            else:
                a_lines.append(stripped)
        q_nums = []
        for ql in q_lines:
            q_nums.extend(re.findall(r"\d+", ql))
        a_vals = []
        for al in a_lines:
            a_vals.extend(re.findall(r"[Ａ-ＤA-D]", al))
        for q_str, a_str in zip(q_nums, a_vals):
            q_int = int(q_str)
            a_map = {"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D"}
            if a_str in a_map:
                answers[q_int] = a_map[a_str]
            else:
                answers[q_int] = a_str
    return answers

def combine_to_markdown(question_text: str, answer_text: str) -> str:
    answers = parse_answers(answer_text)
    print(f"Parsed {len(answers)} answers: {answers}")
    lines = question_text.split("\n")
    header_lines = []
    essay_lines = []
    choice_lines = []
    mode = "header"
    for line in lines:
        stripped = line.strip()
        if "一、申論題" in stripped or "壹、申論題" in stripped:
            mode = "essay"
            continue
        if "二、測驗題" in stripped or "貳、測驗題" in stripped:
            mode = "choice"
            continue
        if mode == "header":
            header_lines.append(line)
        elif mode == "essay":
            essay_lines.append(line)
        elif mode == "choice":
            choice_lines.append(line)
    header_text = "\n".join(header_lines)
    essay_text = "\n".join(essay_lines)
    choice_text = "\n".join(choice_lines)

    essay_questions = split_essay_questions(essay_text)
    choice_questions = split_choice_questions(choice_text)

    md = "# 考畢試題與答案整合\n\n"
    md += "---\n\n"
    md += "## 考試資訊\n\n"
    for ml in header_lines:
        ml_stripped = ml.strip()
        if ml_stripped:
            md += f"{ml_stripped}\n\n"
    md += "---\n\n"
    md += "## 申論題\n\n"
    if not essay_questions:
        md += "*本試卷無申論題*\n\n"
    else:
        for title, body in essay_questions:
            md += f"### {title}\n\n"
            md += f"{body}\n\n"
            md += "> **⚠️ 申論題無標準答案，請自行參考相關資料**\n\n"
    md += "---\n\n"
    md += "## 測驗題\n\n"
    for qn, question_body in choice_questions:
        md += f"### 第 {qn} 題\n\n"
        md += f"{question_body}\n\n"
        ans = answers.get(qn)
        if ans:
            md += f"**正確答案：{ans}**\n\n"
        else:
            md += "**正確答案：無**\n\n"
        md += "---\n\n"
    return md

def split_essay_questions(text: str) -> list[tuple[str, str]]:
    questions = []
    lines = text.split("\n")
    current_title = ""
    current_body: list[str] = []
    in_q = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_q:
                current_body.append(line)
            continue
        if re.match(r"^\d+\.\s?", stripped):
            if in_q and current_title:
                questions.append((current_title, "\n".join(current_body).strip()))
            current_body = [line]
            current_title = stripped
            in_q = True
        elif in_q:
            current_body.append(line)
    if in_q and current_title:
        questions.append((current_title, "\n".join(current_body).strip()))
    return questions

def split_choice_questions(text: str) -> list[tuple[int, str]]:
    questions = []
    lines = text.split("\n")
    current_q_num = 0
    current_body: list[str] = []
    in_q = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_q:
                current_body.append(line)
            continue
        m = re.match(r"^(\d+)\.\s?", stripped)
        if m:
            if in_q and current_q_num > 0:
                questions.append((current_q_num, "\n".join(current_body).strip()))
            current_q_num = int(m.group(1))
            current_body = [stripped]
            in_q = True
        elif in_q:
            current_body.append(line)
    if in_q and current_q_num > 0:
        questions.append((current_q_num, "\n".join(current_body).strip()))
    print(f"Parsed {len(questions)} choice questions")
    return questions

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1800})
        page = await context.new_page()

        await page.goto(EXAM_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        await page.screenshot(path=str(SCREENSHOTS / "final_execution_1_open_exam_page.png"))
        log(1, "開啟考試頁面，確認 114100 考試載入")

        title = await page.title()
        print(f"Page title: {title}")

        subject_visible = await page.get_by_text("膳食療養學", exact=False).count()
        print(f"膳食療養學 出現次數: {subject_visible}")

        await page.screenshot(path=str(SCREENSHOTS / "final_execution_2_subject_list.png"))
        log(2, "確認科目列表中包含膳食療養學")

        await browser.close()

    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        question_url = f"{BASE_URL}/wHandExamQandA_File.ashx?t=Q&code={EXAM_CODE}&c={CATEGORY}&s={SUBJECT}&q=1"
        answer_url = f"{BASE_URL}/wHandExamQandA_File.ashx?t=S&code={EXAM_CODE}&c={CATEGORY}&s={SUBJECT}&q=1"

        pdf_dir = RUN_DIR / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        q_pdf = pdf_dir / f"{SUBJECT_NAME}_試題.pdf"
        a_pdf = pdf_dir / f"{SUBJECT_NAME}_答案.pdf"

        await download_pdf(client, question_url, q_pdf)
        log(3, f"下載試題 PDF ({q_pdf.stat().st_size} bytes)")

        await download_pdf(client, answer_url, a_pdf)
        log(4, f"下載答案 PDF ({a_pdf.stat().st_size} bytes)")

    q_text = extract_text_from_pdf(q_pdf)
    a_text = extract_text_from_pdf(a_pdf)
    log(5, f"從 PDF 萃取文字，試題 {len(q_text)} 字元，答案 {len(a_text)} 字元")

    markdown_content = combine_to_markdown(q_text, a_text)
    output_md = RUN_DIR / f"{SUBJECT_NAME}_試題與答案整合.md"
    output_md.write_text(markdown_content, encoding="utf-8")
    log(6, f"合併試題與答案為 markdown 檔案 ({output_md})")

    total_questions = markdown_content.count("### 第")
    log(7, f"Markdown 檔案包含 {total_questions} 題測驗題")

    with LOG.open("a") as f:
        f.write(f"\nFINAL_RESPONSE: 成功下載 {SUBJECT_NAME} 試題與答案，"
                f"整合為 {output_md.name}，共 {total_questions} 題\n")

    print(f"\n=== 完成 ===")
    print(f"Markdown 檔案: {output_md}")
    print(f"共 {total_questions} 題測驗題")

asyncio.run(main())
