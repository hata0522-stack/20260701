import random
import tkinter as tk
from tkinter import messagebox

# --- 顏色主題 ---
BG_DARK = "#1a1a1a"
BG_MID = "#2d2d2d"
BG_PANEL = "#3a3a3a"
BORDER = "#555555"
ACCENT = "#f0a500"
ACCENT_DIM = "#b8860b"
TEXT_LIGHT = "#e0e0e0"
TEXT_DIM = "#888888"
DANGER = "#cc3333"
SUCCESS = "#22aa44"

# --- 遊戲邏輯 ---
target = random.randint(1, 100)
low, high = 1, 100
attempts = 0
game_over = False

# --- GUI 初始化 ---
root = tk.Tk()
root.title("猜數字遊戲")
root.configure(bg=BG_DARK)
root.resizable(False, False)

# 窗口尺寸與置中
win_w, win_h = 420, 400
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
x = (screen_w - win_w) // 2
y = (screen_h - win_h) // 2
root.geometry(f"{win_w}x{win_h}+{x}+{y}")

# --- 標題區 ---
header = tk.Frame(root, bg=ACCENT, height=48)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(header, text="/// 猜數字遊戲 ///", font=("Microsoft JhengHei", 14, "bold"),
         bg=ACCENT, fg=BG_DARK).pack(expand=True)

# --- 主容器 ---
main_frame = tk.Frame(root, bg=BG_DARK, padx=20, pady=10)
main_frame.pack(fill="both", expand=True)

# --- 範圍顯示 ---
range_frame = tk.Frame(main_frame, bg=BG_MID, relief="flat", bd=0)
range_frame.pack(fill="x", pady=(0, 10))

tk.Label(range_frame, text="目標範圍", font=("Microsoft JhengHei", 9, "bold"),
         bg=BG_MID, fg=TEXT_DIM).pack(pady=(6, 0))
range_label = tk.Label(range_frame, text=f"[ {low} ~ {high} ]",
                       font=("Consolas", 22, "bold"), bg=BG_MID, fg=ACCENT)
range_label.pack(pady=(0, 8))

# --- 輸入區 ---
input_frame = tk.Frame(main_frame, bg=BG_DARK)
input_frame.pack(fill="x", pady=(0, 10))

tk.Label(input_frame, text="輸入 >>", font=("Microsoft JhengHei", 10, "bold"),
         bg=BG_DARK, fg=TEXT_DIM).pack(anchor="w")

entry_frame = tk.Frame(input_frame, bg=BORDER, bd=1, relief="solid")
entry_frame.pack(fill="x")

guess_var = tk.StringVar()
guess_entry = tk.Entry(entry_frame, textvariable=guess_var,
                       font=("Consolas", 18), bg=BG_PANEL, fg=TEXT_LIGHT,
                       insertbackground=ACCENT, relief="flat", bd=6,
                       justify="center")
guess_entry.pack(fill="x")
guess_entry.focus()

# --- 按鈕區 ---
btn_frame = tk.Frame(main_frame, bg=BG_DARK)
btn_frame.pack(fill="x", pady=(0, 10))

submit_btn = tk.Button(btn_frame, text="[ 送出 ]", font=("Microsoft JhengHei", 12, "bold"),
                       bg=ACCENT_DIM, fg=BG_DARK, activebackground=ACCENT,
                       activeforeground=BG_DARK, relief="flat", bd=0,
                       cursor="hand2", command=lambda: submit_guess())
submit_btn.pack(fill="x", ipady=4)

# --- 訊息區 ---
msg_frame = tk.Frame(main_frame, bg=BG_MID, relief="flat", bd=0)
msg_frame.pack(fill="x", pady=(0, 8))

msg_label = tk.Label(msg_frame, text="系統就緒",
                     font=("Microsoft JhengHei", 11, "bold"), bg=BG_MID, fg=TEXT_DIM,
                     wraplength=360)
msg_label.pack(pady=8)

# --- 狀態列 ---
status_bar = tk.Frame(root, bg=ACCENT, height=24)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

attempts_label = tk.Label(status_bar, text="猜測次數：0",
                          font=("Microsoft JhengHei", 10, "bold"), bg=ACCENT, fg=BG_DARK)
attempts_label.pack(expand=True)

# --- 功能 ---
def update_range_display():
    range_label.config(text=f"[ {low} ~ {high} ]")

def update_status():
    attempts_label.config(text=f"猜測次數：{attempts}")

def set_message(text, color=TEXT_DIM):
    msg_label.config(text=text, fg=color)

def submit_guess():
    global low, high, attempts, game_over

    if game_over:
        return

    raw = guess_var.get().strip()
    if not raw:
        set_message("請輸入數字", DANGER)
        return

    try:
        guess = int(raw)
    except ValueError:
        set_message("無效的數字格式", DANGER)
        guess_var.set("")
        return

    if guess < low or guess > high:
        set_message(f"超出範圍，請輸入 {low} ~ {high}", DANGER)
        return

    attempts += 1
    update_status()

    if guess == target:
        game_over = True
        set_message(f"目標命中：{target}", SUCCESS)
        messagebox.showinfo("任務完成", f"恭喜猜中！\n答案：{target}\n共嘗試 {attempts} 次")
        guess_entry.config(state="disabled")
        submit_btn.config(state="disabled", bg=TEXT_DIM)
    elif guess < target:
        low = guess + 1
        update_range_display()
        set_message(">> 太小了", DANGER)
    else:
        high = guess - 1
        update_range_display()
        set_message(">> 太大了", DANGER)

    guess_var.set("")
    guess_entry.focus()

# Enter 鍵綁定
root.bind("<Return>", lambda e: submit_guess())

root.mainloop()
