import random
import tkinter as tk
from tkinter import messagebox


# ── 色彩主題常數 ──────────────────────────────────────────

BG_COLOR = "#1a1a2e"          # 主背景（深藍黑）
CARD_BG = "#16213e"           # 卡片區塊背景
ACCENT = "#0f3460"            # 強調色
HIGHLIGHT = "#e94560"         # 亮點色（紅粉）
GOLD = "#f5c518"              # 金色（標題/成功）
TEXT_WHITE = "#ffffff"         # 白色文字
TEXT_GRAY = "#a0a0b0"         # 灰色文字
SUCCESS_GREEN = "#4ecca3"     # 成功綠
TOO_HIGH = "#e94560"          # 太大（紅粉）
TOO_LOW = "#f5c518"           # 太小（金）


class GuessGameGUI:
    """猜數字遊戲 - 精緻版 tkinter 圖形介面"""

    def __init__(self, root):
        self.root = root
        self.root.title("猜數字遊戲")
        self.root.configure(bg=BG_COLOR)

        # 鎖定視窗尺寸
        win_w, win_h = 420, 480
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.resizable(False, False)

        # 遊戲變數
        self.target = random.randint(1, 100)
        self.low = 1
        self.high = 100
        self.attempts = 0
        self.game_over = False

        self._build_ui()

    # ── 介面建構 ──────────────────────────────────────────

    def _build_ui(self):
        # ─ 標題區 ─
        title_frame = tk.Frame(self.root, bg=BG_COLOR)
        title_frame.pack(fill=tk.X, pady=(28, 4))

        tk.Label(
            title_frame, text="G U E S S", font=("Helvetica", 10, "bold"),
            bg=BG_COLOR, fg=HIGHLIGHT,
        ).pack()
        tk.Label(
            title_frame, text="猜數字遊戲", font=("Arial", 24, "bold"),
            bg=BG_COLOR, fg=GOLD,
        ).pack()

        # ─ 卡片容器（帶有視覺邊框） ─
        card = tk.Frame(self.root, bg=CARD_BG, bd=0, highlightthickness=2,
                         highlightbackground=ACCENT, highlightcolor=ACCENT)
        card.pack(padx=30, pady=(18, 0), fill=tk.X)

        # 範圍提示
        self.range_label = tk.Label(
            card, text=f"請猜 {self.low} ~ {self.high} 之間的數字",
            font=("Arial", 12), bg=CARD_BG, fg=TEXT_GRAY,
        )
        self.range_label.pack(pady=(22, 16))

        # 輸入框（自訂樣式）
        entry_frame = tk.Frame(card, bg=ACCENT, bd=0)
        entry_frame.pack(pady=(0, 6))

        self.entry = tk.Entry(
            entry_frame, font=("Helvetica", 22, "bold"),
            width=6, justify="center", bd=0,
            bg=CARD_BG, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
            highlightthickness=2, highlightbackground=ACCENT,
            highlightcolor=HIGHLIGHT,
        )
        self.entry.pack(ipady=6)
        self.entry.bind("<Return>", lambda e: self._on_guess())

        # 輸入框下方分隔線
        tk.Frame(card, bg=ACCENT, height=1).pack(fill=tk.X, padx=40, pady=(0, 18))

        # 結果訊息
        self.result_label = tk.Label(
            card, text="", font=("Arial", 15, "bold"),
            bg=CARD_BG, fg=TEXT_WHITE,
        )
        self.result_label.pack(pady=(0, 4))

        # 猜測次數
        self.attempts_label = tk.Label(
            card, text="已猜次數：0", font=("Arial", 11),
            bg=CARD_BG, fg=TEXT_GRAY,
        )
        self.attempts_label.pack(pady=(0, 22))

        # ─ 按鈕區 ─
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(fill=tk.X, padx=30, pady=(20, 0))

        # 猜按鈕（亮色主按鈕）
        self.guess_btn = tk.Label(
            btn_frame, text="猜 ！", font=("Arial", 14, "bold"),
            bg=HIGHLIGHT, fg=TEXT_WHITE, cursor="hand2",
            padx=30, pady=10,
        )
        self.guess_btn.pack(fill=tk.X)
        self.guess_btn.bind("<Button-1>", lambda e: self._on_guess())
        self.guess_btn.bind("<Enter>", self._btn_hover_in)
        self.guess_btn.bind("<Leave>", self._btn_hover_out)

        # 新遊戲按鈕（次要按鈕）
        self.new_game_btn = tk.Label(
            btn_frame, text="新遊戲", font=("Arial", 11),
            bg=BG_COLOR, fg=TEXT_GRAY, cursor="hand2",
            padx=10, pady=6,
        )
        self.new_game_btn.pack(pady=(14, 0))
        self.new_game_btn.bind("<Button-1>", lambda e: self._new_game())
        self.new_game_btn.bind("<Enter>", lambda e: self.new_game_btn.config(fg=TEXT_WHITE))
        self.new_game_btn.bind("<Leave>", lambda e: self.new_game_btn.config(fg=TEXT_GRAY))

    # ── 按鈕 hover 效果 ────────────────────────────────────

    def _btn_hover_in(self, _):
        self.guess_btn.config(bg="#ff6b81")

    def _btn_hover_out(self, _):
        self.guess_btn.config(bg=HIGHLIGHT)

    # ── 遊戲邏輯 ──────────────────────────────────────────

    def _on_guess(self):
        if self.game_over:
            return

        raw = self.entry.get().strip()
        if not raw:
            messagebox.showwarning("提示", "請先輸入一個數字！")
            return

        try:
            guess = int(raw)
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的整數！")
            return

        if guess < self.low or guess > self.high:
            messagebox.showwarning("提示", f"請輸入 {self.low} ~ {self.high} 之間的數字！")
            return

        self.attempts += 1
        self.entry.delete(0, tk.END)
        self.attempts_label.config(text=f"已猜次數：{self.attempts}")

        if guess == self.target:
            self.result_label.config(text=f"答案：{self.target}！", fg=SUCCESS_GREEN)
            self.range_label.config(
                text=f"總共猜了 {self.attempts} 次",
                fg=SUCCESS_GREEN, font=("Arial", 12, "bold"),
            )
            self.guess_btn.config(bg="#2d6a4f", text="猜中了！", cursor="")
            self.entry.config(state=tk.DISABLED)
            self.game_over = True

        elif guess < self.target:
            self.low = guess + 1
            self.result_label.config(text="太小了 ▲", fg=TOO_LOW)
        else:
            self.high = guess - 1
            self.result_label.config(text="太大了 ▼", fg=TOO_HIGH)

        self.range_label.config(text=f"請猜 {self.low} ~ {self.high} 之間的數字", fg=TEXT_GRAY,
                                font=("Arial", 12))

    def _new_game(self):
        self.target = random.randint(1, 100)
        self.low = 1
        self.high = 100
        self.attempts = 0
        self.game_over = False

        self.range_label.config(text=f"請猜 {self.low} ~ {self.high} 之間的數字",
                                fg=TEXT_GRAY, font=("Arial", 12))
        self.result_label.config(text="", fg=TEXT_WHITE)
        self.attempts_label.config(text="已猜次數：0")
        self.entry.config(state=tk.NORMAL)
        self.entry.delete(0, tk.END)
        self.guess_btn.config(bg=HIGHLIGHT, text="猜 ！", cursor="hand2")


# ── 程式進入點 ──────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = GuessGameGUI(root)
    root.mainloop()
