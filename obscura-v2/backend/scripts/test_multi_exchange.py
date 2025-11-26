#!/usr/bin/env python3
"""
Multi-Exchange Test Script

Tests connectivity and trade fetching across multiple exchanges.

Usage:
  # Public API only (no credentials needed)
  python scripts/test_multi_exchange.py --exchange binance
  
  # With API credentials for private endpoints
  python scripts/test_multi_exchange.py --exchange binance --api-key KEY --api-secret SECRET
  python scripts/test_multi_exchange.py --exchange coinbase --api-key KEY --api-secret SECRET
  python scripts/test_multi_exchange.py --exchange kraken --api-key KEY --api-secret SECRET
  python scripts/test_multi_exchange.py --exchange bybit --api-key KEY --api-secret SECRET
  python scripts/test_multi_exchange.py --exchange okx --api-key KEY --api-secret SECRET --passphrase PASS

Supported exchanges: binance, coinbase, kraken, bybit, okx, kucoin, bitget, gate
"""

import asyncio
import os
import sys
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Parse arguments
parser = argparse.ArgumentParser(description='Test multiple exchanges')
parser.add_argument('--exchange', required=True, help='Exchange to test (binance, coinbase, kraken, bybit, okx, kucoin)')
parser.add_argument('--api-key', help='API key (optional for public API testing)')
parser.add_argument('--api-secret', help='API secret (optional for public API testing)')
parser.add_argument('--passphrase', help='Passphrase (required for OKX, KuCoin)')
parser.add_argument('--testnet', action='store_true', help='Use testnet/sandbox mode')
parser.add_argument('--demo', action='store_true', help='Use demo trading mode (Binance)')
args = parser.parse_args()


# Exchange-specific configurations
EXCHANGE_CONFIGS = {
    'binance': {
        'class': 'binance',
        'testnet_url': '`​https://demo-api.binance.com`' if args.demo else ('https://testnet.binance.vision' if args.testnet else ''),
        'demo_method': 'enable_demo_trading',
        'pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT'],
    },
    'coinbase': {
        'class': 'coinbase',
        'sandbox_mode': True,
        'pairs': ['BTC/USD', 'ETH/USD', 'SOL/USD'],
    },
    'kraken': {
        'class': 'kraken',
        'pairs': ['BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD'],
    },
    'bybit': {
        'class': 'bybit',
        'testnet': True,
        'pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    },
    'okx': {
        'class': 'okx',
        'requires_passphrase': True,
        'pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    },
    'kucoin': {
        'class': 'kucoin',
        'requires_passphrase': True,
        'pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    },
    'bitget': {
        'class': 'bitget',
        'requires_passphrase': True,
        'pairs': ['BTC/USDT', 'ETH/USDT'],
    },
    'gate': {
        'class': 'gate',
        'pairs': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
    },
}


async def test_exchange(exchange_id: str, config: Dict[str, Any]):
    """Test an exchange connection"""
    print(f"\n{'=' * 60}")
    print(f"Testing {exchange_id.upper()}")
    print('=' * 60)
    
    has_credentials = config.get('api_key') and config.get('api_secret')
    if not has_credentials:
        print("ℹ️  No API credentials provided - testing PUBLIC API only")
    
    try:
        import ccxt.async_support as ccxt
    except ImportError:
        print("❌ CCXT not installed. Run: pip install ccxt")
        return False
    
    exchange_config = EXCHANGE_CONFIGS.get(exchange_id)
    if not exchange_config:
        print(f"❌ Exchange {exchange_id} not configured")
        return False
    
    # Check passphrase requirement (only if we have credentials)
    if has_credentials and exchange_config.get('requires_passphrase') and not args.passphrase:
        print(f"❌ {exchange_id} requires --passphrase for authenticated requests")
        return False
    
    # Build CCXT config
    ccxt_config = {
        'enableRateLimit': True,
    }
    
    if has_credentials:
        ccxt_config['apiKey'] = config['api_key']
        ccxt_config['secret'] = config['api_secret']
        if config.get('passphrase'):
            ccxt_config['password'] = config['passphrase']
    
    # Get exchange class
    exchange_class_name = exchange_config['class']
    if not hasattr(ccxt, exchange_class_name):
        print(f"❌ CCXT does not support {exchange_class_name}")
        return False
    
    exchange_class = getattr(ccxt, exchange_class_name)
    exchange = exchange_class(ccxt_config)
    
    # Apply testnet/demo mode
    if has_credentials and (args.testnet or args.demo):
        if exchange_id == 'binance' and args.demo:
            exchange.enable_demo_trading(True)
            print("📋 Using Binance Demo Trading")
        elif hasattr(exchange, 'set_sandbox_mode'):
            exchange.set_sandbox_mode(True)
            print(f"📋 Using {exchange_id} Sandbox/Testnet")
    
    results = {
        'connection': False,
        'markets': False,
        'balance': False,
        'trades': False,
    }
    all_trades = []
    
    try:
        # Test 1: Load markets
        print("\n📊 Loading markets...")
        markets = await exchange.load_markets()
        results['markets'] = True
        print(f"✅ Loaded {len(markets)} trading pairs")
        
        # Show sample pairs
        sample_pairs = exchange_config['pairs']
        available = [p for p in sample_pairs if p in markets]
        print(f"   Available test pairs: {available}")
        
        results['connection'] = True
        
        # Test 2: Fetch ticker
        if available:
            test_pair = available[0]
            print(f"\n💹 Fetching {test_pair} ticker...")
            ticker = await exchange.fetch_ticker(test_pair)
            print(f"✅ {test_pair}:")
            print(f"   Last: ${ticker['last']:,.2f}" if ticker.get('last') else "   Last: N/A")
            if ticker.get('bid'):
                print(f"   Bid:  ${ticker['bid']:,.2f}")
            if ticker.get('ask'):
                print(f"   Ask:  ${ticker['ask']:,.2f}")
        
        # Test 3: Fetch balance (requires credentials)
        if has_credentials:
            print("\n💰 Fetching account balance...")
            try:
                balance = await exchange.fetch_balance()
                non_zero = {k: v for k, v in balance.get('total', {}).items() 
                           if isinstance(v, (int, float)) and v > 0}
                
                if non_zero:
                    results['balance'] = True
                    print("✅ Non-zero balances:")
                    for asset, amount in list(non_zero.items())[:10]:
                        print(f"   {asset}: {amount}")
                else:
                    print("⚠️  No non-zero balances found")
                    results['balance'] = True  # API worked, just empty
            except Exception as e:
                print(f"⚠️  Could not fetch balance: {e}")
        else:
            print("\n💰 Skipping balance check (no credentials)")
        
        # Test 4: Fetch trades (requires credentials)
        if has_credentials:
            print("\n📋 Fetching trade history...")
            if exchange.has.get('fetchMyTrades'):
                try:
                    for pair in available[:3]:
                        try:
                            trades = await exchange.fetch_my_trades(pair, limit=20)
                            all_trades.extend(trades)
                            if trades:
                                print(f"   ✅ {pair}: {len(trades)} trades")
                        except Exception as e:
                            print(f"   ⚠️  {pair}: {str(e)[:50]}")
                    
                    if all_trades:
                        results['trades'] = True
                        print(f"\n📊 Total trades found: {len(all_trades)}")
                        
                        # Show recent trades
                        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
                        print("\n   Recent trades:")
                        for trade in all_trades[:5]:
                            ts = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M')
                            print(f"   {ts} - {trade['symbol']:12} {trade['side']:4} {trade['amount']:.6f} @ ${trade['price']:,.2f}")
                    else:
                        print("ℹ️  No trades found (this is normal for new/test accounts)")
                        results['trades'] = True  # API worked
                        
                except Exception as e:
                    print(f"⚠️  Could not fetch trades: {e}")
            else:
                print(f"⚠️  {exchange_id} does not support fetchMyTrades")
        else:
            print("\n📋 Skipping trade history (no credentials)")
        
        # Test 5: PnL Calculation (if trades exist)
        if all_trades and len(all_trades) > 0:
            print("\n📈 Calculating PnL...")
            try:
                from modules.trading.pnl_calculator import PnLCalculator
                calculator = PnLCalculator()
                score, closed_trades = calculator.calculate_from_ccxt_trades(all_trades, f"{exchange_id}_user")
                
                print(f"\n   PERFORMANCE SUMMARY")
                print(f"   Total Closed Trades: {score.total_trades}")
                print(f"   Win Rate: {score.win_rate:.1f}%")
                print(f"   Profit Factor: {score.profit_factor:.2f}")
                print(f"   Total PnL: ${float(score.total_pnl_usd):+,.2f}")
                print(f"   Reputation Score: {score.score:.1f}/100")
                
            except Exception as e:
                print(f"⚠️  PnL calculation error: {e}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing {exchange_id}: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await exchange.close()
        
        # Summary
        print(f"\n{'=' * 60}")
        print(f"TEST RESULTS for {exchange_id.upper()}")
        print('=' * 60)
        for test, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test:15} {status}")


async def main():
    """Main entry point"""
    print("\n🔧 " * 15)
    print("   Multi-Exchange Test Suite")
    print("🔧 " * 15)
    
    config = {
        'api_key': args.api_key,
        'api_secret': args.api_secret,
        'passphrase': args.passphrase,
    }
    
    success = await test_exchange(args.exchange, config)
    
    print("\n" + "=" * 60)
    print("REQUIREMENTS FOR EACH EXCHANGE")
    print("=" * 60)
    print("""
    BINANCE:
      - API Key + Secret
      - Enable "Enable Reading" and "Enable Spot Trading"
      - Optional: IP whitelist
      - Demo: --demo flag uses demo-api.binance.com
    
    COINBASE:
      - API Key + Secret
      - Permissions: view, trade
    
    KRAKEN:
      - API Key + Private Key
      - Permissions: Query Funds, Query Orders & Trades
    
    BYBIT:
      - API Key + Secret
      - Permissions: Read, Trade
      - Optional: IP restriction
    
    OKX:
      - API Key + Secret + Passphrase (required)
      - Permissions: Read, Trade
    
    KUCOIN:
      - API Key + Secret + Passphrase (required)
      - Permissions: General, Trade
    
    BITGET:
      - API Key + Secret + Passphrase (required)
      
    GATE.IO:
      - API Key + Secret
    """)
    
    return 0 if success else 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
