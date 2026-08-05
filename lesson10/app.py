"""線上表單自動化助理 - Gradio UI 介面"""
import gradio as gr
from pathlib import Path
from typing import Any

from core import execute_automation, TARGET_URL


# 自訂 CSS
CUSTOM_CSS = """
/* 品牌標題 */
.brand-header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 20px;
}
.brand-header h1 {
    margin: 0;
    font-size: 24px;
}
.brand-header p {
    margin: 5px 0 0 0;
    opacity: 0.9;
    font-size: 14px;
}

/* 步驟指示器 */
.steps-indicator {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 15px 0;
    flex-wrap: wrap;
}
.step-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    background: #e0e0e0;
    color: #666;
}
.step-badge.active {
    background: #4caf50;
    color: white;
}
.step-badge.pending {
    background: #ff9800;
    color: white;
}

/* 結果區域 */
.result-box {
    padding: 15px;
    border-radius: 8px;
    margin: 10px 0;
}
.result-success {
    background: #e8f5e9;
    border-left: 4px solid #4caf50;
}
.result-error {
    background: #ffebee;
    border-left: 4px solid #f44336;
}

/* 截圖預覽 */
.screenshot-preview {
    max-width: 100%;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 表單容器 */
.form-container {
    padding: 10px;
}
"""


def get_demo_data() -> dict[str, Any]:
    """返回示範資料"""
    return {
        "name": "李大華",
        "password": "demo_password",
        "notes": "這是示範資料，用於測試表單自動化功能。",
        "dropdown_value": "3",
        "checkbox_checked": True,
        "radio_checked": True,
        "headless": True,
        "timeout_ms": 30000,
    }


def clear_form() -> dict[str, Any]:
    """清除所有表單欄位"""
    return {
        "name": "",
        "password": "",
        "notes": "",
        "dropdown_value": "1",
        "checkbox_checked": False,
        "radio_checked": False,
        "headless": True,
        "timeout_ms": 30000,
    }


def run_automation(
    name: str,
    password: str,
    notes: str,
    dropdown_value: str,
    checkbox_checked: bool,
    radio_checked: bool,
    headless: bool,
    timeout_ms: int,
) -> tuple[str, str, str, str, str]:
    """
    執行自動化並返回結果。

    回傳:
        (steps_html, result_html, screenshot_path, final_url, status_message)
    """
    # 驗證輸入
    if not name.strip():
        name = "王小明"
    if not password.strip():
        password = "practice-only"
    if not notes.strip():
        notes = "這是 Playwright 表單自動化練習。"

    # 確保 timeout 合理
    timeout_ms = max(5000, min(timeout_ms, 120000))

    # 執行自動化
    result = execute_automation(
        name=name.strip(),
        password=password.strip(),
        notes=notes.strip(),
        dropdown_value=dropdown_value,
        checkbox_checked=checkbox_checked,
        radio_checked=radio_checked,
        headless=headless,
        timeout_ms=timeout_ms,
    )

    # 建立步驟指示 HTML
    steps_html = '<div class="steps-indicator">'
    for i, step in enumerate(result["steps"]):
        status = "active" if i == len(result["steps"]) - 1 else "completed"
        steps_html += f'<span class="step-badge {status}">{step}</span>'
    steps_html += "</div>"

    # 建立結果 HTML
    if result["success"]:
        result_html = f'''
        <div class="result-box result-success">
            <h3 style="color: #2e7d32; margin-top: 0;">✅ 執行成功</h3>
            <p><strong>最終網址：</strong>{result["final_url"]}</p>
            <p><strong>驗證訊息：</strong>{result["received_message"]}</p>
            <p><strong>執行時間：</strong>{result["elapsed_ms"]} ms</p>
        </div>
        '''
        status_message = f"✅ 成功！耗時 {result['elapsed_ms']} ms"
    else:
        result_html = f'''
        <div class="result-box result-error">
            <h3 style="color: #c62828; margin-top: 0;">❌ 執行失敗</h3>
            <p><strong>錯誤訊息：</strong>{result["error_message"]}</p>
            <p><strong>執行時間：</strong>{result["elapsed_ms"]} ms</p>
        </div>
        '''
        status_message = f"❌ 失敗：{result['error_message']}"

    # 截圖路徑
    screenshot_path = result.get("screenshot_path", "")
    final_url = result.get("final_url", "")

    return steps_html, result_html, screenshot_path, final_url, status_message


def create_app() -> gr.Blocks:
    """建立 Gradio 應用程式"""
    with gr.Blocks(
        title="線上表單自動化助理",
    ) as app:
        # 品牌標題
        gr.HTML("""
        <div class="brand-header">
            <h1>🤖 線上表單自動化助理</h1>
            <p>使用 Playwright 自動填寫 Selenium 官方測試表單</p>
        </div>
        """)

        with gr.Row():
            # 左側：表單輸入
            with gr.Column(scale=1):
                gr.Markdown("### 📝 表單設定")

                with gr.Group():
                    name_input = gr.Textbox(
                        label="姓名",
                        placeholder="請輸入姓名",
                        value="王小明",
                    )
                    password_input = gr.Textbox(
                        label="練習用密碼",
                        placeholder="請輸入密碼",
                        value="practice-only",
                        type="password",
                    )
                    notes_input = gr.Textbox(
                        label="備註",
                        placeholder="請輸入備註內容",
                        value="這是 Playwright 表單自動化練習。",
                        lines=3,
                    )

                with gr.Group():
                    dropdown_input = gr.Dropdown(
                        label="下拉選項",
                        choices=[
                            ("選項 1", "1"),
                            ("選項 2", "2"),
                            ("選項 3", "3"),
                            ("選項 4", "4"),
                            ("選項 5", "5"),
                        ],
                        value="2",
                    )
                    checkbox_input = gr.Checkbox(
                        label="預設核取方塊",
                        value=True,
                    )
                    radio_input = gr.Radio(
                        label="預設單選按鈕",
                        choices=["選取"],
                        value="選取",
                    )

                with gr.Group():
                    headless_input = gr.Checkbox(
                        label="無頭模式（不顯示瀏覽器視窗）",
                        value=True,
                    )
                    timeout_input = gr.Slider(
                        label="超時時間（毫秒）",
                        minimum=5000,
                        maximum=120000,
                        value=30000,
                        step=1000,
                    )

                with gr.Row():
                    load_demo_btn = gr.Button(
                        "📋 載入示範資料",
                        variant="secondary",
                        size="sm",
                    )
                    clear_btn = gr.Button(
                        "🗑️ 清除",
                        variant="secondary",
                        size="sm",
                    )

                execute_btn = gr.Button(
                    "🚀 執行自動化",
                    variant="primary",
                    size="lg",
                )

            # 右側：執行結果
            with gr.Column(scale=1):
                gr.Markdown("### 📊 執行結果")

                steps_output = gr.HTML(
                    label="執行步驟",
                    value='<div class="steps-indicator"><span class="step-badge">等待執行...</span></div>',
                )

                result_output = gr.HTML(
                    label="執行結果",
                    value='<div class="result-box"><p>執行結果將顯示在這裡...</p></div>',
                )

                with gr.Group():
                    screenshot_output = gr.Image(
                        label="截圖預覽",
                        height=300,
                    )
                    screenshot_file = gr.File(
                        label="下載截圖",
                        visible=False,
                    )

                final_url_output = gr.Textbox(
                    label="最終網址",
                    interactive=False,
                )

                status_output = gr.Textbox(
                    label="狀態訊息",
                    interactive=False,
                )

        # 事件處理
        def update_screenshot_visibility(screenshot_path: str) -> dict:
            """更新截圖下載連結的可見性"""
            return {
                "visible": bool(screenshot_path and Path(screenshot_path).exists()),
            }

        def prepare_screenshot_download(screenshot_path: str) -> str | None:
            """準備截圖下載"""
            if screenshot_path and Path(screenshot_path).exists():
                return screenshot_path
            return None

        # 載入示範資料
        load_demo_btn.click(
            fn=get_demo_data,
            outputs=[
                name_input,
                password_input,
                notes_input,
                dropdown_input,
                checkbox_input,
                radio_input,
                headless_input,
                timeout_input,
            ],
        )

        # 清除表單
        clear_btn.click(
            fn=clear_form,
            outputs=[
                name_input,
                password_input,
                notes_input,
                dropdown_input,
                checkbox_input,
                radio_input,
                headless_input,
                timeout_input,
            ],
        )

        # 執行自動化
        execute_btn.click(
            fn=run_automation,
            inputs=[
                name_input,
                password_input,
                notes_input,
                dropdown_input,
                checkbox_input,
                radio_input,
                headless_input,
                timeout_input,
            ],
            outputs=[
                steps_output,
                result_output,
                screenshot_output,
                final_url_output,
                status_output,
            ],
            api_name="execute",
        )

        # 更新截圖下載連結
        screenshot_output.change(
            fn=update_screenshot_visibility,
            inputs=[screenshot_output],
            outputs=[screenshot_file],
        )

        screenshot_output.change(
            fn=prepare_screenshot_download,
            inputs=[screenshot_output],
            outputs=[screenshot_file],
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
    )
