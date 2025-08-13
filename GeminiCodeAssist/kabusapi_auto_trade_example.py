import os
import sys
from kabu_s_api.kabusapi import KabusApi
from kabu_s_api.models import Symbol, Order, Side, Exchange, OrderType, TimeInForce

# --- 設定項目 ---

# 環境変数からAPIパスワードを読み込むことを強く推奨します
# 例: export API_PASSWORD="YOUR_PASSWORD"
API_PASSWORD = os.getenv("API_PASSWORD")

# 取引対象の銘柄コードと市場
TARGET_SYMBOL = "7203"  # トヨタ自動車
TARGET_EXCHANGE = Exchange.TOUSHOU # 東証

# --- ここまで ---

def main():
    """
    メインの処理を実行する関数
    """
    if not API_PASSWORD:
        print("エラー: 環境変数 'API_PASSWORD' が設定されていません。")
        sys.exit(1)

    # is_prod=Trueで本番環境に接続
    api = KabusApi(is_prod=True)

    print("1. APIトークンを取得します...")
    try:
        api.token.get_token(api_password=API_PASSWORD)
        print("トークンの取得に成功しました。")
    except Exception as e:
        print(f"トークンの取得に失敗しました: {e}")
        sys.exit(1)

    # 2. 株価を取得する
    print(f"\n2. 銘柄コード {TARGET_SYMBOL} の現在値を取得します...")
    try:
        symbol_info = api.symbol.get_symbol(symbol_code=TARGET_SYMBOL, exchange=TARGET_EXCHANGE)
        current_price = symbol_info.current_price
        if current_price is None:
            print("現在値が取得できませんでした。市場が動いていない可能性があります。")
            sys.exit(1)
        print(f"現在の株価: {current_price} 円")
    except Exception as e:
        print(f"株価の取得に失敗しました: {e}")
        sys.exit(1)

    # 3. 取引ロジック（非常にシンプルな例）
    # ここに本格的な取引戦略を実装します
    buy_trigger_price = 3500.0  # この価格以下なら買うというトリガー（例）
    print(f"\n3. 取引ロジックを実行します (トリガー価格: {buy_trigger_price}円)")

    if current_price <= buy_trigger_price:
        print(f"株価({current_price}円)がトリガー価格({buy_trigger_price}円)以下のため、買い注文を試みます。")
        
        # 4. 買い注文を出す
        try:
            order = Order(
                side=Side.BUY,
                symbol_code=TARGET_SYMBOL,
                exchange=TARGET_EXCHANGE,
                qty=100,  # 注文株数（単元株数にご注意ください）
                order_type=OrderType.MO, # 成行注文
                time_in_force=TimeInForce.FAS, # Fill and Store (執行されなければキャンセル)
            )
            
            print(f"\n4. 買い注文（成行・100株）を送信します...")
            order_id = api.sendorder.post_sendorder(api_password=API_PASSWORD, order=order)
            print(f"注文が正常に送信されました。注文ID: {order_id.order_id}")

        except Exception as e:
            print(f"注文の送信に失敗しました: {e}")
    else:
        print(f"株価({current_price}円)がトリガー価格({buy_trigger_price}円)より高いため、今回は注文を見送ります。")


if __name__ == "__main__":
    main()