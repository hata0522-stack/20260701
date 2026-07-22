import gradio as gr
from playwright.sync_api import sync_playwright, Playwright, Browser, Page, TimeoutError as PwTimeout
import tempfile
import os

WIKI_URL = "https://zh.wikipedia.org"


def crawl_wiki(keyword: str) -> tuple[str, str, str | None]:
    """爬取維基百科搜尋頁面，查詢關鍵字並顯示摘要"""
    title = ""
    summary = ""
    screenshot_path = None

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch()
        try:
            page: Page = browser.new_page()
            page.goto(WIKI_URL)
            page.get_by_role("searchbox").first.fill(keyword)

            # 截圖
            tmp_dir = tempfile.mkdtemp()
            screenshot_path = os.path.join(tmp_dir, "screenshot.png")
            page.screenshot(path=screenshot_path)

            page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle", timeout=30000)

            title = page.locator("#firstHeading").inner_text()
            content = page.locator("#mw-content-text p").first.inner_text()
            summary = content[:300]

        except PwTimeout as e:
            title = "操作逾時"
            summary = str(e)
        except Exception as e:
            title = "發生錯誤"
            summary = str(e)
        finally:
            browser.close()

    return title, summary, screenshot_path


def search_wiki(keyword: str):
    if not keyword.strip():
        return "請輸入關鍵字", "", None

    title, summary, screenshot_path = crawl_wiki(keyword)
    return title, summary, screenshot_path


# 建立 Gradio 介面
custom_theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="gray",
)

with gr.Blocks(
    theme=custom_theme,
    title="維基百科搜尋器",
    css="""
    .gradio-container { max-width: 800px !important; margin: auto !important; }
    #title { text-align: center; margin-bottom: 0.5em; }
    #search-btn { height: 45px; font-size: 16px; }
    """,
) as demo:
    gr.Markdown(
        "# 維基百科搜尋器",
        elem_id="title",
    )
    gr.Markdown("輸入關鍵字，自動搜尋中文維基百科並顯示摘要與頁面截圖。")

    with gr.Row():
        keyword_input = gr.Textbox(
            label="搜尋關鍵字",
            placeholder="請輸入關鍵字，例如：臺灣",
            scale=4,
        )
        search_btn = gr.Button(
            "搜尋",
            variant="primary",
            elem_id="search-btn",
            scale=1,
        )

    with gr.Group():
        title_output = gr.Textbox(label="搜尋主題", interactive=False)
        summary_output = gr.Textbox(label="摘要內容", lines=5, interactive=False)

    with gr.Group():
        screenshot_output = gr.Image(label="頁面截圖", type="filepath")

    search_btn.click(
        fn=search_wiki,
        inputs=keyword_input,
        outputs=[title_output, summary_output, screenshot_output],
    )

    keyword_input.submit(
        fn=search_wiki,
        inputs=keyword_input,
        outputs=[title_output, summary_output, screenshot_output],
    )

if __name__ == "__main__":
    demo.launch()
