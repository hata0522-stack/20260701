import time

def download_file(file_name):
  """模擬下載檔案（同步版本）"""
  print(f"開始下載 {file_name}...")
  time.sleep(2)  # 模擬下載需要 2 秒
  print(f"✅ {file_name} 下載完成")
  return f"{file_name}_data"

def main_sync():
  start = time.time()

  # 下載 3 個檔案（循序執行）
  result1 = download_file("檔案A.pdf")
  result2 = download_file("檔案B.pdf")
  result3 = download_file("檔案C.pdf")

  end = time.time()
  print(f"\n總耗時: {end - start:.2f} 秒")

if __name__ == "__main__":
  main_sync()
