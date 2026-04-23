import yfinance as yf
import json
import os
from datetime import datetime
import pytz

def get_stock_data(ticker_symbol, include_ohlc=False):
    """
    負責向 Yahoo Finance 索取最新金融報價的函數
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 抓取近 5 天資料，確保能避開假日拿到最新交易日
        hist = ticker.history(period="5d")
        
        if len(hist) >= 2:
            latest = hist.iloc[-1]
            previous = hist.iloc[-2]
            
            # 收盤價與漲跌點數
            close_price = round(latest['Close'], 2)
            diff = round(close_price - previous['Close'], 2)
            
            # 加上正負號格式化
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            
            result = {
                "price": str(close_price),
                "diff": diff_str
            }
            
            # 如果是台股大盤，額外抓取開、高、低
            if include_ohlc:
                result["open"] = str(round(latest['Open'], 2))
                result["high"] = str(round(latest['High'], 2))
                result["low"] = str(round(latest['Low'], 2))
                
            return result
        return None
    except Exception as e:
        print(f"抓取 {ticker_symbol} 失敗: {e}")
        return None

def main():
    # 1. 設定為台灣時間
    tw_tz = pytz.timezone('Asia/Taipei')
    date_str = datetime.now(tw_tz).strftime('%Y/%m/%d')
    print(f"開始執行抓取任務，今日日期: {date_str}")
    
    # 2. 讀取現有的 data.json 檔案 (為了保留過去的歷史紀錄)
    file_path = 'data.json'
    all_data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except Exception as e:
            print(f"讀取舊資料失敗: {e}")
            
    # 確保今天的資料節點存在
    if date_str not in all_data:
        all_data[date_str] = {}

    # 3. 抓取全球金融大環境數據 (自動寫入或更新當天節點)
    print("正在抓取 台股大盤(含開高低收)...")
    twii_data = get_stock_data("^TWII", include_ohlc=True)
    if twii_data: all_data[date_str]["twii"] = twii_data
    
    print("正在抓取 日經、韓國、恐慌指數...")
    if nikkei := get_stock_data("^N225"): all_data[date_str]["nikkei"] = nikkei
    if kospi := get_stock_data("^KS11"): all_data[date_str]["kospi"] = kospi
    if vix := get_stock_data("^VIX"): all_data[date_str]["vix"] = vix
    
    print("正在抓取 匯率與原物料(黃金/原油)...")
    if usd_twd := get_stock_data("TWD=X"): all_data[date_str]["usd_twd"] = usd_twd
    if gold := get_stock_data("GC=F"): all_data[date_str]["gold"] = gold
    if oil := get_stock_data("CL=F"): all_data[date_str]["oil"] = oil

    # 4. 將合併後的最新數據寫回 data.json
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print("✅ 資料更新成功！開高低收與國際指數已寫入 data.json。")

if __name__ == "__main__":
    main()
