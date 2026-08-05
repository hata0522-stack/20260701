import random
import tkinter as tk
from tkinter import font


class GuessNumberApp(tk.Tk):
    """1 到 100 的範圍縮小猜數字遊戲。"""

    WINDOW_BG = "#F4F6F5"
    SURFACE = "#FFFFFF"
    INK = "#172321"
    MUTED = "#667572"
    BORDER = "#DCE4E1"
    PRIMARY = "#087E72"
    PRIMARY_HOVER = "#066A61"
    TRACK = "#E3E9E7"
    LOW_COLOR = "#B16A08"
    HIGH_COLOR = "#C4493D"
    SUCCESS = "#16805A"

    def __init__(self):
        super().__init__()
        self.title("猜數字遊戲")
        self.geometry("520x680")
        self.minsize(480, 640)
        self.configure(bg=self.WINDOW_BG)

        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.range_font = font.Font(family="Arial", size=30, weight="bold")
        self.number_font = font.Font(family="Arial", size=22, weight="bold")
        self.body_font = font.Font(family="Arial", size=12)
        self.body_bold_font = font.Font(family="Arial", size=12, weight="bold")
        self.small_font = font.Font(family="Arial", size=10)

        self._build_interface()
        self._bind_events()
        self.start_new_game()
        self._center_window()

    def _build_interface(self):
        main = tk.Frame(self, bg=self.WINDOW_BG, padx=36, pady=30)
        main.pack(fill="both", expand=True)

        header = tk.Frame(main, bg=self.WINDOW_BG)
        header.pack(fill="x")

        title_group = tk.Frame(header, bg=self.WINDOW_BG)
        title_group.pack(side="left", anchor="n")
        tk.Label(
            title_group,
            text="猜數字",
            font=self.title_font,
            bg=self.WINDOW_BG,
            fg=self.INK,
        ).pack(anchor="w")
        tk.Label(
            title_group,
            text="逐步縮小範圍，找出隱藏的答案",
            font=self.body_font,
            bg=self.WINDOW_BG,
            fg=self.MUTED,
        ).pack(anchor="w", pady=(5, 0))

        self.new_game_button = self._make_button(
            header,
            text="重新開始",
            command=self.start_new_game,
            bg=self.SURFACE,
            fg=self.PRIMARY,
            hover_bg="#E8F3F1",
            border=True,
            padx=14,
            pady=9,
        )
        self.new_game_button.pack(side="right", anchor="n")

        range_card = self._make_card(main)
        range_card.pack(fill="x", pady=(24, 14))

        tk.Label(
            range_card,
            text="目前有效範圍",
            font=self.small_font,
            bg=self.SURFACE,
            fg=self.MUTED,
        ).pack(pady=(18, 2))
        self.range_label = tk.Label(
            range_card,
            text="1  -  100",
            font=self.range_font,
            bg=self.SURFACE,
            fg=self.INK,
        )
        self.range_label.pack()

        self.range_canvas = tk.Canvas(
            range_card,
            height=20,
            bg=self.SURFACE,
            highlightthickness=0,
        )
        self.range_canvas.pack(fill="x", padx=28, pady=(12, 20))
        self.range_canvas.bind("<Configure>", lambda _event: self._draw_range())

        stats = tk.Frame(main, bg=self.WINDOW_BG)
        stats.pack(fill="x", pady=(0, 14))
        stats.grid_columnconfigure((0, 1), weight=1, uniform="stat")

        self.attempts_value = self._make_stat(stats, 0, "猜測次數")
        self.remaining_value = self._make_stat(stats, 1, "剩餘數字")

        play_card = self._make_card(main)
        play_card.pack(fill="x")

        self.feedback_label = tk.Label(
            play_card,
            text="輸入一個數字開始",
            font=self.body_bold_font,
            bg=self.SURFACE,
            fg=self.INK,
            height=2,
            wraplength=370,
        )
        self.feedback_label.pack(fill="x", padx=24, pady=(18, 8))

        input_row = tk.Frame(play_card, bg=self.SURFACE)
        input_row.pack(padx=24, pady=(0, 22))

        entry_shell = tk.Frame(
            input_row,
            bg=self.SURFACE,
            highlightthickness=2,
            highlightbackground=self.BORDER,
            highlightcolor=self.PRIMARY,
        )
        entry_shell.pack(side="left")
        self.guess_entry = tk.Entry(
            entry_shell,
            width=7,
            justify="center",
            font=self.number_font,
            bg=self.SURFACE,
            fg=self.INK,
            insertbackground=self.INK,
            relief="flat",
            bd=0,
        )
        self.guess_entry.pack(ipady=9, padx=6)

        self.guess_button = self._make_button(
            input_row,
            text="送出猜測",
            command=self.submit_guess,
            bg=self.PRIMARY,
            fg="#FFFFFF",
            hover_bg=self.PRIMARY_HOVER,
            padx=22,
            pady=13,
        )
        self.guess_button.pack(side="left", padx=(12, 0))

        history_header = tk.Frame(main, bg=self.WINDOW_BG)
        history_header.pack(fill="x", pady=(20, 8))
        tk.Label(
            history_header,
            text="猜測紀錄",
            font=self.body_bold_font,
            bg=self.WINDOW_BG,
            fg=self.INK,
        ).pack(side="left")
        self.history_count_label = tk.Label(
            history_header,
            text="0 筆",
            font=self.small_font,
            bg=self.WINDOW_BG,
            fg=self.MUTED,
        )
        self.history_count_label.pack(side="right")

        history_card = self._make_card(main)
        history_card.pack(fill="both", expand=True)
        self.history_label = tk.Label(
            history_card,
            text="尚無紀錄",
            font=self.body_font,
            bg=self.SURFACE,
            fg=self.MUTED,
            justify="left",
            anchor="nw",
            wraplength=380,
        )
        self.history_label.pack(fill="both", expand=True, padx=20, pady=16)

    def _make_card(self, parent):
        return tk.Frame(
            parent,
            bg=self.SURFACE,
            highlightthickness=1,
            highlightbackground=self.BORDER,
        )

    def _make_stat(self, parent, column, caption):
        card = self._make_card(parent)
        card.grid(row=0, column=column, sticky="ew", padx=(0, 7) if column == 0 else (7, 0))
        value = tk.Label(
            card,
            text="0",
            font=self.number_font,
            bg=self.SURFACE,
            fg=self.PRIMARY,
        )
        value.pack(pady=(12, 0))
        tk.Label(
            card,
            text=caption,
            font=self.small_font,
            bg=self.SURFACE,
            fg=self.MUTED,
        ).pack(pady=(0, 12))
        return value

    def _make_button(
        self,
        parent,
        text,
        command,
        bg,
        fg,
        hover_bg,
        padx,
        pady,
        border=False,
    ):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.body_bold_font,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            bd=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            highlightthickness=1 if border else 0,
            highlightbackground=self.BORDER,
        )
        button.bind("<Enter>", lambda _event: button.config(bg=hover_bg))
        button.bind("<Leave>", lambda _event: button.config(bg=bg))
        return button

    def _bind_events(self):
        self.guess_entry.bind("<Return>", lambda _event: self.submit_guess())
        self.bind("<Escape>", lambda _event: self.start_new_game())

    def start_new_game(self):
        self.target = random.randint(1, 100)
        self.low = 1
        self.high = 100
        self.attempts = 0
        self.history = []
        self.game_over = False

        self.range_label.config(text="1  -  100", fg=self.INK)
        self.attempts_value.config(text="0")
        self.remaining_value.config(text="100")
        self.feedback_label.config(text="輸入一個數字開始", fg=self.INK)
        self.history_label.config(text="尚無紀錄", fg=self.MUTED)
        self.history_count_label.config(text="0 筆")
        self.guess_entry.config(state="normal")
        self.guess_button.config(state="normal", text="送出猜測", cursor="hand2")
        self.guess_entry.delete(0, tk.END)
        self.guess_entry.focus_set()
        self.after_idle(self._draw_range)

    def submit_guess(self):
        if self.game_over:
            return

        raw_value = self.guess_entry.get().strip()
        try:
            guess = int(raw_value)
        except ValueError:
            self._show_input_error("請輸入有效的整數")
            return

        if not self.low <= guess <= self.high:
            self._show_input_error(f"請輸入 {self.low} 到 {self.high} 之間的數字")
            return

        self.attempts += 1
        self.guess_entry.delete(0, tk.END)

        if guess == self.target:
            self._finish_game(guess)
            return

        if guess < self.target:
            self.low = guess + 1
            direction = "太小"
            marker = "↑"
            color = self.LOW_COLOR
        else:
            self.high = guess - 1
            direction = "太大"
            marker = "↓"
            color = self.HIGH_COLOR

        self.history.append(f"{guess} {marker} {direction}")
        self.feedback_label.config(
            text=f"{guess} {direction}了，再試一次",
            fg=color,
        )
        self._refresh_game_state()
        self.guess_entry.focus_set()

    def _show_input_error(self, message):
        self.feedback_label.config(text=message, fg=self.HIGH_COLOR)
        self.guess_entry.selection_range(0, tk.END)
        self.guess_entry.focus_set()
        self.bell()

    def _finish_game(self, guess):
        self.game_over = True
        self.history.append(f"{guess}  ✓  猜中")
        self.low = self.high = guess
        self.feedback_label.config(
            text=f"答對了！你用了 {self.attempts} 次猜中 {guess}",
            fg=self.SUCCESS,
        )
        self.range_label.config(fg=self.SUCCESS)
        self.guess_entry.config(state="disabled")
        self.guess_button.config(state="disabled", text="已猜中", cursor="arrow")
        self._refresh_game_state()
        self.new_game_button.focus_set()

    def _refresh_game_state(self):
        remaining = self.high - self.low + 1
        self.range_label.config(text=f"{self.low}  -  {self.high}")
        self.attempts_value.config(text=str(self.attempts))
        self.remaining_value.config(text=str(remaining))
        self.history_count_label.config(text=f"{len(self.history)} 筆")
        self.history_label.config(
            text="   ·   ".join(self.history),
            fg=self.INK,
        )
        self._draw_range()

    def _draw_range(self):
        canvas = self.range_canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 1)
        y1, y2 = 6, 14
        canvas.create_rectangle(0, y1, width, y2, fill=self.TRACK, outline="")

        start = (self.low - 1) / 100 * width
        end = self.high / 100 * width
        color = self.SUCCESS if self.game_over else self.PRIMARY
        canvas.create_rectangle(start, y1, end, y2, fill=color, outline="")
        canvas.create_oval(start - 4, y1 - 2, start + 4, y2 + 2, fill=color, outline="")
        canvas.create_oval(end - 4, y1 - 2, end + 4, y2 + 2, fill=color, outline="")

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = max((self.winfo_screenwidth() - width) // 2, 0)
        y = max((self.winfo_screenheight() - height) // 2, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")


if __name__ == "__main__":
    app = GuessNumberApp()
    app.mainloop()
