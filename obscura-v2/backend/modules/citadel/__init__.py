"""
Citadel Module

Secure computing and key management using Nillion SecretVault.
Provides TEE-like functionality for private key operations.

Components:
- nillion_client: Nillion SecretVault integration
- main: FastAPI service for secure operations
- service: Standalone service wrapper
"""

from .nillion_client import (
    NillionClient,
    SecretType,
    PermissionLevel,
    nillion,
)

__all__ = [
    "NillionClient",
    "SecretType",
    "PermissionLevel",
    "nillion",
]
