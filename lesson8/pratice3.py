import random  # 引入 random 模組，用於產生隨機數

def play_game():
    # 產生 1~100 之間的隨機整數作為目標答案
    target = random.randint(1, 100)
    print(target)

    # 初始化搜尋範圍的上下界與猜測次數
    low, high = 1, 100
    attempts = 0

    # 顯示遊戲標題與規則
    print("猜數字遊戲（範圍縮小版）")
    print(f"請猜一個介於 {low} ~ {high} 之間的數字\n")

    while True:
        # 輸入與錯誤處理：確保玩家輸入的是整數
        try:
            guess = int(input(f"請輸入你的猜測（{low} ~ {high}）："))
        except ValueError:
            # 若輸入非數字字串，顯示提示並跳過本次迴圈
            print("請輸入有效數字\n")
            continue

        # 檢查輸入是否在目前的有效範圍內
        if guess < low or guess > high:
            print(f"超出範圍，請輸入 {low} ~ {high} 之間的數字\n")
            continue


        # 猜測次數累加
        attempts += 1

        # 判斷玩家猜測的結果
        if guess == target:
            # 猜中：顯示答案與總次數，結束遊戲
            print(f"🎉 恭喜你猜中了！答案就是 {target}")
            print(f"你總共猜了 {attempts} 次")
            break
        elif guess < target:
            # 猜太小：將下界提高，縮小搜尋範圍
            low = guess + 1
            print(f"再大一點！範圍縮小為 {low} ~ {high}\n")
        else:
            # 猜太大：將上界降低，縮小搜尋範圍
            high = guess - 1
            print(f"再小一點！範圍縮小為 {low} ~ {high}\n")

while True:
  play_game()
  is_play = input("您還要繼續嗎?(y,n)")
  if is_play == "n":
    break
