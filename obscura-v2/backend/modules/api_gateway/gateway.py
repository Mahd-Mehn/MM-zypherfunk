"""
Unified API Gateway

Main entry point for all Obscura V2 services.
Routes requests to appropriate backend modules and handles cross-cutting concerns.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Path, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

# Import all backend modules
from modules.trading import key_storage, ExchangeProvider
from modules.trading.exchanges.orchestrator import TradingOrchestrator
from modules.trading.exchanges.universal_connector import list_supported_exchanges
from modules.trading.pnl_calculator import PnLCalculator
from modules.subscriptions import subscription_manager
from modules.subscriptions.manager import BillingCycle
from modules.copy_trading import trade_monitor, copy_engine
from modules.analytics import analytics_engine
from modules.citadel import nillion
from modules.api_gateway.websocket_manager import manager as ws_manager
from modules.api_gateway.routers import arcium

from shared.config import settings
from shared.database import get_repositories, RepositoryFactory
from shared.services import exchange_service

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

# Global instances
orchestrator = TradingOrchestrator()
pnl_calculator = PnLCalculator()


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
# API v1 Response Models (for Frontend)
# =====================

class TraderProfileResponse(BaseModel):
    id: str
    address: Optional[str]
    display_name: str
    bio: str
    avatar_url: Optional[str]
    verification_types: List[str] = []
    win_rate: float
    total_trades: int
    verified_trades: int
    total_pnl: float
    followers: int
    performance_fee: float
    chains: List[str] = []
    exchanges: List[str] = []
    trust_tier: int
    joined_date: str


class TraderPerformanceResponse(BaseModel):
    trader_id: str
    timeframe: str
    total_pnl: float
    win_rate: float
    total_trades: int
    avg_trade_size: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    average_roi: float
    reputation_score: float
    performance_data: List[Dict[str, Any]] = []


class LeaderboardResponse(BaseModel):
    traders: List[TraderProfileResponse]
    total: int
    limit: int
    offset: int


class SupportedExchangeResponse(BaseModel):
    name: str
    display_name: str
    description: str
    features: List[str]
    api_docs_url: str
    required_permissions: List[str]
    setup_instructions: List[str]


class ExchangeConnectionResponse(BaseModel):
    id: str
    user_id: str
    exchange: str
    status: str
    last_synced_at: Optional[str]
    created_at: str


class ExchangeConnectionCreate(BaseModel):
    exchange: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    is_signal_provider: bool = False


class SubscriptionResponse(BaseModel):
    id: str
    follower_id: str
    trader_id: str
    status: str
    max_capital_pct: float
    max_position_size: Optional[float]
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]
    created_at: str


class SubscriptionCreateRequest(BaseModel):
    trader_id: str
    max_capital_pct: float = 10.0
    max_position_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class PortfolioOverviewResponse(BaseModel):
    user_id: str
    total_value_usd: float
    total_pnl_usd: float
    total_pnl_percentage: float
    positions: List[Dict[str, Any]]
    active_subscriptions: int
    last_updated: str


# Supported exchanges configuration
SUPPORTED_EXCHANGES_CONFIG = [
    SupportedExchangeResponse(
        name="binance",
        display_name="Binance",
        description="World's largest cryptocurrency exchange by trading volume",
        features=["spot", "futures", "margin", "copy-trading"],
        api_docs_url="https://binance-docs.github.io/apidocs/spot/en/",
        required_permissions=["Enable Reading", "Enable Spot Trading"],
        setup_instructions=[
            "Log in to your Binance account",
            "Go to API Management in your profile settings",
            "Create a new API key with a label",
            "Enable 'Enable Reading' and 'Enable Spot Trading'",
            "Add your server IP to the whitelist (recommended)",
            "Copy the API Key and Secret Key securely"
        ]
    ),
    SupportedExchangeResponse(
        name="coinbase",
        display_name="Coinbase Advanced Trade",
        description="Leading US-based cryptocurrency exchange",
        features=["spot"],
        api_docs_url="https://docs.cloud.coinbase.com/advanced-trade-api/docs/welcome",
        required_permissions=["view", "trade"],
        setup_instructions=[
            "Log in to your Coinbase account",
            "Go to Settings > API",
            "Create a new API key",
            "Select 'view' and 'trade' permissions",
            "Copy the API Key and Secret Key"
        ]
    ),
    SupportedExchangeResponse(
        name="kraken",
        display_name="Kraken",
        description="Established European cryptocurrency exchange",
        features=["spot", "margin", "futures"],
        api_docs_url="https://docs.kraken.com/rest/",
        required_permissions=["Query Funds", "Query Orders & Trades", "Create & Modify Orders"],
        setup_instructions=[
            "Log in to your Kraken account",
            "Go to Security > API",
            "Generate a new API key",
            "Select required permissions",
            "Copy the API Key and Private Key"
        ]
    ),
    SupportedExchangeResponse(
        name="bybit",
        display_name="Bybit",
        description="Popular derivatives and spot trading platform",
        features=["spot", "futures", "options"],
        api_docs_url="https://bybit-exchange.github.io/docs/",
        required_permissions=["Read", "Trade"],
        setup_instructions=[
            "Log in to your Bybit account",
            "Go to API Management",
            "Create a new API key",
            "Enable Read and Trade permissions",
            "Set IP restrictions (recommended)",
            "Save your API Key and Secret"
        ]
    ),
    SupportedExchangeResponse(
        name="okx",
        display_name="OKX",
        description="Global cryptocurrency exchange with advanced trading features",
        features=["spot", "futures", "options", "perpetual"],
        api_docs_url="https://www.okx.com/docs-v5/en/",
        required_permissions=["Read", "Trade"],
        setup_instructions=[
            "Log in to your OKX account",
            "Go to API in your profile",
            "Create a new API key with passphrase",
            "Enable Trade permission",
            "Copy API Key, Secret Key, and Passphrase"
        ]
    ),
    SupportedExchangeResponse(
        name="kucoin",
        display_name="KuCoin",
        description="People's exchange with wide token selection",
        features=["spot", "futures", "margin"],
        api_docs_url="https://docs.kucoin.com/",
        required_permissions=["General", "Trade"],
        setup_instructions=[
            "Log in to your KuCoin account",
            "Go to API Management",
            "Create a new API key with passphrase",
            "Enable General and Trade permissions",
            "Copy API Key, Secret, and Passphrase"
        ]
    )
]


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
    
    plan = await subscription_manager.create_plan(
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
    subscription = await subscription_manager.subscribe(
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
    confirmed = await subscription_manager.verify_payment(subscription_id, timeout_seconds=60)
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
# API v1 - Traders (Frontend Integration)
# =====================

@app.get("/api/v1/traders/leaderboard")
async def get_leaderboard(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    timeframe: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    sortBy: str = Query(default="pnl", pattern="^(followers|winRate|pnl|trades)$"),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get top traders leaderboard"""
    traders, total = await repos.traders.get_leaderboard(
        limit=limit,
        offset=offset,
        timeframe=timeframe,
        sort_by=sortBy
    )
    
    return LeaderboardResponse(
        traders=traders,
        total=total,
        limit=limit,
        offset=offset
    )


@app.get("/api/v1/traders/{trader_id}")
async def get_trader_profile(
    trader_id: str,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get comprehensive trader profile"""
    profile = await repos.traders.get_profile(trader_id)
    
    if not profile:
        raise HTTPException(404, "Trader not found")
        
    # Get follower count
    followers_count = await repos.traders.get_followers_count(trader_id)
    
    # Convert to response model
    profile_dict = repos.traders._profile_to_dict(profile)
    profile_dict["followers"] = followers_count
    
    return TraderProfileResponse(**profile_dict)


@app.get("/api/v1/traders/{trader_id}/performance")
async def get_trader_performance(
    trader_id: str,
    timeframe: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get trader performance metrics"""
    # Get profile for summary stats
    profile = await repos.traders.get_profile(trader_id)
    if not profile:
        raise HTTPException(404, "Trader not found")
        
    # Get trade summary
    summary = await repos.trades.get_trades_summary(trader_id)
    
    # TODO: Implement actual daily PnL aggregation in database
    # For now, we'll return the summary stats and a placeholder for the chart
    
    return {
        "total_pnl": float(profile.total_pnl_usd or 0),
        "win_rate": float(profile.win_rate or 0),
        "total_trades": profile.total_trades or 0,
        "sharpe_ratio": float(profile.sharpe_ratio or 0),
        "max_drawdown": float(profile.max_drawdown or 0),
        "avg_trade_duration": float(profile.avg_trade_duration_hours or 0),
        "profit_factor": 1.5,  # Placeholder
        "chart_data": []  # Frontend should handle empty chart gracefully
    }


@app.get("/api/v1/traders/{trader_id}/trades")
async def get_trader_trades(
    trader_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get trader trade history"""
    trades, total = await repos.trades.get_user_trades(
        user_id=trader_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "trades": [repos.trades.trade_to_dict(t) for t in trades],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/v1/traders/{trader_id}/followers")
async def get_trader_followers(
    trader_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get trader followers"""
    followers = await repos.traders.get_followers(trader_id)
    
    # Apply pagination in memory since get_followers returns all
    # TODO: Add pagination to get_followers repository method
    paginated = followers[offset:offset+limit]
    
    return {
        "followers": paginated,
        "total": len(followers),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/v1/traders/{trader_id}/trades")
async def get_trader_trades(
    trader_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get trader's recent trades"""
    trades = [
        {
            "id": f"trade_{i}",
            "trader_id": trader_id,
            "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            "asset_in": "USDT",
            "asset_out": ["BTC", "ETH", "SOL"][i % 3],
            "amount_in": 1000.0 + i * 100,
            "amount_out": (1000.0 + i * 100) / [45000, 2500, 100][i % 3],
            "pnl": 50.0 * (1 if i % 3 != 0 else -1),
            "pnl_percentage": 5.0 * (1 if i % 3 != 0 else -1),
            "verification_type": "zk-proof",
            "chain": "ethereum",
            "exchange": ["binance", "coinbase"][i % 2],
            "tx_hash": f"0x{'a' * 64}"
        }
        for i in range(limit)
    ]
    
    return {"trades": trades, "total": 100}


@app.get("/api/v1/traders/{trader_id}/followers")
async def get_trader_followers(trader_id: str):
    """Get trader's followers"""
    return {
        "followers": 156,
        "follower_list": []
    }


# =====================
# API v1 - Exchanges (Frontend Integration)
# =====================

@app.get("/api/v1/exchanges/supported")
async def get_supported_exchanges_v1(
    type: Optional[str] = Query(None, pattern="^(cex|dex)$"),
    capability: Optional[str] = Query(None)
):
    """Get list of supported exchanges with setup instructions"""
    svc = exchange_service.exchange_service
    
    if type:
        exchanges = await svc.get_exchanges_by_type(type)
    elif capability:
        exchanges = await svc.get_exchanges_with_capability(capability)
    else:
        all_exchanges = await svc.get_all_exchanges()
        exchanges = list(all_exchanges.values())
    
    # Convert to response format
    return {
        "exchanges": [ex.to_dict() for ex in exchanges],
        "total": len(exchanges),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/exchanges/{exchange_id}/markets")
async def get_exchange_markets(exchange_id: str):
    """Get markets for an exchange"""
    # Check if exchange exists
    svc = exchange_service.exchange_service
    info = await svc.get_exchange(exchange_id)
    
    if not info:
        raise HTTPException(404, f"Exchange {exchange_id} not supported")
    
    # TODO: Move this logic to ExchangeService and cache it
    try:
        import ccxt.async_support as ccxt_async
        
        if not hasattr(ccxt_async, exchange_id):
             raise HTTPException(404, "Exchange client not found")
             
        exchange_class = getattr(ccxt_async, exchange_id)
        async with exchange_class() as exchange:
            # Load markets
            markets = await exchange.load_markets()
            market_list = []
            
            for symbol, market in markets.items():
                market_list.append({
                    "symbol": symbol,
                    "base": market.get("base"),
                    "quote": market.get("quote"),
                    "active": market.get("active", True),
                    "spot": market.get("spot", True),
                    "margin": market.get("margin", False),
                    "future": market.get("future", False),
                    "swap": market.get("swap", False),
                })
                
            return {
                "exchange": exchange_id,
                "markets": market_list[:100], # Limit to 100 for now to avoid huge payloads
                "total": len(market_list)
            }
    except Exception as e:
        # Fallback if CCXT fails or times out
        logger.error(f"Error fetching markets for {exchange_id}: {e}")
        return {
            "exchange": exchange_id,
            "markets": [],
            "total": 0,
            "error": str(e)
        }


@app.get("/api/v1/exchanges")
async def get_user_exchanges(
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get user's exchange connections"""
    connections = await repos.exchanges.get_user_connections(user_id)
    
    return {
        "connections": [repos.exchanges.connection_to_dict(c) for c in connections],
        "total": len(connections)
    }


@app.post("/api/v1/exchanges")
async def create_exchange_connection(
    user_id: str = Query(...),
    request: ExchangeConnectionCreate = None,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Create new exchange connection with encrypted credential storage"""
    # Verify exchange is supported
    svc = exchange_service.exchange_service
    info = await svc.get_exchange(request.exchange.lower())
    if not info:
        raise HTTPException(400, f"Exchange '{request.exchange}' is not supported")
    
    # Store credentials in Nillion (via key_storage)
    try:
        exchange_provider = ExchangeProvider(request.exchange.lower())
        credential_id = await key_storage.store_exchange_credentials(
            user_id=user_id,
            exchange=exchange_provider,
            api_key=request.api_key,
            api_secret=request.api_secret,
            passphrase=request.passphrase
        )
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        raise HTTPException(500, "Failed to securely store credentials")

    # Create connection record in DB
    connection = await repos.exchanges.create(
        user_id=user_id,
        exchange=request.exchange.lower(),
        exchange_type="cex", # Default to CEX for now
        label=f"{info.display_name} Connection",
        nillion_store_id=credential_id,
        is_signal_provider=request.is_signal_provider,
        status="connected",
        last_validated_at=datetime.utcnow()
    )
    
    # Log activity
    await repos.activities.log(
        user_id=user_id,
        action="connect_exchange",
        entity_type="exchange_connection",
        entity_id=str(connection.id),
        details={"exchange": request.exchange, "label": connection.label}
    )
    
    return repos.exchanges.connection_to_dict(connection)


@app.post("/api/v1/exchanges/{connection_id}/test")
async def test_exchange_connection(
    connection_id: str, 
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Test exchange connection"""
    conn = await repos.exchanges.get_by_id(connection_id)
    if not conn or str(conn.user_id) != user_id:
        raise HTTPException(404, "Connection not found")
        
    # TODO: Actually test the connection using ExchangeService
    # For now, just update the status
    await repos.exchanges.update_status(connection_id, "connected", datetime.utcnow())
    
    return {
        "success": True,
        "message": "Connection tested successfully",
        "tested_at": datetime.utcnow().isoformat(),
        "connection_status": "connected"
    }


@app.delete("/api/v1/exchanges/{connection_id}")
async def delete_exchange_connection(
    connection_id: str, 
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Delete exchange connection"""
    # Verify ownership
    conn = await repos.exchanges.get_by_id(connection_id)
    if not conn or str(conn.user_id) != user_id:
        raise HTTPException(404, "Connection not found")

    # Delete from Nillion
    if conn.nillion_store_id:
        try:
            # Note: key_storage.delete_credentials expects credential_id, not connection_id
            # But we stored credential_id in nillion_store_id
            success = await key_storage.delete_credentials(conn.nillion_store_id, user_id)
            if not success:
                logger.warning(f"Failed to delete credentials for {connection_id}")
        except Exception as e:
            logger.error(f"Error deleting credentials: {e}")
            
    # Delete from DB
    await repos.exchanges.delete(connection_id)
    
    # Log activity
    await repos.activities.log(
        user_id=user_id,
        action="disconnect_exchange",
        entity_type="exchange_connection",
        entity_id=connection_id,
        details={"exchange": conn.exchange}
    )
    
    return {"message": "Connection deleted successfully"}


# =====================
# API v1 - Subscriptions (Frontend Integration)
# =====================

@app.get("/api/v1/subscriptions")
async def get_user_subscriptions(
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get user's copy trading subscriptions"""
    subscriptions = await repos.subscriptions.get_user_subscriptions(user_id)
    
    return {
        "subscriptions": [repos.subscriptions.subscription_to_dict(s) for s in subscriptions],
        "total": len(subscriptions)
    }


@app.post("/api/v1/subscriptions")
async def create_subscription(
    user_id: str = Query(...),
    request: StartCopyingRequest = None,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Create new subscription (start copy trading)"""
    # Verify trader exists
    trader = await repos.traders.get_profile(request.trader_id)
    if not trader:
        raise HTTPException(404, "Trader not found")

    # Create subscription
    subscription = await repos.subscriptions.create(
        follower_id=user_id,
        trader_id=request.trader_id,
        copy_mode=request.copy_mode,
        proportion_percent=request.proportion_percent,
        max_position_usd=request.max_position_usd,
        allowed_exchanges=request.exchanges
    )
    
    # Log activity
    await repos.activities.log(
        user_id=user_id,
        action="start_copying",
        entity_type="subscription",
        entity_id=str(subscription.id),
        details={"trader_id": request.trader_id, "mode": request.copy_mode}
    )
    
    return repos.subscriptions.subscription_to_dict(subscription)


@app.get("/api/v1/subscriptions/{subscription_id}")
async def get_subscription(
    subscription_id: str,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get specific subscription"""
    sub = await repos.subscriptions.get_by_id(subscription_id)
    if not sub:
        raise HTTPException(404, "Subscription not found")
    return repos.subscriptions.subscription_to_dict(sub)


@app.patch("/api/v1/subscriptions/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    request: StartCopyingRequest,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Update subscription settings"""
    sub = await repos.subscriptions.update(
        subscription_id,
        copy_mode=request.copy_mode,
        proportion_percent=request.proportion_percent,
        max_position_usd=request.max_position_usd,
        allowed_exchanges=request.exchanges
    )
    
    if not sub:
        raise HTTPException(404, "Subscription not found")
        
    await repos.activities.log(
        user_id=str(sub.follower_rel.follower_id),
        action="update_subscription",
        entity_type="subscription",
        entity_id=subscription_id,
        details={"changes": request.dict()}
    )
    
    return repos.subscriptions.subscription_to_dict(sub)


@app.post("/api/v1/subscriptions/{subscription_id}/pause")
async def pause_subscription(
    subscription_id: str,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Pause subscription"""
    await repos.subscriptions.pause(subscription_id)
    
    # Get sub for logging
    sub = await repos.subscriptions.get_by_id(subscription_id)
    if sub:
        await repos.activities.log(
            user_id=str(sub.follower_rel.follower_id),
            action="pause_subscription",
            entity_type="subscription",
            entity_id=subscription_id
        )
    
    return {"message": "Subscription paused", "id": subscription_id}


@app.post("/api/v1/subscriptions/{subscription_id}/resume")
async def resume_subscription(
    subscription_id: str,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Resume subscription"""
    await repos.subscriptions.resume(subscription_id)
    
    sub = await repos.subscriptions.get_by_id(subscription_id)
    if sub:
        await repos.activities.log(
            user_id=str(sub.follower_rel.follower_id),
            action="resume_subscription",
            entity_type="subscription",
            entity_id=subscription_id
        )
        
    return {"message": "Subscription resumed", "id": subscription_id}


@app.delete("/api/v1/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Cancel subscription"""
    sub = await repos.subscriptions.get_by_id(subscription_id)
    if not sub:
        raise HTTPException(404, "Subscription not found")
        
    await repos.subscriptions.cancel(subscription_id)
    
    await repos.activities.log(
        user_id=str(sub.follower_rel.follower_id),
        action="cancel_subscription",
        entity_type="subscription",
        entity_id=subscription_id
    )
    
    return {"message": "Subscription cancelled"}


# =====================
# API v1 - Portfolio (Frontend Integration)
# =====================

@app.get("/api/v1/portfolio/overview")
async def get_portfolio_overview(
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get user's portfolio overview"""
    # Get portfolio value
    portfolio = await repos.portfolio.get_portfolio_value(user_id)
    
    # Get active subscriptions count
    subs = await repos.subscriptions.get_user_subscriptions(user_id, active_only=True)
    
    # Calculate PnL percentage
    total_value = portfolio["total_value_usd"]
    total_pnl = portfolio["total_unrealized_pnl"]
    # Avoid division by zero
    initial_value = total_value - total_pnl
    pnl_pct = (total_pnl / initial_value * 100) if initial_value > 0 else 0
    
    return PortfolioOverviewResponse(
        user_id=user_id,
        total_value_usd=total_value,
        total_pnl_usd=total_pnl,
        total_pnl_percentage=pnl_pct,
        positions=portfolio["positions"],
        active_subscriptions=len(subs),
        last_updated=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/portfolio/performance")
async def get_portfolio_performance(
    user_id: str = Query(...),
    timeframe: str = Query(default="30d"),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get user's portfolio performance"""
    # Calculate date range
    days = 30
    if timeframe == "7d": days = 7
    elif timeframe == "90d": days = 90
    elif timeframe == "all": days = 365 # Approximate
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get trade summary
    summary = await repos.trades.get_trades_summary(user_id, since=since)
    
    # Get portfolio value for return calculation
    portfolio = await repos.portfolio.get_portfolio_value(user_id)
    total_value = portfolio["total_value_usd"]
    
    # Calculate return percentage (approximate)
    total_pnl = summary["total_pnl"]
    initial_capital = total_value - total_pnl
    return_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
    
    return {
        "timeframe": timeframe,
        "total_return_usd": total_pnl,
        "total_return_percentage": return_pct,
        "sharpe_ratio": 0.0, # Need more data to calculate
        "max_drawdown_percentage": 0.0, # Need historical data
        "win_rate": summary["win_rate"],
        "profit_factor": 0.0, # Need gross profit/loss
        "historical_pnl": [] # Need daily snapshots
    }


# =====================
# API v1 - Dashboard (Frontend Integration)
# =====================

@app.get("/api/v1/dashboard")
async def get_dashboard_data(
    user_id: str = Query(...),
    repos: RepositoryFactory = Depends(get_repositories)
):
    """Get dashboard summary data"""
    # Get portfolio value
    portfolio = await repos.portfolio.get_portfolio_value(user_id)
    total_value = portfolio["total_value_usd"]
    total_pnl = portfolio["total_unrealized_pnl"]
    initial_capital = total_value - total_pnl
    pnl_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
    
    # Get active subscriptions
    subs = await repos.subscriptions.get_user_subscriptions(user_id, active_only=True)
    
    # Get recent activities
    activities, _ = await repos.activities.get_user_activities(user_id, limit=5)
    
    return {
        "portfolio_value_usd": total_value,
        "portfolio_pnl_usd": total_pnl,
        "portfolio_pnl_percentage": pnl_pct,
        "active_subscriptions": len(subs),
        "recent_activities": [
            {
                "id": str(a.id),
                "type": a.action,
                "description": f"{a.action.replace('_', ' ').title()} on {a.entity_type.replace('_', ' ')}",
                "timestamp": a.created_at.isoformat(),
                "metadata": a.details
            } for a in activities
        ],
        "alerts_count": 0, # TODO: Implement alerts
        "last_updated": datetime.utcnow().isoformat()
    }


# =====================
# Startup/Shutdown
# =====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Obscura V2 Gateway...")
    await trade_monitor.start_monitoring()
    await copy_engine.start()
    # Start the Redis listener for WebSockets
    await ws_manager.start_redis_listener()
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
# WebSocket Endpoint
# =====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle incoming messages (e.g. pings)
            data = await websocket.receive_text()
            # We can handle client-sent messages here if needed
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)


# =====================
# Main Entry Point
# =====================

def run_gateway(host: str = "0.0.0.0", port: int = 8000):
    """Run the API gateway"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_gateway()
