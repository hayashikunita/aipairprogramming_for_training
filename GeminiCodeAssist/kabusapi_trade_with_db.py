import os
import sys
import sqlite3
from datetime import datetime
from kabu_s_api.kabusapi import KabusApi
from kabu_s_api.models import Order, Side, Exchange, OrderType, TimeInForce

# --- 設定項目 ---
DB_NAME = "trade_history.db"
API_PASSWORD = os.getenv("API_PASSWORD")
TARGET_SYMBOL = "7203"  # トヨタ自動車
TARGET_EXCHANGE = Exchange.TOUSHOU # 東証

# --- DB関連の関数 ---

def setup_database():
    """データベースファイルとテーブルを準備する"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # trade_activityテーブルが存在しない場合のみ作成する
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trade_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_time TEXT NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            current_price REAL,
            trigger_price REAL,
            action TEXT NOT NULL,
            order_id TEXT,
            status TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"データベース '{DB_NAME}' の準備が完了しました。")

def log_to_db(log_data):
    """辞書形式のデータをDBに記録する"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trade_activity (
            execution_time, symbol, exchange, current_price, trigger_price,
            action, order_id, status, details
        ) VALUES (:execution_time, :symbol, :exchange, :current_price, :trigger_price,
                  :action, :order_id, :status, :details)
    """, log_data)
    conn.commit()
    conn.close()
    print("取引活動をデータベースに記録しました。")

# --- メイン処理 ---

def main():
    """メインの処理を実行する関数"""
    # ログ用のデータを保持する辞書を初期化
    log_data = {
        "execution_time": datetime.now().isoformat(),
        "symbol": TARGET_SYMBOL,
        "exchange": TARGET_EXCHANGE.value, # Enumの値を文字列として保存
        "current_price": None,
        "trigger_price": None,
        "action": "START",
        "order_id": None,
        "status": "ERROR", # デフォルトはエラーとし、成功時に上書きする
        "details": ""
    }

    if not API_PASSWORD:
        log_data["details"] = "環境変数 'API_PASSWORD' が設定されていません。"
        print(f"エラー: {log_data['details']}")
        log_to_db(log_data) # 失敗ログもDBに残す
        sys.exit(1)

    try:
        api = KabusApi(is_prod=True)

        print("1. APIトークンを取得します...")
        api.token.get_token(api_password=API_PASSWORD)
        print("トークンの取得に成功しました。")

        print(f"\n2. 銘柄コード {TARGET_SYMBOL} の現在値を取得します...")
        symbol_info = api.symbol.get_symbol(symbol_code=TARGET_SYMBOL, exchange=TARGET_EXCHANGE)
        current_price = symbol_info.current_price
        log_data["current_price"] = current_price

        if current_price is None:
            raise RuntimeError("現在値が取得できませんでした。市場が動いていない可能性があります。")

        print(f"現在の株価: {current_price} 円")

        buy_trigger_price = 3500.0
        log_data["trigger_price"] = buy_trigger_price
        print(f"\n3. 取引ロジックを実行します (トリガー価格: {buy_trigger_price}円)")

        if current_price <= buy_trigger_price:
            log_data["action"] = "ATTEMPT_BUY"
            print(f"株価({current_price}円)がトリガー価格({buy_trigger_price}円)以下のため、買い注文を試みます。")

            order = Order(side=Side.BUY, symbol_code=TARGET_SYMBOL, exchange=TARGET_EXCHANGE, qty=100, order_type=OrderType.MO, time_in_force=TimeInForce.FAS)
            print(f"\n4. 買い注文（成行・100株）を送信します...")
            order_response = api.sendorder.post_sendorder(api_password=API_PASSWORD, order=order)
            
            log_data["order_id"] = order_response.order_id
            log_data["status"] = "SUCCESS"
            log_data["details"] = f"注文が正常に送信されました。注文ID: {order_response.order_id}"
            print(log_data["details"])
        else:
            log_data["action"] = "SKIP"
            log_data["status"] = "SUCCESS"
            log_data["details"] = f"株価({current_price}円)がトリガー価格({buy_trigger_price}円)より高いため、注文を見送りました。"
            print(log_data["details"])

    except Exception as e:
        # 発生したエラーをログに記録
        log_data["details"] = f"処理中にエラーが発生しました: {e}"
        print(log_data["details"])

    finally:
        # 処理が成功しても失敗しても、最後に必ずログをDBに書き込む
        log_to_db(log_data)

if __name__ == "__main__":
    setup_database()
    main()