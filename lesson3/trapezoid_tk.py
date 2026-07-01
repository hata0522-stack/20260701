import tkinter as tk
from tkinter import messagebox


def calculate_area():
    try:
        top = float(entry_top.get())
        bottom = float(entry_bottom.get())
        height = float(entry_height.get())
        area = (top + bottom) * height / 2
        label_result.config(text=f"梯形面積: {area:.2f} 平方公分")
    except ValueError:
        messagebox.showerror("輸入錯誤", "請輸入有效的數字")


root = tk.Tk()
root.title("梯形面積計算機")
root.geometry("400x400")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill=tk.BOTH, expand=True)

tk.Label(frame, text="梯形面積計算", font=("Arial", 18)).pack(pady=(0, 20))

tk.Label(frame, text="上底 (公分):", anchor="w").pack(fill=tk.X)
entry_top = tk.Entry(frame)
entry_top.pack(fill=tk.X, pady=(0, 10))

tk.Label(frame, text="下底 (公分):", anchor="w").pack(fill=tk.X)
entry_bottom = tk.Entry(frame)
entry_bottom.pack(fill=tk.X, pady=(0, 10))

tk.Label(frame, text="高 (公分):", anchor="w").pack(fill=tk.X)
entry_height = tk.Entry(frame)
entry_height.pack(fill=tk.X, pady=(0, 10))

tk.Button(
    frame,
    text="計算面積",
    command=calculate_area,
    bg="#4CAF50",
    fg="black",
    font=("Arial", 12),
).pack(pady=(10, 10))

label_result = tk.Label(frame, text="", font=("Arial", 14, "bold"), fg="#333333")
label_result.pack(pady=(10, 0))

root.mainloop()
