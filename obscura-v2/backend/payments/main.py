from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .zcash_client import zcash

app = FastAPI(title="Payments (Zcash Shielded)", version="2.0.0")

class SubscriptionRequest(BaseModel):
    user_id: str
    tier: str # "basic", "pro"

class PaymentResponse(BaseModel):
    payment_address: str
    amount_zec: float
    status: str

class PaymentCheck(BaseModel):
    payment_address: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "payment_rail": "zcash-shielded"}

@app.post("/subscribe", response_model=PaymentResponse)
async def create_subscription(request: SubscriptionRequest):
    """
    Create a new subscription request. Returns a Zcash address to pay to.
    """
    address = zcash.get_new_address()
    amount = 0.1 if request.tier == "pro" else 0.01
    
    zcash.watch_address(address, amount)
    
    return {
        "payment_address": address,
        "amount_zec": amount,
        "status": "pending_payment"
    }

@app.post("/check", response_model=dict)
async def check_payment_status(request: PaymentCheck):
    """
    Check if payment has been received.
    """
    received = zcash.check_payment(request.payment_address)
    return {"received": received}

@app.post("/simulate", response_model=dict)
async def simulate_payment(request: PaymentCheck):
    """
    DEV ONLY: Simulate a payment for demo purposes.
    """
    zcash.simulate_payment(request.payment_address)
    return {"status": "simulated", "received": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
