import os
import json
import yfinance as yf
from google import genai
from datetime import datetime, timedelta

# 1. 取得 API 鑰匙
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. 定義抓價工具
def get_price(ticker):
    try:
        hist = yf.Ticker(ticker).history(period="2d")
        curr = round(hist['Close'].iloc[-1], 2)
        prev = round(hist['Close'].iloc[-2], 2)
        diff = round(curr - prev, 2)
        return curr, diff
    except:
        return 0, 0

# 3. 抓取大盤、全球數據與美國三大指數
twii, twii_diff = get_price("^TWII")
nikkei, nikkei_diff = get_price("^N225")
kospi, kospi_diff = get_price("^KS11")
usd_twd, usd_diff = get_price("TWD=X")
gold, gold_diff = get_price("GC=F")
oil, oil_diff = get_price("BZ=F")
vix, vix_diff = get_price("^VIX")
dow, dow_diff = get_price("^DJI")
sp500, sp500_diff = get_price("^GSPC")
nasdaq, nasdaq_diff = get_price("^IXIC")

yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")

# 4. 呼叫 Gemini 產出全真實分析 (加入強制數量指令)
prompt = f"""
現在是台灣時間早上 8:30，亞洲股市剛開盤。請根據以下真實最新數據，寫一份台股全方位分析報告：
【全球與大盤數據】
加權指數: {twii} (漲跌 {twii_diff}) 
道瓊: {dow} / 標普500: {sp500} / 那斯達克: {nasdaq}
日經: {nikkei} / 韓國: {kospi} / 美元台幣: {usd_twd} / VIX: {vix}

請回傳嚴格的 JSON 格式 (絕對不要加 ```json 標記，直接從大括號開始)：
{{
  "status_light": "🔴 紅燈 (危險)、🟡 黃燈 (警戒)、或 🟢 綠燈 (安全)",
  "status_desc": "今日台股大盤趨勢預測",
  "warning_event": "今日大盤開盤操作建議",
  "usMarket": {{
    "events": "根據上述道瓊、標普、那斯達克的漲跌，一句話解說昨晚美股對今日台股的影響"
  }},
  "twFlow": {{
    "conclusion": "一句話總結今日外資與投信可能的佈局方向",
    "foreign": "預估買超或賣超",
    "trust": "預估買超或賣超"
  }},
  "dark_horses": [
    {{ "name": "股票名稱與代號", "price": "當前位階", "reason": "為什麼今天是黑馬", "sector": "產業", "sustain": "延續性判斷" }}
    // ⚠️ 嚴格指令：請務必給出【剛好 5 檔】不同的黑馬股，不可多也不可少！
  ],
  "intraday_guide": [
    {{ "time": "09:30 早盤確認", "title": "早盤判讀", "desc": "開盤要觀察什麼指標" }},
    {{ "time": "10:30 盤中轉折", "title": "盤中確認", "desc": "趨勢確認方法" }},
    {{ "time": "12:30 尾盤佈局", "title": "尾盤追蹤", "desc": "中尾盤操作建議" }}
  ],
  "gurus": {{
    "buffett": {{ "name": "華倫・巴菲特 (長抱安心型)", "desc": "以巴菲特價值投資邏輯，今日適合買進的防禦型股票", "stocks": [
      // ⚠️ 嚴格指令：請務必給出【剛好 3 檔】股票！
      {{ "name": "代號 名稱", "price": "位階", "score": 90, "reason": "推薦原因" }}
    ] }},
    "lynch": {{ "name": "彼得・林區 (抓爆發成長型)", "desc": "以成長股邏輯，今日具備爆發力的股票", "stocks": [
      // ⚠️ 嚴格指令：請務必給出【剛好 3 檔】股票！
    ] }},
    "graham": {{ "name": "班傑明・葛拉漢 (撿便宜安全牌)", "desc": "以撿便宜邏輯，今日被低估的股票", "stocks": [
      // ⚠️ 嚴格指令：請務必給出【剛好 3 檔】股票！
    ] }}
  }},
  "prediction_review": {{
    "date": "{yesterday_str}",
    "prediction": "預測昨日大盤可能的走勢",
    "actual": "昨日大盤實際收盤狀況({twii_diff}點)",
    "accurate": true,
    "gap": "命中 / 看錯",
    "detail": "檢討原因"
  }}
}}
"""

try:
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    ai_text = response.text.replace("```json", "").replace("```", "").strip()
    ai_data = json.loads(ai_text)
except Exception as e:
    print("AI 生成失敗:", e)
    ai_data = {}

# 5. 整理並存檔
today_str = datetime.now().strftime("%Y/%m/%d")

new_data = {
    "date": today_str,
    "twii": {"price": twii, "diff": twii_diff},
    "nikkei": {"price": nikkei, "diff": nikkei_diff},
    "kospi": {"price": kospi, "diff": kospi_diff},
    "usd_twd": {"price": usd_twd, "diff": usd_diff},
    "gold": {"price": gold, "diff": gold_diff},
    "oil": {"price": oil, "diff": oil_diff},
    "vix": {"price": vix, "diff": vix_diff},
    "usMarket": {
        "dow": f"{dow} ({'+' if dow_diff > 0 else ''}{dow_diff})",
        "sp500": f"{sp500} ({'+' if sp500_diff > 0 else ''}{sp500_diff})",
        "nasdaq": f"{nasdaq} ({'+' if nasdaq_diff > 0 else ''}{nasdaq_diff})",
        "events": ai_data.get("usMarket", {}).get("events", "等待 AI 判斷中")
    },
    "twFlow": ai_data.get("twFlow", {"conclusion": "等待更新", "foreign": "未知", "trust": "未知"}),
    "ai_analysis": {
        "status_light": ai_data.get("status_light", "⚪ 系統連線中"),
        "status_desc": ai_data.get("status_desc", "AI 正在分析中..."),
        "warning_event": ai_data.get("warning_event", "等待分析")
    },
    "dark_horses": ai_data.get("dark_horses", []),
    "intraday_guide": ai_data.get("intraday_guide", []),
    "gurus": ai_data.get("gurus", {}),
    "prediction_review": ai_data.get("prediction_review", {})
}

history_data = {}
if os.path.exists("data.json"):
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                history_data = json.loads(content)
                if "date" in history_data and isinstance(history_data.get("date"), str):
                    history_data = {history_data["date"].replace("-", "/"): history_data}
    except Exception as e:
        pass

history_data[today_str] = new_data

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(history_data, f, ensure_ascii=False, indent=4)
print(f"{today_str} 數量強制修正版更新完成！")
