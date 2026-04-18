import os
import json
import yfinance as yf
from google import genai

# 1. 拿出我們藏在 GitHub 保險箱的鑰匙
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. 定義一個抓取最新價格與漲跌幅的小工具
def get_price(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        curr = round(hist['Close'].iloc[-1], 2)
        prev = round(hist['Close'].iloc[-2], 2)
        diff = round(curr - prev, 2)
        return curr, diff
    except:
        return 0, 0

# 3. 抓取全球大環境關鍵數據
usd_twd, usd_diff = get_price("TWD=X") # 美元/台幣
gold, gold_diff = get_price("GC=F")    # 黃金期貨
oil, oil_diff = get_price("BZ=F")      # 布蘭特原油
vix, vix_diff = get_price("^VIX")      # 恐慌指數

# 4. 呼叫 Gemini 幫我們寫風險警示與燈號判斷
prompt = f"""
今日總經數據：
美元/台幣: {usd_twd} (漲跌 {usd_diff})
黃金期貨: {gold} (漲跌 {gold_diff})
原油期貨: {oil} (漲跌 {oil_diff})
VIX恐慌指數: {vix} (漲跌 {vix_diff})

請扮演資深理財專員，判斷今日全球市場風險。
回傳嚴格的 JSON 格式，不要加 ```json 標籤，只要大括號與內容即可：
{{
  "status_light": "請根據數值判斷填寫：🔴 紅燈 (危險)、🟡 黃燈 (警戒)、或 🟢 綠燈 (安全)",
  "status_desc": "一句話描述目前大環境主要風險來源或穩定原因",
  "warning_event": "一段50字以內的重大事件預警，以及給投資人的開盤操作建議"
}}
"""

try:
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    # 清理格式，確保是乾淨的 JSON
    ai_text = response.text.replace("```json", "").replace("```", "").strip()
    ai_data = json.loads(ai_text)
except Exception as e:
    ai_data = {
        "status_light": "🟡 系統連線中",
        "status_desc": "AI 分析生成中...",
        "warning_event": "暫時無法取得 AI 分析，請手動留意市場波動。"
    }

# 5. 把所有數據打包成 JSON 檔案
output_data = {
    "date": str(yf.Ticker("^VIX").history(period="1d").index[-1].date()),
    "usd_twd": {"price": usd_twd, "diff": usd_diff},
    "gold": {"price": gold, "diff": gold_diff},
    "oil": {"price": oil, "diff": oil_diff},
    "vix": {"price": vix, "diff": vix_diff},
    "ai_analysis": ai_data
}

# 存成 data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)
print("全球大環境與風險雷達資料更新完成！")
