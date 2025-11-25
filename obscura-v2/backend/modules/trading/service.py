"""
Trading Service - Standalone FastAPI service for trade execution

Can run as:
- Part of monolith (imported by api_gateway)
- Standalone microservice (python -m modules.trading.service)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn

from .key_storage import SecureKeyStorage, ExchangeProvider
from .exchanges.orchestrator import TradingOrchestrator
from .exchanges.universal_connector import list_supported_exchanges
from .exchanges.base import TradeOrder, OrderType, OrderSide

logger = logging.getLogger("obscura.trading")

# Initialize service
app = FastAPI(
    title="Obscura Trading Service",
    description="Multi-exchange trade execution with secure key storage",
    version="2.0.0",
)

# Service instances
key_storage = SecureKeyStorage()
orchestrator = TradingOrchestrator()


# =====================
# Request/Response Models
# =====================

class StoreCredentialsRequest(BaseModel):
    exchange: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    uid: Optional[str] = None
    label: Optional[str] = ""


class TradeRequest(BaseModel):
    credential_id: str
    exchange: str
    symbol: str
    side: str  # buy/sell
    order_type: str = "market"  # market/limit
    amount: float
    price: Optional[float] = None
    slippage: float = 0.02


class TradeResponse(BaseModel):
    order_id: str
    status: str
    filled_amount: float
    average_price: Optional[float]
    exchange: str


# =====================
# Health & Info
# =====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "trading",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/exchanges")
async def get_supported_exchanges():
    """List all supported exchanges"""
    supported = list_supported_exchanges()
    initialized = orchestrator.get_initialized_exchanges()
    
    return {
        "supported": supported,
        "initialized": initialized,
        "total_supported": supported['total']
    }


# =====================
# Credential Management
# =====================

@app.post("/credentials/store")
async def store_credentials(user_id: str, request: StoreCredentialsRequest):
    """Store exchange API credentials securely"""
    try:
        exchange = ExchangeProvider(request.exchange.lower())
    except ValueError:
        raise HTTPException(400, f"Unsupported exchange: {request.exchange}")
    
    credential_id = await key_storage.store_exchange_credentials(
        user_id=user_id,
        exchange=exchange,
        api_key=request.api_key,
        api_secret=request.api_secret,
        passphrase=request.passphrase,
        uid=request.uid,
        label=request.label
    )
    
    return {
        "credential_id": credential_id,
        "exchange": request.exchange,
        "message": "Credentials stored securely"
    }


@app.get("/credentials/list")
async def list_credentials(user_id: str):
    """List stored credentials (metadata only)"""
    credentials = await key_storage.list_user_credentials(user_id)
    return {"credentials": credentials}


@app.post("/credentials/{credential_id}/grant")
async def grant_access(
    credential_id: str,
    owner_id: str,
    grantee_id: str,
    permission: str = "trade"
):
    """Grant trade permission to another user"""
    success = await key_storage.grant_trade_permission(
        credential_id, owner_id, grantee_id, permission
    )
    if not success:
        raise HTTPException(400, "Failed to grant access")
    return {"message": f"Granted {permission} access to {grantee_id}"}


@app.delete("/credentials/{credential_id}")
async def delete_credentials(credential_id: str, owner_id: str):
    """Delete stored credentials"""
    success = await key_storage.delete_credentials(credential_id, owner_id)
    if not success:
        raise HTTPException(400, "Failed to delete credentials")
    return {"message": "Credentials deleted"}


# =====================
# Trade Execution
# =====================

@app.post("/trade/execute", response_model=TradeResponse)
async def execute_trade(user_id: str, request: TradeRequest):
    """Execute a trade"""
    # Get credentials
    creds = await key_storage.get_credentials_for_trading(
        request.credential_id, user_id
    )
    
    if not creds:
        raise HTTPException(401, "Invalid credentials or access denied")
    
    # Initialize exchange if needed
    if request.exchange not in orchestrator.exchanges:
        await orchestrator.add_exchange(request.exchange, creds)
    
    # Build order
    order = TradeOrder(
        symbol=request.symbol,
        side=OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL,
        order_type=OrderType.MARKET if request.order_type.lower() == "market" else OrderType.LIMIT,
        amount=Decimal(str(request.amount)),
        price=Decimal(str(request.price)) if request.price else None,
        slippage=Decimal(str(request.slippage))
    )
    
    result = await orchestrator.place_order(request.exchange, order)
    
    return TradeResponse(
        order_id=result.order_id,
        status=result.status,
        filled_amount=float(result.filled_amount),
        average_price=float(result.average_price) if result.average_price else None,
        exchange=request.exchange
    )


@app.get("/trade/best-price/{symbol}")
async def get_best_price(symbol: str, side: str = "buy"):
    """Get best price across exchanges"""
    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    prices = await orchestrator.get_best_price(symbol, order_side)
    return prices


@app.get("/trade/balance")
async def get_balance(asset: Optional[str] = None):
    """Get aggregated balance"""
    balance = await orchestrator.get_aggregated_balance(asset)
    return balance


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8001):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_standalone()
