from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import uuid
import json
from .zcash_client import zcash

app = FastAPI(title="Payments (Zcash Shielded)", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Subscription tier pricing in ZEC
SUBSCRIPTION_TIERS = {
    "basic": {"price": 0.01, "name": "Basic", "days": 30},
    "pro": {"price": 0.1, "name": "Pro", "days": 30},
    "premium": {"price": 0.5, "name": "Premium", "days": 30},
}

# In-memory store (replace with database in production)
pending_payments: Dict[str, dict] = {}
confirmed_payments: Dict[str, dict] = {}


class SubscriptionRequest(BaseModel):
    user_id: str = Field(..., alias="userId")
    tier: str = Field(..., description="Subscription tier: basic, pro, or premium")
    trader_id: Optional[str] = Field(None, alias="traderId")

    class Config:
        populate_by_name = True


class PaymentResponse(BaseModel):
    id: str
    payment_address: str = Field(..., alias="paymentAddress")
    amount_zec: float = Field(..., alias="amountZec")
    memo: str
    status: str
    payment_uri: str = Field(..., alias="paymentUri")
    created_at: str = Field(..., alias="createdAt")
    expires_at: str = Field(..., alias="expiresAt")

    class Config:
        populate_by_name = True


class PaymentCheck(BaseModel):
    payment_address: str


class PaymentStatus(BaseModel):
    id: str
    status: str
    confirmations: Optional[int] = None
    txid: Optional[str] = None
    confirmed_at: Optional[str] = Field(None, alias="confirmedAt")

    class Config:
        populate_by_name = True


def generate_memo(user_id: str, tier: str, trader_id: Optional[str] = None) -> str:
    """Generate a JSON memo for tracking subscriptions."""
    data = {
        "type": "obscura_subscription",
        "user": user_id,
        "tier": tier,
        "trader": trader_id,
        "ts": int(datetime.utcnow().timestamp()),
    }
    return json.dumps(data)


def generate_payment_uri(address: str, amount: float, memo: str = "") -> str:
    """Generate a ZIP-321 compliant payment URI."""
    import base64
    
    params = [f"amount={amount:.8f}"]
    
    if memo:
        # Base64url encode the memo
        memo_b64 = base64.urlsafe_b64encode(memo.encode()).decode().rstrip("=")
        params.append(f"memo={memo_b64}")
    
    params.append("label=Obscura%20Subscription")
    
    return f"zcash:{address}?{'&'.join(params)}"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "payment_rail": "zcash-shielded",
        "wallet_connected": zcash._wallet is not None,
        "balance": str(zcash.get_balance()) if zcash._wallet else "0",
    }


@app.post("/subscribe", response_model=PaymentResponse)
async def create_subscription(request: SubscriptionRequest):
    """
    Create a new subscription payment request.
    Returns a Zcash unified address and payment details.
    """
    if request.tier not in SUBSCRIPTION_TIERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {list(SUBSCRIPTION_TIERS.keys())}",
        )

    tier_info = SUBSCRIPTION_TIERS[request.tier]
    payment_id = str(uuid.uuid4())
    address = zcash.get_new_unified_address()
    amount = tier_info["price"]
    memo = generate_memo(request.user_id, request.tier, request.trader_id)
    
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=1)  # 1 hour payment window

    # Store payment for tracking
    payment_data = {
        "id": payment_id,
        "user_id": request.user_id,
        "tier": request.tier,
        "trader_id": request.trader_id,
        "address": address,
        "amount": amount,
        "memo": memo,
        "status": "pending",
        "created_at": now.isoformat() + "Z",
        "expires_at": expires_at.isoformat() + "Z",
    }
    pending_payments[payment_id] = payment_data
    pending_payments[address] = payment_data  # Also index by address

    # Register address for monitoring
    zcash.watch_address(address, amount)

    return {
        "id": payment_id,
        "paymentAddress": address,
        "amountZec": amount,
        "memo": memo,
        "status": "pending",
        "paymentUri": generate_payment_uri(address, amount, memo),
        "createdAt": payment_data["created_at"],
        "expiresAt": payment_data["expires_at"],
    }


@app.get("/status/{payment_id}", response_model=PaymentStatus)
async def get_payment_status(payment_id: str):
    """
    Check payment status by payment ID.
    """
    # Check confirmed payments first
    if payment_id in confirmed_payments:
        payment = confirmed_payments[payment_id]
        return {
            "id": payment_id,
            "status": "confirmed",
            "confirmations": payment.get("confirmations", 1),
            "txid": payment.get("txid"),
            "confirmedAt": payment.get("confirmed_at"),
        }

    # Check pending payments
    if payment_id not in pending_payments:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = pending_payments[payment_id]

    # Check if expired
    expires_at = datetime.fromisoformat(payment["expires_at"].rstrip("Z"))
    if datetime.utcnow() > expires_at:
        payment["status"] = "expired"
        return {"id": payment_id, "status": "expired"}

    # Check blockchain for payment
    address = payment["address"]
    received = await zcash.check_payment(address)

    if received:
        # Move to confirmed
        payment["status"] = "confirmed"
        payment["confirmed_at"] = datetime.utcnow().isoformat() + "Z"
        payment["confirmations"] = 1
        confirmed_payments[payment_id] = payment
        del pending_payments[payment_id]
        del pending_payments[address]

        return {
            "id": payment_id,
            "status": "confirmed",
            "confirmations": 1,
            "confirmedAt": payment["confirmed_at"],
        }

    return {"id": payment_id, "status": "pending"}


@app.post("/check", response_model=PaymentStatus)
async def check_payment_by_address(request: PaymentCheck):
    """
    Check if payment has been received at an address.
    """
    address = request.payment_address

    # Look up payment by address
    if address not in pending_payments:
        # Check if it's already confirmed
        for pid, payment in confirmed_payments.items():
            if payment.get("address") == address:
                return {
                    "id": pid,
                    "status": "confirmed",
                    "confirmations": payment.get("confirmations", 1),
                    "txid": payment.get("txid"),
                    "confirmedAt": payment.get("confirmed_at"),
                }
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = pending_payments[address]
    payment_id = payment["id"]

    # Check blockchain
    received = await zcash.check_payment(address)

    if received:
        payment["status"] = "confirmed"
        payment["confirmed_at"] = datetime.utcnow().isoformat() + "Z"
        payment["confirmations"] = 1
        confirmed_payments[payment_id] = payment
        del pending_payments[payment_id]
        del pending_payments[address]

        return {
            "id": payment_id,
            "status": "confirmed",
            "confirmations": 1,
            "confirmedAt": payment["confirmed_at"],
        }

    return {"id": payment_id, "status": "pending"}


@app.get("/history", response_model=List[dict])
async def get_payment_history():
    """
    Get all confirmed payments (for admin/debugging).
    """
    return list(confirmed_payments.values())


@app.post("/simulate", response_model=dict)
async def simulate_payment(request: PaymentCheck):
    """
    DEV ONLY: Simulate a payment for demo purposes.
    """
    address = request.payment_address

    if address not in pending_payments:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Simulate the payment
    zcash.simulate_payment(address)

    payment = pending_payments[address]
    payment_id = payment["id"]
    payment["status"] = "confirmed"
    payment["confirmed_at"] = datetime.utcnow().isoformat() + "Z"
    payment["confirmations"] = 1
    payment["txid"] = f"mock_txid_{uuid.uuid4().hex[:16]}"

    confirmed_payments[payment_id] = payment
    del pending_payments[payment_id]
    del pending_payments[address]

    return {
        "status": "simulated",
        "received": True,
        "payment_id": payment_id,
        "txid": payment["txid"],
    }


@app.get("/tiers")
async def get_subscription_tiers():
    """
    Get available subscription tiers and pricing.
    """
    return SUBSCRIPTION_TIERS


@app.get("/price")
async def get_zec_price():
    """
    Get current ZEC price in USD.
    """
    price = zcash.get_zec_price()
    return {"zec_usd": float(price) if price else None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
