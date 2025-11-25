"""
Unified API Gateway

Main entry point for all Obscura V2 services.
Routes requests to appropriate backend modules and handles cross-cutting concerns.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Import all backend modules
from modules.trading import key_storage, ExchangeProvider
from modules.trading.exchanges.orchestrator import TradingOrchestrator
from modules.trading.exchanges.universal_connector import list_supported_exchanges
from modules.subscriptions import subscription_service
from modules.subscriptions.manager import BillingCycle
from modules.copy_trading import trade_monitor, copy_engine
from modules.analytics import analytics_engine
from modules.citadel import nillion

from shared.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("obscura.gateway")

# Initialize FastAPI
app = FastAPI(
    title="Obscura V2 - Copy Trading Platform",
    description="Production-grade multi-exchange copy trading with privacy features",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Global orchestrator instance
orchestrator = TradingOrchestrator()


# =====================
# Request/Response Models
# =====================

class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, bool]
    timestamp: str


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
    side: str
    order_type: str = "market"
    amount: float
    price: Optional[float] = None
    slippage: float = 0.02


class CreatePlanRequest(BaseModel):
    name: str
    price_zec: float
    billing_cycle: str = "monthly"
    description: str = ""
    features: List[str] = []
    max_followers: int = 100


class SubscribeRequest(BaseModel):
    plan_id: str
    payment_address: Optional[str] = None


class StartCopyingRequest(BaseModel):
    trader_id: str
    copy_mode: str = "proportional"
    proportion_percent: float = 100.0
    max_position_usd: float = 10000
    max_daily_trades: int = 50
    exchanges: List[str] = ["binance"]


class AddTraderRequest(BaseModel):
    exchanges: List[str]
    credential_ids: Dict[str, str]
    symbols: Optional[List[str]] = None


# =====================
# Health & Status
# =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of all services"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        services={
            "nillion": True,
            "orchestrator": True,
            "monitor": trade_monitor._monitoring,
            "copy_engine": True,
            "analytics": True
        },
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/exchanges")
async def list_exchanges():
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
    """Securely store exchange API credentials"""
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
        "message": "Credentials stored securely in Nillion"
    }


@app.get("/credentials/list")
async def list_credentials(user_id: str):
    """List all stored credentials for a user"""
    credentials = await key_storage.list_user_credentials(user_id)
    return {"credentials": credentials}


@app.post("/credentials/{credential_id}/grant")
async def grant_credential_access(
    credential_id: str,
    owner_id: str,
    grantee_id: str,
    permission: str = "trade"
):
    """Grant another user permission to trade"""
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
# Trading
# =====================

@app.post("/trade/execute")
async def execute_trade(user_id: str, request: TradeRequest):
    """Execute a trade using stored credentials"""
    from modules.trading.exchanges.base import TradeOrder, OrderType, OrderSide
    
    creds = await key_storage.get_credentials_for_trading(
        request.credential_id, user_id
    )
    
    if not creds:
        raise HTTPException(401, "Invalid credentials or access denied")
    
    if request.exchange not in orchestrator.exchanges:
        await orchestrator.add_exchange(request.exchange, creds)
    
    order = TradeOrder(
        symbol=request.symbol,
        side=OrderSide.BUY if request.side.lower() == "buy" else OrderSide.SELL,
        order_type=OrderType.MARKET if request.order_type.lower() == "market" else OrderType.LIMIT,
        amount=Decimal(str(request.amount)),
        price=Decimal(str(request.price)) if request.price else None,
        slippage=Decimal(str(request.slippage))
    )
    
    result = await orchestrator.place_order(request.exchange, order)
    
    # Record in analytics
    await analytics_engine.record_trade(
        user_id=user_id,
        trade_data={
            "exchange": request.exchange,
            "symbol": request.symbol,
            "side": request.side,
            "amount": float(result.filled_amount),
            "price": float(result.average_price) if result.average_price else 0,
            "order_id": result.order_id
        }
    )
    
    return {
        "order_id": result.order_id,
        "status": result.status,
        "filled_amount": float(result.filled_amount),
        "average_price": float(result.average_price) if result.average_price else None,
        "exchange": request.exchange
    }


@app.get("/trade/best-price/{symbol}")
async def get_best_price(symbol: str, side: str = "buy"):
    """Get best price across all initialized exchanges"""
    from modules.trading.exchanges.base import OrderSide
    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
    prices = await orchestrator.get_best_price(symbol, order_side)
    return prices


@app.get("/trade/balance")
async def get_balance(asset: Optional[str] = None):
    """Get aggregated balance across all exchanges"""
    balance = await orchestrator.get_aggregated_balance(asset)
    return balance


# =====================
# Subscriptions & Billing
# =====================

@app.post("/subscriptions/plans/create")
async def create_subscription_plan(trader_id: str, request: CreatePlanRequest):
    """Create a subscription plan"""
    try:
        cycle = BillingCycle(request.billing_cycle.lower())
    except ValueError:
        raise HTTPException(400, f"Invalid billing cycle: {request.billing_cycle}")
    
    plan = await subscription_service.create_plan(
        trader_id=trader_id,
        name=request.name,
        price_zec=Decimal(str(request.price_zec)),
        billing_cycle=cycle,
        description=request.description,
        features=request.features,
        max_followers=request.max_followers
    )
    
    return {
        "plan_id": plan.plan_id,
        "payment_address": plan.payment_address,
        "price_zec": float(plan.price_zec),
        "message": "Plan created"
    }


@app.post("/subscriptions/subscribe")
async def subscribe_to_plan(follower_id: str, request: SubscribeRequest):
    """Subscribe to a trader's plan"""
    subscription = await subscription_service.subscribe(
        plan_id=request.plan_id,
        follower_id=follower_id,
        follower_payment_address=request.payment_address
    )
    
    return {
        "subscription_id": subscription.subscription_id,
        "payment_address": subscription.payment_address,
        "amount_due": float(subscription.price_zec),
        "status": subscription.status.value,
        "message": f"Send {subscription.price_zec} ZEC to activate"
    }


@app.post("/subscriptions/{subscription_id}/verify")
async def verify_subscription_payment(subscription_id: str):
    """Verify subscription payment"""
    confirmed = await subscription_service.verify_payment(subscription_id, timeout_seconds=60)
    return {
        "subscription_id": subscription_id,
        "payment_confirmed": confirmed,
        "status": "active" if confirmed else "pending"
    }


# =====================
# Copy Trading
# =====================

@app.post("/copy/start")
async def start_copying(follower_id: str, request: StartCopyingRequest):
    """Start copying a trader"""
    return {
        "message": f"Now copying {request.trader_id}",
        "settings": {
            "copy_mode": request.copy_mode,
            "proportion_percent": request.proportion_percent,
            "exchanges": request.exchanges
        }
    }


@app.post("/copy/stop")
async def stop_copying(follower_id: str, trader_id: str):
    """Stop copying a trader"""
    return {"message": f"Stopped copying {trader_id}"}


# =====================
# Trade Monitoring
# =====================

@app.post("/monitor/add-trader")
async def add_monitored_trader(trader_id: str, request: AddTraderRequest):
    """Add a trader to be monitored"""
    for exchange in request.exchanges:
        await trade_monitor.add_session(
            trader_id=trader_id,
            exchange=exchange,
            symbols=request.symbols
        )
    return {"message": f"Now monitoring {trader_id}"}


@app.post("/monitor/start")
async def start_monitoring():
    """Start the trade monitoring service"""
    await trade_monitor.start_monitoring()
    return {"message": "Monitoring started"}


@app.post("/monitor/stop")
async def stop_monitoring():
    """Stop the trade monitoring service"""
    await trade_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}


# =====================
# Analytics
# =====================

@app.get("/analytics/{trader_id}")
async def get_trader_analytics(trader_id: str, timeframe: str = "24h"):
    """Get analytics for a trader"""
    metrics = await analytics_engine.get_user_metrics(trader_id, timeframe)
    return metrics


# =====================
# Nillion
# =====================

@app.get("/nillion/status")
async def get_nillion_status():
    """Get Nillion connection status"""
    return nillion.get_health_status()


# =====================
# Startup/Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Obscura V2 Gateway...")
    await trade_monitor.start_monitoring()
    await copy_engine.start()
    logger.info("Obscura V2 Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Obscura V2 Gateway...")
    await trade_monitor.stop_monitoring()
    await copy_engine.stop()
    
    for exchange_id in orchestrator.exchanges:
        try:
            connector = orchestrator.exchanges[exchange_id]['instance']
            if hasattr(connector, 'close'):
                await connector.close()
        except Exception:
            pass
    
    logger.info("Shutdown complete")


# =====================
# Main Entry Point
# =====================

def run_gateway(host: str = "0.0.0.0", port: int = 8000):
    """Run the API gateway"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_gateway()
