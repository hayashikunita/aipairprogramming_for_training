import sqlite3

def init_db(db_path="trade_orders.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            exchange INTEGER,
            price REAL,
            quantity INTEGER,
            account_type INTEGER,
            order_result TEXT
        )
    ''')
    conn.commit()
    conn.close()

# DBへ注文情報を保存
def save_order_to_db(symbol, exchange, price, quantity, account_type, order_result, db_path="trade_orders.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (symbol, exchange, price, quantity, account_type, order_result)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (symbol, exchange, price, quantity, account_type, str(order_result)))
    conn.commit()
    conn.close()
