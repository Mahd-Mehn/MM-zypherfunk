"""
Citadel Service - Standalone FastAPI service for secure key operations

Can run as:
- Part of monolith (imported by api_gateway)  
- Standalone microservice (python -m modules.citadel.service)
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import uvicorn

from .nillion_client import NillionClient, SecretType, PermissionLevel, nillion

logger = logging.getLogger("obscura.citadel")

# Initialize service
app = FastAPI(
    title="Obscura Citadel Service",
    description="Secure key storage and blind computation via Nillion",
    version="2.0.0",
)


# =====================
# Request/Response Models
# =====================

class StoreSecretRequest(BaseModel):
    secret: str
    name: str
    secret_type: str = "generic"
    tags: Dict[str, str] = {}


class StoreExchangeCredentialsRequest(BaseModel):
    """Request to store exchange API credentials"""
    exchange: str  # binance, coinbase, kraken, etc.
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None  # For exchanges like Coinbase
    label: str = ""  # User-friendly label (e.g., "Main Trading Account")


class ComputeRequest(BaseModel):
    store_id: str
    payload: str  # Base64 encoded
    operation: str = "sign"


# =====================
# Health & Info
# =====================

@app.get("/health")
async def health_check():
    status = nillion.get_health_status()
    return {
        "status": "healthy" if status.get("connected") else "degraded",
        "service": "citadel",
        "nillion": status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def get_status():
    """Get Nillion connection status"""
    return nillion.get_health_status()


# =====================
# Secret Management
# =====================

@app.post("/secrets/store")
async def store_secret(owner_id: str, request: StoreSecretRequest):
    """Store a secret in Nillion"""
    try:
        secret_type = SecretType(request.secret_type)
    except ValueError:
        secret_type = SecretType.GENERIC
    
    store_id = await nillion.store_secret(
        secret=request.secret,
        name=request.name,
        secret_type=secret_type,
        owner=owner_id,
        permissions={owner_id: PermissionLevel.OWNER},
        tags=request.tags
    )
    
    return {
        "store_id": store_id,
        "message": "Secret stored securely"
    }


@app.get("/secrets/{store_id}")
async def retrieve_secret(store_id: str, requester_id: str):
    """Retrieve a secret (if permitted)"""
    secret = await nillion.retrieve_secret(store_id, requester_id)
    
    if secret is None:
        raise HTTPException(403, "Access denied or secret not found")
    
    return {
        "value": secret.decode() if isinstance(secret, bytes) else secret
    }


@app.delete("/secrets/{store_id}")
async def delete_secret(store_id: str, owner_id: str):
    """Delete a secret"""
    # Would implement deletion in Nillion
    return {"message": "Secret deleted"}


# =====================
# Exchange Credentials
# =====================

@app.post("/exchange/credentials")
async def store_exchange_credentials(owner_id: str, request: StoreExchangeCredentialsRequest):
    """
    Store exchange API credentials securely via Nillion.
    
    This is the recommended way to store API keys - they are encrypted
    and distributed across Nillion's network, never stored in plaintext.
    
    Returns store_ids for both api_key and api_secret which can be used
    to retrieve credentials when needed for trading.
    """
    exchange_lower = request.exchange.lower()
    
    # Store API key
    api_key_store_id = await nillion.store_secret(
        secret=request.api_key,
        name=f"{exchange_lower}_api_key",
        secret_type=SecretType.API_KEY,
        owner=owner_id,
        permissions={owner_id: PermissionLevel.OWNER},
        tags={
            "exchange": exchange_lower,
            "type": "api_key",
            "label": request.label
        }
    )
    
    # Store API secret
    api_secret_store_id = await nillion.store_secret(
        secret=request.api_secret,
        name=f"{exchange_lower}_api_secret",
        secret_type=SecretType.API_SECRET,
        owner=owner_id,
        permissions={owner_id: PermissionLevel.OWNER},
        tags={
            "exchange": exchange_lower,
            "type": "api_secret",
            "label": request.label
        }
    )
    
    result = {
        "exchange": exchange_lower,
        "api_key_store_id": api_key_store_id,
        "api_secret_store_id": api_secret_store_id,
        "label": request.label,
        "message": f"{request.exchange} credentials stored securely"
    }
    
    # Store passphrase if provided (for Coinbase, etc.)
    if request.passphrase:
        passphrase_store_id = await nillion.store_secret(
            secret=request.passphrase,
            name=f"{exchange_lower}_passphrase",
            secret_type=SecretType.API_KEY,
            owner=owner_id,
            permissions={owner_id: PermissionLevel.OWNER},
            tags={
                "exchange": exchange_lower,
                "type": "passphrase",
                "label": request.label
            }
        )
        result["passphrase_store_id"] = passphrase_store_id
    
    return result


@app.get("/exchange/credentials/{exchange}")
async def get_exchange_credentials(exchange: str, owner_id: str):
    """
    Retrieve exchange credentials for trading.
    
    Returns the decrypted API key and secret for the specified exchange.
    Only the owner can retrieve their own credentials.
    """
    exchange_lower = exchange.lower()
    
    # Get stored credentials metadata
    credentials = await nillion.list_secrets_by_owner(owner_id)
    
    api_key_id = None
    api_secret_id = None
    passphrase_id = None
    
    for cred in credentials:
        tags = cred.get("tags", {})
        if tags.get("exchange") == exchange_lower:
            if tags.get("type") == "api_key":
                api_key_id = cred.get("store_id")
            elif tags.get("type") == "api_secret":
                api_secret_id = cred.get("store_id")
            elif tags.get("type") == "passphrase":
                passphrase_id = cred.get("store_id")
    
    if not api_key_id or not api_secret_id:
        raise HTTPException(404, f"No credentials found for {exchange}")
    
    # Retrieve the actual secrets
    api_key = await nillion.retrieve_secret(api_key_id, owner_id)
    api_secret = await nillion.retrieve_secret(api_secret_id, owner_id)
    
    if api_key is None or api_secret is None:
        raise HTTPException(403, "Failed to retrieve credentials")
    
    result = {
        "exchange": exchange_lower,
        "api_key": api_key.decode() if isinstance(api_key, bytes) else api_key,
        "api_secret": api_secret.decode() if isinstance(api_secret, bytes) else api_secret,
    }
    
    if passphrase_id:
        passphrase = await nillion.retrieve_secret(passphrase_id, owner_id)
        if passphrase:
            result["passphrase"] = passphrase.decode() if isinstance(passphrase, bytes) else passphrase
    
    return result


@app.delete("/exchange/credentials/{exchange}")
async def delete_exchange_credentials(exchange: str, owner_id: str):
    """Delete exchange credentials"""
    exchange_lower = exchange.lower()
    
    # Get stored credentials
    credentials = await nillion.list_secrets_by_owner(owner_id)
    
    deleted = []
    for cred in credentials:
        tags = cred.get("tags", {})
        if tags.get("exchange") == exchange_lower:
            store_id = cred.get("store_id")
            # Delete the secret
            await nillion.delete_secret(store_id, owner_id)
            deleted.append(store_id)
    
    if not deleted:
        raise HTTPException(404, f"No credentials found for {exchange}")
    
    return {
        "exchange": exchange_lower,
        "deleted_count": len(deleted),
        "message": f"{exchange} credentials deleted"
    }


@app.get("/exchange/list")
async def list_exchange_credentials(owner_id: str):
    """List all stored exchange credentials (metadata only, no secrets)"""
    credentials = await nillion.list_secrets_by_owner(owner_id)
    
    exchanges = {}
    for cred in credentials:
        tags = cred.get("tags", {})
        exchange = tags.get("exchange")
        if exchange:
            if exchange not in exchanges:
                exchanges[exchange] = {
                    "exchange": exchange,
                    "label": tags.get("label", ""),
                    "created_at": cred.get("created_at"),
                    "credentials": []
                }
            exchanges[exchange]["credentials"].append({
                "type": tags.get("type"),
                "store_id": cred.get("store_id")
            })
    
    return {"exchanges": list(exchanges.values())}


# =====================
# Permissions
# =====================

@app.post("/permissions/grant")
async def grant_permission(
    store_id: str,
    owner_id: str,
    grantee_id: str,
    level: str = "read"
):
    """Grant access to a secret"""
    try:
        perm_level = PermissionLevel(level)
    except ValueError:
        perm_level = PermissionLevel.READ
    
    success = await nillion.grant_access(store_id, grantee_id, perm_level, owner_id)
    
    if not success:
        raise HTTPException(400, "Failed to grant access")
    
    return {"message": f"Granted {level} access to {grantee_id}"}


@app.post("/permissions/revoke")
async def revoke_permission(store_id: str, owner_id: str, revokee_id: str):
    """Revoke access to a secret"""
    success = await nillion.revoke_access(store_id, revokee_id, owner_id)
    
    if not success:
        raise HTTPException(400, "Failed to revoke access")
    
    return {"message": f"Revoked access from {revokee_id}"}


# =====================
# Blind Compute
# =====================

@app.post("/compute/sign")
async def compute_signature(request: ComputeRequest, requester_id: str):
    """Compute signature using blind compute"""
    import base64
    
    payload = base64.b64decode(request.payload)
    
    signature = await nillion.compute_signature(
        store_id=request.store_id,
        payload=payload,
        requester=requester_id
    )
    
    if signature is None:
        raise HTTPException(403, "Access denied or computation failed")
    
    return {"signature": signature}


# =====================
# Main Entry Point
# =====================

def run_standalone(host: str = "0.0.0.0", port: int = 8005):
    """Run as standalone service"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_standalone()
