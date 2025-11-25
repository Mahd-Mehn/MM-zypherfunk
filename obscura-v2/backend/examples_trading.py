"""
Multi-Exchange Trading Examples
Demonstrates full-scale trading across CEXes and DEXes
"""

import asyncio
from decimal import Decimal
from exchanges.orchestrator import TradingOrchestrator
from exchanges.base import TradeOrder, OrderType, OrderSide

async def example_1_configure_exchanges():
    """Example 1: Initialize multiple exchanges"""
    orchestrator = TradingOrchestrator()
    
    config = {
        'binance': {
            'api_key': 'your-binance-api-key',
            'api_secret': 'your-binance-secret'
        },
        'coinbase': {
            'api_key': 'your-coinbase-api-key',
            'api_secret': 'your-coinbase-secret'
        },
        'uniswap': {
            'private_key': 'your-eth-private-key',
            'rpc_url': 'https://mainnet.base.org'
        },
        'starknet': {
            'private_key': 'your-starknet-private-key',
            'account_address': 'your-starknet-account'
        }
    }
    
    results = await orchestrator.initialize_all_exchanges(config)
    print(f"Initialization results: {results}")
    
    return orchestrator


async def example_2_simple_market_order():
    """Example 2: Place a simple market order on Binance"""
    orchestrator = await example_1_configure_exchanges()
    
    order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.001")  # 0.001 BTC
    )
    
    result = await orchestrator.place_order('binance', order)
    print(f"Order placed: {result}")
    

async def example_3_smart_routing():
    """Example 3: Use smart routing to find best price"""
    orchestrator = await example_1_configure_exchanges()
    
    # Get best price across all exchanges
    best_price = await orchestrator.get_best_price("BTC/USDT", OrderSide.BUY)
    print(f"Best price found on {best_price['best_exchange']}: ${best_price['best_price']}")
    
    # Execute on best exchange automatically
    order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.001")
    )
    
    result = await orchestrator.execute_smart_order(order, strategy="best_price")
    print(f"Executed on {result.exchange}: {result}")


async def example_4_dex_swap():
    """Example 4: Perform a DEX swap on Uniswap (Base)"""
    orchestrator = await example_1_configure_exchanges()
    
    order = TradeOrder(
        symbol="WETH/USDC",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        amount=Decimal("0.1"),  # 0.1 WETH
        slippage=Decimal("0.005"),  # 0.5% slippage tolerance
        deadline=int(asyncio.get_event_loop().time()) + 1200  # 20 min deadline
    )
    
    result = await orchestrator.place_order('uniswap', order)
    print(f"DEX swap completed: {result.tx_hash}")


async def example_5_copy_trading():
    """Example 5: Replicate trade across multiple exchanges"""
    orchestrator = await example_1_configure_exchanges()
    
    # Original trade on Binance
    order = TradeOrder(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("0.1")
    )
    
    # Copy to Coinbase and Uniswap
    results = await orchestrator.replicate_trade(
        source_exchange='binance',
        target_exchanges=['coinbase', 'uniswap'],
        order=order,
        delay_ms=100  # 100ms delay between trades
    )
    
    for result in results:
        print(f"Trade executed on {result.exchange}: {result.order_id}")


async def example_6_aggregated_portfolio():
    """Example 6: View portfolio across all exchanges"""
    orchestrator = await example_1_configure_exchanges()
    
    # Get BTC balance across all exchanges
    btc_balance = await orchestrator.get_aggregated_balance('BTC')
    print(f"Total BTC: {btc_balance['total']}")
    print(f"Distribution: {btc_balance['by_exchange']}")
    
    # Get all balances
    all_balances = await orchestrator.get_aggregated_balance()
    print(f"All balances: {all_balances}")


async def example_7_limit_order_with_fallback():
    """Example 7: Place limit order with fallback"""
    orchestrator = await example_1_configure_exchanges()
    
    order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        amount=Decimal("0.001"),
        price=Decimal("45000")  # Buy at $45,000
    )
    
    # Try Binance first, fallback to Coinbase if fails
    result = await orchestrator.place_order_with_fallback(
        preferred_exchanges=['binance', 'coinbase'],
        order=order
    )
    
    print(f"Order placed on {result.exchange}")


async def example_8_cross_exchange_arbitrage():
    """Example 8: Detect arbitrage opportunities"""
    orchestrator = await example_1_configure_exchanges()
    
    symbol = "BTC/USDT"
    
    # Get prices from all exchanges
    best_buy = await orchestrator.get_best_price(symbol, OrderSide.BUY)
    best_sell = await orchestrator.get_best_price(symbol, OrderSide.SELL)
    
    print(f"Best buy: {best_buy['best_exchange']} @ ${best_buy['best_price']}")
    print(f"Best sell: {best_sell['best_exchange']} @ ${best_sell['best_price']}")
    
    # Calculate arbitrage spread
    if best_sell['best_price'] > best_buy['best_price']:
        spread = (best_sell['best_price'] - best_buy['best_price']) / best_buy['best_price'] * 100
        print(f"Arbitrage opportunity: {spread:.2f}%")
        
        if spread > 0.5:  # If spread > 0.5%
            # Buy on cheaper exchange
            buy_order = TradeOrder(
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                amount=Decimal("0.001")
            )
            
            # Sell on expensive exchange
            sell_order = TradeOrder(
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                amount=Decimal("0.001")
            )
            
            # Execute simultaneously
            buy_result = await orchestrator.place_order(best_buy['best_exchange'], buy_order)
            sell_result = await orchestrator.place_order(best_sell['best_exchange'], sell_order)
            
            print(f"Arbitrage executed: profit = {spread:.2f}%")


async def example_9_multi_chain_strategy():
    """Example 9: Execute strategy across CEX and DEX"""
    orchestrator = await example_1_configure_exchanges()
    
    # Buy on CEX (cheaper, faster)
    cex_order = TradeOrder(
        symbol="ETH/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        amount=Decimal("1.0")
    )
    
    cex_result = await orchestrator.place_order('binance', cex_order)
    print(f"Bought on Binance: {cex_result.order_id}")
    
    # Use in DEX for DeFi strategy
    dex_order = TradeOrder(
        symbol="WETH/USDC",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        amount=Decimal("0.5"),
        slippage=Decimal("0.01")
    )
    
    dex_result = await orchestrator.place_order('uniswap', dex_order)
    print(f"DEX swap on Base: {dex_result.tx_hash}")


if __name__ == "__main__":
    # Run an example
    print("=== Example 3: Smart Routing ===")
    asyncio.run(example_3_smart_routing())
