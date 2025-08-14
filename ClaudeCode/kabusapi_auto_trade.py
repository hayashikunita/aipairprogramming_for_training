#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本株自動売買システム - kabu STATION API版
必要な設定：
- auカブコム証券の口座開設
- kabu STATIONのインストールと起動
- APIパスワードの設定
"""

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
from dataclasses import dataclass
import configparser
import os

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TradingConfig:
    """取引設定クラス"""
    api_password: str
    base_url: str = "http://localhost:18080/kabusapi"
    max_positions: int = 10
    risk_per_trade: float = 0.02  # 1取引あたりのリスク（資金の2%）
    stop_loss_ratio: float = 0.05  # 5%の損切り
    take_profit_ratio: float = 0.10  # 10%の利確

class KabuAPI:
    """kabu STATION API クライアント"""
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.token = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """API認証"""
        try:
            url = f"{self.config.base_url}/token"
            data = {"APIPassword": self.config.api_password}
            
            response = self.session.post(url, json=data)
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get("Token")
            
            # セッションヘッダーにトークンを設定
            self.session.headers.update({"X-API-KEY": self.token})
            
            logger.info("API認証成功")
            return True
            
        except Exception as e:
            logger.error(f"API認証失敗: {e}")
            return False
    
    def get_board_info(self, symbol: str, exchange: int = 1) -> Optional[Dict]:
        """板情報取得"""
        try:
            url = f"{self.config.base_url}/board/{symbol}@{exchange}"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"板情報取得エラー {symbol}: {e}")
            return None
    
    def get_positions(self) -> List[Dict]:
        """建玉情報取得"""
        try:
            url = f"{self.config.base_url}/positions"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"建玉情報取得エラー: {e}")
            return []
    
    def get_balance(self) -> Optional[Dict]:
        """残高情報取得"""
        try:
            url = f"{self.config.base_url}/wallet/cash"
            response = self.session.get(url)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"残高情報取得エラー: {e}")
            return None
    
    def place_order(self, symbol: str, side: str, qty: int, price: float = None, 
                   order_type: int = 2, exchange: int = 1) -> Optional[str]:
        """注文発注
        Args:
            symbol: 銘柄コード
            side: '1'=売, '2'=買
            qty: 数量
            price: 価格（成行の場合はNone）
            order_type: 1=成行, 2=指値, 3=逆指値
            exchange: 市場（1=東証）
        """
        try:
            url = f"{self.config.base_url}/sendorder"
            
            order_data = {
                "Password": self.config.api_password,
                "Symbol": symbol,
                "Exchange": exchange,
                "SecurityType": 1,  # 株式
                "Side": side,
                "CashMargin": 1,  # 現物
                "DelivType": 2,   # お預け金
                "FundType": "  ",  # 空白
                "AccountType": 4,  # 特定
                "Qty": qty,
                "FrontOrderType": order_type,
                "Price": 0 if price is None else int(price),
                "ExpireDay": 0  # 当日
            }
            
            response = self.session.post(url, json=order_data)
            response.raise_for_status()
            
            result = response.json()
            order_id = result.get("OrderId")
            
            logger.info(f"注文発注成功: {symbol} {side} {qty}株 OrderID: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"注文発注エラー {symbol}: {e}")
            return None

class TechnicalAnalyzer:
    """テクニカル分析クラス"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """単純移動平均計算"""
        if len(prices) < period:
            return 0
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """RSI計算"""
        if len(prices) < period + 1:
            return 50
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

class AutoTrader:
    """自動売買システム"""
    
    def __init__(self, config: TradingConfig, symbols: List[str]):
        self.config = config
        self.symbols = symbols
        self.api = KabuAPI(config)
        self.analyzer = TechnicalAnalyzer()
        self.price_history = {symbol: [] for symbol in symbols}
        self.positions = {}
        self.running = False
    
    def start(self):
        """自動売買開始"""
        if not self.api.authenticate():
            logger.error("認証失敗のため終了")
            return
        
        self.running = True
        logger.info("自動売買開始")
        
        try:
            while self.running:
                self.trading_loop()
                time.sleep(10)  # 10秒間隔で実行
                
        except KeyboardInterrupt:
            logger.info("手動停止")
        except Exception as e:
            logger.error(f"システムエラー: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """自動売買停止"""
        self.running = False
        logger.info("自動売買停止")
    
    def trading_loop(self):
        """メインの取引ループ"""
        # 1. 建玉情報更新
        self.update_positions()
        
        # 2. 損切り・利確チェック
        self.check_exit_signals()
        
        # 3. 新規エントリーチェック
        if len(self.positions) < self.config.max_positions:
            self.check_entry_signals()
    
    def update_positions(self):
        """建玉情報更新"""
        positions = self.api.get_positions()
        current_positions = {}
        
        for pos in positions:
            symbol = pos.get("Symbol")
            if symbol:
                current_positions[symbol] = {
                    'qty': pos.get("LeavesQty", 0),
                    'price': pos.get("Price", 0),
                    'side': pos.get("Side"),
                    'pnl': pos.get("ProfitLoss", 0)
                }
        
        self.positions = current_positions
    
    def check_exit_signals(self):
        """決済シグナルチェック"""
        for symbol, position in self.positions.items():
            board = self.api.get_board_info(symbol)
            if not board:
                continue
            
            current_price = board.get("CurrentPrice", 0)
            entry_price = position['price']
            qty = position['qty']
            
            if qty == 0:
                continue
            
            # 損切り・利確判定
            if position['side'] == '2':  # 買いポジション
                pnl_ratio = (current_price - entry_price) / entry_price
                
                if pnl_ratio <= -self.config.stop_loss_ratio:
                    # 損切り
                    self.api.place_order(symbol, '1', qty, order_type=1)  # 成行売り
                    logger.info(f"損切り実行: {symbol} {pnl_ratio:.2%}")
                    
                elif pnl_ratio >= self.config.take_profit_ratio:
                    # 利確
                    self.api.place_order(symbol, '1', qty, order_type=1)  # 成行売り
                    logger.info(f"利確実行: {symbol} {pnl_ratio:.2%}")
    
    def check_entry_signals(self):
        """新規エントリーシグナルチェック"""
        for symbol in self.symbols:
            if symbol in self.positions:
                continue
            
            # 価格データ取得・蓄積
            board = self.api.get_board_info(symbol)
            if not board:
                continue
            
            current_price = board.get("CurrentPrice", 0)
            if current_price == 0:
                continue
            
            # 価格履歴更新（最大100件保持）
            self.price_history[symbol].append(current_price)
            if len(self.price_history[symbol]) > 100:
                self.price_history[symbol].pop(0)
            
            # エントリー判定
            if self.should_buy(symbol):
                self.enter_position(symbol, current_price)
    
    def should_buy(self, symbol: str) -> bool:
        """買いシグナル判定"""
        prices = self.price_history[symbol]
        
        if len(prices) < 20:
            return False
        
        # 移動平均クロス戦略
        sma_short = self.analyzer.calculate_sma(prices, 5)
        sma_long = self.analyzer.calculate_sma(prices, 20)
        
        # RSI判定
        rsi = self.analyzer.calculate_rsi(prices)
        
        # 買いシグナル: 短期移動平均が長期移動平均を上抜け & RSI < 70
        if (sma_short > sma_long and 
            len(prices) >= 2 and
            self.analyzer.calculate_sma(prices[:-1], 5) <= self.analyzer.calculate_sma(prices[:-1], 20) and
            rsi < 70):
            return True
        
        return False
    
    def enter_position(self, symbol: str, price: float):
        """新規ポジション作成"""
        # 残高チェック
        balance = self.api.get_balance()
        if not balance:
            return
        
        available_cash = balance.get("StockAccountWallet", 0)
        
        # リスク管理：資金の一定割合でポジションサイズ決定
        position_value = available_cash * self.config.risk_per_trade
        qty = int(position_value / price / 100) * 100  # 単元株調整
        
        if qty >= 100:  # 最小単位チェック
            order_id = self.api.place_order(symbol, '2', qty, price, order_type=2)  # 指値買い
            if order_id:
                logger.info(f"新規買い注文: {symbol} {qty}株 @{price}円")

def load_config(config_path: str = "config.ini") -> TradingConfig:
    """設定ファイル読み込み"""
    config = configparser.ConfigParser()
    
    if os.path.exists(config_path):
        config.read(config_path, encoding='utf-8')
    else:
        # デフォルト設定ファイル作成
        config['DEFAULT'] = {
            'api_password': 'YOUR_API_PASSWORD',
            'base_url': 'http://localhost:18080/kabusapi',
            'max_positions': '10',
            'risk_per_trade': '0.02',
            'stop_loss_ratio': '0.05',
            'take_profit_ratio': '0.10'
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
        
        logger.info(f"設定ファイル {config_path} を作成しました。パスワードを設定してください。")
        return None
    
    return TradingConfig(
        api_password=config['DEFAULT']['api_password'],
        base_url=config['DEFAULT']['base_url'],
        max_positions=int(config['DEFAULT']['max_positions']),
        risk_per_trade=float(config['DEFAULT']['risk_per_trade']),
        stop_loss_ratio=float(config['DEFAULT']['stop_loss_ratio']),
        take_profit_ratio=float(config['DEFAULT']['take_profit_ratio'])
    )

def main():
    """メイン関数"""
    # 設定読み込み
    config = load_config()
    if config is None:
        return
    
    # 監視銘柄リスト（例：東証プライム主力株）
    symbols = [
        "7203",  # トヨタ自動車
        "9984",  # ソフトバンクグループ
        "6098",  # リクルートホールディングス
        "8035",  # 東京エレクトロン
        "4063",  # 信越化学工業
        "6954",  # ファナック
        "4502",  # 武田薬品工業
        "8031",  # 三井物産
        "8058",  # 三菱商事
        "9432",  # 日本電信電話
    ]
    
    # 自動売買システム開始
    trader = AutoTrader(config, symbols)
    
    print("=== 日本株自動売買システム ===")
    print("監視銘柄数:", len(symbols))
    print("最大ポジション数:", config.max_positions)
    print("リスク設定:", f"{config.risk_per_trade:.1%}")
    print("Ctrl+C で停止\n")
    
    trader.start()

if __name__ == "__main__":
    main()