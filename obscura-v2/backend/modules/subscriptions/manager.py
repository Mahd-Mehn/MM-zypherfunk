"""
Subscription Billing System with Zcash Shielded Payments

Handles monthly subscriptions for copy trading platform.
Traders can charge followers using Zcash Unified Addresses.
Uses PostgreSQL for persistence and Redis for caching.
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import uuid

from sqlalchemy import select, update, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from .payments.zcash_client import ZcashClient
from shared.database import (
    get_async_session, UserSubscription, PaymentTransaction, 
    TraderProfile, User, SubscriptionTier, PaymentStatus
)
from shared.services import redis_service, CacheKeys

logger = logging.getLogger("obscura.subscriptions")


class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELED = "canceled"
    SUSPENDED = "suspended"


class BillingCycle(Enum):
    """Billing frequency"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class SubscriptionPlanDTO:
    """Subscription plan data transfer object"""
    plan_id: str
    trader_id: str
    name: str
    description: str
    price_zec: Decimal
    billing_cycle: BillingCycle
    features: List[str]
    max_followers: int
    profit_share_percent: Decimal = Decimal("0")
    payment_address: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "trader_id": self.trader_id,
            "name": self.name,
            "description": self.description,
            "price_zec": str(self.price_zec),
            "billing_cycle": self.billing_cycle.value,
            "features": self.features,
            "max_followers": self.max_followers,
            "profit_share_percent": str(self.profit_share_percent),
            "payment_address": self.payment_address,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubscriptionPlanDTO":
        return cls(
            plan_id=data["plan_id"],
            trader_id=data["trader_id"],
            name=data["name"],
            description=data["description"],
            price_zec=Decimal(data["price_zec"]),
            billing_cycle=BillingCycle(data["billing_cycle"]),
            features=data["features"],
            max_followers=data["max_followers"],
            profit_share_percent=Decimal(data.get("profit_share_percent", "0")),
            payment_address=data.get("payment_address", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )


class SubscriptionManager:
    """
    Manages subscriptions and billing with Zcash payments.
    Uses PostgreSQL for persistence and Redis for caching.
    
    Features:
    - Monthly/quarterly/yearly billing
    - Automatic payment verification
    - Grace periods for failed payments
    - Profit sharing calculations
    - Subscription analytics
    """
    
    def __init__(self, zcash_client: Optional[ZcashClient] = None):
        self.zcash_client = zcash_client or ZcashClient()
        self._initialized = False
        logger.info("SubscriptionManager initialized")

    async def initialize(self):
        """Initialize Redis connection"""
        if not self._initialized:
            await redis_service.initialize()
            self._initialized = True

    async def _get_session(self) -> AsyncSession:
        """Get database session"""
        return await get_async_session()

    # =========================================================================
    # Plan Management
    # =========================================================================

    async def create_plan(
        self,
        trader_id: str,
        name: str,
        price_zec: Decimal,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        description: str = "",
        features: Optional[List[str]] = None,
        max_followers: int = 100,
        profit_share_percent: Decimal = Decimal("0")
    ) -> SubscriptionPlanDTO:
        """
        Create a new subscription plan for a trader.
        Stored in Redis with backup in trader profile.
        """
        await self.initialize()
        
        # Generate Zcash Unified Address for this plan
        payment_address = await self.zcash_client.get_new_unified_address(
            diversifier=f"plan-{trader_id}"
        )
        
        plan_id = f"plan_{trader_id}_{uuid.uuid4().hex[:8]}"
        
        plan = SubscriptionPlanDTO(
            plan_id=plan_id,
            trader_id=trader_id,
            name=name,
            description=description,
            price_zec=price_zec,
            billing_cycle=billing_cycle,
            features=features or [],
            max_followers=max_followers,
            profit_share_percent=profit_share_percent,
            payment_address=payment_address
        )
        
        # Store in Redis hash
        cache_key = CacheKeys.subscription_plans()
        await redis_service.hset_json(cache_key, plan_id, plan.to_dict())
        
        # Also store trader-specific reference
        trader_plans_key = f"plans:trader:{trader_id}"
        await redis_service.sadd(trader_plans_key, plan_id)
        
        # Update trader profile in database with plan info
        async with await self._get_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(TraderProfile).where(TraderProfile.user_id == trader_id)
                )
                trader_profile = result.scalar_one_or_none()
                
                if trader_profile:
                    trader_profile.monthly_fee_usd = float(price_zec) * 30  # Approx USD
                    trader_profile.zcash_payout_address = payment_address
        
        logger.info(f"Created subscription plan: {plan_id} for trader {trader_id}")
        return plan

    async def get_plan(self, plan_id: str) -> Optional[SubscriptionPlanDTO]:
        """Get a subscription plan by ID"""
        await self.initialize()
        
        cache_key = CacheKeys.subscription_plans()
        plan_data = await redis_service.hget_json(cache_key, plan_id)
        
        if plan_data:
            return SubscriptionPlanDTO.from_dict(plan_data)
        return None

    async def get_trader_plans(self, trader_id: str) -> List[SubscriptionPlanDTO]:
        """Get all plans for a trader"""
        await self.initialize()
        
        trader_plans_key = f"plans:trader:{trader_id}"
        plan_ids = await redis_service.smembers(trader_plans_key)
        
        plans = []
        cache_key = CacheKeys.subscription_plans()
        
        for plan_id in plan_ids:
            plan_data = await redis_service.hget_json(cache_key, plan_id)
            if plan_data:
                plans.append(SubscriptionPlanDTO.from_dict(plan_data))
        
        return plans

    # =========================================================================
    # Subscription Management
    # =========================================================================

    async def subscribe(
        self,
        plan_id: str,
        follower_id: str,
        follower_payment_address: Optional[str] = None
    ) -> UserSubscription:
        """
        Subscribe a follower to a trader's plan.
        Creates subscription record in database.
        """
        await self.initialize()
        
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # Check max followers
        active_count = await self._count_active_subscriptions(plan_id)
        if active_count >= plan.max_followers:
            raise ValueError(f"Plan {plan_id} has reached maximum followers")
        
        # Calculate billing dates
        now = datetime.utcnow()
        
        if plan.billing_cycle == BillingCycle.MONTHLY:
            expires_at = now + timedelta(days=30)
        elif plan.billing_cycle == BillingCycle.QUARTERLY:
            expires_at = now + timedelta(days=90)
        else:  # YEARLY
            expires_at = now + timedelta(days=365)
        
        # Create subscription in database
        async with await self._get_session() as session:
            async with session.begin():
                subscription = UserSubscription(
                    user_id=follower_id,
                    tier=SubscriptionTier.PRO,  # Map plan to tier
                    is_active=False,  # Pending payment
                    auto_renew=True,
                    monthly_price_usd=float(plan.price_zec) * 30,
                    zcash_payment_address=plan.payment_address,
                    started_at=now,
                    expires_at=expires_at
                )
                session.add(subscription)
                await session.flush()
                
                subscription_id = str(subscription.id)
        
        # Cache subscription info
        await self._cache_subscription(subscription_id, {
            "subscription_id": subscription_id,
            "plan_id": plan_id,
            "follower_id": follower_id,
            "trader_id": plan.trader_id,
            "status": SubscriptionStatus.PENDING.value,
            "price_zec": str(plan.price_zec),
            "payment_address": plan.payment_address,
            "follower_payment_address": follower_payment_address,
            "started_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        })
        
        logger.info(f"Created subscription: {subscription_id}")
        return subscription

    async def verify_payment(
        self,
        subscription_id: str,
        expected_amount: Optional[Decimal] = None,
        timeout_seconds: int = 300
    ) -> bool:
        """Verify that a subscription payment has been received."""
        await self.initialize()
        
        # Get subscription from cache or database
        sub_data = await self._get_cached_subscription(subscription_id)
        if not sub_data:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        plan = await self.get_plan(sub_data["plan_id"])
        amount = expected_amount or Decimal(sub_data["price_zec"])
        payment_address = sub_data["payment_address"]
        
        logger.info(f"Verifying payment for {subscription_id}: {amount} ZEC to {payment_address}")
        
        # Check for payment
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
            payment_info = await self.zcash_client.check_payment(
                address=payment_address,
                expected_amount=amount,
                memo_contains=f"sub:{subscription_id}"
            )
            
            if payment_info and payment_info.get('confirmed'):
                # Payment confirmed - update database
                await self._record_payment(
                    subscription_id=subscription_id,
                    amount=amount,
                    tx_hash=payment_info['tx_hash'],
                    block_height=payment_info.get('block_height'),
                    confirmations=payment_info.get('confirmations', 0)
                )
                
                # Activate subscription
                await self._activate_subscription(subscription_id)
                
                logger.info(f"Payment confirmed for {subscription_id}")
                return True
            
            await asyncio.sleep(5)
        
        logger.warning(f"Payment timeout for {subscription_id}")
        return False

    async def cancel_subscription(
        self,
        subscription_id: str,
        refund_prorated: bool = False
    ) -> bool:
        """Cancel a subscription."""
        await self.initialize()
        
        async with await self._get_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(UserSubscription).where(
                        UserSubscription.id == subscription_id
                    )
                )
                subscription = result.scalar_one_or_none()
                
                if not subscription:
                    return False
                
                subscription.is_active = False
                subscription.cancelled_at = datetime.utcnow()
                subscription.auto_renew = False
        
        # Update cache
        await redis_service.delete(CacheKeys.subscription(subscription_id))
        
        logger.info(f"Canceled subscription {subscription_id}")
        return True

    # =========================================================================
    # Analytics
    # =========================================================================

    async def get_subscriber_count(self, trader_id: str) -> int:
        """Get number of active subscribers for a trader"""
        plans = await self.get_trader_plans(trader_id)
        total = 0
        
        for plan in plans:
            total += await self._count_active_subscriptions(plan.plan_id)
        
        return total

    async def get_monthly_revenue(self, trader_id: str) -> Decimal:
        """Calculate monthly recurring revenue for a trader"""
        plans = await self.get_trader_plans(trader_id)
        revenue = Decimal("0")
        
        for plan in plans:
            count = await self._count_active_subscriptions(plan.plan_id)
            
            if plan.billing_cycle == BillingCycle.MONTHLY:
                revenue += plan.price_zec * count
            elif plan.billing_cycle == BillingCycle.QUARTERLY:
                revenue += (plan.price_zec / 3) * count
            else:  # YEARLY
                revenue += (plan.price_zec / 12) * count
        
        return revenue

    async def get_subscription_analytics(self, trader_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a trader's subscriptions"""
        await self.initialize()
        
        # Check cache first
        cache_key = f"analytics:subscriptions:{trader_id}"
        cached = await redis_service.get_json(cache_key)
        if cached:
            return cached
        
        # Calculate analytics from database
        async with await self._get_session() as session:
            # Get all subscriptions for trader's plans
            plans = await self.get_trader_plans(trader_id)
            plan_ids = [p.plan_id for p in plans]
            
            # This is a simplified query - in production you'd join properly
            result = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.zcash_payment_address.in_(
                        [p.payment_address for p in plans]
                    )
                )
            )
            subs = result.scalars().all()
        
        active = sum(1 for s in subs if s.is_active)
        canceled = sum(1 for s in subs if s.cancelled_at is not None)
        expired = sum(1 for s in subs if not s.is_active and s.cancelled_at is None)
        
        mrr = await self.get_monthly_revenue(trader_id)
        churn_rate = (canceled / len(subs) * 100) if subs else 0
        
        analytics = {
            "trader_id": trader_id,
            "total_subscribers": len(subs),
            "active_subscribers": active,
            "canceled_subscribers": canceled,
            "expired_subscribers": expired,
            "monthly_recurring_revenue_zec": float(mrr),
            "churn_rate_percent": round(churn_rate, 2),
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        await redis_service.set_json(cache_key, analytics, ttl_seconds=CacheTTL.MEDIUM)
        
        return analytics

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _count_active_subscriptions(self, plan_id: str) -> int:
        """Count active subscriptions for a plan"""
        plan = await self.get_plan(plan_id)
        if not plan:
            return 0
        
        async with await self._get_session() as session:
            result = await session.execute(
                select(func.count(UserSubscription.id)).where(
                    and_(
                        UserSubscription.zcash_payment_address == plan.payment_address,
                        UserSubscription.is_active == True
                    )
                )
            )
            return result.scalar() or 0

    async def _cache_subscription(self, subscription_id: str, data: Dict[str, Any]):
        """Cache subscription data in Redis"""
        cache_key = CacheKeys.subscription(subscription_id)
        await redis_service.set_json(cache_key, data, ttl_seconds=CacheTTL.DAY)
        
        # Also add to user's subscription set
        user_subs_key = CacheKeys.user_subscriptions(data["follower_id"])
        await redis_service.sadd(user_subs_key, subscription_id)

    async def _get_cached_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Get subscription from cache or database"""
        cache_key = CacheKeys.subscription(subscription_id)
        cached = await redis_service.get_json(cache_key)
        
        if cached:
            return cached
        
        # Fallback to database
        async with await self._get_session() as session:
            result = await session.execute(
                select(UserSubscription).where(
                    UserSubscription.id == subscription_id
                )
            )
            sub = result.scalar_one_or_none()
            
            if sub:
                data = {
                    "subscription_id": str(sub.id),
                    "follower_id": str(sub.user_id),
                    "status": "active" if sub.is_active else "inactive",
                    "started_at": sub.started_at.isoformat() if sub.started_at else None,
                    "expires_at": sub.expires_at.isoformat() if sub.expires_at else None
                }
                await redis_service.set_json(cache_key, data, ttl_seconds=CacheTTL.LONG)
                return data
        
        return None

    async def _record_payment(
        self,
        subscription_id: str,
        amount: Decimal,
        tx_hash: str,
        block_height: Optional[int] = None,
        confirmations: int = 0
    ):
        """Record a payment in the database"""
        async with await self._get_session() as session:
            async with session.begin():
                # Get subscription
                result = await session.execute(
                    select(UserSubscription).where(
                        UserSubscription.id == subscription_id
                    )
                )
                subscription = result.scalar_one_or_none()
                
                if not subscription:
                    return
                
                # Create payment record
                payment = PaymentTransaction(
                    subscription_id=subscription.id,
                    amount_usd=float(amount) * 30,  # Approx conversion
                    amount_zec=float(amount),
                    tx_hash=tx_hash,
                    status=PaymentStatus.CONFIRMED,
                    confirmations=confirmations,
                    period_start=subscription.started_at or datetime.utcnow(),
                    period_end=subscription.expires_at or datetime.utcnow() + timedelta(days=30),
                    confirmed_at=datetime.utcnow()
                )
                session.add(payment)
        
        # Cache payment
        payments_key = CacheKeys.payments(subscription_id)
        await redis_service.lpush(payments_key, json.dumps({
            "tx_hash": tx_hash,
            "amount_zec": str(amount),
            "confirmed_at": datetime.utcnow().isoformat()
        }))
        
        logger.info(f"Recorded payment for {subscription_id}: {tx_hash}")

    async def _activate_subscription(self, subscription_id: str):
        """Activate a subscription after payment"""
        async with await self._get_session() as session:
            async with session.begin():
                await session.execute(
                    update(UserSubscription)
                    .where(UserSubscription.id == subscription_id)
                    .values(is_active=True)
                )
        
        # Update cache
        sub_data = await self._get_cached_subscription(subscription_id)
        if sub_data:
            sub_data["status"] = SubscriptionStatus.ACTIVE.value
            await self._cache_subscription(subscription_id, sub_data)


# Singleton instance
subscription_manager = SubscriptionManager()
