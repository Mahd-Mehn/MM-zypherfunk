"""
Copy Trading Service - Standalone FastAPI service

Can run as:
- Part of monolith (imported by api_gateway)
- Standalone microservice (python -m modules.copy_trading.service)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn

from .engine import CopyTradingEngine, copy_engine
from .monitor import TradeMonitor, trade_monitor

logger = logging.getLogger("obscura.copy_trading")

# Initialize service
app = FastAPI(
    title="Obscura Copy Trading Service",
    description="Real-time trade copying from lead traders to followers",
    version="2.0.0",
)


# =====================
# Request/Response Models
# =====================

class StartCopyingRequest(BaseModel):
    trader_id: str
    copy_mode: str = "proportional"  # proportional, fixed_amount
    fixed_amount_usd: Optional[float] = None
    proportion_percent: float = 100.0
    max_position_usd: Optional[float] = None
    max_daily_loss_usd: Optional[float] = None
    allowed_exchanges: List[str] = []
    allowed_pairs: List[str] = []


class AddTraderRequest(BaseModel):
    exchanges: List[str]
    symbols: Optional[List[str]] = None


class CopyStatsResponse(BaseModel):
    total_copied_trades: int
    total_pnl_usd: float
    active_since: Optional[str]
    is_active: bool


# =====================
# Health & Info
# =====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "copy_trading",
        "monitoring_active": trade_monitor._monitoring,
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================
# Monitoring
# =====================

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


@app.post("/monitor/add-trader")
async def add_monitored_trader(trader_id: str, request: AddTraderRequest):
    """Add a trader to be monitored"""
    for exchange in request.exchanges:
        await trade_monitor.add_session(
            trader_id=trader_id,
            exchange=exchange,
            symbols=request.symbols
        )
    return {"message": f"Now monitoring {trader_id} on {request.exchanges}"}


@app.delete("/monitor/remove-trader/{trader_id}")
async def remove_monitored_trader(trader_id: str, exchange: str):
    """Remove a trader from monitoring"""
    # Would need to track session IDs by trader
    return {"message": f"Stopped monitoring {trader_id}"}


@app.get("/monitor/positions/{trader_id}")
async def get_trader_positions(trader_id: str):
    """Get current positions of a monitored trader"""
    # Would query from Redis or DB
    return {"positions": {}}


# =====================
# Copy Trading
# =====================

@app.post("/copy/setup")
async def setup_copy_trading(
    follower_id: str,
    credentials: Dict[str, str]  # exchange -> credential_id
):
    """Set up a follower for copy trading"""
    # Store credentials mapping in Redis for quick access
    return {"message": f"Copy trading set up for {follower_id}"}


@app.post("/copy/start")
async def start_copying(follower_id: str, request: StartCopyingRequest):
    """Start copying a trader"""
    # This would create the CopyTradingConfig and Follower records
    return {
        "message": f"Now copying {request.trader_id}",
        "settings": {
            "copy_mode": request.copy_mode,
            "proportion_percent": request.proportion_percent,
            "allowed_exchanges": request.allowed_exchanges
        }
    }


@app.post("/copy/stop")
async def stop_copying(follower_id: str, trader_id: str):
    """Stop copying a trader"""
    return {"message": f"Stopped copying {trader_id}"}


@app.get("/copy/stats/{follower_id}")
async def get_copy_stats(follower_id: str) -> CopyStatsResponse:
    """Get copy trading statistics"""
    # Would query from DB
    return CopyStatsResponse(
        total_copied_trades=0,
        total_pnl_usd=0.0,
        active_since=None,
        is_active=False
    )


# =====================
# Lifecycle
# =====================

@app.on_event("startup")
async def startup_event():
    """Start monitoring and copy engine on startup"""
    await trade_monitor.start_monitoring()
    await copy_engine.start()
    logger.info("Copy trading service started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await trade_monitor.stop_monitoring()
    await copy_engine.stop()
    logger.info("Copy trading service stopped")


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8003):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_standalone()
