"""
Arcium API Routes

Endpoints for the frontend to record and track Arcium private execution tasks.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from modules.solana.arcium_service import arcium_service
# from shared.auth import get_current_user # Assuming auth exists

router = APIRouter(prefix="/arcium", tags=["Arcium"])

class RecordTaskRequest(BaseModel):
    cluster_id: str = "arcium-devnet-cluster-1"
    params: Dict[str, Any]
    # In a real app, we might include a signature or proof of submission

class VerifyTaskRequest(BaseModel):
    task_id: str
    tx_hash: str

class TaskResponse(BaseModel):
    task_id: str
    status: str

@router.post("/record", response_model=TaskResponse)
async def record_arcium_task(
    request: RecordTaskRequest,
    # user = Depends(get_current_user) # Uncomment when auth is ready
):
    """
    Records a client-side Arcium submission in the database.
    """
    # Mock user ID for now
    user_id = "mock-user-id" 
    
    try:
        task_id = await arcium_service.record_submission(
            user_id=user_id,
            cluster_id=request.cluster_id,
            params=request.params
        )
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_arcium_task(request: VerifyTaskRequest):
    """
    Updates the task status to completed with the transaction hash.
    """
    try:
        await arcium_service.verify_execution(request.task_id, request.tx_hash)
        return {"status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
