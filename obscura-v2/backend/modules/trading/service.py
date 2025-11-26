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
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn

from .key_storage import SecureKeyStorage, ExchangeProvider
from .exchanges.orchestrator import TradingOrchestrator
from .exchanges.universal_connector import list_supported_exchanges
from .exchanges.base import TradeOrder, OrderType, OrderSide
from .pnl_calculator import PnLCalculator, ReputationScore, ClosedTrade

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
pnl_calculator = PnLCalculator()


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


class ClosedTradeResponse(BaseModel):
    """Response model for a closed trade"""
    symbol: str
    entry_date: str
    exit_date: str
    duration_hours: float
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    gross_pnl: float
    fee: float
    net_pnl: float
    roi_percentage: float


class PerformanceResponse(BaseModel):
    """Response model for trading performance metrics"""
    user_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_usd: float
    profit_factor: float
    average_roi: float
    reputation_score: float
    generated_at: str
    closed_trades: List[ClosedTradeResponse]
    open_positions: Dict[str, Any]


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
# Performance & Analytics
# =====================

@app.get("/performance/{user_id}", response_model=PerformanceResponse)
async def get_user_performance(
    user_id: str,
    exchange: Optional[str] = Query(None, description="Specific exchange or 'all'"),
    symbol: Optional[str] = Query(None, description="Specific trading pair"),
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
):
    """
    Calculate PnL and reputation score for a user's trades.
    
    Returns:
    - Total trades, win rate, profit factor
    - Total PnL in USD
    - Average ROI per trade
    - Reputation score (0-100)
    - List of closed positions
    - Open positions
    """
    try:
        # Calculate 'since' timestamp
        since_dt = datetime.utcnow() - timedelta(days=days)
        since_ms = int(since_dt.timestamp() * 1000)
        
        # Fetch trades from exchange(s)
        trades_by_exchange = await orchestrator.fetch_user_trades(
            exchange_name=exchange,
            symbol=symbol,
            since=since_ms,
            limit=500  # Fetch more for accurate PnL calculation
        )
        
        # Flatten all trades
        all_trades = []
        for ex_name, trades in trades_by_exchange.items():
            for trade in trades:
                trade['_exchange'] = ex_name  # Tag with exchange name
                all_trades.append(trade)
        
        if not all_trades:
            return PerformanceResponse(
                user_id=user_id,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl_usd=0.0,
                profit_factor=0.0,
                average_roi=0.0,
                reputation_score=0.0,
                generated_at=datetime.utcnow().isoformat(),
                closed_trades=[],
                open_positions={}
            )
        
        # Calculate performance using PnL calculator
        reputation_score, closed_trades = pnl_calculator.calculate_from_ccxt_trades(
            all_trades, 
            trader_id=user_id
        )
        
        # Get open positions
        open_positions = {}
        for symbol, lots in pnl_calculator.get_open_positions().items():
            if lots:
                total_qty = sum(float(lot['quantity']) for lot in lots)
                avg_price = sum(float(lot['price']) * float(lot['quantity']) for lot in lots) / total_qty if total_qty > 0 else 0
                side = lots[0]['side']
                open_positions[symbol] = {
                    'side': side,
                    'quantity': total_qty,
                    'avg_entry_price': avg_price,
                    'lots': len(lots)
                }
        
        # Convert closed trades to response format
        closed_trades_response = [
            ClosedTradeResponse(
                symbol=ct.symbol,
                entry_date=ct.entry_date.isoformat(),
                exit_date=ct.exit_date.isoformat(),
                duration_hours=ct.duration_seconds / 3600,
                side=ct.side,
                quantity=float(ct.quantity),
                entry_price=float(ct.entry_price),
                exit_price=float(ct.exit_price),
                gross_pnl=float(ct.gross_pnl),
                fee=float(ct.fee),
                net_pnl=float(ct.net_pnl),
                roi_percentage=ct.roi_percentage
            )
            for ct in closed_trades[-50:]  # Last 50 closed trades
        ]
        
        return PerformanceResponse(
            user_id=user_id,
            total_trades=reputation_score.total_trades,
            winning_trades=reputation_score.winning_trades,
            losing_trades=reputation_score.losing_trades,
            win_rate=reputation_score.win_rate,
            total_pnl_usd=float(reputation_score.total_pnl_usd),
            profit_factor=reputation_score.profit_factor if reputation_score.profit_factor != float('inf') else 999.99,
            average_roi=reputation_score.average_roi,
            reputation_score=reputation_score.score,
            generated_at=reputation_score.generated_at.isoformat(),
            closed_trades=closed_trades_response,
            open_positions=open_positions
        )
        
    except Exception as e:
        logger.error(f"Failed to calculate performance for {user_id}: {e}")
        raise HTTPException(500, f"Failed to calculate performance: {str(e)}")


@app.get("/performance/{user_id}/summary")
async def get_performance_summary(
    user_id: str,
    exchange: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get a simplified performance summary (no trade details).
    Useful for quick reputation display.
    """
    try:
        since_dt = datetime.utcnow() - timedelta(days=days)
        since_ms = int(since_dt.timestamp() * 1000)
        
        trades_by_exchange = await orchestrator.fetch_user_trades(
            exchange_name=exchange,
            since=since_ms,
            limit=500
        )
        
        all_trades = []
        for trades in trades_by_exchange.values():
            all_trades.extend(trades)
        
        if not all_trades:
            return {
                "user_id": user_id,
                "reputation_score": 0,
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl_usd": 0,
                "status": "no_trades"
            }
        
        score, _ = pnl_calculator.calculate_from_ccxt_trades(all_trades, user_id)
        
        return {
            "user_id": user_id,
            "reputation_score": score.score,
            "total_trades": score.total_trades,
            "win_rate": round(score.win_rate, 2),
            "total_pnl_usd": round(float(score.total_pnl_usd), 2),
            "profit_factor": round(score.profit_factor, 2) if score.profit_factor != float('inf') else "∞",
            "average_roi": round(score.average_roi, 2),
            "status": "calculated",
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Failed to get summary for {user_id}: {e}")
        raise HTTPException(500, f"Failed to calculate summary: {str(e)}")


@app.get("/trades/{user_id}")
async def get_user_trades(
    user_id: str,
    exchange: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Fetch raw trade history for a user.
    Returns trades in CCXT format.
    """
    try:
        since_dt = datetime.utcnow() - timedelta(days=days)
        since_ms = int(since_dt.timestamp() * 1000)
        
        trades_by_exchange = await orchestrator.fetch_user_trades(
            exchange_name=exchange,
            symbol=symbol,
            since=since_ms,
            limit=limit
        )
        
        # Format response
        formatted = {}
        total_count = 0
        
        for ex_name, trades in trades_by_exchange.items():
            formatted[ex_name] = [
                {
                    "id": t.get('id'),
                    "timestamp": t.get('timestamp'),
                    "datetime": t.get('datetime'),
                    "symbol": t.get('symbol'),
                    "side": t.get('side'),
                    "amount": t.get('amount'),
                    "price": t.get('price'),
                    "cost": t.get('cost'),
                    "fee": t.get('fee', {}).get('cost', 0)
                }
                for t in trades
            ]
            total_count += len(trades)
        
        return {
            "user_id": user_id,
            "total_trades": total_count,
            "period_days": days,
            "trades_by_exchange": formatted
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch trades for {user_id}: {e}")
        raise HTTPException(500, f"Failed to fetch trades: {str(e)}")


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8001):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_standalone()
