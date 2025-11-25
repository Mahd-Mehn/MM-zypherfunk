# Multi-Exchange Trading Infrastructure

Complete integration of **CEXes** (Binance, Coinbase) and **DEXes** (Uniswap, Starknet) for full-scale copy trading and execution.

## 🚀 Features

### Centralized Exchanges (CEX)
- ✅ **Binance** - Spot trading via CCXT
- ✅ **Coinbase** - Advanced Trade API via CCXT
- 📊 Real-time order book access
- 💰 Account balance management
- 🔄 Market and limit orders
- ⚡ High-frequency trading ready

### Decentralized Exchanges (DEX)
- ✅ **Uniswap V2/V3** - On Ethereum and Base
- ✅ **Starknet DEXes** - JediSwap, 10KSwap
- 🔐 Self-custodial (uses your private keys)
- 🌉 Cross-chain support
- 💸 Gas optimization
- ⏰ Transaction deadline management

### Smart Execution Features
- 🎯 **Smart Routing** - Automatically find best prices
- 🔄 **Copy Trading** - Replicate trades across multiple exchanges
- 📊 **Aggregated Portfolio** - View balances across all platforms
- 🔀 **Fallback Execution** - Auto-retry on alternative exchanges
- 🤖 **Arbitrage Detection** - Identify profit opportunities
- ⚖️ **Order Splitting** - Distribute large orders

## 📦 Installation

```bash
# Install all trading dependencies
pip install -r requirements.txt

# Key packages:
# - ccxt (CEX integration)
# - web3 (Ethereum/Base DEX)
# - starknet-py (Starknet DEX)
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file in `backend/`:

```bash
# CEX Credentials
BINANCE_API_KEY=your-binance-api-key
BINANCE_API_SECRET=your-binance-secret
BINANCE_TESTNET=true  # Use testnet for development

COINBASE_API_KEY=your-coinbase-api-key
COINBASE_API_SECRET=your-coinbase-secret

# DEX Configuration
ETH_PRIVATE_KEY=0x...  # Your Ethereum/Base private key
BASE_RPC_URL=https://mainnet.base.org
CHAIN_ID=8453  # Base mainnet

# Starknet
STARKNET_PRIVATE_KEY=0x...
STARKNET_ACCOUNT_ADDRESS=0x...
STARKNET_RPC_URL=https://starknet-mainnet.public.blastapi.io

# Uniswap Router (Base)
UNISWAP_ROUTER=0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24
```

## 🎯 Quick Start

### 1. Basic Market Order

```python
from exchanges.orchestrator import TradingOrchestrator
from exchanges.base import TradeOrder, OrderType, OrderSide
from decimal import Decimal

orchestrator = TradingOrchestrator()

# Initialize exchanges
await orchestrator.initialize_all_exchanges({
    'binance': {
        'api_key': 'your-key',
        'api_secret': 'your-secret'
    }
})

# Place market order
order = TradeOrder(
    symbol="BTC/USDT",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    amount=Decimal("0.001")
)

result = await orchestrator.place_order('binance', order)
print(f"Order ID: {result.order_id}")
```

### 2. Smart Routing (Best Price)

```python
# Automatically route to exchange with best price
result = await orchestrator.execute_smart_order(
    order=order,
    strategy="best_price"
)

print(f"Executed on {result.exchange} @ ${result.average_price}")
```

### 3. DEX Swap on Uniswap

```python
# Swap on Uniswap (Base chain)
order = TradeOrder(
    symbol="WETH/USDC",
    side=OrderSide.SELL,
    order_type=OrderType.MARKET,
    amount=Decimal("0.1"),
    slippage=Decimal("0.01"),  # 1% slippage tolerance
)

result = await orchestrator.place_order('uniswap', order)
print(f"Transaction: {result.tx_hash}")
```

### 4. Copy Trading

```python
# Replicate trade from Binance to other exchanges
results = await orchestrator.replicate_trade(
    source_exchange='binance',
    target_exchanges=['coinbase', 'uniswap'],
    order=order,
    delay_ms=100
)

for r in results:
    print(f"{r.exchange}: {r.status}")
```

## 🔌 API Endpoints

### Start the Trading Server

```bash
cd backend/conductor
uvicorn main:app --reload --port 8001
```

### Endpoints

#### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "execution_layer": "multi-exchange-orchestrator",
  "near_mpc": "enabled",
  "exchanges": {
    "total_exchanges": 4,
    "initialized_exchanges": 2,
    "exchanges": {...}
  }
}
```

#### Get Best Price
```bash
GET /price/BTC/USDT?side=buy

Response:
{
  "best_exchange": "binance",
  "best_price": 45123.45,
  "all_prices": {
    "binance": {"bid": 45120, "ask": 45125, "last": 45123},
    "coinbase": {"bid": 45118, "ask": 45128, "last": 45124}
  }
}
```

#### Execute Trade
```bash
POST /execute

Body:
{
  "user_id": "user123",
  "symbol": "BTC/USDT",
  "side": "buy",
  "order_type": "market",
  "amount": "0.001",
  "strategy": "best_price"
}

Response:
{
  "execution_id": "abc123...",
  "status": "filled",
  "exchange": "binance",
  "exchange_type": "cex",
  "filled_amount": "0.001",
  "average_price": "45123.45",
  "fees": {"trading_fee": "0.075"}
}
```

#### Copy Trade
```bash
POST /copy-trade

Body:
{
  "source_exchange": "binance",
  "target_exchanges": ["coinbase", "uniswap"],
  "trade": {
    "user_id": "user123",
    "symbol": "ETH/USDT",
    "side": "buy",
    "order_type": "market",
    "amount": "1.0"
  }
}
```

#### Get Aggregated Balance
```bash
GET /balance?asset=BTC

Response:
{
  "asset": "BTC",
  "total_free": 0.5,
  "total_locked": 0.1,
  "total": 0.6,
  "by_exchange": {
    "binance": [{"asset": "BTC", "free": 0.3, "locked": 0.05, "total": 0.35}],
    "coinbase": [{"asset": "BTC", "free": 0.2, "locked": 0.05, "total": 0.25}]
  }
}
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│     Trading Orchestrator (Conductor)    │
│  - Smart routing                        │
│  - Order management                     │
│  - Multi-exchange coordination          │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼────┐
│  CEXes │      │  DEXes  │
└────────┘      └─────────┘
    │                │
    ├─ Binance       ├─ Uniswap (Base)
    ├─ Coinbase      ├─ Starknet (JediSwap)
    └─ ...           └─ ...
```

## 🔐 Security Best Practices

### API Key Management
```python
# Store CEX keys in Nillion for maximum security
from citadel.nillion_client import nillion

# Store Binance API credentials
key_id = await nillion.store_secret(binance_api_key, "binance-key")
secret_id = await nillion.store_secret(binance_secret, "binance-secret")

# Retrieve when needed for trading
api_key = await nillion.retrieve_secret(key_id)
```

### Private Key Protection
```bash
# Never commit private keys to git
echo "ETH_PRIVATE_KEY=*" >> .gitignore
echo ".env" >> .gitignore

# Use hardware wallets for production
# Or NEAR MPC for distributed key management
```

### Transaction Signing
```python
# Use NEAR MPC for DEX transaction signing
from conductor.near_client import near_mpc

# Derive controlled address
eth_address = near_mpc.derive_eth_address(
    near_account_id="trader.near",
    path="ethereum-trading-1"
)

# Sign DEX transaction via NEAR MPC (no local private key needed)
signature = await near_mpc.request_signature(
    payload=tx_hash,
    path="ethereum-trading-1",
    near_account_id="trader.near"
)
```

## 📊 Trading Strategies

### 1. Market Making
```python
# Provide liquidity on both CEX and DEX
async def market_making_strategy():
    # Place buy orders below market
    buy_order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        amount=Decimal("0.1"),
        price=market_price * Decimal("0.99")
    )
    
    # Place sell orders above market
    sell_order = TradeOrder(
        symbol="BTC/USDT",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        amount=Decimal("0.1"),
        price=market_price * Decimal("1.01")
    )
    
    await orchestrator.place_order('binance', buy_order)
    await orchestrator.place_order('binance', sell_order)
```

### 2. Arbitrage
```python
# Buy low on one exchange, sell high on another
async def arbitrage_strategy():
    prices = await orchestrator.get_best_price("BTC/USDT", OrderSide.BUY)
    
    buy_exchange = prices['best_exchange']
    buy_price = prices['best_price']
    
    # Find highest sell price
    sell_prices = await orchestrator.get_best_price("BTC/USDT", OrderSide.SELL)
    sell_exchange = sell_prices['best_exchange']
    sell_price = sell_prices['best_price']
    
    if sell_price > buy_price * Decimal("1.005"):  # 0.5% profit
        # Execute arbitrage
        await orchestrator.place_order(buy_exchange, buy_order)
        await orchestrator.place_order(sell_exchange, sell_order)
```

### 3. Copy Trading
```python
# Monitor a trader and replicate their trades
async def copy_trading_strategy(trader_exchange, follower_exchanges):
    # Monitor trader's orders
    trader_orders = await get_trader_orders(trader_exchange)
    
    for order in trader_orders:
        # Replicate to followers
        await orchestrator.replicate_trade(
            source_exchange=trader_exchange,
            target_exchanges=follower_exchanges,
            order=order
        )
```

## 🧪 Testing

### Run Examples
```bash
python examples_trading.py
```

### Unit Tests
```bash
pytest tests/test_exchanges.py -v
```

### Integration Tests
```bash
# Test with testnet credentials
export BINANCE_TESTNET=true
python -m pytest tests/integration/ -v
```

## 🎯 Use Cases

1. **Copy Trading Platform** - Replicate expert traders across multiple exchanges
2. **Arbitrage Bot** - Exploit price differences between exchanges
3. **Portfolio Rebalancing** - Maintain target allocations across platforms
4. **Market Making** - Provide liquidity on multiple venues
5. **DeFi Strategy Execution** - Bridge CEX and DEX for optimal yield
6. **Cross-Chain Trading** - Execute on best chain regardless of where funds are

## 🏆 Hackathon Integration

This trading infrastructure integrates with:
- **Nillion** - Secure storage of API keys and trading secrets
- **NEAR MPC** - Sign DEX transactions without local private keys
- **Zcash** - Accept shielded payments for premium trading features
- **Base** - Low-cost DEX execution via Uniswap
- **Starknet** - Alternative DEX for specific trading pairs

## 📚 Resources

- [CCXT Documentation](https://docs.ccxt.com/)
- [Web3.py Docs](https://web3py.readthedocs.io/)
- [Uniswap V2 Docs](https://docs.uniswap.org/contracts/v2/overview)
- [Starknet.py](https://starknetpy.readthedocs.io/)
- [Binance API](https://binance-docs.github.io/apidocs/spot/en/)
- [Coinbase Advanced Trade](https://docs.cloud.coinbase.com/advanced-trade-api/docs/welcome)

## 🤝 Contributing

To add a new exchange:

1. Create connector in `exchanges/{exchange}_connector.py`
2. Implement `ExchangeConnector` interface
3. Add to orchestrator in `exchanges/orchestrator.py`
4. Update tests and documentation

## 📄 License

MIT License - See LICENSE file
