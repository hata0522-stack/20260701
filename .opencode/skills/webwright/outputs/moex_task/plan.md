# Task

從考選部考畢試題查詢平臺下載 114 年第二次專技高考營養師考試的「生理學與生物化學」科目試題與答案。

# Critical Points
- [x] CP1: 成功開啟考畢試題查詢頁面，確認考試年度為 114 年，考試簡稱為「114年第二次專技人員高等考試營養師、護理師、社會工作師考試...」
  - 證據: screenshot `final_execution_1_page_loaded.png` + log 顯示 Selected exam: 114100 - 114年第二次專技人員高等考試營養師...
- [x] CP2: 在頁面中找到「生理學與生物化學」科目，該行包含「試題」和「答案」兩個下載連結
  - 證據: screenshot `final_execution_2_subject_visible.png` + log 顯示 Subject checkbox visible: True, Question href = s=0103, Answer href = s=0103
- [x] CP3: 成功下載「生理學與生物化學」試題 PDF（114100_3101.pdf）
  - 證據: log 顯示 Question PDF: 114100_3101.pdf, 652877 bytes + 檔案存在
- [x] CP4: 成功下載「生理學與生物化學」答案 PDF（114100_ANS3101.pdf）
  - 證據: log 顯示 Answer PDF: 114100_ANS3101.pdf, 44868 bytes + 檔案存在
- [x] CP5: 確認兩個 PDF 檔案內容有效（非空白、格式正確）
  - 證據: PDF 檔頭為 `%PDF-1.4`，檔尾為 `%%EOF`，檔案大小合理
