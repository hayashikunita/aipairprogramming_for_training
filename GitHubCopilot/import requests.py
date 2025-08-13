import requests
import json
from db_utils import init_db, save_order_to_db

# kabuステーションのAPI URL
BASE_URL = "http://localhost:18080/kabusapi"

# 1. 認証トークン取得
def get_token(api_key):
    url = f"{BASE_URL}/token"
    headers = {"Content-Type": "application/json"}
    data = {"APIPassword": api_key}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()["Token"]

# 2. 現物買い注文
def send_order(token, symbol, exchange, price, quantity, account_type=2):
    url = f"{BASE_URL}/sendorder"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": token
    }
    order_data = {
        "Password": "あなたの取引パスワード",
        "Symbol": symbol,         # 銘柄コード（例: 7203 トヨタ）
        "Exchange": exchange,     # 1: 東証, 3: 名証
        "SecurityType": 1,        # 1: 現物
        "Side": "2",              # 2: 買い
        "CashMargin": 1,          # 1: 現物
        "DelivType": 0,
        "AccountType": account_type,
        "Qty": quantity,
        "Price": price,
        "ExpireDay": 0,
        "FrontOrderType": 20      # 20: 成行, 10: 指値
    }
    response = requests.post(url, headers=headers, data=json.dumps(order_data))
    return response.json()

if __name__ == "__main__":
    # DB初期化
    init_db()
    api_key = "あなたのAPIキー"
    token = get_token(api_key)
    symbol = "7203"
    exchange = 1
    price = 0
    quantity = 100
    account_type = 2
    result = send_order(token, symbol=symbol, exchange=exchange, price=price, quantity=quantity, account_type=account_type)
    print(result)
    # DBへ保存
    save_order_to_db(symbol, exchange, price, quantity, account_type, result)