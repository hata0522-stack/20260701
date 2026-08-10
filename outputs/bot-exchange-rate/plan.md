# Task

前往臺灣銀行牌告匯率官網查詢並回報最新的美金現鈔買入與賣出匯率

# Critical Points

- [x] CP1: 成功開啟臺灣銀行牌告匯率官網 → `final_execution_1_open_page.png` + URL `https://rate.bot.com.tw/xrt?Lang=zh-TW`
- [x] CP2: 擷取到美金現鈔買入匯率 **31.625** → `final_execution_2_usd_cash_buying.png` + log step 2
- [x] CP3: 擷取到美金現鈔賣出匯率 **32.295** → `final_execution_3_usd_cash_selling.png` + log step 3
- [x] CP4: 最終結果寫入 `final_script_log.txt` → `FINAL_RESPONSE: 美金現鈔買入: 31.625, 美金現鈔賣出: 32.295`
