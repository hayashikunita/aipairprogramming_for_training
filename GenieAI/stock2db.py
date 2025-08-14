import sqlite3
import requests

API_URL = "http://localhost:18080"
API_KEY = "YOUR_API_KEY"

def kabusapi(path, method="GET", params=None):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY,
    }
    url = f"{API_URL}{path}"
    response = requests.request(method, url, headers=headers, params=params)
    return response.json()

def get_symbol_price(symbol_code, exchange="1"):
    path = f"/kabusapi/board/{symbol_code}@{exchange}"
    response = kabusapi(path)
    if 'CurrentPrice' in response:
        return response['Symbol'], response['CurrentPrice']
    return None, None

def create_database():
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_to_database(symbol, price):
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stock_prices (symbol, price) VALUES (?, ?)", (symbol, price))
    conn.commit()
    conn.close()

def main():
    create_database()
    
    symbol_code = "4755"  # 例: 楽天(株)の証券コード
    
    symbol, current_price = get_symbol_price(symbol_code)
    if symbol and current_price is not None:
        print(f"Symbol: {symbol}, Current Price: {current_price}")
        save_to_database(symbol, current_price)
        print("Data saved to database.")
    else:
        print("Price not available.")

if __name__ == "__main__":
    main()
