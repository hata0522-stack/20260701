import re
import gradio as gr
from playwright.sync_api import sync_playwright, Playwright, Browser, Page


def launch_browser(p: Playwright) -> Browser:
    """啟動 Chromium 瀏覽器實例"""
    return p.chromium.launch()


def search_wikipedia(page: Page, keyword: str) -> None:
    """在維基百科搜尋指定關鍵字"""
    page.goto("https://zh.wikipedia.org")
    search_input = page.locator("#searchInput")
    search_input.fill(keyword)
    search_input.press("Enter")
    page.wait_for_selector("#firstHeading")


def get_search_result(page: Page) -> dict[str, str]:
    """擷取搜尋結果頁面的標題與摘要"""
    heading: str = page.locator("#firstHeading").inner_text()
    paragraphs = page.locator("#mw-content-text p").filter(has_text=re.compile(r"\S"))
    content: str = paragraphs.first.inner_text() if paragraphs.count() > 0 else ""
    return {"heading": heading, "content": content[:500]}


def crawl_wikipedia(keyword: str) -> tuple[str, str, str | None]:
    """爬蟲主流程，回傳 (標題, 摘要, 截圖路徑)"""
    if not keyword.strip():
        return "⚠️ 請輸入搜尋關鍵字", "", None

    screenshot_path = None
    with sync_playwright() as p:
        browser: Browser = launch_browser(p)
        try:
            page: Page = browser.new_page()
            search_wikipedia(page, keyword)

            screenshot_path = "wikipedia_screenshot.png"
            page.screenshot(path=screenshot_path, full_page=False)

            result: dict[str, str] = get_search_result(page)
            return result["heading"], result["content"], screenshot_path
        except Exception as e:
            return f"❌ 爬蟲執行失敗: {e}", "", None
        finally:
            browser.close()


custom_theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Noto Sans TC"),
)

with gr.Blocks(theme=custom_theme, title="維基百科搜尋器") as demo:
    gr.Markdown(
        """
        # 🌐 維基百科搜尋器
        輸入關鍵字，自動搜尋中文維基百科並擷取摘要內容與頁面截圖。
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            keyword_input = gr.Textbox(
                label="搜尋關鍵字",
                placeholder="例如：臺灣、Python、人工智慧",
                lines=1,
            )
            search_btn = gr.Button("🔍 開始搜尋", variant="primary", size="lg")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.TabItem("📄 搜尋結果"):
                    heading_output = gr.Textbox(label="標題", interactive=False)
                    content_output = gr.Textbox(
                        label="摘要", lines=6, interactive=False
                    )
                with gr.TabItem("🖼️ 頁面截圖"):
                    screenshot_output = gr.Image(label="維基百科截圖", type="filepath")

    search_btn.click(
        fn=crawl_wikipedia,
        inputs=keyword_input,
        outputs=[heading_output, content_output, screenshot_output],
    )

    keyword_input.submit(
        fn=crawl_wikipedia,
        inputs=keyword_input,
        outputs=[heading_output, content_output, screenshot_output],
    )

    gr.Examples(
        examples=["臺灣", "Python", "人工智慧", "宇宙", "紅樓夢"],
        inputs=keyword_input,
        label="點選快速搜尋",
    )

if __name__ == "__main__":
    demo.launch()
