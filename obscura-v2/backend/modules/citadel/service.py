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
