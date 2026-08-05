import random
import tkinter as tk
from tkinter import font


class GuessNumberGame(tk.Tk):
    """猜數字遊戲（範圍縮小版）— tkinter 圖形介面"""

    # 介面配色
    BG = "#1e2233"          # 主背景（深藍）
    CARD = "#2a2f45"        # 卡片背景
    ACCENT = "#5b8def"      # 主色（藍）
    SUCCESS = "#4caf7d"     # 成功（綠）
    WARN_LOW = "#e6a23c"    # 太小（橘）
    WARN_HIGH = "#e05c5c"   # 太大（紅）
    TEXT = "#e8eaf2"        # 主要文字
    SUBTEXT = "#9aa3bd"     # 次要文字

    def __init__(self):
        super().__init__()
        self.title("猜數字遊戲")
        self.resizable(False, False)
        self.configure(bg=self.BG)

        # 建立字型
        self.font_title = font.Font(family="Helvetica", size=22, weight="bold")
        self.font_range = font.Font(family="Helvetica", size=28, weight="bold")
        self.font_body = font.Font(family="Helvetica", size=14)
        self.font_small = font.Font(family="Helvetica", size=12)
        self.font_entry = font.Font(family="Helvetica", size=20, weight="bold")

        self._build_ui()
        self.reset_game()

        # 視窗置中
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    # ---------- 介面建立 ----------
    def _build_ui(self):
        main = tk.Frame(self, bg=self.BG, padx=32, pady=24)
        main.pack()

        # 標題區
        tk.Label(main, text="🎯 猜數字遊戲", font=self.font_title,
                 bg=self.BG, fg=self.TEXT).pack()
        tk.Label(main, text="範圍縮小版｜猜一個 1 ~ 100 之間的數字",
                 font=self.font_small, bg=self.BG, fg=self.SUBTEXT).pack(pady=(4, 16))

        # 範圍顯示卡片
        card = tk.Frame(main, bg=self.CARD, padx=24, pady=16)
        card.pack(fill="x")
        tk.Label(card, text="目前範圍", font=self.font_small,
                 bg=self.CARD, fg=self.SUBTEXT).pack()
        self.range_label = tk.Label(card, text="1 ~ 100", font=self.font_range,
                                    bg=self.CARD, fg=self.ACCENT)
        self.range_label.pack(pady=(2, 8))

        # 範圍視覺化長條（Canvas）
        self.bar_width = 320
        self.bar = tk.Canvas(card, width=self.bar_width, height=18,
                             bg=self.BG, highlightthickness=0)
        self.bar.pack()

        # 提示訊息
        self.hint_label = tk.Label(main, text="", font=self.font_body,
                                   bg=self.BG, fg=self.TEXT, height=2)
        self.hint_label.pack(pady=(12, 4))

        # 輸入區
        input_frame = tk.Frame(main, bg=self.BG)
        input_frame.pack(pady=4)

        self.entry = tk.Entry(input_frame, font=self.font_entry, width=8,
                              justify="center", bg=self.CARD, fg=self.TEXT,
                              insertbackground=self.TEXT, relief="flat",
                              highlightthickness=2,
                              highlightbackground=self.CARD,
                              highlightcolor=self.ACCENT)
        self.entry.pack(side="left", ipady=6)
        self.entry.bind("<Return>", lambda e: self.check_guess())

        self.guess_btn = tk.Button(input_frame, text="猜！", font=self.font_body,
                                   bg=self.ACCENT, fg="white",
                                   activebackground="#4a7bd8", activeforeground="white",
                                   relief="flat", padx=20, pady=6, cursor="hand2",
                                   command=self.check_guess)
        self.guess_btn.pack(side="left", padx=(12, 0))

        # 猜測次數
        self.attempts_label = tk.Label(main, text="已猜 0 次", font=self.font_small,
                                       bg=self.BG, fg=self.SUBTEXT)
        self.attempts_label.pack(pady=(8, 4))

        # 猜測紀錄
        history_frame = tk.Frame(main, bg=self.CARD, padx=16, pady=12)
        history_frame.pack(fill="x", pady=(8, 0))
        tk.Label(history_frame, text="猜測紀錄", font=self.font_small,
                 bg=self.CARD, fg=self.SUBTEXT).pack(anchor="w")
        self.history_label = tk.Label(history_frame, text="（尚無紀錄）",
                                      font=self.font_small, bg=self.CARD,
                                      fg=self.TEXT, justify="left",
                                      wraplength=340, anchor="w")
        self.history_label.pack(anchor="w", pady=(4, 0))

        # 再玩一次按鈕（猜中後才顯示）
        self.restart_btn = tk.Button(main, text="🔄 再玩一次", font=self.font_body,
                                     bg=self.SUCCESS, fg="white",
                                     activebackground="#3d9066", activeforeground="white",
                                     relief="flat", padx=20, pady=6, cursor="hand2",
                                     command=self.reset_game)

    # ---------- 遊戲邏輯 ----------
    def reset_game(self):
        """重設遊戲狀態並更新畫面"""
        self.target = random.randint(1, 100)
        self.low, self.high = 1, 100
        self.attempts = 0
        self.history = []
        self.game_over = False

        self.restart_btn.pack_forget()
        self.range_label.config(text="1 ~ 100", fg=self.ACCENT)
        self.hint_label.config(text="請輸入你的猜測，按 Enter 或「猜！」", fg=self.TEXT)
        self.attempts_label.config(text="已猜 0 次")
        self.history_label.config(text="（尚無紀錄）")
        self.entry.config(state="normal")
        self.guess_btn.config(state="normal")
        self.entry.delete(0, tk.END)
        self.entry.focus_set()
        self._draw_bar()

    def _draw_bar(self):
        """繪製範圍視覺化長條：亮色區段代表剩餘的有效範圍"""
        self.bar.delete("all")
        # 底色（1~100 全範圍）
        self.bar.create_rectangle(0, 0, self.bar_width, 18,
                                  fill="#3a4060", outline="")
        # 有效範圍區段
        x1 = (self.low - 1) / 100 * self.bar_width
        x2 = self.high / 100 * self.bar_width
        color = self.SUCCESS if self.game_over else self.ACCENT
        self.bar.create_rectangle(x1, 0, x2, 18, fill=color, outline="")

    def check_guess(self):
        """處理一次猜測：驗證輸入、判斷大小、更新畫面"""
        if self.game_over:
            return

        raw = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        # 輸入驗證：必須是整數
        try:
            guess = int(raw)
        except ValueError:
            self.hint_label.config(text="⚠️ 請輸入有效數字", fg=self.WARN_HIGH)
            self._shake()
            return

        # 檢查是否在目前有效範圍內
        if guess < self.low or guess > self.high:
            self.hint_label.config(
                text=f"⚠️ 超出範圍，請輸入 {self.low} ~ {self.high} 之間的數字",
                fg=self.WARN_HIGH)
            self._shake()
            return

        self.attempts += 1
        self.attempts_label.config(text=f"已猜 {self.attempts} 次")

        if guess == self.target:
            self._win()
        elif guess < self.target:
            self.low = guess + 1
            self.history.append(f"{guess}↑")
            self.hint_label.config(text=f"📈 太小了！範圍縮小為 {self.low} ~ {self.high}",
                                   fg=self.WARN_LOW)
        else:
            self.high = guess - 1
            self.history.append(f"{guess}↓")
            self.hint_label.config(text=f"📉 太大了！範圍縮小為 {self.low} ~ {self.high}",
                                   fg=self.WARN_HIGH)

        if not self.game_over:
            self.range_label.config(text=f"{self.low} ~ {self.high}")
            self.history_label.config(text="  ".join(self.history))
            self._draw_bar()

    def _win(self):
        """猜中：顯示結果並鎖定輸入"""
        self.game_over = True
        self.history.append(f"{self.target}🎯")
        self.range_label.config(text=str(self.target), fg=self.SUCCESS)
        self.hint_label.config(
            text=f"🎉 恭喜猜中！答案是 {self.target}，共猜了 {self.attempts} 次",
            fg=self.SUCCESS)
        self.history_label.config(text="  ".join(self.history))
        self.entry.config(state="disabled")
        self.guess_btn.config(state="disabled")
        self._draw_bar()
        self.restart_btn.pack(pady=(16, 0))
        self.restart_btn.focus_set()

    def _shake(self):
        """輸入錯誤時讓視窗左右晃動，給予視覺回饋"""
        x, y = self.winfo_x(), self.winfo_y()
        offsets = [8, -8, 6, -6, 3, -3, 0]
        for i, dx in enumerate(offsets):
            self.after(i * 30, lambda dx=dx: self.geometry(f"+{x + dx}+{y}"))


if __name__ == "__main__":
    app = GuessNumberGame()
    app.mainloop()
