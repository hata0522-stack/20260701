import random

target = random.randint(1, 100)
low, high = 1, 100
attempts = 0

print("猜數字遊戲（範圍縮小版）")
print(f"請猜一個介於 {low} ~ {high} 之間的數字\n")

while True:
    try:
        guess = int(input(f"請輸入你的猜測（{low} ~ {high}）："))
    except ValueError:
        print("請輸入有效數字\n")
        continue

    if guess < low or guess > high:
        print(f"超出範圍，請輸入 {low} ~ {high} 之間的數字\n")
        continue

    attempts += 1

    if guess == target:
        print(f"🎉 恭喜你猜中了！答案就是 {target}")
        print(f"你總共猜了 {attempts} 次")
        break
    elif guess < target:
        low = guess + 1
        print(f"太小了！範圍縮小為 {low} ~ {high}\n")
    else:
        high = guess - 1
        print(f"太大了！範圍縮小為 {low} ~ {high}\n")
