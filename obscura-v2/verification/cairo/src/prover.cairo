// =============================================================================
// Obscura Prover - Cairo 1.0
// =============================================================================
// Off-chain proof generation logic for trading performance verification.
// This module contains the core ZK circuit logic that processes trades and
// generates verifiable performance reports.
// =============================================================================

use core::hash::{HashStateTrait, HashStateExTrait};
use core::poseidon::PoseidonTrait;
use super::types::{
    Trade, Position, PositionTrait, BuyLot, SymbolPnL, TradeResult, TradeResultTrait,
    I128, I128Trait, MAX_TRADES, MAX_QUEUE_SIZE, SCALE_FACTOR
};

// =============================================================================
// Position Management
// =============================================================================

/// Compact the FIFO queue to remove empty lots
fn compact_queue(ref position: Position) {
    let mut new_queue: Array<BuyLot> = array![];
    
    let mut i: u32 = 0;
    loop {
        if i >= position.queue_length {
            break;
        }
        let lot = position.get_lot(i);
        if lot.quantity > 0 {
            new_queue.append(lot);
        }
        i += 1;
    };

    // Reset all slots
    position.queue_0 = Default::default();
    position.queue_1 = Default::default();
    position.queue_2 = Default::default();
    position.queue_3 = Default::default();
    position.queue_4 = Default::default();
    position.queue_5 = Default::default();
    position.queue_6 = Default::default();
    position.queue_7 = Default::default();
    position.queue_8 = Default::default();
    position.queue_9 = Default::default();

    // Refill from compacted array
    let new_len = new_queue.len();
    let mut j: u32 = 0;
    loop {
        if j >= new_len {
            break;
        }
        position = position.set_lot(j, *new_queue.at(j));
        j += 1;
    };
    position.queue_length = new_len;
}

/// Calculate PnL for a single trade using FIFO cost-basis accounting
/// 
/// For BUY orders: Add to the FIFO queue
/// For SELL orders: Match against oldest lots first, calculate realized PnL
pub fn calculate_trade_pnl(ref position: Position, trade: Trade) -> I128 {
    assert(trade.quantity > 0, 'Trade quantity must be positive');
    assert(trade.price > 0, 'Trade price must be positive');

    let mut realized_pnl = I128Trait::zero();
    let is_buy = trade.side == 0;

    if is_buy {
        // BUY: Add lot to queue
        assert(position.queue_length < MAX_QUEUE_SIZE, 'Queue is full');
        
        let new_lot = BuyLot { quantity: trade.quantity, price: trade.price };
        position = position.set_lot(position.queue_length, new_lot);
        position.queue_length += 1;
    } else {
        // SELL: Match against FIFO queue
        let mut remaining_sell_qty = trade.quantity;

        let mut queue_index: u32 = 0;
        loop {
            if remaining_sell_qty == 0 || queue_index >= position.queue_length {
                break;
            }

            let mut current_lot = position.get_lot(queue_index);

            if current_lot.quantity > 0 {
                // Determine how much to sell from this lot
                let sell_from_lot = if current_lot.quantity < remaining_sell_qty {
                    current_lot.quantity
                } else {
                    remaining_sell_qty
                };

                // Calculate PnL for this portion
                let (pnl_magnitude, is_profit) = if trade.price >= current_lot.price {
                    ((trade.price - current_lot.price), true)
                } else {
                    ((current_lot.price - trade.price), false)
                };

                // Scale PnL: (price_diff * quantity) / SCALE_FACTOR
                // Using u256 to prevent overflow
                let pnl_u256: u256 = (pnl_magnitude.into() * sell_from_lot.into()) / SCALE_FACTOR;
                let lot_pnl_magnitude: u128 = pnl_u256.try_into().unwrap();
                
                let lot_pnl = I128Trait::new(lot_pnl_magnitude, !is_profit);
                realized_pnl = realized_pnl.add(lot_pnl);

                // Update lot quantity
                current_lot.quantity -= sell_from_lot;
                position = position.set_lot(queue_index, current_lot);
                remaining_sell_qty -= sell_from_lot;
            }

            queue_index += 1;
        };

        assert(remaining_sell_qty == 0, 'Insufficient inventory');
        
        // Compact queue after sells
        compact_queue(ref position);

        // Deduct fee from PnL
        if trade.fee > 0 {
            realized_pnl = realized_pnl.sub(I128Trait::from_u128(trade.fee));
        }
    }

    // Update position's accumulated PnL
    position.realized_pnl = position.realized_pnl.add(realized_pnl);
    realized_pnl
}

// =============================================================================
// Hash Functions
// =============================================================================

/// Create a commitment to the trade batch (private data)
pub fn create_trade_commitment(
    trades: Span<Trade>,
    trade_count: u32,
    trader: felt252,
    timestamp_start: u64,
    timestamp_end: u64,
) -> felt252 {
    let mut state = PoseidonTrait::new();
    
    // Add public context
    state = state.update(trader);
    state = state.update(timestamp_start.into());
    state = state.update(timestamp_end.into());
    state = state.update(trade_count.into());

    // Add each trade's data
    let mut i: u32 = 0;
    loop {
        if i >= trade_count {
            break;
        }
        let trade = *trades.at(i);
        
        // Hash all trade fields
        state = state.update(trade.trade_id);
        state = state.update(trade.trader_user_id);
        state = state.update(trade.symbol);
        state = state.update(trade.side.into());
        state = state.update(trade.order_type.into());
        state = state.update(trade.quantity.into());
        state = state.update(trade.price.into());
        state = state.update(trade.fee.into());
        state = state.update(trade.order_updated_at.into());
        state = state.update(trade.exchange);
        
        i += 1;
    };

    state.finalize()
}

/// Create a hash of the report (public output)
pub fn create_report_hash(
    trader: felt252,
    timestamp_start: u64,
    timestamp_end: u64,
    symbol_pnls: Span<SymbolPnL>,
    symbol_count: u32,
    trade_count: u32,
) -> felt252 {
    let mut state = PoseidonTrait::new();
    
    // Add basic report info
    state = state.update(trader);
    state = state.update(timestamp_start.into());
    state = state.update(timestamp_end.into());
    state = state.update(trade_count.into());
    state = state.update(symbol_count.into());

    // Add each symbol's PnL
    let mut i: u32 = 0;
    loop {
        if i >= symbol_count {
            break;
        }
        let symbol_pnl = *symbol_pnls.at(i);
        state = state.update(symbol_pnl.symbol);
        state = state.update(symbol_pnl.pnl.value.into());
        state = state.update(if symbol_pnl.pnl.is_negative { 1 } else { 0 });
        state = state.update(if symbol_pnl.is_profitable { 1 } else { 0 });
        
        i += 1;
    };

    state.finalize()
}

// =============================================================================
// Main Prover Entry Point
// =============================================================================

/// Process a batch of trades and generate a verifiable result
/// 
/// # Arguments
/// * `trades` - Array of private trade data
/// * `actual_trade_count` - Number of valid trades in the array
/// * `trader` - Trader's identifier (public)
/// * `timestamp_start` - Report period start (public)
/// * `timestamp_end` - Report period end (public)
/// * `expected_report_hash` - Hash claimed by the trader (public)
/// 
/// # Returns
/// * `TradeResult` - Verified performance data
pub fn verify_trades(
    trades: Span<Trade>,
    actual_trade_count: u32,
    trader: felt252,
    timestamp_start: u64,
    timestamp_end: u64,
    expected_report_hash: felt252,
) -> TradeResult {
    // Sanity checks
    assert(actual_trade_count <= MAX_TRADES, 'Trade count exceeds maximum');
    assert(timestamp_start < timestamp_end, 'Invalid timestamp range');

    // Track positions per symbol (simplified: we use a fixed array approach)
    // In practice, you'd use a more efficient symbol->position mapping
    let mut symbol_positions: Array<(felt252, Position)> = array![];
    
    // Process each trade
    let mut processed_trades: u32 = 0;
    let mut i: u32 = 0;
    loop {
        if i >= actual_trade_count {
            break;
        }
        
        let trade = *trades.at(i);
        
        // Validate trade data
        assert(trade.quantity > 0, 'Invalid trade quantity');
        assert(trade.price > 0, 'Invalid trade price');

        // Find or create position for this symbol
        let mut found = false;
        let mut j: u32 = 0;
        let len = symbol_positions.len();
        
        loop {
            if j >= len {
                break;
            }
            let (sym, _pos) = *symbol_positions.at(j);
            if sym == trade.symbol {
                found = true;
                // Update existing position
                let (_, mut position) = symbol_positions.pop_front().unwrap();
                // Re-insert others first
                let mut temp: Array<(felt252, Position)> = array![];
                let mut k: u32 = 0;
                loop {
                    if k >= j {
                        break;
                    }
                    temp.append(*symbol_positions.at(k));
                    k += 1;
                };
                // Process trade
                let _ = calculate_trade_pnl(ref position, trade);
                temp.append((trade.symbol, position));
                // Add remaining
                loop {
                    if symbol_positions.len() == 0 {
                        break;
                    }
                    temp.append(symbol_positions.pop_front().unwrap());
                };
                symbol_positions = temp;
                break;
            }
            j += 1;
        };

        if !found {
            // Create new position for this symbol
            let mut new_position: Position = Default::default();
            let _ = calculate_trade_pnl(ref new_position, trade);
            symbol_positions.append((trade.symbol, new_position));
        }

        processed_trades += 1;
        i += 1;
    };

    assert(processed_trades == actual_trade_count, 'Trade count mismatch');

    // Build symbol PnL results
    let mut symbol_pnls: Array<SymbolPnL> = array![];
    let symbol_count = symbol_positions.len();
    
    let mut i: u32 = 0;
    loop {
        if i >= symbol_count {
            break;
        }
        let (symbol, position) = *symbol_positions.at(i);
        symbol_pnls.append(SymbolPnL {
            symbol,
            pnl: position.realized_pnl,
            is_profitable: position.realized_pnl.is_positive(),
        });
        i += 1;
    };

    // Create commitment to trade data
    let commitment = create_trade_commitment(
        trades,
        actual_trade_count,
        trader,
        timestamp_start,
        timestamp_end,
    );

    // Verify report hash matches computed values
    let computed_hash = create_report_hash(
        trader,
        timestamp_start,
        timestamp_end,
        symbol_pnls.span(),
        symbol_count,
        actual_trade_count,
    );

    assert(computed_hash == expected_report_hash, 'Report hash mismatch');

    // Build result (pad to fixed size)
    TradeResult {
        symbol_pnl_0: if symbol_count > 0 { *symbol_pnls.at(0) } else { Default::default() },
        symbol_pnl_1: if symbol_count > 1 { *symbol_pnls.at(1) } else { Default::default() },
        symbol_pnl_2: if symbol_count > 2 { *symbol_pnls.at(2) } else { Default::default() },
        symbol_pnl_3: if symbol_count > 3 { *symbol_pnls.at(3) } else { Default::default() },
        symbol_pnl_4: if symbol_count > 4 { *symbol_pnls.at(4) } else { Default::default() },
        symbol_pnl_5: if symbol_count > 5 { *symbol_pnls.at(5) } else { Default::default() },
        symbol_pnl_6: if symbol_count > 6 { *symbol_pnls.at(6) } else { Default::default() },
        symbol_pnl_7: if symbol_count > 7 { *symbol_pnls.at(7) } else { Default::default() },
        symbol_pnl_8: if symbol_count > 8 { *symbol_pnls.at(8) } else { Default::default() },
        symbol_pnl_9: if symbol_count > 9 { *symbol_pnls.at(9) } else { Default::default() },
        symbol_count,
        trade_count: actual_trade_count,
        commitment,
    }
}
