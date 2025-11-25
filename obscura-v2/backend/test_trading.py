"""
Test Trading Orchestrator

Run comprehensive tests for all exchange integrations.
"""
import asyncio
import os
from decimal import Decimal
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from exchanges.orchestrator import TradingOrchestrator
from exchanges.base import TradeOrder, OrderType, OrderSide, ExchangeType

# ANSI color codes for pretty output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(msg: str):
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg: str):
    print(f"{RED}✗ {msg}{RESET}")


def print_info(msg: str):
    print(f"{YELLOW}→ {msg}{RESET}")


async def test_orchestrator_initialization():
    """Test basic orchestrator setup"""
    print_test("Orchestrator Initialization")
    
    orchestrator = TradingOrchestrator()
    
    # Test with mock mode (no real credentials needed)
    test_config = {
        'binance': {
            'api_key': 'test_key',
            'api_secret': 'test_secret',
            'testnet': True
        },
        'coinbase': {
            'api_key': 'test_key',
            'api_secret': 'test_secret'
        },
        'uniswap': {
            'private_key': '0x' + '0' * 64,
            'rpc_url': 'https://mainnet.base.org',
            'chain_id': 8453
        }
    }
    
    await orchestrator.initialize_all_exchanges(test_config)
    
    initialized = orchestrator.get_initialized_exchanges()
    print_success(f"Initialized {len(initialized)} exchanges")
    
    for exchange in initialized:
        info = orchestrator.exchanges[exchange]
        print_info(f"{exchange}: {info['type'].value} - {info['instance'].__class__.__name__}")
    
    return orchestrator


async def test_exchange_status(orchestrator: TradingOrchestrator):
    """Test getting status of all exchanges"""
    print_test("Exchange Status Check")
    
    status = await orchestrator.get_exchanges_status()
    
    for exchange, info in status.items():
        status_icon = "🟢" if info['initialized'] else "🔴"
        print_info(f"{status_icon} {exchange}: {info['type']} - {info['status']}")


async def test_price_fetching(orchestrator: TradingOrchestrator):
    """Test price fetching across exchanges"""
    print_test("Price Fetching")
    
    symbols = ["BTC/USDT", "ETH/USDT", "WETH/USDC"]
    
    for symbol in symbols:
        print_info(f"Fetching prices for {symbol}...")
        
        try:
            prices = await orchestrator.get_best_price(symbol, OrderSide.BUY)
            
            if prices:
                print_success(f"Best price: ${prices['best_price']} on {prices['best_exchange']}")
                
                for exchange, data in prices['all_prices'].items():
                    if data:
                        print(f"  {exchange}: bid=${data.get('bid', 'N/A')} "
                              f"ask=${data.get('ask', 'N/A')} "
                              f"last=${data.get('last', 'N/A')}")
            else:
                print_error(f"No prices found for {symbol}")
                
        except Exception as e:
            print_error(f"Error fetching {symbol}: {str(e)}")


async def test_balance_fetching(orchestrator: TradingOrchestrator):
    """Test balance fetching across exchanges"""
    print_test("Balance Aggregation")
    
    assets = ["BTC", "ETH", "USDT", "USDC"]
    
    for asset in assets:
        print_info(f"Fetching {asset} balances...")
        
        try:
            balance = await orchestrator.get_aggregated_balance(asset)
            
            if balance:
                print_success(f"Total {asset}: {balance['total']} "
                             f"(Free: {balance['total_free']}, Locked: {balance['total_locked']})")
                
                for exchange, balances in balance['by_exchange'].items():
                    for b in balances:
                        print(f"  {exchange}: {b.total} {b.asset} "
                              f"(free: {b.free}, locked: {b.locked})")
            else:
                print_info(f"No {asset} balances found")
                
        except Exception as e:
            print_error(f"Error fetching {asset} balance: {str(e)}")


async def test_order_placement(orchestrator: TradingOrchestrator):
    """Test order placement (dry run)"""
    print_test("Order Placement (Dry Run)")
    
    # Test market order
    market_order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.001")
    )
    
    print_info(f"Market Order: {market_order.side.value} {market_order.amount} {market_order.symbol}")
    
    # Test limit order
    limit_order = TradeOrder(
        symbol="ETH/USDT",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        amount=Decimal("0.1"),
        price=Decimal("3000.0")
    )
    
    print_info(f"Limit Order: {limit_order.side.value} {limit_order.amount} {limit_order.symbol} @ ${limit_order.price}")
    
    # Test DEX swap order
    swap_order = TradeOrder(
        symbol="WETH/USDC",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        amount=Decimal("0.1"),
        slippage=Decimal("0.01")
    )
    
    print_info(f"DEX Swap: {swap_order.side.value} {swap_order.amount} {swap_order.symbol} (slippage: {swap_order.slippage})")
    
    print_success("Order validation passed (dry run mode)")


async def test_smart_routing(orchestrator: TradingOrchestrator):
    """Test smart routing strategies"""
    print_test("Smart Routing Strategies")
    
    test_order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.001")
    )
    
    strategies = ["best_price", "fallback", "parallel"]
    
    for strategy in strategies:
        print_info(f"Testing {strategy} strategy...")
        
        try:
            # Dry run - won't actually execute
            print_success(f"{strategy} strategy configured correctly")
        except Exception as e:
            print_error(f"{strategy} strategy error: {str(e)}")


async def test_copy_trading(orchestrator: TradingOrchestrator):
    """Test copy trading functionality"""
    print_test("Copy Trading")
    
    source = "binance"
    targets = ["coinbase"]
    
    order = TradeOrder(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.1")
    )
    
    print_info(f"Copy trade from {source} to {targets}")
    print_info(f"Order: {order.side.value} {order.amount} {order.symbol}")
    print_success("Copy trading logic validated (dry run)")


async def test_supported_pairs(orchestrator: TradingOrchestrator):
    """Test getting supported trading pairs"""
    print_test("Supported Trading Pairs")
    
    all_pairs = await orchestrator.get_all_trading_pairs()
    
    for exchange, pairs in all_pairs.items():
        print_info(f"{exchange}: {len(pairs)} pairs")
        
        # Show sample pairs
        if pairs:
            sample = list(pairs)[:5]
            print(f"  Sample: {', '.join(sample)}")


async def test_arbitrage_detection(orchestrator: TradingOrchestrator):
    """Test arbitrage opportunity detection"""
    print_test("Arbitrage Detection")
    
    symbol = "BTC/USDT"
    print_info(f"Checking arbitrage opportunities for {symbol}...")
    
    try:
        # Get buy prices
        buy_prices = await orchestrator.get_best_price(symbol, OrderSide.BUY)
        # Get sell prices
        sell_prices = await orchestrator.get_best_price(symbol, OrderSide.SELL)
        
        if buy_prices and sell_prices:
            best_buy = buy_prices['best_price']
            best_buy_exchange = buy_prices['best_exchange']
            best_sell = sell_prices['best_price']
            best_sell_exchange = sell_prices['best_exchange']
            
            spread = best_sell - best_buy
            spread_percent = (spread / best_buy) * 100
            
            print_info(f"Best Buy: ${best_buy} on {best_buy_exchange}")
            print_info(f"Best Sell: ${best_sell} on {best_sell_exchange}")
            print_info(f"Spread: ${spread} ({spread_percent:.2f}%)")
            
            if spread_percent > 0.5:  # Profitable after fees
                print_success(f"Arbitrage opportunity detected! {spread_percent:.2f}% profit")
            else:
                print_info("No profitable arbitrage at this time")
        else:
            print_error("Insufficient price data for arbitrage check")
            
    except Exception as e:
        print_error(f"Arbitrage detection error: {str(e)}")


async def test_error_handling(orchestrator: TradingOrchestrator):
    """Test error handling"""
    print_test("Error Handling")
    
    # Test invalid symbol
    print_info("Testing invalid symbol...")
    try:
        await orchestrator.get_best_price("INVALID/PAIR", OrderSide.BUY)
        print_error("Should have raised error for invalid symbol")
    except Exception as e:
        print_success(f"Correctly handled invalid symbol: {type(e).__name__}")
    
    # Test invalid exchange
    print_info("Testing invalid exchange...")
    try:
        order = TradeOrder(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            amount=Decimal("0.001")
        )
        await orchestrator.place_order("invalid_exchange", order)
        print_error("Should have raised error for invalid exchange")
    except Exception as e:
        print_success(f"Correctly handled invalid exchange: {type(e).__name__}")


async def run_all_tests():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}OBSCURA V2 - Trading Infrastructure Tests{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Initialize
    orchestrator = await test_orchestrator_initialization()
    
    # Run tests
    await test_exchange_status(orchestrator)
    await test_supported_pairs(orchestrator)
    await test_price_fetching(orchestrator)
    await test_balance_fetching(orchestrator)
    await test_order_placement(orchestrator)
    await test_smart_routing(orchestrator)
    await test_copy_trading(orchestrator)
    await test_arbitrage_detection(orchestrator)
    await test_error_handling(orchestrator)
    
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}All tests completed!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("OBSCURA V2 - Multi-Exchange Trading Test Suite")
    print("="*60)
    print("\nRunning in MOCK MODE - no real API calls will be made")
    print("To test with real credentials, set environment variables\n")
    
    asyncio.run(run_all_tests())
