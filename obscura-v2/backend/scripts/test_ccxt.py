#!/usr/bin/env python3
"""
Test script for CCXT integration
Run with: python scripts/test_ccxt.py

For testing with API keys:
  python scripts/test_ccxt.py --api-key YOUR_KEY --api-secret YOUR_SECRET

This script tests:
1. Public API (no auth) - fetch tickers, markets
2. Private API (with auth) - fetch trades, balance (if keys provided)
3. PnL Calculation - calculate realized PnL and reputation score

NOTE: In production, API keys are stored via Citadel/Nillion and retrieved
when needed. This test script accepts keys directly for development/testing.
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Parse command line arguments for API keys
parser = argparse.ArgumentParser(description='Test CCXT integration')
parser.add_argument('--api-key', help='Binance API key')
parser.add_argument('--api-secret', help='Binance API secret')
parser.add_argument('--testnet', action='store_true', default=True, help='Use testnet/demo mode')
parser.add_argument('--demo', action='store_true', default=True, help='Use demo trading (demo-api.binance.com)')
args, _ = parser.parse_known_args()

# Override env vars with command line args
if args.api_key:
    os.environ['BINANCE_API_KEY'] = args.api_key
if args.api_secret:
    os.environ['BINANCE_API_SECRET'] = args.api_secret


# =============================================================================
# PnL Calculator Classes (inline for testing)
# =============================================================================

@dataclass
class TradeExecution:
    """Represents a single trade execution (fill)."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: Decimal
    price: Decimal
    fee: Decimal
    timestamp: int
    platform: str = "spot"


@dataclass
class ClosedTrade:
    """Represents a completed round-trip trade (Entry + Exit)."""
    symbol: str
    entry_date: datetime
    exit_date: datetime
    duration_seconds: float
    side: str  # 'long' or 'short'
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    fee: Decimal
    net_pnl: Decimal
    roi_percentage: float


@dataclass
class ReputationScore:
    """Trader reputation metrics."""
    trader_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_usd: Decimal
    profit_factor: float
    average_roi: float
    score: float  # 0-100
    generated_at: datetime = field(default_factory=datetime.utcnow)


class PnLCalculator:
    """
    Calculates PnL and Reputation Scores using FIFO accounting.
    """

    def __init__(self):
        self.positions: Dict[str, List[Dict[str, Any]]] = {}

    def calculate_from_ccxt_trades(self, trades: List[dict], trader_id: str = "test_user") -> ReputationScore:
        """
        Calculate performance metrics from CCXT trade format.
        
        Args:
            trades: List of trade dicts from ccxt.fetch_my_trades()
            trader_id: ID of the trader
            
        Returns:
            ReputationScore object
        """
        # Convert CCXT format to TradeExecution objects
        executions = []
        for t in trades:
            try:
                fee_cost = t.get('fee', {}).get('cost', 0) or 0
                executions.append(TradeExecution(
                    id=str(t.get('id', '')),
                    symbol=t.get('symbol', ''),
                    side=t.get('side', '').lower(),
                    quantity=Decimal(str(t.get('amount', 0))),
                    price=Decimal(str(t.get('price', 0))),
                    fee=Decimal(str(fee_cost)),
                    timestamp=t.get('timestamp', 0),
                    platform="spot"
                ))
            except Exception as e:
                print(f"   ⚠️  Skipping invalid trade: {e}")
                
        # Sort by timestamp
        executions.sort(key=lambda x: x.timestamp)
        
        # Process trades to generate closed positions
        closed_trades = self._process_executions(executions)
        
        # Calculate metrics
        return self._calculate_metrics(closed_trades, trader_id), closed_trades

    def _process_executions(self, executions: List[TradeExecution]) -> List[ClosedTrade]:
        """Process executions using FIFO to generate closed trades."""
        closed_trades = []
        self.positions = {}

        for exec in executions:
            symbol = exec.symbol
            if symbol not in self.positions:
                self.positions[symbol] = []
            
            open_lots = self.positions[symbol]
            remaining_qty = exec.quantity
            
            while remaining_qty > 0 and open_lots:
                oldest_lot = open_lots[0]
                is_closing = (oldest_lot['side'] != exec.side)
                
                if not is_closing:
                    break
                
                match_qty = min(remaining_qty, oldest_lot['quantity'])
                entry_price = oldest_lot['price']
                exit_price = exec.price
                
                if oldest_lot['side'] == 'buy':
                    gross_pnl = (exit_price - entry_price) * match_qty
                    trade_side = 'long'
                else:
                    gross_pnl = (entry_price - exit_price) * match_qty
                    trade_side = 'short'
                
                entry_fee = oldest_lot['fee'] * (match_qty / oldest_lot['initial_quantity'])
                exit_fee = exec.fee * (match_qty / exec.quantity) if exec.quantity > 0 else Decimal(0)
                total_fee = entry_fee + exit_fee
                
                net_pnl = gross_pnl - total_fee
                invested = entry_price * match_qty
                roi = (net_pnl / invested) * 100 if invested > 0 else Decimal(0)
                
                closed_trades.append(ClosedTrade(
                    symbol=symbol,
                    entry_date=datetime.fromtimestamp(oldest_lot['timestamp'] / 1000),
                    exit_date=datetime.fromtimestamp(exec.timestamp / 1000),
                    duration_seconds=(exec.timestamp - oldest_lot['timestamp']) / 1000,
                    side=trade_side,
                    quantity=match_qty,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    gross_pnl=gross_pnl,
                    fee=total_fee,
                    net_pnl=net_pnl,
                    roi_percentage=float(roi)
                ))
                
                remaining_qty -= match_qty
                oldest_lot['quantity'] -= match_qty
                oldest_lot['fee'] -= entry_fee
                
                if oldest_lot['quantity'] <= 0:
                    open_lots.pop(0)
            
            if remaining_qty > 0:
                open_lots.append({
                    'quantity': remaining_qty,
                    'initial_quantity': remaining_qty,
                    'price': exec.price,
                    'side': exec.side,
                    'timestamp': exec.timestamp,
                    'fee': exec.fee * (remaining_qty / exec.quantity) if exec.quantity > 0 else Decimal(0)
                })
                
        return closed_trades

    def _calculate_metrics(self, closed_trades: List[ClosedTrade], trader_id: str) -> ReputationScore:
        """Aggregate closed trades into reputation metrics."""
        if not closed_trades:
            return ReputationScore(
                trader_id=trader_id,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl_usd=Decimal("0"),
                profit_factor=0.0,
                average_roi=0.0,
                score=0.0
            )
            
        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t.net_pnl > 0)
        losing_trades = sum(1 for t in closed_trades if t.net_pnl <= 0)
        
        total_pnl = sum((t.net_pnl for t in closed_trades), Decimal("0"))
        gross_profit = sum((t.net_pnl for t in closed_trades if t.net_pnl > 0), Decimal("0"))
        gross_loss = abs(sum((t.net_pnl for t in closed_trades if t.net_pnl < 0), Decimal("0")))
        
        win_rate = (winning_trades / total_trades) * 100
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        avg_roi = float(sum(t.roi_percentage for t in closed_trades) / total_trades)
        
        # Reputation Score (0-100)
        score_win_rate = min(win_rate, 100)
        score_pf = min(profit_factor * 33, 100) if profit_factor != float('inf') else 100
        score_roi = min(max(avg_roi * 5, 0), 100)
        score_activity = min(total_trades * 2, 100)
        
        final_score = (
            (score_win_rate * 0.30) +
            (score_pf * 0.30) +
            (score_roi * 0.20) +
            (score_activity * 0.20)
        )
        
        return ReputationScore(
            trader_id=trader_id,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl_usd=total_pnl,
            profit_factor=profit_factor,
            average_roi=avg_roi,
            score=round(final_score, 2)
        )


def test_ccxt_installation():
    """Test that CCXT is installed correctly"""
    print("\n" + "=" * 60)
    print("TEST 1: CCXT Installation Check")
    print("=" * 60)
    
    try:
        import ccxt
        print(f"✅ CCXT installed: version {ccxt.__version__}")
        print(f"   Supported exchanges: {len(ccxt.exchanges)}")
        return True
    except ImportError:
        print("❌ CCXT not installed!")
        print("   Run: pip install ccxt")
        return False


def test_exchange_list():
    """List available exchanges"""
    print("\n" + "=" * 60)
    print("TEST 2: List Popular Exchanges")
    print("=" * 60)
    
    import ccxt
    
    popular = ['binance', 'coinbase', 'kraken', 'kucoin', 'bybit', 'okx', 'bitget']
    
    for ex_name in popular:
        if ex_name in ccxt.exchanges:
            exchange_class = getattr(ccxt, ex_name)
            ex = exchange_class()
            has_fetch_trades = ex.has.get('fetchMyTrades', False)
            has_fetch_orders = ex.has.get('fetchOrders', False)
            print(f"✅ {ex_name:12} - fetchMyTrades: {has_fetch_trades}, fetchOrders: {has_fetch_orders}")
        else:
            print(f"❌ {ex_name:12} - Not supported")


async def test_public_api():
    """Test public API endpoints (no auth required)"""
    print("\n" + "=" * 60)
    print("TEST 3: Public API - Fetch Market Data (No Auth)")
    print("=" * 60)
    
    import ccxt.async_support as ccxt
    
    exchange = ccxt.binance({'enableRateLimit': True})
    
    try:
        # Load markets
        print("\n📊 Loading markets...")
        markets = await exchange.load_markets()
        print(f"✅ Loaded {len(markets)} trading pairs")
        
        # Sample pairs
        sample_pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        print(f"\n📈 Sample pairs available: {[p for p in sample_pairs if p in markets]}")
        
        # Fetch ticker
        print("\n💹 Fetching BTC/USDT ticker...")
        ticker = await exchange.fetch_ticker('BTC/USDT')
        print(f"✅ BTC/USDT:")
        print(f"   Last: ${ticker['last']:,.2f}")
        print(f"   Bid:  ${ticker['bid']:,.2f}")
        print(f"   Ask:  ${ticker['ask']:,.2f}")
        print(f"   24h Volume: {ticker['quoteVolume']:,.0f} USDT")
        print(f"   24h Change: {ticker['percentage']:.2f}%")
        
        # Fetch OHLCV (candles)
        print("\n🕯️ Fetching last 5 hourly candles for BTC/USDT...")
        ohlcv = await exchange.fetch_ohlcv('BTC/USDT', '1h', limit=5)
        print("✅ OHLCV Data:")
        print(f"   {'Timestamp':<20} {'Open':>12} {'High':>12} {'Low':>12} {'Close':>12}")
        for candle in ohlcv:
            ts = datetime.fromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M')
            print(f"   {ts:<20} ${candle[1]:>11,.2f} ${candle[2]:>11,.2f} ${candle[3]:>11,.2f} ${candle[4]:>11,.2f}")
        
        # Fetch public trades (not user trades)
        print("\n📋 Fetching recent public trades for BTC/USDT...")
        public_trades = await exchange.fetch_trades('BTC/USDT', limit=5)
        print(f"✅ Last {len(public_trades)} public trades:")
        for trade in public_trades:
            ts = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%H:%M:%S')
            print(f"   {ts} - {trade['side']:4} {trade['amount']:.6f} BTC @ ${trade['price']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        await exchange.close()


async def test_private_api():
    """Test private API endpoints (requires auth)"""
    print("\n" + "=" * 60)
    print("TEST 4: Private API - Fetch User Trades (Auth Required)")
    print("=" * 60)
    
    # Check for API keys (from env or command line args)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    use_demo = os.getenv('BINANCE_USE_DEMO', 'true').lower() == 'true'
    
    if not api_key or not api_secret:
        print("\n⚠️  No API keys provided!")
        print("\n   Option 1: Pass as command line arguments:")
        print("   python scripts/test_ccxt.py --api-key YOUR_KEY --api-secret YOUR_SECRET")
        print("\n   Option 2: Set environment variables:")
        print("   export BINANCE_API_KEY='your-api-key'")
        print("   export BINANCE_API_SECRET='your-api-secret'")
        print("\n   NOTE: In production, keys are stored securely via Citadel/Nillion.")
        print("   Users submit keys via: POST /citadel/exchange/credentials")
        return False
    
    import ccxt.async_support as ccxt
    
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    
    if use_testnet:
        if use_demo:
            # Use demo trading (demo-api.binance.com) - recommended for 2025+
            exchange.enable_demo_trading(True)
            print("📋 Using Binance DEMO TRADING (demo-api.binance.com)")
        else:
            # Use old sandbox (testnet.binance.vision) - deprecated
            exchange.set_sandbox_mode(True)
            print("📋 Using Binance TESTNET (testnet.binance.vision) - DEPRECATED")
    else:
        print("📋 Using Binance MAINNET (read-only recommended!)")
    
    try:
        # Fetch balance
        print("\n💰 Fetching account balance...")
        balance = await exchange.fetch_balance()
        
        non_zero = {k: v for k, v in balance['total'].items() if v > 0}
        if non_zero:
            print("✅ Non-zero balances:")
            for asset, amount in non_zero.items():
                print(f"   {asset}: {amount}")
        else:
            print("⚠️  No non-zero balances found")
        
        # Fetch my trades
        print("\n📋 Fetching your trades for BTC/USDT...")
        try:
            # fetchMyTrades requires the symbol
            my_trades = await exchange.fetch_my_trades('BTC/USDT', limit=10)
            
            if my_trades:
                print(f"✅ Found {len(my_trades)} trades:")
                for trade in my_trades[-5:]:  # Last 5
                    ts = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M')
                    side = trade['side']
                    amount = trade['amount']
                    price = trade['price']
                    fee = trade.get('fee', {}).get('cost', 0)
                    print(f"   {ts} - {side:4} {amount:.6f} BTC @ ${price:,.2f} (fee: {fee})")
            else:
                print("⚠️  No trades found for BTC/USDT")
                print("   (This is normal if you haven't traded this pair)")
                
        except Exception as e:
            print(f"⚠️  Could not fetch trades: {e}")
        
        # Fetch open orders
        print("\n📋 Fetching open orders...")
        try:
            open_orders = await exchange.fetch_open_orders()
            
            if open_orders:
                print(f"✅ Found {len(open_orders)} open orders:")
                for order in open_orders[:5]:
                    print(f"   {order['symbol']} - {order['side']} {order['amount']} @ {order['price']}")
            else:
                print("ℹ️  No open orders")
                
        except Exception as e:
            print(f"⚠️  Could not fetch orders: {e}")
        
        # Fetch closed orders (recent)
        print("\n📋 Fetching recent closed orders for BTC/USDT...")
        try:
            since = int((datetime.now() - timedelta(days=30)).timestamp() * 1000)
            closed_orders = await exchange.fetch_closed_orders('BTC/USDT', since=since, limit=5)
            
            if closed_orders:
                print(f"✅ Found {len(closed_orders)} closed orders (last 30 days):")
                for order in closed_orders:
                    ts = datetime.fromtimestamp(order['timestamp'] / 1000).strftime('%Y-%m-%d')
                    print(f"   {ts} - {order['side']:4} {order['amount']} @ {order['price']} ({order['status']})")
            else:
                print("ℹ️  No closed orders in last 30 days")
                
        except Exception as e:
            print(f"⚠️  Could not fetch closed orders: {e}")
        
        return True
        
    except ccxt.AuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        print("   Check your API key and secret")
        return False
        
    except ccxt.PermissionDenied as e:
        print(f"❌ Permission denied: {e}")
        print("   Your API key may not have read permissions enabled")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        await exchange.close()


async def test_fetch_all_trades():
    """Demonstrate fetching trades across multiple pairs"""
    print("\n" + "=" * 60)
    print("TEST 5: Fetch All User Trades (Multiple Pairs)")
    print("=" * 60)
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    use_testnet = os.getenv('BINANCE_TESTNET', 'false').lower() == 'true'
    use_demo = os.getenv('BINANCE_USE_DEMO', 'true').lower() == 'true'
    
    if not api_key or not api_secret:
        print("⏭️  Skipping - No API keys")
        return False, []
    
    import ccxt.async_support as ccxt
    
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    
    if use_testnet:
        if use_demo:
            exchange.enable_demo_trading(True)
        else:
            exchange.set_sandbox_mode(True)
    
    try:
        # Get trading pairs we have balance in
        balance = await exchange.fetch_balance()
        assets_with_balance = [k for k, v in balance['total'].items() if v > 0 and k != 'USDT']
        
        print(f"\n🔍 Checking trades for assets: {assets_with_balance[:5]}")
        
        all_trades = []
        
        for asset in assets_with_balance[:5]:  # Limit to 5 assets
            symbol = f"{asset}/USDT"
            try:
                trades = await exchange.fetch_my_trades(symbol, limit=50)  # Fetch more for PnL
                all_trades.extend(trades)
                if trades:
                    print(f"   ✅ {symbol}: {len(trades)} trades")
            except Exception:
                # Symbol might not exist
                pass
        
        if all_trades:
            # Sort by timestamp
            all_trades.sort(key=lambda x: x['timestamp'], reverse=True)
            
            print(f"\n📊 Total trades found: {len(all_trades)}")
            print("\n   Most recent trades:")
            for trade in all_trades[:10]:
                ts = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M')
                print(f"   {ts} - {trade['symbol']:12} {trade['side']:4} {trade['amount']:.6f} @ ${trade['price']:,.2f}")
        else:
            print("ℹ️  No trades found")
        
        return True, all_trades
        
    finally:
        await exchange.close()


async def test_pnl_calculation(trades: List[dict]):
    """Calculate PnL and Reputation Score from fetched trades"""
    print("\n" + "=" * 60)
    print("TEST 6: PnL Calculation & Reputation Score")
    print("=" * 60)
    
    if not trades:
        print("⏭️  Skipping - No trades available for PnL calculation")
        return False
    
    calculator = PnLCalculator()
    
    try:
        # Calculate PnL
        print(f"\n📊 Analyzing {len(trades)} trades...")
        score, closed_trades = calculator.calculate_from_ccxt_trades(trades)
        
        if not closed_trades:
            print("\n⚠️  No closed positions found (need matching buy/sell pairs)")
            print("   This happens when you only have one-sided trades (all buys or all sells)")
            
            # Show open positions
            print("\n📈 Current Open Positions (FIFO):")
            for symbol, lots in calculator.positions.items():
                if lots:
                    total_qty = sum(lot['quantity'] for lot in lots)
                    avg_price = sum(lot['price'] * lot['quantity'] for lot in lots) / total_qty if total_qty > 0 else 0
                    side = lots[0]['side']
                    print(f"   {symbol}: {side.upper()} {float(total_qty):.6f} @ avg ${float(avg_price):,.2f}")
            return True
        
        # Display closed trades
        print(f"\n✅ Found {len(closed_trades)} closed positions:")
        print(f"\n   {'Symbol':<12} {'Side':<6} {'Qty':>10} {'Entry':>12} {'Exit':>12} {'PnL':>12} {'ROI':>8}")
        print("   " + "-" * 78)
        
        for ct in closed_trades[-10:]:  # Last 10 closed trades
            pnl_str = f"${float(ct.net_pnl):+,.2f}"
            roi_str = f"{ct.roi_percentage:+.2f}%"
            pnl_color = "🟢" if ct.net_pnl > 0 else "🔴"
            print(f"   {ct.symbol:<12} {ct.side:<6} {float(ct.quantity):>10.4f} ${float(ct.entry_price):>10,.2f} ${float(ct.exit_price):>10,.2f} {pnl_color}{pnl_str:>10} {roi_str:>8}")
        
        # Display summary
        print("\n" + "=" * 60)
        print("📊 TRADING PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"""
   Trader ID:        {score.trader_id}
   Total Trades:     {score.total_trades}
   Winning Trades:   {score.winning_trades} 🟢
   Losing Trades:    {score.losing_trades} 🔴
   
   Win Rate:         {score.win_rate:.1f}%
   Profit Factor:    {score.profit_factor:.2f}
   Average ROI:      {score.average_roi:+.2f}%
   
   Total PnL:        ${float(score.total_pnl_usd):+,.2f} {'🟢' if score.total_pnl_usd > 0 else '🔴'}
   
   ════════════════════════════════════════
   REPUTATION SCORE: {score.score:.1f} / 100
   ════════════════════════════════════════
""")
        
        # Score interpretation
        if score.score >= 80:
            print("   🏆 Excellent trader performance!")
        elif score.score >= 60:
            print("   👍 Good trading performance")
        elif score.score >= 40:
            print("   📊 Average trading performance")
        else:
            print("   ⚠️  Needs improvement")
        
        # Show remaining open positions
        if any(calculator.positions.values()):
            print("\n📈 Remaining Open Positions:")
            for symbol, lots in calculator.positions.items():
                if lots:
                    total_qty = sum(lot['quantity'] for lot in lots)
                    avg_price = sum(lot['price'] * lot['quantity'] for lot in lots) / total_qty if total_qty > 0 else 0
                    side = lots[0]['side']
                    print(f"   {symbol}: {side.upper()} {float(total_qty):.6f} @ avg ${float(avg_price):,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error calculating PnL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connector_integration():
    """Test the BinanceConnector class from the backend"""
    print("\n" + "=" * 60)
    print("TEST 7: BinanceConnector Integration")
    print("=" * 60)
    
    try:
        from modules.trading.exchanges.binance_connector import BinanceConnector
        print("✅ BinanceConnector imported successfully")
        
        connector = BinanceConnector()
        print(f"   Exchange: {connector.name}")
        print(f"   Type: {connector.exchange_type}")
        print(f"   Has API key: {'Yes' if connector.api_key else 'No'}")
        
        return True
    except ImportError as e:
        print(f"⚠️  Could not import BinanceConnector: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "🔧 " * 20)
    print("   CCXT Integration Test Suite")
    print("🔧 " * 20)
    
    results = {}
    all_trades = []
    
    # Test 1: Installation
    results['installation'] = test_ccxt_installation()
    
    if not results['installation']:
        print("\n❌ CCXT not installed. Please run: pip install ccxt")
        return
    
    # Test 2: Exchange list
    test_exchange_list()
    
    # Test 3: Public API
    results['public_api'] = await test_public_api()
    
    # Test 4: Private API
    results['private_api'] = await test_private_api()
    
    # Test 5: Fetch all trades
    results['all_trades'], all_trades = await test_fetch_all_trades()
    
    # Test 6: PnL Calculation
    results['pnl_calculation'] = await test_pnl_calculation(all_trades)
    
    # Test 7: Connector integration
    results['connector'] = test_connector_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test:20} {status}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if not os.getenv('BINANCE_API_KEY'):
        print("""
To test with real/testnet data:

1. Create testnet account at https://testnet.binance.vision/
2. Generate API keys (with read permissions)
3. Set environment variables:

   export BINANCE_API_KEY='your-testnet-api-key'
   export BINANCE_API_SECRET='your-testnet-secret'
   export BINANCE_TESTNET='true'

4. Run this script again
""")
    else:
        print("""
✅ API keys configured! You can now:

1. Use the trading service to place orders
2. Fetch your trade history for ZK proof generation
3. Monitor positions in real-time
4. Calculate PnL and Reputation Scores
""")


if __name__ == '__main__':
    asyncio.run(main())
