from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from conductor.near_client import near_mpc
from exchanges.orchestrator import TradingOrchestrator
from exchanges.base import TradeOrder, OrderType, OrderSide

app = FastAPI(title="Conductor (Multi-Exchange Trading)", version="3.0.0")

# Global trading orchestrator
orchestrator = TradingOrchestrator()

class TradeIntent(BaseModel):
    user_id: str
    exchange: Optional[str] = None  # If None, uses smart routing
    symbol: str  # e.g., "BTC/USDT"
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    amount: Decimal
    price: Optional[Decimal] = None
    slippage: Optional[Decimal] = None
    strategy: str = "best_price"  # "best_price", "fallback", "parallel"

class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    exchange: str
    exchange_type: str
    tx_hash: Optional[str] = None
    derived_address: Optional[str] = None
    filled_amount: Decimal
    average_price: Decimal
    fees: Dict[str, Decimal]

class ExchangeConfig(BaseModel):
    exchanges: Dict[str, Dict[str, Any]]


@app.on_event("startup")
async def startup_event():
    """Initialize trading infrastructure on startup"""
    config = {
        'binance': {
            'api_key': os.getenv('BINANCE_API_KEY'),
            'api_secret': os.getenv('BINANCE_API_SECRET')
        } if os.getenv('BINANCE_API_KEY') else None,
        'coinbase': {
            'api_key': os.getenv('COINBASE_API_KEY'),
            'api_secret': os.getenv('COINBASE_API_SECRET')
        } if os.getenv('COINBASE_API_KEY') else None,
        'uniswap': {
            'private_key': os.getenv('ETH_PRIVATE_KEY'),
            'rpc_url': os.getenv('BASE_RPC_URL')
        } if os.getenv('ETH_PRIVATE_KEY') else None,
        'starknet': {
            'private_key': os.getenv('STARKNET_PRIVATE_KEY'),
            'account_address': os.getenv('STARKNET_ACCOUNT_ADDRESS')
        } if os.getenv('STARKNET_PRIVATE_KEY') else None
    }
    
    # Filter out None values
    config = {k: v for k, v in config.items() if v}
    
    if config:
        results = await orchestrator.initialize_all_exchanges(config)
        print(f"Exchange initialization results: {results}")
    else:
        print("No exchange credentials configured. Running in demo mode.")

@app.get("/health")
async def health_check():
    status = orchestrator.get_exchange_status()
    return {
        "status": "healthy",
        "execution_layer": "multi-exchange-orchestrator",
        "near_mpc": "enabled",
        "exchanges": status
    }

@app.post("/configure", status_code=200)
async def configure_exchanges(config: ExchangeConfig):
    """Dynamically configure exchanges at runtime"""
    try:
        results = await orchestrator.initialize_all_exchanges(config.exchanges)
        return {
            "status": "configured",
            "results": results,
            "active_exchanges": orchestrator.initialized_exchanges
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exchanges")
async def get_exchanges():
    """Get status of all configured exchanges"""
    return orchestrator.get_exchange_status()

@app.get("/pairs")
async def get_supported_pairs():
    """Get all supported trading pairs across exchanges"""
    try:
        pairs = await orchestrator.get_all_supported_pairs()
        return {"pairs": pairs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/balance")
async def get_balance(asset: Optional[str] = None):
    """Get aggregated balance across all exchanges"""
    try:
        balance = await orchestrator.get_aggregated_balance(asset)
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/price/{symbol}")
async def get_best_price(symbol: str, side: str = "buy"):
    """Get best price across all exchanges"""
    try:
        side_enum = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        best_price = await orchestrator.get_best_price(symbol, side_enum)
        return best_price
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute", response_model=ExecutionResponse)
async def execute_trade(intent: TradeIntent):
    """
    Execute a trade with smart routing across CEXes and DEXes.
    Supports:
    - Binance, Coinbase (CEX)
    - Uniswap on Base (DEX)
    - Starknet DEXes (DEX)
    - NEAR MPC for cross-chain execution
    """
    try:
        # Build trade order
        order = TradeOrder(
            symbol=intent.symbol,
            side=OrderSide(intent.side.lower()),
            order_type=OrderType(intent.order_type.lower()),
            amount=intent.amount,
            price=intent.price,
            slippage=intent.slippage
        )
        
        # Execute based on strategy
        if intent.exchange:
            # Execute on specific exchange
            result = await orchestrator.place_order(intent.exchange, order)
        else:
            # Use smart routing
            result = await orchestrator.execute_smart_order(order, strategy=intent.strategy)
        
        # If DEX trade, optionally use NEAR MPC for signing
        derived_address = None
        if result.exchange_type.value == "dex" and os.getenv("NEAR_ACCOUNT_ID"):
            path = f"user/{intent.user_id}/trade"
            derived_address = near_mpc.derive_eth_address(
                os.getenv("NEAR_ACCOUNT_ID", "obscura.testnet"), 
                path
            )
        
        return ExecutionResponse(
            execution_id=result.order_id,
            status=result.status,
            exchange=result.exchange,
            exchange_type=result.exchange_type.value,
            tx_hash=result.tx_hash,
            derived_address=derived_address,
            filled_amount=result.filled_amount,
            average_price=result.average_price,
            fees=result.fees
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/copy-trade")
async def copy_trade(
    source_exchange: str,
    target_exchanges: List[str],
    trade: TradeIntent
):
    """
    Replicate a trade from source to multiple target exchanges.
    Perfect for copy-trading implementation.
    """
    try:
        order = TradeOrder(
            symbol=trade.symbol,
            side=OrderSide(trade.side.lower()),
            order_type=OrderType(trade.order_type.lower()),
            amount=trade.amount,
            price=trade.price,
            slippage=trade.slippage
        )
        
        results = await orchestrator.replicate_trade(
            source_exchange,
            target_exchanges,
            order,
            delay_ms=100
        )
        
        return {
            "status": "replicated",
            "source_exchange": source_exchange,
            "target_exchanges": target_exchanges,
            "total_executions": len(results),
            "results": [
                {
                    "exchange": r.exchange,
                    "order_id": r.order_id,
                    "status": r.status,
                    "filled_amount": float(r.filled_amount),
                    "average_price": float(r.average_price)
                } for r in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import hashlib

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
