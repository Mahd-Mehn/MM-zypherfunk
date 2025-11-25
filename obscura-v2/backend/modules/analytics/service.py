"""
Analytics Service - Standalone FastAPI service

Can run as:
- Part of monolith (imported by api_gateway)
- Standalone microservice (python -m modules.analytics.service)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn

from .engine import AnalyticsEngine, analytics_engine

logger = logging.getLogger("obscura.analytics")

# Initialize service
app = FastAPI(
    title="Obscura Analytics Service",
    description="Trading performance analytics and leaderboards",
    version="2.0.0",
)


# =====================
# Request/Response Models
# =====================

class MetricsResponse(BaseModel):
    total_trades: int
    win_rate: float
    total_pnl: float
    volume: float
    profit_factor: float
    updated_at: str


class LeaderboardEntry(BaseModel):
    user_id: str
    username: Optional[str]
    total_pnl: float
    win_rate: float
    total_trades: int
    rank: int


# =====================
# Health & Info
# =====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================
# User Analytics
# =====================

@app.get("/metrics/{user_id}")
async def get_user_metrics(
    user_id: str,
    timeframe: str = Query("24h", regex="^(24h|7d|30d|all)$")
):
    """Get trading metrics for a user"""
    metrics = await analytics_engine.get_user_metrics(user_id, timeframe)
    return metrics


@app.post("/trade")
async def record_trade(user_id: str, trade_data: Dict[str, Any]):
    """Record a trade for analytics"""
    trade_id = await analytics_engine.record_trade(user_id, trade_data)
    return {"trade_id": trade_id, "message": "Trade recorded"}


# =====================
# Leaderboards
# =====================

@app.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("30d", regex="^(24h|7d|30d|all)$"),
    min_trades: int = Query(10, ge=1),
    limit: int = Query(10, ge=1, le=100)
) -> List[LeaderboardEntry]:
    """Get top performing traders"""
    # Would query AnalyticsSnapshot for rankings
    return []


@app.get("/compare")
async def compare_traders(
    trader_ids: str,
    timeframe: str = Query("30d", regex="^(24h|7d|30d|all)$")
):
    """Compare multiple traders"""
    ids = trader_ids.split(",")
    comparison = {}
    
    for trader_id in ids:
        metrics = await analytics_engine.get_user_metrics(trader_id, timeframe)
        comparison[trader_id] = metrics
    
    return {"comparison": comparison}


# =====================
# Snapshots
# =====================

@app.post("/snapshot/{user_id}")
async def create_snapshot(user_id: str, period_type: str = "daily"):
    """Create an analytics snapshot"""
    await analytics_engine.update_user_metrics(user_id)
    return {"message": f"Snapshot created for {user_id}"}


@app.get("/history/{user_id}")
async def get_analytics_history(
    user_id: str,
    period_type: str = Query("daily", regex="^(hourly|daily|weekly|monthly)$"),
    limit: int = Query(30, ge=1, le=365)
):
    """Get historical analytics snapshots"""
    # Would query AnalyticsSnapshot
    return {"snapshots": []}


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8004):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_standalone()
