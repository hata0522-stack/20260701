import tkinter as tk
from tkinter import messagebox, ttk


def calculate_area():
    try:
        top = float(top_var.get())
        bottom = float(bottom_var.get())
        height = float(height_var.get())
    except ValueError:
        messagebox.showerror("輸入錯誤", "請輸入有效的數字。")
        return

    if top <= 0 or bottom <= 0 or height <= 0:
        messagebox.showwarning("輸入提醒", "上底、下底和高都必須大於 0。")
        return

    area = (top + bottom) * height / 2
    result_var.set(f"{area:,.2f} 平方公分")


def clear_inputs():
    top_var.set("")
    bottom_var.set("")
    height_var.set("")
    result_var.set("等待輸入")
    top_entry.focus()


root = tk.Tk()
root.title("梯形面積計算機")
root.geometry("460x520")
root.resizable(False, False)
root.configure(bg="#f4f7fb")

style = ttk.Style()
style.theme_use("clam")
style.configure("Main.TFrame", background="#f4f7fb")
style.configure("Card.TFrame", background="#ffffff", relief="flat")
style.configure("Title.TLabel", background="#f4f7fb", foreground="#1f2937", font=("Arial", 22, "bold"))
style.configure("Hint.TLabel", background="#f4f7fb", foreground="#6b7280", font=("Arial", 11))
style.configure("Field.TLabel", background="#ffffff", foreground="#374151", font=("Arial", 12))
style.configure("ResultTitle.TLabel", background="#eef6ff", foreground="#2563eb", font=("Arial", 12, "bold"))
style.configure("Result.TLabel", background="#eef6ff", foreground="#111827", font=("Arial", 20, "bold"))
style.configure("TEntry", padding=8)
style.configure(
    "Accent.TButton",
    background="#2563eb",
    foreground="#ffffff",
    borderwidth=0,
    font=("Arial", 12, "bold"),
    padding=(16, 9),
)
style.map("Accent.TButton", background=[("active", "#1d4ed8")])
style.configure(
    "Clear.TButton",
    background="#e5e7eb",
    foreground="#374151",
    borderwidth=0,
    font=("Arial", 12),
    padding=(16, 9),
)
style.map("Clear.TButton", background=[("active", "#d1d5db")])

top_var = tk.StringVar()
bottom_var = tk.StringVar()
height_var = tk.StringVar()
result_var = tk.StringVar(value="等待輸入")

main_frame = ttk.Frame(root, style="Main.TFrame", padding=28)
main_frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(main_frame, text="梯形面積計算機", style="Title.TLabel").pack(anchor="w")
ttk.Label(
    main_frame,
    text="輸入上底、下底與高，快速計算梯形面積。",
    style="Hint.TLabel",
).pack(anchor="w", pady=(4, 18))

card = ttk.Frame(main_frame, style="Card.TFrame", padding=22)
card.pack(fill=tk.X)

ttk.Label(card, text="上底 (公分)", style="Field.TLabel").grid(row=0, column=0, sticky="w")
top_entry = ttk.Entry(card, textvariable=top_var, font=("Arial", 13), width=26)
top_entry.grid(row=1, column=0, sticky="ew", pady=(6, 14))

ttk.Label(card, text="下底 (公分)", style="Field.TLabel").grid(row=2, column=0, sticky="w")
bottom_entry = ttk.Entry(card, textvariable=bottom_var, font=("Arial", 13), width=26)
bottom_entry.grid(row=3, column=0, sticky="ew", pady=(6, 14))

ttk.Label(card, text="高 (公分)", style="Field.TLabel").grid(row=4, column=0, sticky="w")
height_entry = ttk.Entry(card, textvariable=height_var, font=("Arial", 13), width=26)
height_entry.grid(row=5, column=0, sticky="ew", pady=(6, 4))

card.columnconfigure(0, weight=1)

button_frame = ttk.Frame(main_frame, style="Main.TFrame")
button_frame.pack(fill=tk.X, pady=18)

ttk.Button(button_frame, text="計算面積", style="Accent.TButton", command=calculate_area).pack(
    side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
)
ttk.Button(button_frame, text="清除", style="Clear.TButton", command=clear_inputs).pack(
    side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0)
)

result_frame = tk.Frame(root, bg="#eef6ff", padx=26, pady=18)
result_frame.pack(fill=tk.X, padx=28, pady=(0, 28))

ttk.Label(result_frame, text="計算結果", style="ResultTitle.TLabel").pack(anchor="w")
ttk.Label(result_frame, textvariable=result_var, style="Result.TLabel").pack(anchor="w", pady=(4, 0))

root.bind("<Return>", lambda event: calculate_area())
top_entry.focus()

root.mainloop()
