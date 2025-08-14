#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本株自動売買システム - バックテスト・分析ツール
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import yfinance as yf
from typing import List, Dict, Tuple
import json
import logging

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'

logger = logging.getLogger(__name__)

class BacktestEngine:
    """バックテストエンジン"""
    
    def __init__(self, initial_capital: float = 1000000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trade_log = []
        self.equity_curve = []
        self.max_positions = 10
        self.stop_loss_ratio = 0.05
        self.take_profit_ratio = 0.10
        self.risk_per_trade = 0.02
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """単純移動平均計算"""
        return prices.rolling(window=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI計算"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """売買シグナル生成"""
        # テクニカル指標計算
        data['SMA5'] = self.calculate_sma(data['Close'], 5)
        data['SMA20'] = self.calculate_sma(data['Close'], 20)
        data['RSI'] = self.calculate_rsi(data['Close'])
        
        # 買いシグナル：短期移動平均が長期移動平均を上抜け & RSI < 70
        data['Buy_Signal'] = (
            (data['SMA5'] > data['SMA20']) &
            (data['SMA5'].shift(1) <= data['SMA20'].shift(1)) &
            (data['RSI'] < 70)
        )
        
        return data
    
    def backtest_symbol(self, symbol: str, data: pd.DataFrame) -> List[Dict]:
        """個別銘柄のバックテスト"""
        trades = []
        data = self.generate_signals(data)
        position = None
        
        for i, row in data.iterrows():
            if pd.isna(row['SMA5']) or pd.isna(row['SMA20']):
                continue
            
            # 買いシグナルチェック
            if row['Buy_Signal'] and position is None:
                # ポジションサイズ計算
                position_value = self.capital * self.risk_per_trade
                qty = int(position_value / row['Close'] / 100) * 100  # 単元株調整
                
                if qty >= 100:
                    position = {
                        'symbol': symbol,
                        'entry_date': i,
                        'entry_price': row['Close'],
                        'qty': qty,
                        'value': qty * row['Close']
                    }
            
            # ポジション保持中の損切り・利確チェック
            elif position is not None:
                entry_price = position['entry_price']
                current_price = row['Close']
                pnl_ratio = (current_price - entry_price) / entry_price
                
                exit_reason = None
                if pnl_ratio <= -self.stop_loss_ratio:
                    exit_reason = "stop_loss"
                elif pnl_ratio >= self.take_profit_ratio:
                    exit_reason = "take_profit"
                
                if exit_reason:
                    trade = {
                        'symbol': symbol,
                        'entry_date': position['entry_date'],
                        'exit_date': i,
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'qty': position['qty'],
                        'pnl': (current_price - entry_price) * position['qty'],
                        'pnl_ratio': pnl_ratio,
                        'days_held': (i - position['entry_date']).days,
                        'exit_reason': exit_reason
                    }
                    trades.append(trade)
                    position = None
        
        # 未決済ポジションの処理
        if position is not None:
            final_price = data['Close'].iloc[-1]
            pnl_ratio = (final_price - position['entry_price']) / position['entry_price']
            trade = {
                'symbol': symbol,
                'entry_date': position['entry_date'],
                'exit_date': data.index[-1],
                'entry_price': position['entry_price'],
                'exit_price': final_price,
                'qty': position['qty'],
                'pnl': (final_price - position['entry_price']) * position['qty'],
                'pnl_ratio': pnl_ratio,
                'days_held': (data.index[-1] - position['entry_date']).days,
                'exit_reason': 'end_of_period'
            }
            trades.append(trade)
        
        return trades
    
    def run_backtest(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """バックテスト実行"""
        all_trades = []
        
        for symbol in symbols:
            try:
                # Yahoo Financeから株価データ取得（東証銘柄は.T追加）
                ticker = f"{symbol}.T"
                stock = yf.Ticker(ticker)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    logger.warning(f"データ取得失敗: {symbol}")
                    continue
                
                # バックテスト実行
                trades = self.backtest_symbol(symbol, data)
                all_trades.extend(trades)
                
                logger.info(f"{symbol}: {len(trades)}件の取引")
                
            except Exception as e:
                logger.error(f"エラー {symbol}: {e}")
                continue
        
        return self.analyze_results(all_trades)
    
    def analyze_results(self, trades: List[Dict]) -> Dict:
        """バックテスト結果分析"""
        if not trades:
            return {"error": "取引データがありません"}
        
        df = pd.DataFrame(trades)
        
        # 基本統計
        total_trades = len(df)
        winning_trades = len(df[df['pnl'] > 0])
        losing_trades = len(df[df['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_pnl = df['pnl'].sum()
        avg_pnl = df['pnl'].mean()
        avg_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # リスク指標
        profit_factor = abs(df[df['pnl'] > 0]['pnl'].sum() / df[df['pnl'] < 0]['pnl'].sum()) if losing_trades > 0 else float('inf')
        avg_holding_days = df['days_held'].mean()
        
        # 最大ドローダウン計算
        cumulative_pnl = df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        results = {
            "総取引数": total_trades,
            "勝率": f"{win_rate:.1%}",
            "勝ちトレード": winning_trades,
            "負けトレード": losing_trades,
            "総損益": f"¥{total_pnl:,.0f}",
            "平均損益": f"¥{avg_pnl:,.0f}",
            "平均利益": f"¥{avg_win:,.0f}",
            "平均損失": f"¥{avg_loss:,.0f}",
            "プロフィットファクター": f"{profit_factor:.2f}",
            "平均保有日数": f"{avg_holding_days:.1f}日",
            "最大ドローダウン": f"¥{max_drawdown:,.0f}",
            "リターン": f"{total_pnl/self.initial_capital:.1%}",
            "取引データ": df
        }
        
        return results

class PerformanceAnalyzer:
    """パフォーマンス分析・可視化"""
    
    @staticmethod
    def plot_equity_curve(trades_df: pd.DataFrame, title: str = "資産推移"):
        """資産推移グラフ"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 累積損益
        cumulative_pnl = trades_df['pnl'].cumsum()
        dates = pd.to_datetime(trades_df['exit_date'])
        
        ax1.plot(dates, cumulative_pnl, linewidth=2, color='blue')
        ax1.set_title(f"{title} - 累積損益", fontsize=14)
        ax1.set_ylabel("損益 (円)")
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        # ドローダウン
        running_max = cumulative_pnl.expanding().max()
        drawdown = cumulative_pnl - running_max
        
        ax2.fill_between(dates, drawdown, 0, color='red', alpha=0.3)
        ax2.plot(dates, drawdown, color='red')
        ax2.set_title("ドローダウン", fontsize=14)
        ax2.set_ylabel("ドローダウン (円)")
        ax2.set_xlabel("日付")
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def plot_trade_analysis(trades_df: pd.DataFrame):
        """取引分析グラフ"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # 1. 損益分布
        ax1.hist(trades_df['pnl'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        ax1.set_title("損益分布", fontsize=12)
        ax1.set_xlabel("損益 (円)")
        ax1.set_ylabel("取引数")
        ax1.grid(True, alpha=0.3)
        
        # 2. 保有日数分布
        ax2.hist(trades_df['days_held'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_title("保有日数分布", fontsize=12)
        ax2.set_xlabel("保有日数")
        ax2.set_ylabel("取引数")
        ax2.grid(True, alpha=0.3)
        
        # 3. 月別損益
        trades_df['exit_month'] = pd.to_datetime(trades_df['exit_date']).dt.to_period('M')
        monthly_pnl = trades_df.groupby('exit_month')['pnl'].sum()
        
        colors = ['green' if x >= 0 else 'red' for x in monthly_pnl.values]
        ax3.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
        ax3.set_title("月別損益", fontsize=12)
        ax3.set_xlabel("月")
        ax3.set_ylabel("損益 (円)")
        ax3.set_xticks(range(0, len(monthly_pnl), max(1, len(monthly_pnl)//12)))
        ax3.grid(True, alpha=0.3)
        
        # 4. 銘柄別成績
        symbol_performance = trades_df.groupby('symbol').agg({
            'pnl': 'sum',
            'symbol': 'count'
        }).rename(columns={'symbol': 'count'}).sort_values('pnl', ascending=True)
        
        top_symbols = symbol_performance.tail(10)  # 上位10銘柄
        colors = ['green' if x >= 0 else 'red' for x in top_symbols['pnl'].values]
        
        ax4.barh(range(len(top_symbols)), top_symbols['pnl'].values, color=colors, alpha=0.7)
        ax4.set_title("銘柄別損益 (上位10)", fontsize=12)
        ax4.set_xlabel("損益 (円)")
        ax4.set_yticks(range(len(top_symbols)))
        ax4.set_yticklabels(top_symbols.index)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def generate_report(results: Dict) -> str:
        """レポート生成"""
        report = f"""
=== バックテスト結果レポート ===
生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【基本統計】
総取引数: {results['総取引数']}
勝率: {results['勝率']}
勝ちトレード: {results['勝ちトレード']}
負けトレード: {results['負けトレード']}

【損益】
総損益: {results['総損益']}
平均損益: {results['平均損益']}
平均利益: {results['平均利益']}
平均損失: {results['平均損失']}
リターン: {results['リターン']}

【リスク指標】
プロフィットファクター: {results['プロフィットファクター']}
平均保有日数: {results['平均保有日数']}
最大ドローダウン: {results['最大ドローダウン']}

【評価】"""
        
        # 簡単な評価コメント
        trades_df = results['取引データ']
        win_rate = float(results['勝率'].strip('%')) / 100
        pf = float(results['プロフィットファクター'])
        
        if win_rate >= 0.6 and pf >= 1.5:
            report += "\n✅ 優秀な戦略です。実運用を検討できます。"
        elif win_rate >= 0.5 and pf >= 1.2:
            report += "\n⚠️  まずまずの戦略です。パラメータ調整を検討してください。"
        else:
            report += "\n❌ 改善が必要な戦略です。ロジックの見直しをお勧めします。"
        
        return report

def run_sample_backtest():
    """サンプルバックテスト実行"""
    print("=== 日本株自動売買システム バックテスト ===\n")
    
    # テスト対象銘柄
    symbols = [
        "7203",  # トヨタ自動車
        "9984",  # ソフトバンクグループ
        "6098",  # リクルートHD
        "8035",  # 東京エレクトロン
        "4063"   # 信越化学
    ]
    
    # バックテストエンジン初期化
    engine = BacktestEngine(initial_capital=1000000)  # 100万円
    
    # バックテスト期間設定
    start_date = "2022-01-01"
    end_date = "2024-01-01"
    
    print(f"期間: {start_date} ～ {end_date}")
    print(f"銘柄数: {len(symbols)}")
    print(f"初期資金: ¥{engine.initial_capital:,}")
    print("取引ロジック: 移動平均クロス + RSIフィルター\n")
    
    # バックテスト実行
    print("バックテスト実行中...")
    results = engine.run_backtest(symbols, start_date, end_date)
    
    if "error" in results:
        print(f"エラー: {results['error']}")
        return
    
    # 結果表示
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(results)
    print(report)
    
    # グラフ表示
    trades_df = results['取引データ']
    if len(trades_df) > 0:
        print(f"\n取引詳細: {len(trades_df)}件")
        print(trades_df[['symbol', 'entry_date', 'exit_date', 'pnl', 'pnl_ratio', 'exit_reason']].head(10))
        
        # 可視化
        try:
            analyzer.plot_equity_curve(trades_df, "移動平均クロス戦略")
            analyzer.plot_trade_analysis(trades_df)
        except Exception as e:
            print(f"グラフ表示エラー: {e}")
    
    return results

def optimize_parameters():
    """パラメータ最適化"""
    print("=== パラメータ最適化 ===\n")
    
    symbols = ["7203", "9984", "6098"]  # 主要3銘柄
    start_date = "2022-01-01"
    end_date = "2024-01-01"
    
    # 最適化対象パラメータ
    sma_short_range = [3, 5, 7]
    sma_long_range = [15, 20, 25]
    rsi_threshold_range = [60, 70, 80]
    
    best_result = None
    best_params = None
    best_profit = -float('inf')
    
    total_combinations = len(sma_short_range) * len(sma_long_range) * len(rsi_threshold_range)
    current = 0
    
    for short in sma_short_range:
        for long in sma_long_range:
            for rsi_threshold in rsi_threshold_range:
                if short >= long:  # 短期 >= 長期は無効
                    continue
                
                current += 1
                print(f"進捗: {current}/{total_combinations} - SMA({short},{long}), RSI<{rsi_threshold}")
                
                # カスタムバックテストエンジン
                engine = OptimizedBacktestEngine(
                    sma_short=short,
                    sma_long=long, 
                    rsi_threshold=rsi_threshold
                )
                
                try:
                    results = engine.run_backtest(symbols, start_date, end_date)
                    if "error" not in results:
                        total_pnl = results['取引データ']['pnl'].sum()
                        
                        if total_pnl > best_profit:
                            best_profit = total_pnl
                            best_params = (short, long, rsi_threshold)
                            best_result = results
                            
                except Exception as e:
                    continue
    
    # 最適結果表示
    if best_result:
        print(f"\n=== 最適パラメータ ===")
        print(f"短期移動平均: {best_params[0]}日")
        print(f"長期移動平均: {best_params[1]}日")
        print(f"RSI閾値: {best_params[2]}")
        print(f"最適化総損益: ¥{best_profit:,.0f}")
        
        analyzer = PerformanceAnalyzer()
        report = analyzer.generate_report(best_result)
        print(report)
        
    return best_params, best_result

class OptimizedBacktestEngine(BacktestEngine):
    """最適化用バックテストエンジン"""
    
    def __init__(self, sma_short=5, sma_long=20, rsi_threshold=70, **kwargs):
        super().__init__(**kwargs)
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.rsi_threshold = rsi_threshold
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """カスタマイズされたシグナル生成"""
        data[f'SMA{self.sma_short}'] = self.calculate_sma(data['Close'], self.sma_short)
        data[f'SMA{self.sma_long}'] = self.calculate_sma(data['Close'], self.sma_long)
        data['RSI'] = self.calculate_rsi(data['Close'])
        
        # 買いシグナル
        data['Buy_Signal'] = (
            (data[f'SMA{self.sma_short}'] > data[f'SMA{self.sma_long}']) &
            (data[f'SMA{self.sma_short}'].shift(1) <= data[f'SMA{self.sma_long}'].shift(1)) &
            (data['RSI'] < self.rsi_threshold)
        )
        
        return data

def save_results_to_json(results: Dict, filename: str = None):
    """結果をJSONファイルに保存"""
    if filename is None:
        filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # DataFrameをdict形式に変換
    save_data = results.copy()
    if '取引データ' in save_data:
        save_data['取引データ'] = save_data['取引データ'].to_dict('records')
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"結果を {filename} に保存しました。")

if __name__ == "__main__":
    # メニュー表示
    print("=== 日本株自動売買システム - バックテスト・分析ツール ===")
    print("1. サンプルバックテスト実行")
    print("2. パラメータ最適化")
    print("3. 終了")
    
    choice = input("\n選択してください (1-3): ")
    
    if choice == "1":
        results = run_sample_backtest()
        if results and "error" not in results:
            save_choice = input("\n結果をJSONファイルに保存しますか？ (y/n): ")
            if save_choice.lower() == 'y':
                save_results_to_json(results)
    
    elif choice == "2":
        best_params, best_result = optimize_parameters()
        if best_result:
            save_choice = input("\n最適化結果をJSONファイルに保存しますか？ (y/n): ")
            if save_choice.lower() == 'y':
                save_results_to_json(best_result, "optimized_backtest_results.json")
    
    elif choice == "3":
        print("終了します。")
    
    else:
        print("無効な選択です。")