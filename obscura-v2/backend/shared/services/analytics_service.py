"""
Analytics Service

Calculates PnL and other metrics for trades and positions.
"""

import logging
from decimal import Decimal
from typing import Dict, Any

logger = logging.getLogger("obscura.analytics")

class AnalyticsService:
    def calculate_trade_pnl(self, entry_price: float, exit_price: float, amount: float, side: str) -> Dict[str, float]:
        """
        Calculate PnL for a closed trade.
        """
        entry = Decimal(str(entry_price))
        exit = Decimal(str(exit_price))
        qty = Decimal(str(amount))
        
        if side == 'long' or side == 'buy': # Closing a short (buy) or opening a long (buy)? 
            # Wait, if we are calculating PnL, we assume we have an entry and an exit.
            # If side is 'long' (meaning we were long), then PnL = (Exit - Entry) * Qty
            pnl = (exit - entry) * qty
        else: # Short
            pnl = (entry - exit) * qty
            
        pnl_float = float(pnl)
        roi = (pnl_float / (entry_price * amount)) * 100 if entry_price > 0 else 0
        
        return {
            "pnl_usd": pnl_float,
            "roi_percentage": roi
        }

analytics_service = AnalyticsService()
