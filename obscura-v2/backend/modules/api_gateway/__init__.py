"""
API Gateway Module

Unified entry point for all Obscura V2 services.
Routes requests to appropriate backend modules.

Components:
- gateway: Main FastAPI application
- routes: API route definitions
- middleware: Auth, rate limiting, logging
"""

from .gateway import app, run_gateway

__all__ = [
    "app",
    "run_gateway",
]
