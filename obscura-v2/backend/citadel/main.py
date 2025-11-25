from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from .nillion_client import nillion

app = FastAPI(title="Citadel (Nillion Edition)", version="2.0.0")

class StoreSecretRequest(BaseModel):
    secret: str
    name: str

class StoreSecretResponse(BaseModel):
    store_id: str
    status: str

class SignRequest(BaseModel):
    store_id: str
    payload_hash: str

class SignResponse(BaseModel):
    signature: str
    status: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "backend": "nillion-mock"}

@app.post("/store", response_model=StoreSecretResponse)
async def store_secret(request: StoreSecretRequest):
    """
    Store a secret (API Key) in the Nillion Network.
    """
    try:
        store_id = await nillion.store_secret(request.secret, request.name)
        return {"store_id": store_id, "status": "stored_in_nillion"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sign", response_model=SignResponse)
async def sign_payload(request: SignRequest):
    """
    Request a blind signature from the Nillion Network.
    """
    try:
        signature = await nillion.compute_signature(request.store_id, request.payload_hash)
        return {"signature": signature, "status": "signed_by_nilcc"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
