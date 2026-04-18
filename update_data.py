import os
import json
import yfinance as yf
from google import genai

# 1. 拿出我們藏在 GitHub 保險箱的鑰匙
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. 抓取真實數據 (這裡以抓取台積電收盤價為例)
tsmc = yf.Ticker("2330.TW")
hist = tsmc.history(period="1d")
close_price = round(hist['Close'].iloc[-1], 2)

# 3. 呼叫 Gemini 幫我們寫分析 (使用最新的 Flash 模型，速度快且免費額度高)
prompt = f"台積電今天收盤價是 {close_price}。請扮演一位理財專員，用一句新手能懂的白話文，評論一下這個價格。"
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=prompt,
)

# 4. 把 Gemini 寫好的內容，打包成 JSON 檔案 (供前端網頁讀取)
output_data = {
    "date": str(hist.index[-1].date()),
    "tsmc_price": close_price,
    "analysis": response.text
}

# 存成 data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=4)
print("資料更新完成！")
