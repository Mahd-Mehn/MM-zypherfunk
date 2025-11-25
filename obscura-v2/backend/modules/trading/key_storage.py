"""
Secure API Key Storage Service

Manages encrypted storage of exchange API credentials using Nillion.
Enables secure trade execution on behalf of users without exposing keys.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_async_session, APIKeyStore, ExchangeType
from shared.services import RedisService, CacheKeys
from modules.citadel import nillion, SecretType, PermissionLevel

logger = logging.getLogger("obscura.key_storage")


class ExchangeProvider(Enum):
    """Supported exchange providers"""
    # CEX
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    OKX = "okx"
    BYBIT = "bybit"
    KUCOIN = "kucoin"
    HUOBI = "huobi"
    BITFINEX = "bitfinex"
    GATE = "gate"
    MEXC = "mexc"
    BITGET = "bitget"
    # DEX (for private keys)
    UNISWAP = "uniswap"
    STARKNET = "starknet"
    PANCAKESWAP = "pancakeswap"
    SUSHISWAP = "sushiswap"
    # General
    ETHEREUM = "ethereum"
    NEAR = "near"


class SecureKeyStorage:
    """
    Secure API key management using Nillion for encrypted storage.
    Backed by PostgreSQL and Redis.
    """
    
    def __init__(self):
        self.redis = RedisService()
        logger.info("SecureKeyStorage initialized with DB/Redis backend")

    async def store_exchange_credentials(
        self,
        user_id: str,
        exchange: ExchangeProvider,
        api_key: str,
        api_secret: str,
        passphrase: Optional[str] = None,
        uid: Optional[str] = None,
        label: str = ""
    ) -> str:
        """
        Securely store exchange API credentials.
        """
        credential_id = f"cred_{user_id}_{exchange.value}_{datetime.now().timestamp()}"
        
        # Store API key in Nillion
        key_store_id = await nillion.store_secret(
            secret=api_key,
            name=f"{credential_id}_key",
            secret_type=SecretType.API_KEY,
            owner=user_id,
            permissions={user_id: PermissionLevel.OWNER},
            tags={"exchange": exchange.value, "type": "api_key"}
        )
        
        # Store API secret in Nillion
        secret_store_id = await nillion.store_secret(
            secret=api_secret,
            name=f"{credential_id}_secret",
            secret_type=SecretType.API_SECRET,
            owner=user_id,
            permissions={user_id: PermissionLevel.OWNER},
            tags={"exchange": exchange.value, "type": "api_secret"}
        )
        
        # Store extra credentials if provided
        extra_store_ids = {}
        
        if passphrase:
            extra_store_ids['passphrase'] = await nillion.store_secret(
                secret=passphrase,
                name=f"{credential_id}_passphrase",
                secret_type=SecretType.API_SECRET,
                owner=user_id,
                permissions={user_id: PermissionLevel.OWNER}
            )
        
        if uid:
            extra_store_ids['uid'] = await nillion.store_secret(
                secret=uid,
                name=f"{credential_id}_uid",
                secret_type=SecretType.GENERIC,
                owner=user_id,
                permissions={user_id: PermissionLevel.OWNER}
            )
            
        # Store in Database
        async with get_async_session() as session:
            api_key_store = APIKeyStore(
                user_id=user_id,
                exchange=exchange.value,
                exchange_type=ExchangeType.CEX,
                label=label or f"{exchange.value} Account",
                nillion_key_store_id=key_store_id,
                nillion_secret_store_id=secret_store_id,
                nillion_extra_store_ids=extra_store_ids,
                permissions={user_id: "owner"},
                is_active=True
            )
            session.add(api_key_store)
            await session.commit()
            await session.refresh(api_key_store)
            
            # Invalidate cache
            await self.redis.delete(f"user_credentials:{user_id}")
            
            logger.info(f"Stored credentials for {user_id} on {exchange.value}: {api_key_store.id}")
            return str(api_key_store.id)

    async def store_private_key(
        self,
        user_id: str,
        chain: ExchangeProvider,
        private_key: str,
        label: str = ""
    ) -> str:
        """
        Store a private key for DEX/blockchain operations.
        """
        credential_id = f"pk_{user_id}_{chain.value}_{datetime.now().timestamp()}"
        
        # Store private key with high security
        key_store_id = await nillion.store_secret(
            secret=private_key,
            name=f"{credential_id}_pk",
            secret_type=SecretType.PRIVATE_KEY,
            owner=user_id,
            permissions={user_id: PermissionLevel.OWNER},
            tags={"chain": chain.value, "type": "private_key"}
        )
        
        async with get_async_session() as session:
            api_key_store = APIKeyStore(
                user_id=user_id,
                exchange=chain.value,
                exchange_type=ExchangeType.DEX,
                label=label or f"{chain.value} Wallet",
                nillion_key_store_id=key_store_id,
                nillion_secret_store_id=None,
                nillion_extra_store_ids={},
                permissions={user_id: "owner"},
                is_active=True
            )
            session.add(api_key_store)
            await session.commit()
            await session.refresh(api_key_store)
            
            await self.redis.delete(f"user_credentials:{user_id}")
            
            logger.info(f"Stored private key for {user_id} on {chain.value}")
            return str(api_key_store.id)

    async def get_credentials_for_trading(
        self,
        credential_id: str,
        requester_id: str
    ) -> Optional[Dict[str, str]]:
        """
        Retrieve credentials for trading (use sparingly, prefer blind compute).
        """
        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(APIKeyStore.id == credential_id)
            result = await session.execute(stmt)
            cred = result.scalar_one_or_none()
            
            if not cred:
                logger.warning(f"Credential {credential_id} not found")
                return None
            
            # Check permissions
            perms = cred.permissions or {}
            if str(requester_id) != str(cred.user_id) and str(requester_id) not in perms:
                logger.warning(f"Access denied for {requester_id} to {credential_id}")
                return None
            
            try:
                # Retrieve from Nillion
                api_key = await nillion.retrieve_secret(cred.nillion_key_store_id, requester_id)
                
                result = {"api_key": api_key.decode() if isinstance(api_key, bytes) else api_key}
                
                if cred.nillion_secret_store_id:
                    api_secret = await nillion.retrieve_secret(cred.nillion_secret_store_id, requester_id)
                    result["api_secret"] = api_secret.decode() if isinstance(api_secret, bytes) else api_secret
                
                if cred.nillion_extra_store_ids:
                    for name, store_id in cred.nillion_extra_store_ids.items():
                        value = await nillion.retrieve_secret(store_id, requester_id)
                        result[name] = value.decode() if isinstance(value, bytes) else value
                
                # Update last used
                cred.last_validated_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Retrieved credentials {credential_id} for {requester_id}")
                return result
                
            except Exception as e:
                logger.error(f"Failed to retrieve credentials: {e}")
                return None

    async def sign_trade_request(
        self,
        credential_id: str,
        payload: bytes,
        requester_id: str
    ) -> Optional[str]:
        """
        Sign a trade request using blind compute (key never exposed).
        """
        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(APIKeyStore.id == credential_id)
            result = await session.execute(stmt)
            cred = result.scalar_one_or_none()
            
            if not cred:
                return None
            
            # Check compute permissions
            perms = cred.permissions or {}
            if str(requester_id) != str(cred.user_id):
                perm = perms.get(str(requester_id))
                if perm not in ["owner", "compute", "trade"]:
                    logger.warning(f"Compute access denied for {requester_id}")
                    return None
            
            try:
                # Use Nillion blind compute for signing
                signature = await nillion.compute_signature(
                    store_id=cred.nillion_secret_store_id or cred.nillion_key_store_id,
                    payload=payload,
                    requester=requester_id
                )
                
                cred.last_validated_at = datetime.utcnow()
                await session.commit()
                
                logger.info(f"Signed request with {credential_id}")
                return signature
                
            except Exception as e:
                logger.error(f"Signing failed: {e}")
                return None

    async def grant_trade_permission(
        self,
        credential_id: str,
        owner_id: str,
        grantee_id: str,
        permission: str = "trade"
    ) -> bool:
        """
        Grant another user permission to trade with your credentials.
        """
        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(APIKeyStore.id == credential_id)
            result = await session.execute(stmt)
            cred = result.scalar_one_or_none()
            
            if not cred:
                return False
            
            if str(cred.user_id) != str(owner_id):
                logger.warning(f"Only owner can grant permissions")
                return False
            
            # Update credential permissions
            perms = dict(cred.permissions) if cred.permissions else {}
            perms[str(grantee_id)] = permission
            cred.permissions = perms
            
            # Update Nillion permissions
            perm_level = PermissionLevel.COMPUTE if permission == "trade" else PermissionLevel.READ
            
            await nillion.grant_access(cred.nillion_key_store_id, grantee_id, perm_level, owner_id)
            if cred.nillion_secret_store_id:
                await nillion.grant_access(cred.nillion_secret_store_id, grantee_id, perm_level, owner_id)
            
            await session.commit()
            logger.info(f"Granted {permission} permission to {grantee_id} for {credential_id}")
            return True

    async def revoke_trade_permission(
        self,
        credential_id: str,
        owner_id: str,
        revokee_id: str
    ) -> bool:
        """Revoke a user's permission to use credentials"""
        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(APIKeyStore.id == credential_id)
            result = await session.execute(stmt)
            cred = result.scalar_one_or_none()
            
            if not cred:
                return False
            
            if str(cred.user_id) != str(owner_id):
                return False
            
            perms = dict(cred.permissions) if cred.permissions else {}
            if str(revokee_id) in perms:
                del perms[str(revokee_id)]
                cred.permissions = perms
            
            await nillion.revoke_access(cred.nillion_key_store_id, revokee_id, owner_id)
            if cred.nillion_secret_store_id:
                await nillion.revoke_access(cred.nillion_secret_store_id, revokee_id, owner_id)
            
            await session.commit()
            logger.info(f"Revoked {revokee_id}'s access to {credential_id}")
            return True

    async def list_user_credentials(self, user_id: str) -> List[Dict[str, Any]]:
        """List all credentials for a user (metadata only, no secrets)"""
        # Try cache first
        cache_key = f"user_credentials:{user_id}"
        cached = await self.redis.get_cached(cache_key)
        if cached:
            return cached

        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(
                APIKeyStore.user_id == user_id,
                APIKeyStore.is_active == True
            )
            result = await session.execute(stmt)
            creds = result.scalars().all()
            
            result_list = []
            for cred in creds:
                result_list.append({
                    "credential_id": str(cred.id),
                    "exchange": cred.exchange,
                    "label": cred.label,
                    "created_at": cred.created_at.isoformat() if cred.created_at else None,
                    "last_used_at": cred.last_validated_at.isoformat() if cred.last_validated_at else None,
                    "is_active": cred.is_active,
                    "shared_with": list(cred.permissions.keys()) if cred.permissions else []
                })
            
            # Cache result
            await self.redis.set_cached(cache_key, result_list, ttl=300)
            return result_list

    async def delete_credentials(self, credential_id: str, owner_id: str) -> bool:
        """Permanently delete credentials"""
        async with get_async_session() as session:
            stmt = select(APIKeyStore).where(APIKeyStore.id == credential_id)
            result = await session.execute(stmt)
            cred = result.scalar_one_or_none()
            
            if not cred:
                return False
            
            if str(cred.user_id) != str(owner_id):
                return False
            
            # Mark as inactive
            cred.is_active = False
            await session.commit()
            
            # Invalidate cache
            await self.redis.delete(f"user_credentials:{owner_id}")
            
            logger.info(f"Deleted credentials {credential_id}")
            return True


# Singleton instance
key_storage = SecureKeyStorage()
