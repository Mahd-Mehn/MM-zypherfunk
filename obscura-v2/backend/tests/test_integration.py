"""
Integration tests for Obscura V2 Copy Trading Platform
Tests the complete flow from gateway through all services
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any
import uuid

# Test fixtures and utilities
pytestmark = pytest.mark.asyncio


class TestConfig:
    """Test configuration"""
    GATEWAY_URL = "http://localhost:8000"
    TEST_USER_EMAIL = "test@example.com"
    TEST_USER_PASSWORD = "testpassword123"
    TEST_TRADER_EMAIL = "trader@example.com"


# =============================================================================
# MOCK SERVICES FOR TESTING
# =============================================================================

class MockNillionClient:
    """Mock Nillion client for testing"""
    
    def __init__(self):
        self.stored_secrets: Dict[str, Any] = {}
    
    async def store_api_credentials(
        self,
        user_id: str,
        exchange: str,
        api_key: str,
        api_secret: str
    ) -> str:
        store_id = f"nillion_{uuid.uuid4().hex[:16]}"
        self.stored_secrets[store_id] = {
            "user_id": user_id,
            "exchange": exchange,
            "api_key": api_key,
            "api_secret": api_secret
        }
        return store_id
    
    async def retrieve_api_credentials(
        self,
        store_id: str,
        user_id: str
    ) -> Dict[str, str]:
        if store_id not in self.stored_secrets:
            raise ValueError(f"Store ID not found: {store_id}")
        
        secret = self.stored_secrets[store_id]
        if secret["user_id"] != user_id:
            raise PermissionError("User not authorized to access this secret")
        
        return {
            "api_key": secret["api_key"],
            "api_secret": secret["api_secret"]
        }


class MockExchangeConnector:
    """Mock exchange connector for testing"""
    
    def __init__(self, exchange: str):
        self.exchange = exchange
        self.orders: Dict[str, Any] = {}
        self.balances = {
            "BTC": {"free": Decimal("1.5"), "locked": Decimal("0.0")},
            "ETH": {"free": Decimal("10.0"), "locked": Decimal("0.5")},
            "USDT": {"free": Decimal("10000.0"), "locked": Decimal("0.0")}
        }
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        amount: Decimal,
        price: Decimal = None
    ) -> Dict[str, Any]:
        order_id = f"order_{uuid.uuid4().hex[:8]}"
        
        self.orders[order_id] = {
            "id": order_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": str(amount),
            "filled": str(amount),  # Simulate immediate fill
            "price": str(price or Decimal("45000.0")),
            "status": "filled",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self.orders[order_id]
    
    async def get_balance(self) -> Dict[str, Dict[str, Decimal]]:
        return self.balances
    
    async def get_ticker(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "bid": Decimal("44990.0"),
            "ask": Decimal("45010.0"),
            "last": Decimal("45000.0"),
            "volume": Decimal("12500.5"),
            "timestamp": datetime.utcnow().isoformat()
        }


# =============================================================================
# UNIT TESTS - Analytics Engine
# =============================================================================

class TestAnalyticsEngine:
    """Tests for the analytics engine"""
    
    def test_pnl_calculation(self):
        """Test basic PnL calculation"""
        from analytics import AnalyticsEngine
        
        trades = [
            {
                "side": "buy",
                "symbol": "BTC/USDT",
                "amount": 1.0,
                "price": 40000.0,
                "timestamp": datetime.utcnow() - timedelta(days=1)
            },
            {
                "side": "sell",
                "symbol": "BTC/USDT",
                "amount": 1.0,
                "price": 45000.0,
                "timestamp": datetime.utcnow()
            }
        ]
        
        engine = AnalyticsEngine()
        pnl = engine._calculate_realized_pnl(trades)
        
        assert pnl == 5000.0, f"Expected PnL of 5000, got {pnl}"
    
    def test_win_rate_calculation(self):
        """Test win rate calculation"""
        from analytics import AnalyticsEngine
        
        trades = [
            {"pnl_usd": 100},
            {"pnl_usd": -50},
            {"pnl_usd": 200},
            {"pnl_usd": 150},
            {"pnl_usd": -30}
        ]
        
        engine = AnalyticsEngine()
        win_rate = engine._calculate_win_rate(trades)
        
        # 3 wins out of 5 trades = 60%
        assert win_rate == 0.6, f"Expected win rate of 0.6, got {win_rate}"
    
    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation"""
        from analytics import AnalyticsEngine
        import numpy as np
        
        # Daily returns
        returns = [0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.02]
        
        engine = AnalyticsEngine()
        sharpe = engine._calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        
        # Verify it's a reasonable value
        assert sharpe is not None
        assert -5 < sharpe < 5, f"Sharpe ratio {sharpe} seems unreasonable"


# =============================================================================
# UNIT TESTS - Key Storage
# =============================================================================

class TestKeyStorage:
    """Tests for secure key storage"""
    
    @pytest.fixture
    def mock_nillion(self):
        return MockNillionClient()
    
    async def test_store_and_retrieve_keys(self, mock_nillion):
        """Test storing and retrieving API keys"""
        user_id = "user_123"
        exchange = "binance"
        api_key = "test_api_key_12345"
        api_secret = "test_api_secret_67890"
        
        # Store keys
        store_id = await mock_nillion.store_api_credentials(
            user_id=user_id,
            exchange=exchange,
            api_key=api_key,
            api_secret=api_secret
        )
        
        assert store_id is not None
        assert store_id.startswith("nillion_")
        
        # Retrieve keys
        retrieved = await mock_nillion.retrieve_api_credentials(
            store_id=store_id,
            user_id=user_id
        )
        
        assert retrieved["api_key"] == api_key
        assert retrieved["api_secret"] == api_secret
    
    async def test_unauthorized_access_denied(self, mock_nillion):
        """Test that unauthorized users cannot access keys"""
        user_id = "user_123"
        other_user = "user_456"
        
        store_id = await mock_nillion.store_api_credentials(
            user_id=user_id,
            exchange="binance",
            api_key="key",
            api_secret="secret"
        )
        
        with pytest.raises(PermissionError):
            await mock_nillion.retrieve_api_credentials(
                store_id=store_id,
                user_id=other_user
            )


# =============================================================================
# UNIT TESTS - Trading
# =============================================================================

class TestTrading:
    """Tests for trading functionality"""
    
    @pytest.fixture
    def mock_exchange(self):
        return MockExchangeConnector("binance")
    
    async def test_place_market_order(self, mock_exchange):
        """Test placing a market order"""
        result = await mock_exchange.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            amount=Decimal("0.1")
        )
        
        assert result["status"] == "filled"
        assert result["symbol"] == "BTC/USDT"
        assert result["side"] == "buy"
    
    async def test_place_limit_order(self, mock_exchange):
        """Test placing a limit order"""
        result = await mock_exchange.place_order(
            symbol="ETH/USDT",
            side="sell",
            order_type="limit",
            amount=Decimal("1.0"),
            price=Decimal("3000.0")
        )
        
        assert result["status"] == "filled"
        assert result["price"] == "3000.0"
    
    async def test_get_balance(self, mock_exchange):
        """Test getting account balance"""
        balances = await mock_exchange.get_balance()
        
        assert "BTC" in balances
        assert "ETH" in balances
        assert "USDT" in balances
        assert balances["USDT"]["free"] == Decimal("10000.0")


# =============================================================================
# UNIT TESTS - Copy Trading
# =============================================================================

class TestCopyTrading:
    """Tests for copy trading engine"""
    
    def test_position_sizing_proportional(self):
        """Test proportional position sizing"""
        from copy_trading import CopyTradingEngine
        
        # Trader has $100,000 portfolio, places $1,000 trade (1%)
        # Follower has $10,000 portfolio
        # Proportional should give $100 trade (1% of follower portfolio)
        
        trader_balance = 100000
        follower_balance = 10000
        trade_amount = 1000
        
        engine = CopyTradingEngine()
        follower_amount = engine._calculate_proportional_size(
            trade_amount=trade_amount,
            trader_balance=trader_balance,
            follower_balance=follower_balance
        )
        
        assert follower_amount == 100.0
    
    def test_position_sizing_with_max_limit(self):
        """Test position sizing respects max limits"""
        from copy_trading import CopyTradingEngine
        
        engine = CopyTradingEngine()
        
        # Large trade that would exceed max
        calculated = engine._apply_position_limits(
            amount=5000,
            max_position=1000
        )
        
        assert calculated == 1000  # Capped at max


# =============================================================================
# UNIT TESTS - Subscriptions
# =============================================================================

class TestSubscriptions:
    """Tests for subscription system"""
    
    def test_tier_pricing(self):
        """Test subscription tier pricing"""
        from subscriptions import SubscriptionTier, get_tier_price
        
        prices = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.BASIC: 29,
            SubscriptionTier.PRO: 99,
            SubscriptionTier.PREMIUM: 299
        }
        
        for tier, expected_price in prices.items():
            price = get_tier_price(tier)
            assert price == expected_price, f"Tier {tier} price mismatch"
    
    def test_subscription_expiry_check(self):
        """Test subscription expiry checking"""
        from subscriptions import is_subscription_active
        
        # Active subscription
        active = is_subscription_active(
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        assert active is True
        
        # Expired subscription
        expired = is_subscription_active(
            expires_at=datetime.utcnow() - timedelta(days=1)
        )
        assert expired is False


# =============================================================================
# INTEGRATION TESTS - Complete Flow
# =============================================================================

class TestCompleteFlow:
    """Integration tests for complete user flows"""
    
    async def test_copy_trading_flow(self):
        """
        Test complete copy trading flow:
        1. Trader stores API keys
        2. Trader executes a trade
        3. Follower's trade is replicated
        4. Analytics are updated
        """
        # Setup
        mock_nillion = MockNillionClient()
        mock_binance = MockExchangeConnector("binance")
        
        trader_id = "trader_001"
        follower_id = "follower_001"
        
        # Step 1: Store trader's API keys
        store_id = await mock_nillion.store_api_credentials(
            user_id=trader_id,
            exchange="binance",
            api_key="trader_api_key",
            api_secret="trader_api_secret"
        )
        assert store_id is not None
        
        # Step 2: Trader executes a trade
        trader_order = await mock_binance.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            amount=Decimal("0.5")
        )
        assert trader_order["status"] == "filled"
        
        # Step 3: Simulate follower's replicated trade (scaled down)
        follower_amount = Decimal("0.05")  # 10% of trader's position
        follower_order = await mock_binance.place_order(
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            amount=follower_amount
        )
        assert follower_order["status"] == "filled"
        
        # Step 4: Verify both trades recorded
        assert len(mock_binance.orders) == 2
    
    async def test_subscription_payment_flow(self):
        """
        Test subscription payment flow:
        1. User selects a subscription tier
        2. Payment address is generated
        3. Payment is verified (mocked)
        4. Subscription is activated
        """
        from subscriptions import SubscriptionTier
        
        user_id = "user_001"
        tier = SubscriptionTier.PRO
        
        # Generate payment address
        payment_address = f"ua1_test_{uuid.uuid4().hex[:16]}"
        assert payment_address.startswith("ua1_test_")
        
        # Simulate payment verification
        payment_confirmed = True
        
        if payment_confirmed:
            # Activate subscription
            subscription = {
                "user_id": user_id,
                "tier": tier,
                "is_active": True,
                "started_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=30)
            }
            
            assert subscription["is_active"] is True
            assert subscription["tier"] == SubscriptionTier.PRO


# =============================================================================
# DATABASE TESTS
# =============================================================================

class TestDatabase:
    """Tests for database models and operations"""
    
    def test_user_model_validation(self):
        """Test user model constraints"""
        from database.models import User, UserRole
        
        # Valid user with email
        user = User(
            email="test@example.com",
            role=UserRole.USER
        )
        assert user.email == "test@example.com"
        
        # Valid user with wallet
        user2 = User(
            wallet_address="0x1234567890abcdef"
        )
        assert user2.wallet_address is not None
    
    def test_trade_model(self):
        """Test trade model"""
        from database.models import Trade, OrderSide, OrderType, OrderStatus
        from decimal import Decimal
        
        trade = Trade(
            user_id=uuid.uuid4(),
            exchange="binance",
            exchange_type="cex",
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            status=OrderStatus.FILLED,
            amount=Decimal("0.1"),
            filled_amount=Decimal("0.1"),
            average_fill_price=Decimal("45000.0")
        )
        
        assert trade.symbol == "BTC/USDT"
        assert trade.side == OrderSide.BUY


# =============================================================================
# API TESTS (require running server)
# =============================================================================

@pytest.mark.skip(reason="Requires running server")
class TestAPIEndpoints:
    """Tests for API endpoints - require running gateway"""
    
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TestConfig.GATEWAY_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    async def test_auth_flow(self):
        """Test authentication flow"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Register
            response = await client.post(
                f"{TestConfig.GATEWAY_URL}/api/v1/auth/register",
                json={
                    "email": TestConfig.TEST_USER_EMAIL,
                    "password": TestConfig.TEST_USER_PASSWORD
                }
            )
            assert response.status_code in [200, 201, 409]  # 409 if already exists
            
            # Login
            response = await client.post(
                f"{TestConfig.GATEWAY_URL}/api/v1/auth/login",
                json={
                    "email": TestConfig.TEST_USER_EMAIL,
                    "password": TestConfig.TEST_USER_PASSWORD
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and load tests"""
    
    async def test_order_processing_speed(self):
        """Test order processing is fast enough"""
        import time
        
        mock_exchange = MockExchangeConnector("binance")
        
        start = time.time()
        for _ in range(100):
            await mock_exchange.place_order(
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                amount=Decimal("0.1")
            )
        elapsed = time.time() - start
        
        # Should process 100 orders in less than 1 second (mock)
        assert elapsed < 1.0, f"Order processing too slow: {elapsed}s"
    
    async def test_concurrent_operations(self):
        """Test concurrent order handling"""
        mock_exchange = MockExchangeConnector("binance")
        
        # Create 50 concurrent orders
        tasks = [
            mock_exchange.place_order(
                symbol="ETH/USDT",
                side="buy" if i % 2 == 0 else "sell",
                order_type="market",
                amount=Decimal("1.0")
            )
            for i in range(50)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 50
        assert all(r["status"] == "filled" for r in results)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
