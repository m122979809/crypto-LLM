import requests
import time
import datetime
import csv
import configparser
import os

# 讀取 API Key
config = configparser.ConfigParser()
config.read('config.ini')
coinmarketcap_api_key = config['API']['coinmarketcap_api_key']

# 確保 price 目錄存在
if not os.path.exists("price"):
    os.makedirs("price")

# 取得市值前 10 大的虛擬貨幣（排除穩定幣）
def get_top_10_cryptos(api_key):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
    params = {'convert': 'USD', 'sort': 'market_cap'}
    headers = {'X-CMC_PRO_API_KEY': api_key, 'Accept': 'application/json'}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    stablecoins = {'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'LUSD', 'GUSD', 'PAX'}
    filtered_cryptos = [crypto for crypto in data['data'] if crypto['symbol'] not in stablecoins]
    
    return [crypto['symbol'] + 'USDT' for crypto in filtered_cryptos[:10]]

# 取得幣種的最早交易日期（修正 onboardDate 問題）
def get_first_trade_date(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": 1, "startTime": 0}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if isinstance(data, list) and len(data) > 0:
        return int(data[0][0])  # 第一筆 K 線的時間戳
    else:
        print(f"⚠️ 無法獲取 {symbol} 的最早交易日期，使用當前時間")
        return int(time.time() * 1000)

# 取得歷史價格並存入 CSV
def get_historical_prices(symbol):
    end_time = int(time.time() * 1000)
    start_time = get_first_trade_date(symbol)
    
    base_path = os.path.join(os.path.dirname(__file__), "../price")
    csv_filename = os.path.join(base_path, f"{symbol}_historical_prices.csv")
    
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        
        while start_time < end_time:
            params = {
                "symbol": symbol,
                "interval": "1d",
                "startTime": start_time,
                "endTime": end_time,
                "limit": 1000
            }
            
            response = requests.get("https://api.binance.com/api/v3/klines", params=params)
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                for entry in data:
                    timestamp = entry[0]
                    date = datetime.datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d')
                    writer.writerow([date, entry[1], entry[2], entry[3], entry[4], entry[5]])
                
                start_time = int(data[-1][0]) + (24 * 60 * 60 * 1000)  # 移動到下一天
                print(f"✅ {symbol} 的數據已寫入 {csv_filename}，更新到 {date}")
            else:
                print(f"⚠️ {symbol} 無法獲取更多數據")
                break

if __name__ == '__main__':
    top_10_cryptos = get_top_10_cryptos(coinmarketcap_api_key)
    for crypto in top_10_cryptos:
        get_historical_prices(crypto)

print("所有幣種的歷史數據已更新完畢！")