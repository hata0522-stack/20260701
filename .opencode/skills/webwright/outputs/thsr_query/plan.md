# Task

查詢台灣高鐵網站，台北到台中單程票，2026 年 7 月 29 日 19:00 的所有車次資料。

# Critical Points

- [x] CP1: 成功開啟台灣高鐵官網 (https://www.thsrc.com.tw/)
  - 證據: `final_execution_1_open_start_page.png` — 頁面標題含「台灣高鐵」
  - Log: `step 1 action: open THSR website`
- [x] CP2: 選擇出發站「台北」
  - 證據: `final_execution_2_select_departure.png` — `select_location01` 設為 `TaiPei`
  - Log: `step 2 action: select departure station 台北`
  - Assertion: `dep_value == "TaiPei"` PASS
- [x] CP3: 選擇抵達站「台中」
  - 證據: `final_execution_3_select_arrival.png` — `select_location02` 設為 `TaiZhong`
  - Log: `step 3 action: select arrival station 台中`
  - Assertion: `arr_value == "TaiZhong"` PASS
- [x] CP4: 選擇日期 2026/07/29
  - 證據: `final_execution_4_check_date.png` — `Departdate01` 值為 `2026/07/29`
  - Log: `step 4 action: check departure date 2026/07/29`
  - Assertion: `date_value == "2026/07/29"` PASS
- [x] CP5: 選擇時間 19:00
  - 證據: `final_execution_5_set_time.png` — `outWardTime` 填為 `19:00`
  - Log: `step 5 action: set departure time 19:00`
  - Assertion: `time_value == "19:00"` PASS
- [x] CP6: 顯示查詢結果中的所有車次資料（共 5 班車次）
  - 證據: `final_execution_6_results_overview.png` — 結果頁面呈現 5 列車次
  - Log: `step 7 action: extracted 5 train schedules`
  - 資料:
    ```
    19:11 → 20:15 (01:04) | 車次: 0853 | 自由座車廂: 8-12
    19:21 → 20:23 (01:02) | 車次: 0679 | 自由座車廂: 10-12
    19:31 → 20:18 (00:47) | 車次: 0157 | 自由座車廂: 10-12
    19:46 → 20:46 (01:00) | 車次: 0681 | 自由座車廂: 8-12
    19:51 → 20:38 (00:47) | 車次: 1253 | 自由座車廂: 10-12
    ```

# 票價資訊

| 車廂類型 | 全票 | 孩童票/敬老票/愛心票 |
|---------|------|---------------------|
| 標準車廂 | $700 | $350 |
| 商務車廂 | $1250 | $625 |
| 自由座車廂 | $675 | $335 |
