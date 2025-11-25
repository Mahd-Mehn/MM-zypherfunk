"""
Subscriptions Service - Standalone FastAPI service for billing

Can run as:
- Part of monolith (imported by api_gateway)
- Standalone microservice (python -m modules.subscriptions.service)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import uvicorn

from .manager import SubscriptionManager, BillingCycle, SubscriptionPlanDTO
from .payments.zcash_client import ZcashClient, zcash

logger = logging.getLogger("obscura.subscriptions")

# Initialize service
app = FastAPI(
    title="Obscura Subscriptions Service",
    description="Subscription management with Zcash payments",
    version="2.0.0",
)

# Service instances
subscription_manager = SubscriptionManager()


# =====================
# Request/Response Models
# =====================

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


class PaymentResponse(BaseModel):
    address: str
    amount_zec: float
    memo: Optional[str] = None


# =====================
# Health & Info
# =====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "subscriptions",
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================
# Plan Management
# =====================

@app.post("/plans/create")
async def create_plan(trader_id: str, request: CreatePlanRequest):
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
        "message": "Plan created successfully"
    }


@app.get("/plans/{trader_id}")
async def list_trader_plans(trader_id: str):
    """List all plans for a trader"""
    plans = await subscription_manager.get_trader_plans(trader_id)
    return {"plans": [p.to_dict() for p in plans]}


@app.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, trader_id: str):
    """Delete a subscription plan"""
    success = await subscription_manager.delete_plan(plan_id, trader_id)
    if not success:
        raise HTTPException(400, "Failed to delete plan")
    return {"message": "Plan deleted"}


# =====================
# Subscriptions
# =====================

@app.post("/subscribe")
async def subscribe(follower_id: str, request: SubscribeRequest):
    """Subscribe to a plan"""
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
async def verify_payment(subscription_id: str):
    """Verify subscription payment"""
    confirmed = await subscription_manager.verify_payment(subscription_id, timeout_seconds=60)
    
    return {
        "subscription_id": subscription_id,
        "payment_confirmed": confirmed,
        "status": "active" if confirmed else "pending"
    }


@app.get("/subscriptions/user/{user_id}")
async def get_user_subscriptions(user_id: str):
    """Get all subscriptions for a user"""
    subscriptions = await subscription_manager.get_user_subscriptions(user_id)
    return {"subscriptions": subscriptions}


@app.delete("/subscriptions/{subscription_id}")
async def cancel_subscription(subscription_id: str, user_id: str):
    """Cancel a subscription"""
    success = await subscription_manager.cancel_subscription(subscription_id, user_id)
    if not success:
        raise HTTPException(400, "Failed to cancel subscription")
    return {"message": "Subscription cancelled"}


# =====================
# Analytics
# =====================

@app.get("/analytics/{trader_id}")
async def get_subscription_analytics(trader_id: str):
    """Get subscription analytics for a trader"""
    analytics = await subscription_manager.get_subscription_analytics(trader_id)
    return analytics


# =====================
# Payments
# =====================

@app.get("/payments/new-address")
async def get_new_payment_address():
    """Generate new Zcash Unified Address"""
    address = zcash.get_new_unified_address()
    return {"address": address, "type": "unified"}


@app.post("/payments/send")
async def send_payment(to_address: str, amount: float, memo: str = ""):
    """Send Zcash payment"""
    tx_id = zcash.send_payment(to_address, amount, memo)
    if tx_id:
        return {"tx_id": tx_id, "amount": amount, "to": to_address}
    raise HTTPException(500, "Payment failed")


@app.get("/payments/balance")
async def get_balance():
    """Get Zcash wallet balance"""
    balance = zcash.get_balance()
    price = zcash.get_zec_price()
    return {
        "balance_zec": float(balance),
        "usd_price": float(price) if price else None,
        "balance_usd": float(balance * price) if price else None
    }


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8002):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


# Export for monolith use
subscription_service = subscription_manager

if __name__ == "__main__":
    run_standalone()
