"""
PnL Calculator and Reputation Scoring Service.

This module provides functionality to:
1. Reconstruct trading positions from raw trade history (FIFO method).
2. Calculate Realized PnL for closed positions.
3. Generate Reputation Scores based on trading performance.
"""
from decimal import Decimal
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeExecution:
    """Represents a single trade execution (fill)."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: Decimal
    price: Decimal
    fee: Decimal
    timestamp: int
    platform: str = "spot"


@dataclass
class ClosedTrade:
    """Represents a completed round-trip trade (Entry + Exit)."""
    symbol: str
    entry_date: datetime
    exit_date: datetime
    duration_seconds: float
    side: str  # 'long' or 'short'
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    fee: Decimal
    net_pnl: Decimal
    roi_percentage: float


@dataclass
class ReputationScore:
    """Trader reputation metrics."""
    trader_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl_usd: Decimal
    profit_factor: float
    average_roi: float
    score: float  # 0-100
    generated_at: datetime = field(default_factory=datetime.utcnow)


class PnLCalculator:
    """
    Calculates PnL and Reputation Scores using FIFO accounting.
    """

    def __init__(self):
        self.positions: Dict[str, List[Dict[str, Any]]] = {}  # symbol -> list of open lots

    def calculate_performance(self, trades: List[Any], trader_id: str) -> ReputationScore:
        """
        Calculate performance metrics from a list of raw trades.
        
        Args:
            trades: List of RawTrade objects (SQLAlchemy models or dicts)
            trader_id: ID of the trader
            
        Returns:
            ReputationScore object
        """
        # 1. Convert to standardized TradeExecution objects
        executions = self._normalize_trades(trades)
        
        # 2. Sort by timestamp
        executions.sort(key=lambda x: x.timestamp)
        
        # 3. Process trades to generate closed positions
        closed_trades = self._process_executions(executions)
        
        # 4. Calculate metrics
        return self._calculate_metrics(closed_trades, trader_id)

    def calculate_from_ccxt_trades(self, trades: List[dict], trader_id: str = "user") -> tuple[ReputationScore, List[ClosedTrade]]:
        """
        Calculate performance metrics from CCXT trade format.
        
        Args:
            trades: List of trade dicts from ccxt.fetch_my_trades()
            trader_id: ID of the trader
            
        Returns:
            Tuple of (ReputationScore, List[ClosedTrade])
        """
        # Convert CCXT format to TradeExecution objects
        executions = []
        for t in trades:
            try:
                fee_cost = t.get('fee', {}).get('cost', 0) or 0
                executions.append(TradeExecution(
                    id=str(t.get('id', '')),
                    symbol=t.get('symbol', ''),
                    side=t.get('side', '').lower(),
                    quantity=Decimal(str(t.get('amount', 0))),
                    price=Decimal(str(t.get('price', 0))),
                    fee=Decimal(str(fee_cost)),
                    timestamp=t.get('timestamp', 0),
                    platform="spot"
                ))
            except Exception as e:
                logger.warning(f"Skipping invalid trade: {e}")
                
        # Sort by timestamp
        executions.sort(key=lambda x: x.timestamp)
        
        # Process trades to generate closed positions
        closed_trades = self._process_executions(executions)
        
        # Calculate metrics
        return self._calculate_metrics(closed_trades, trader_id), closed_trades

    def _normalize_trades(self, raw_trades: List[Any]) -> List[TradeExecution]:
        """Convert raw DB models to TradeExecution objects."""
        executions = []
        for t in raw_trades:
            # Handle both SQLAlchemy objects and dicts
            get = lambda x, k: x.get(k) if isinstance(x, dict) else getattr(x, k)
            
            try:
                executions.append(TradeExecution(
                    id=str(get(t, 'id')),
                    symbol=get(t, 'symbol'),
                    side=get(t, 'side').lower(),
                    quantity=Decimal(str(get(t, 'quantity'))),
                    price=Decimal(str(get(t, 'price'))),
                    fee=Decimal(str(get(t, 'fee') or 0)),
                    timestamp=get(t, 'timestamp'),
                    platform=get(t, 'platform') or "spot"
                ))
            except Exception as e:
                logger.warning(f"Skipping invalid trade {get(t, 'id')}: {e}")
                
        return executions

    def _process_executions(self, executions: List[TradeExecution]) -> List[ClosedTrade]:
        """
        Process executions using FIFO to generate closed trades.
        """
        closed_trades = []
        # Reset positions for this calculation
        self.positions = {}  # symbol -> list of {qty, price, side, timestamp, fee}

        for exec in executions:
            symbol = exec.symbol
            if symbol not in self.positions:
                self.positions[symbol] = []
            
            open_lots = self.positions[symbol]
            remaining_qty = exec.quantity
            
            # Determine if this execution opens or closes positions
            # For Spot: Buy = Open Long, Sell = Close Long
            # For Futures: Need to track net position. 
            # Simplified logic: If side matches open lots, add. If opposite, reduce.
            
            while remaining_qty > 0 and open_lots:
                # Check if current execution is opposite to the oldest open lot
                oldest_lot = open_lots[0]
                
                is_closing = (oldest_lot['side'] != exec.side)
                
                if not is_closing:
                    break  # Same side, just add to position
                
                # Match execution against oldest lot
                match_qty = min(remaining_qty, oldest_lot['quantity'])
                
                # Calculate PnL for this portion
                entry_price = oldest_lot['price']
                exit_price = exec.price
                
                # PnL direction depends on position side
                if oldest_lot['side'] == 'buy':  # Long
                    gross_pnl = (exit_price - entry_price) * match_qty
                    trade_side = 'long'
                else:  # Short
                    gross_pnl = (entry_price - exit_price) * match_qty
                    trade_side = 'short'
                
                # Pro-rate fees
                entry_fee = oldest_lot['fee'] * (match_qty / oldest_lot['initial_quantity'])
                exit_fee = exec.fee * (match_qty / exec.quantity) if exec.quantity > 0 else Decimal(0)
                total_fee = entry_fee + exit_fee
                
                net_pnl = gross_pnl - total_fee
                
                # ROI
                invested = entry_price * match_qty
                roi = (net_pnl / invested) * 100 if invested > 0 else Decimal(0)
                
                closed_trades.append(ClosedTrade(
                    symbol=symbol,
                    entry_date=datetime.fromtimestamp(oldest_lot['timestamp'] / 1000),
                    exit_date=datetime.fromtimestamp(exec.timestamp / 1000),
                    duration_seconds=(exec.timestamp - oldest_lot['timestamp']) / 1000,
                    side=trade_side,
                    quantity=match_qty,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    gross_pnl=gross_pnl,
                    fee=total_fee,
                    net_pnl=net_pnl,
                    roi_percentage=float(roi)
                ))
                
                # Update remaining quantities
                remaining_qty -= match_qty
                oldest_lot['quantity'] -= match_qty
                oldest_lot['fee'] -= entry_fee  # Reduce remaining fee on lot
                
                if oldest_lot['quantity'] <= 0:
                    open_lots.pop(0)
            
            # If quantity remains, add as new open lot
            if remaining_qty > 0:
                open_lots.append({
                    'quantity': remaining_qty,
                    'initial_quantity': remaining_qty,
                    'price': exec.price,
                    'side': exec.side,
                    'timestamp': exec.timestamp,
                    'fee': exec.fee * (remaining_qty / exec.quantity) if exec.quantity > 0 else Decimal(0)
                })
                
        return closed_trades

    def _calculate_metrics(self, closed_trades: List[ClosedTrade], trader_id: str) -> ReputationScore:
        """Aggregate closed trades into reputation metrics."""
        if not closed_trades:
            return ReputationScore(
                trader_id=trader_id,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                total_pnl_usd=Decimal("0"),
                profit_factor=0.0,
                average_roi=0.0,
                score=0.0
            )
            
        total_trades = len(closed_trades)
        winning_trades = sum(1 for t in closed_trades if t.net_pnl > 0)
        losing_trades = sum(1 for t in closed_trades if t.net_pnl <= 0)
        
        total_pnl = sum((t.net_pnl for t in closed_trades), Decimal("0"))
        gross_profit = sum((t.net_pnl for t in closed_trades if t.net_pnl > 0), Decimal("0"))
        gross_loss = abs(sum((t.net_pnl for t in closed_trades if t.net_pnl < 0), Decimal("0")))
        
        win_rate = (winning_trades / total_trades) * 100
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        avg_roi = float(sum(t.roi_percentage for t in closed_trades) / total_trades)
        
        # Calculate Reputation Score (0-100)
        # Simple weighted model:
        # - Win Rate (30%): 50% = 50pts
        # - Profit Factor (30%): 1.5 = 50pts, 3.0 = 100pts
        # - ROI (20%): 10% avg = 50pts
        # - Activity (20%): Logarithmic scale of trade count
        
        score_win_rate = min(win_rate, 100)
        score_pf = min(profit_factor * 33, 100) if profit_factor != float('inf') else 100
        score_roi = min(max(avg_roi * 5, 0), 100)  # 20% ROI = 100
        score_activity = min(total_trades * 2, 100)  # 50 trades = 100
        
        final_score = (
            (score_win_rate * 0.30) +
            (score_pf * 0.30) +
            (score_roi * 0.20) +
            (score_activity * 0.20)
        )
        
        return ReputationScore(
            trader_id=trader_id,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl_usd=total_pnl,
            profit_factor=profit_factor,
            average_roi=avg_roi,
            score=round(final_score, 2)
        )

    def get_open_positions(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return current open positions after processing."""
        return self.positions


# Global instance
pnl_calculator = PnLCalculator()
