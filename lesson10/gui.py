"""繁體中文網站健康檢查桌面 App。"""

from __future__ import annotations

import os
import platform
import queue
import subprocess
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from practice5 import (
    OUTPUT_DIR,
    CheckResult,
    check_website_core,
    validate_timeout,
    validate_url,
)


COLORS = {
    "navy": "#0B1930",
    "navy_light": "#122541",
    "card": "#162B49",
    "card_alt": "#10213B",
    "teal": "#20C9B4",
    "teal_hover": "#35DAC4",
    "text": "#F3F7FB",
    "muted": "#9DB0C8",
    "border": "#294563",
    "success": "#34D399",
    "warning": "#FBBF24",
    "danger": "#FB7185",
}


class WebsiteHealthApp:
    """網站健康檢查主視窗。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.result_queue: queue.Queue[CheckResult] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self._closing = False

        self.url_var = tk.StringVar(value="https://example.com/")
        self.browser_var = tk.StringVar(value="chromium")
        self.headless_var = tk.BooleanVar(value=True)
        self.timeout_var = tk.StringVar(value="30000")
        self.http_var = tk.StringVar(value="—")
        self.time_var = tk.StringVar(value="—")
        self.title_var = tk.StringVar(value="尚未執行檢查")
        self.heading_var = tk.StringVar(value="—")
        self.final_url_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="等待檢查")

        self._configure_window()
        self._configure_styles()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configure_window(self) -> None:
        self.root.title("網站健康檢查")
        self.root.geometry("1200x760")
        self.root.minsize(1040, 680)
        self.root.configure(bg=COLORS["navy"])

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=COLORS["navy"])
        style.configure("Card.TFrame", background=COLORS["card"])
        style.configure("Inset.TFrame", background=COLORS["card_alt"])
        style.configure(
            "Title.TLabel",
            background=COLORS["navy"],
            foreground=COLORS["text"],
            font=("TkDefaultFont", 22, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["navy"],
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=COLORS["card"],
            foreground=COLORS["text"],
            font=("TkDefaultFont", 13, "bold"),
        )
        style.configure(
            "Field.TLabel",
            background=COLORS["card"],
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 10, "bold"),
        )
        style.configure(
            "Value.TLabel",
            background=COLORS["card"],
            foreground=COLORS["text"],
            font=("TkDefaultFont", 11),
        )
        style.configure(
            "Metric.TLabel",
            background=COLORS["card_alt"],
            foreground=COLORS["text"],
            font=("TkDefaultFont", 17, "bold"),
        )
        style.configure(
            "MetricName.TLabel",
            background=COLORS["card_alt"],
            foreground=COLORS["muted"],
            font=("TkDefaultFont", 9),
        )
        style.configure(
            "App.TEntry",
            fieldbackground=COLORS["card_alt"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            padding=9,
        )
        style.configure(
            "App.TCombobox",
            fieldbackground=COLORS["card_alt"],
            background=COLORS["card_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["teal"],
            bordercolor=COLORS["border"],
            padding=8,
        )
        style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", COLORS["card_alt"])],
            foreground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Primary.TButton",
            background=COLORS["teal"],
            foreground=COLORS["navy"],
            borderwidth=0,
            padding=(18, 11),
            font=("TkDefaultFont", 11, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[
                ("active", COLORS["teal_hover"]),
                ("disabled", COLORS["border"]),
            ],
            foreground=[("disabled", COLORS["muted"])],
        )
        style.configure(
            "Secondary.TButton",
            background=COLORS["navy_light"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(14, 8),
            font=("TkDefaultFont", 10, "bold"),
        )
        style.map("Secondary.TButton", background=[("active", COLORS["border"])])
        style.configure(
            "App.TCheckbutton",
            background=COLORS["card"],
            foreground=COLORS["text"],
            indicatorcolor=COLORS["card_alt"],
            font=("TkDefaultFont", 10),
        )
        style.map(
            "App.TCheckbutton",
            background=[("active", COLORS["card"])],
            indicatorcolor=[("selected", COLORS["teal"])],
        )
        style.configure(
            "App.Horizontal.TProgressbar",
            troughcolor=COLORS["card_alt"],
            background=COLORS["teal"],
            bordercolor=COLORS["card_alt"],
        )

    def _build_ui(self) -> None:
        shell = ttk.Frame(self.root, style="App.TFrame", padding=(24, 12, 24, 12))
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        header = ttk.Frame(shell, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(header, text="網站健康檢查", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="快速檢查 HTTP 狀態、頁面內容與實際畫面",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        content = ttk.Frame(shell, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0, minsize=330)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self._build_controls(content)
        self._build_results(content)
        self._build_log(shell)

    def _build_controls(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=22)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="檢查設定", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 20)
        )
        ttk.Label(card, text="網站 URL", style="Field.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 6)
        )
        self.url_entry = ttk.Entry(card, textvariable=self.url_var, style="App.TEntry")
        self.url_entry.grid(row=2, column=0, sticky="ew", pady=(0, 17))

        ttk.Label(card, text="瀏覽器引擎", style="Field.TLabel").grid(
            row=3, column=0, sticky="w", pady=(0, 6)
        )
        self.browser_combo = ttk.Combobox(
            card,
            textvariable=self.browser_var,
            values=("chromium", "firefox", "webkit"),
            state="readonly",
            style="App.TCombobox",
        )
        self.browser_combo.grid(row=4, column=0, sticky="ew", pady=(0, 17))

        ttk.Label(card, text="Timeout（毫秒）", style="Field.TLabel").grid(
            row=5, column=0, sticky="w", pady=(0, 6)
        )
        self.timeout_entry = ttk.Entry(
            card, textvariable=self.timeout_var, style="App.TEntry"
        )
        self.timeout_entry.grid(row=6, column=0, sticky="ew", pady=(0, 15))

        self.headless_check = ttk.Checkbutton(
            card,
            text="以 headless 模式執行",
            variable=self.headless_var,
            style="App.TCheckbutton",
        )
        self.headless_check.grid(row=7, column=0, sticky="w", pady=(0, 18))

        self.start_button = ttk.Button(
            card,
            text="開始檢查",
            command=self.start_check,
            style="Primary.TButton",
        )
        self.start_button.grid(row=8, column=0, sticky="ew")

        self.progress = ttk.Progressbar(
            card, mode="indeterminate", style="App.Horizontal.TProgressbar"
        )
        self.progress.grid(row=9, column=0, sticky="ew", pady=(16, 0))

        tip = ttk.Label(
            card,
            text="提示：首次使用前請安裝對應的 Playwright 瀏覽器。",
            style="Field.TLabel",
            wraplength=280,
            justify="left",
        )
        tip.grid(row=10, column=0, sticky="sw", pady=(18, 0))
        card.rowconfigure(10, weight=1)

    def _build_results(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=20)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(3, weight=1)

        title_row = ttk.Frame(card, style="Card.TFrame")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 13))
        ttk.Label(title_row, text="檢查結果", style="CardTitle.TLabel").pack(
            side="left"
        )
        self.status_label = tk.Label(
            title_row,
            textvariable=self.status_var,
            bg=COLORS["border"],
            fg=COLORS["text"],
            padx=12,
            pady=5,
            font=("TkDefaultFont", 9, "bold"),
        )
        self.status_label.pack(side="right")

        metrics = ttk.Frame(card, style="Card.TFrame")
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 13))
        metrics.columnconfigure((0, 1), weight=1)
        self._metric_card(metrics, 0, "HTTP 狀態", self.http_var)
        self._metric_card(metrics, 1, "回應時間", self.time_var)

        details = ttk.Frame(card, style="Card.TFrame")
        details.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        details.columnconfigure(1, weight=1)
        self._detail_row(details, 0, "頁面標題", self.title_var)
        self._detail_row(details, 1, "主標題", self.heading_var)
        self._detail_row(details, 2, "最終 URL", self.final_url_var)

        preview_frame = ttk.Frame(card, style="Inset.TFrame", padding=1)
        preview_frame.grid(row=3, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.preview_label = tk.Label(
            preview_frame,
            text="截圖預覽會顯示在這裡",
            bg=COLORS["card_alt"],
            fg=COLORS["muted"],
            font=("TkDefaultFont", 11),
            compound="center",
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew")

    def _metric_card(
        self, parent: ttk.Frame, column: int, name: str, variable: tk.StringVar
    ) -> None:
        frame = ttk.Frame(parent, style="Inset.TFrame", padding=(15, 10))
        frame.grid(
            row=0,
            column=column,
            sticky="ew",
            padx=(0, 6) if column == 0 else (6, 0),
        )
        ttk.Label(frame, text=name, style="MetricName.TLabel").pack(anchor="w")
        ttk.Label(frame, textvariable=variable, style="Metric.TLabel").pack(
            anchor="w", pady=(2, 0)
        )

    def _detail_row(
        self, parent: ttk.Frame, row: int, name: str, variable: tk.StringVar
    ) -> None:
        ttk.Label(parent, text=name, style="Field.TLabel").grid(
            row=row, column=0, sticky="nw", padx=(0, 14), pady=3
        )
        ttk.Label(
            parent,
            textvariable=variable,
            style="Value.TLabel",
            wraplength=620,
            justify="left",
        ).grid(row=row, column=1, sticky="ew", pady=3)

    def _build_log(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 12))
        card.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        card.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(card, style="Card.TFrame")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(toolbar, text="執行日誌", style="CardTitle.TLabel").pack(side="left")
        ttk.Button(
            toolbar,
            text="清除結果",
            command=self.clear_results,
            style="Secondary.TButton",
        ).pack(side="right")
        ttk.Button(
            toolbar,
            text="開啟輸出資料夾",
            command=self.open_output_folder,
            style="Secondary.TButton",
        ).pack(side="right", padx=(0, 8))

        log_frame = ttk.Frame(card, style="Inset.TFrame")
        log_frame.grid(row=1, column=0, sticky="ew")
        log_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(
            log_frame,
            height=4,
            wrap="word",
            bg=COLORS["card_alt"],
            fg=COLORS["muted"],
            insertbackground=COLORS["text"],
            relief="flat",
            padx=10,
            pady=8,
            font=("TkFixedFont", 9),
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="ew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._append_log("系統已就緒，請設定網址後開始檢查。")

    def start_check(self) -> None:
        if self.worker and self.worker.is_alive():
            return

        try:
            url = validate_url(self.url_var.get())
            timeout_ms = validate_timeout(self.timeout_var.get())
        except ValueError as exc:
            self._set_status("輸入錯誤", "danger")
            self._append_log(f"輸入錯誤：{exc}")
            messagebox.showwarning("請檢查輸入", str(exc), parent=self.root)
            return

        browser = self.browser_var.get()
        headless = self.headless_var.get()
        self._set_busy(True)
        self._set_status("檢查中…", "warning")
        self._append_log(
            f"開始檢查 {url}（{browser}、{'headless' if headless else '有介面'}）"
        )

        self.worker = threading.Thread(
            target=self._run_check,
            args=(url, browser, headless, timeout_ms),
            name="website-check-worker",
            daemon=True,
        )
        self.worker.start()
        self.root.after(100, self._poll_result_queue)

    def _run_check(
        self, url: str, browser: str, headless: bool, timeout_ms: int
    ) -> None:
        result = check_website_core(
            url=url,
            browser_name=browser,
            headless=headless,
            timeout_ms=timeout_ms,
        )
        self.result_queue.put(result)

    def _poll_result_queue(self) -> None:
        if self._closing:
            return
        try:
            result = self.result_queue.get_nowait()
        except queue.Empty:
            if self.worker and self.worker.is_alive():
                self.root.after(100, self._poll_result_queue)
            else:
                self._set_busy(False)
            return

        self._set_busy(False)
        self._display_result(result)

    def _display_result(self, result: CheckResult) -> None:
        self.http_var.set(str(result.http_status) if result.http_status is not None else "無回應")
        self.time_var.set(
            f"{result.response_time_ms:.1f} ms" if result.response_time_ms else "—"
        )
        self.title_var.set(result.page_title or "（頁面沒有標題）")
        self.heading_var.set(result.main_heading or "（找不到 h1 主標題）")
        self.final_url_var.set(result.final_url or result.url)

        if not result.success:
            self._set_status("檢查失敗", "danger")
            self._append_log(f"檢查失敗：{result.error_message}")
            messagebox.showerror("檢查失敗", result.error_message, parent=self.root)
            return

        status = result.http_status
        if status is None or status >= 500:
            self._set_status("失敗", "danger")
        elif status >= 400:
            self._set_status("警告", "warning")
        else:
            self._set_status("成功", "success")

        self._append_log(
            f"完成：HTTP {status if status is not None else '無回應'}，"
            f"回應時間 {result.response_time_ms:.1f} ms"
        )
        if result.screenshot_path:
            self._append_log(f"截圖已儲存：{result.screenshot_path}")
            self._load_preview(Path(result.screenshot_path))

    def _load_preview(self, path: Path) -> None:
        try:
            with Image.open(path) as source:
                image = ImageOps.contain(source.convert("RGB"), (760, 250))
            self.preview_image = ImageTk.PhotoImage(image)
            self.preview_label.configure(image=self.preview_image, text="")
        except (OSError, ValueError) as exc:
            self.preview_image = None
            self.preview_label.configure(image="", text="無法載入截圖預覽")
            self._append_log(f"截圖預覽載入失敗：{exc}")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.start_button.configure(state=state)
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()

    def _set_status(self, text: str, kind: str) -> None:
        background = {
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "danger": COLORS["danger"],
        }.get(kind, COLORS["border"])
        foreground = COLORS["navy"] if kind in {"success", "warning"} else COLORS["text"]
        self.status_var.set(text)
        self.status_label.configure(bg=background, fg=foreground)

    def _append_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_results(self) -> None:
        self.http_var.set("—")
        self.time_var.set("—")
        self.title_var.set("尚未執行檢查")
        self.heading_var.set("—")
        self.final_url_var.set("—")
        self.preview_image = None
        self.preview_label.configure(image="", text="截圖預覽會顯示在這裡")
        self._set_status("等待檢查", "neutral")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self._append_log("畫面結果已清除；已儲存的截圖不受影響。")

    def open_output_folder(self) -> None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(OUTPUT_DIR)  # type: ignore[attr-defined]
            elif system == "Darwin":
                subprocess.Popen(["open", str(OUTPUT_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(OUTPUT_DIR)])
            self._append_log(f"已開啟輸出資料夾：{OUTPUT_DIR}")
        except OSError as exc:
            messagebox.showerror(
                "無法開啟資料夾",
                f"請手動開啟：\n{OUTPUT_DIR}\n\n系統訊息：{exc}",
                parent=self.root,
            )

    def _on_close(self) -> None:
        self._closing = True
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    WebsiteHealthApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
