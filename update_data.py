import os
import json
import yfinance as yf
from google import genai
from datetime import datetime

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

# 3. 抓取全球大環境與【台股大盤及亞股】關鍵數據
twii, twii_diff = get_price("^TWII")    # 台灣加權指數
nikkei, nikkei_diff = get_price("^N225") # 日經225
kospi, kospi_diff = get_price("^KS11")   # 韓國KOSPI
usd_twd, usd_diff = get_price("TWD=X")   # 美元/台幣
gold, gold_diff = get_price("GC=F")      # 黃金期貨
oil, oil_diff = get_price("BZ=F")        # 布蘭特原油
vix, vix_diff = get_price("^VIX")        # 恐慌指數

# 4. 呼叫 Gemini 幫我們寫風險警示與燈號判斷
prompt = f"""
現在是台灣時間早上 8:30，亞洲股市(日本、韓國)剛開盤。請根據以下最新數據，寫一份台股開盤前的分析報告：
【台股昨日收盤】加權指數: {twii} (漲跌 {twii_diff})
【今日亞股早盤】日經225: {nikkei} (漲跌 {nikkei_diff}) / 韓國KOSPI: {kospi} (漲跌 {kospi_diff})
【全球總經】美元/台幣: {usd_twd} / 黃金: {gold} / 原油: {oil} / VIX恐慌指數: {vix} (漲跌 {vix_diff})

請扮演資深理財專員，給予 9:00 台股開盤的預測。
回傳嚴格的 JSON 格式，不要加 ```json 標籤，只要大括號與內容：
{{
  "status_light": "🔴 紅燈 (危險)、🟡 黃燈 (警戒)、或 🟢 綠燈 (安全)",
  "status_desc": "結合日韓早盤表現，預測今日台股開盤趨勢與氣氛",
  "warning_event": "給投資人今日開盤的操作建議(例如：日股大跌請留意台股開低)"
}}
"""

try:
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    ai_text = response.text.replace("```json", "").replace("```", "").strip()
    ai_data = json.loads(ai_text)
except Exception as e:
    ai_data = {
        "status_light": "🟡 系統連線中",
        "status_desc": "AI 分析生成中...",
        "warning_event": "暫時無法取得 AI 分析，請手動留意市場波動。"
    }

# 取得今天日期，格式為 YYYY/MM/DD
today_str = datetime.now().strftime("%Y/%m/%d")

# 5. 把今天的所有數據打包
new_data = {
    "date": today_str,
    "twii": {"price": twii, "diff": twii_diff},
    "nikkei": {"price": nikkei, "diff": nikkei_diff},
    "kospi": {"price": kospi, "diff": kospi_diff},
    "usd_twd": {"price": usd_twd, "diff": usd_diff},
    "gold": {"price": gold, "diff": gold_diff},
    "oil": {"price": oil, "diff": oil_diff},
    "vix": {"price": vix, "diff": vix_diff},
    "ai_analysis": ai_data
}

# --- 歷史日記模式 ---
# 讀取舊資料，把新資料「加進去」而不是覆蓋
history_data = {}
if os.path.exists("data.json"):
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                history_data = json.loads(content)
                # 兼容處理舊版單日資料
                if "date" in history_data and isinstance(history_data.get("date"), str):
                    old_date = history_data["date"].replace("-", "/")
                    history_data = {old_date: history_data}
    except Exception as e:
        print(f"讀取舊資料失敗: {e}")

# 將今天的最新資料存入歷史紀錄中
history_data[today_str] = new_data

# 存成 data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(history_data, f, ensure_ascii=False, indent=4)
print(f"{today_str} 早上 8:30 開盤前報告更新完成，並已存入歷史檔案！")
