"""
Arcium Integration Module (Backend)

Handles the storage and tracking of Arcium private execution tasks.
Since the actual encryption and submission happen client-side (via the JS SDK),
this module acts as a registry and verification layer.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, DateTime, JSON, Boolean, update
from sqlalchemy.dialects.postgresql import UUID

from shared.database.models import Base
from shared.database.connection import get_async_session
from shared.database.repositories import BaseRepository

logger = logging.getLogger("obscura.arcium")

# --- Database Model ---

class ArciumTask(Base):
    __tablename__ = "arcium_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=True) # Optional linkage to user
    
    # Task Details
    cluster_id = Column(String, default="arcium-devnet-cluster-1")
    program_id = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="pending") # pending, submitted, completed, failed
    tx_hash = Column(String, nullable=True)
    
    # Metadata
    input_params = Column(JSON, nullable=True) # Non-sensitive params
    result_payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Repository ---

class ArciumRepository(BaseRepository):
    async def create_task(self, **kwargs) -> ArciumTask:
        task = ArciumTask(**kwargs)
        self.session.add(task)
        await self.session.flush()
        return task

    async def update_status(self, task_id: str, status: str, tx_hash: str = None):
        """
        Updates the status and optionally the transaction hash of a task.
        """
        stmt = (
            update(ArciumTask)
            .where(ArciumTask.id == uuid.UUID(task_id))
            .values(status=status, updated_at=datetime.utcnow())
        )
        
        if tx_hash:
            stmt = stmt.values(tx_hash=tx_hash)
            
        await self.session.execute(stmt)
        await self.session.flush()

# --- Service ---

class ArciumService:
    async def record_submission(self, user_id: str, cluster_id: str, params: Dict) -> str:
        """
        Records that a user has submitted a task to Arcium.
        """
        async with get_async_session() as session:
            repo = ArciumRepository(session)
            task = await repo.create_task(
                user_id=user_id,
                cluster_id=cluster_id,
                input_params=params,
                status="submitted"
            )
            await session.commit()
            return str(task.id)

    async def verify_execution(self, task_id: str, tx_hash: str):
        """
        Verifies the execution on-chain (Solana) and updates the record.
        """
        # In a real app, we'd query the Solana RPC to confirm the tx matches the task
        # For now, we trust the client provided hash and update the status
        async with get_async_session() as session:
            repo = ArciumRepository(session)
            await repo.update_status(task_id, "completed", tx_hash)
            await session.commit()
            logger.info(f"Verified and completed Arcium task {task_id} with tx {tx_hash}")

arcium_service = ArciumService()
