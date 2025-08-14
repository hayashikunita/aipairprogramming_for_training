import requests

API_URL = "http://localhost:18080"
API_KEY = "YOUR_API_KEY"

def kabusapi(path, method="GET", params=None, data=None):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": API_KEY,
    }
    url = f"{API_URL}{path}"
    response = requests.request(method, url, headers=headers, params=params, json=data)
    return response.json()

def get_symbol_price(symbol_code, exchange="1"):
    path = f"/kabusapi/board/{symbol_code}@{exchange}"
    response = kabusapi(path)
    return response['CurrentPrice'] if 'CurrentPrice' in response else None

def send_order(symbol_code, side, qty, price, exchange="1"):
    path = "/kabusapi/sendorder"
    order_data = {
        "Password": "YOUR_PASSWORD",
        "Symbol": symbol_code,
        "Exchange": exchange,
        "SecurityType": 1,
        "Side": side,
        "CashMargin": 1,
        "DelivType": 0,
        "AccountType": 2,
        "Qty": qty,
        "FrontOrderType": 20,
        "Price": price,
        "ExpireDay": 0
    }
    response = kabusapi(path, method="POST", data=order_data)
    return response

def main():
    symbol_code = "4755"  # 例: 楽天(株)の証券コード
    budget = 100000  # 投資予算
    quantity = 1     # 購入数

    current_price = get_symbol_price(symbol_code)
    if current_price and current_price * quantity <= budget:
        print(f"Buying {quantity} shares of {symbol_code} at price {current_price}")
        result = send_order(symbol_code, "2", quantity, current_price)  # "2" for buy
        print(result)
    else:
        print("Insufficient funds or price not available.")

if __name__ == "__main__":
    main()
