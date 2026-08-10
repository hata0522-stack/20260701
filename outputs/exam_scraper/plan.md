# Task

從考選部考畢試題查詢平臺下載一個專科科目的試題與答案，整合為單一 markdown 檔案。

網站: https://wwwq.moex.gov.tw/exam/wFrmExamQandASearch.aspx?y=2025&e=114100
考試: 114年第二次專門職業及技術人員高等考試營養師、護理師、社會工作師考試...
選定科目: 膳食療養學 (營養師類科)

# Critical Points

- [x] CP1: 開啟考試頁面，確認 114100 考試的科目列表已正確載入
  - 證據: `screenshots/final_execution_1_open_exam_page.png` + title 確認為「考畢試題查詢平臺-考選部」
- [x] CP2: 下載「膳食療養學」的試題 PDF
  - 證據: PDF 下載成功 (641077 bytes)，log step 3
- [x] CP3: 下載「膳食療養學」的答案 PDF
  - 證據: PDF 下載成功 (44565 bytes)，log step 4
- [x] CP4: 從 PDF 中成功萃取文字內容
  - 證據: 試題 6945 字元、答案 418 字元萃取成功，log step 5
- [x] CP5: 將試題與答案合併為一個 markdown 檔案，測驗題每題附正確答案
  - 證據: `膳食療養學_試題與答案整合.md` 包含 40 題測驗題，每題皆有正確答案
- [x] CP6: 最終合併後的 markdown 檔案內容正確、格式完整
  - 證據: 40 題答案與官方答案完全吻合（如 Q1=A, Q2=D, Q40=D 等）
