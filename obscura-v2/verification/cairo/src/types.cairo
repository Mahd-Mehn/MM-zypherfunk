// =============================================================================
// Obscura Verification Types - Cairo 1.0
// =============================================================================
// Core data structures for zero-knowledge trading performance verification.
// Adapted from legacy Noir implementation for Starknet/STARK compatibility.
// =============================================================================

use core::hash::{HashStateTrait, HashStateExTrait};
use core::poseidon::PoseidonTrait;
use starknet::ContractAddress;

// =============================================================================
// Constants
// =============================================================================

/// Maximum number of trades per verification batch
pub const MAX_TRADES: u32 = 10;

/// Scaling factor for decimal precision (1e18)
pub const SCALE_FACTOR: u256 = 1_000_000_000_000_000_000;

/// Maximum queue size for FIFO cost-basis tracking
pub const MAX_QUEUE_SIZE: u32 = 10;

// =============================================================================
// Signed Integer (I128) - For PnL calculations
// =============================================================================

/// Signed 128-bit integer implementation for profit/loss calculations
/// Cairo doesn't have native signed integers, so we implement our own
#[derive(Copy, Drop, Serde, Default, PartialEq)]
pub struct I128 {
    pub value: u128,
    pub is_negative: bool,
}

#[generate_trait]
pub impl I128Impl of I128Trait {
    /// Create a new signed integer
    fn new(value: u128, is_negative: bool) -> I128 {
        I128 { value, is_negative }
    }

    /// Create zero value
    fn zero() -> I128 {
        I128 { value: 0, is_negative: false }
    }

    /// Create from unsigned
    fn from_u128(value: u128) -> I128 {
        I128 { value, is_negative: false }
    }

    /// Negate the value
    fn negate(self: I128) -> I128 {
        I128 { value: self.value, is_negative: !self.is_negative }
    }

    /// Get absolute value
    fn abs(self: I128) -> u128 {
        self.value
    }

    /// Check if positive (including zero)
    fn is_positive(self: I128) -> bool {
        !self.is_negative || self.value == 0
    }

    /// Check if zero
    fn is_zero(self: I128) -> bool {
        self.value == 0
    }

    /// Add two signed integers
    fn add(self: I128, other: I128) -> I128 {
        if self.is_negative == other.is_negative {
            // Same sign: add magnitudes, keep sign
            I128 { value: self.value + other.value, is_negative: self.is_negative }
        } else {
            // Different signs: subtract magnitudes
            if self.value >= other.value {
                I128 { value: self.value - other.value, is_negative: self.is_negative }
            } else {
                I128 { value: other.value - self.value, is_negative: other.is_negative }
            }
        }
    }

    /// Subtract two signed integers
    fn sub(self: I128, other: I128) -> I128 {
        self.add(other.negate())
    }

    /// Multiply two signed integers
    fn mul(self: I128, other: I128) -> I128 {
        I128 {
            value: self.value * other.value,
            is_negative: self.is_negative != other.is_negative && self.value != 0 && other.value != 0,
        }
    }

    /// Divide two signed integers
    fn div(self: I128, other: I128) -> I128 {
        assert(other.value != 0, 'Division by zero');
        I128 {
            value: self.value / other.value,
            is_negative: self.is_negative != other.is_negative && self.value != 0,
        }
    }
}

// =============================================================================
// Trade Structure
// =============================================================================

/// Represents a single trade execution
#[derive(Copy, Drop, Serde, Default)]
pub struct Trade {
    /// Trade side: 0 = buy, 1 = sell
    pub side: u8,
    /// Quantity in base asset (scaled by 1e18)
    pub quantity: u128,
    /// Price per unit (scaled by 1e18)
    pub price: u128,
    /// Trading fee (scaled by 1e18)
    pub fee: u128,
    /// Unique trade identifier (hash)
    pub trade_id: felt252,
    /// Trader's user ID (hash)
    pub trader_user_id: felt252,
    /// Trading pair symbol (hash)
    pub symbol: felt252,
    /// Order type: 0=market, 1=limit, 2=stop_loss, etc.
    pub order_type: u8,
    /// Unix timestamp of order update
    pub order_updated_at: u64,
    /// Exchange identifier (hash)
    pub exchange: felt252,
}

// =============================================================================
// Position Tracking (FIFO Cost-Basis)
// =============================================================================

/// A single buy lot for FIFO cost-basis tracking
#[derive(Copy, Drop, Serde, Default)]
pub struct BuyLot {
    pub quantity: u128,
    pub price: u128,
}

/// Position state for a single symbol
#[derive(Copy, Drop, Serde, Default)]
pub struct Position {
    /// FIFO queue of buy lots (fixed size array)
    pub queue_0: BuyLot,
    pub queue_1: BuyLot,
    pub queue_2: BuyLot,
    pub queue_3: BuyLot,
    pub queue_4: BuyLot,
    pub queue_5: BuyLot,
    pub queue_6: BuyLot,
    pub queue_7: BuyLot,
    pub queue_8: BuyLot,
    pub queue_9: BuyLot,
    /// Current queue length
    pub queue_length: u32,
    /// Accumulated realized PnL for this symbol
    pub realized_pnl: I128,
}

#[generate_trait]
pub impl PositionImpl of PositionTrait {
    /// Get lot at index
    fn get_lot(self: @Position, index: u32) -> BuyLot {
        match index {
            0 => *self.queue_0,
            1 => *self.queue_1,
            2 => *self.queue_2,
            3 => *self.queue_3,
            4 => *self.queue_4,
            5 => *self.queue_5,
            6 => *self.queue_6,
            7 => *self.queue_7,
            8 => *self.queue_8,
            9 => *self.queue_9,
            _ => Default::default(),
        }
    }

    /// Set lot at index (returns new Position)
    fn set_lot(self: Position, index: u32, lot: BuyLot) -> Position {
        let mut new_pos = self;
        match index {
            0 => { new_pos.queue_0 = lot; },
            1 => { new_pos.queue_1 = lot; },
            2 => { new_pos.queue_2 = lot; },
            3 => { new_pos.queue_3 = lot; },
            4 => { new_pos.queue_4 = lot; },
            5 => { new_pos.queue_5 = lot; },
            6 => { new_pos.queue_6 = lot; },
            7 => { new_pos.queue_7 = lot; },
            8 => { new_pos.queue_8 = lot; },
            9 => { new_pos.queue_9 = lot; },
            _ => {},
        }
        new_pos
    }
}

// =============================================================================
// Symbol PnL Result
// =============================================================================

/// PnL result for a single trading symbol
#[derive(Copy, Drop, Serde, Default)]
pub struct SymbolPnL {
    /// Symbol identifier (hash)
    pub symbol: felt252,
    /// Realized PnL (signed, scaled)
    pub pnl: I128,
    /// Whether this symbol was profitable
    pub is_profitable: bool,
}

// =============================================================================
// Trading Report (Public Output)
// =============================================================================

/// Complete trading performance report
#[derive(Copy, Drop, Serde)]
pub struct TradingReport {
    /// Trader's Starknet address
    pub trader: ContractAddress,
    /// Report period start (Unix timestamp)
    pub timestamp_start: u64,
    /// Report period end (Unix timestamp)
    pub timestamp_end: u64,
    /// Number of trades in the batch
    pub trade_count: u32,
    /// Number of unique symbols traded
    pub symbol_count: u32,
    /// Cryptographic hash of the report
    pub report_hash: felt252,
    /// Commitment to the private trade data
    pub commitment: felt252,
}

// =============================================================================
// Trade Result (Proof Output)
// =============================================================================

/// Output from the ZK verification program
#[derive(Copy, Drop, Serde)]
pub struct TradeResult {
    /// Per-symbol PnL breakdown (up to MAX_TRADES symbols)
    pub symbol_pnl_0: SymbolPnL,
    pub symbol_pnl_1: SymbolPnL,
    pub symbol_pnl_2: SymbolPnL,
    pub symbol_pnl_3: SymbolPnL,
    pub symbol_pnl_4: SymbolPnL,
    pub symbol_pnl_5: SymbolPnL,
    pub symbol_pnl_6: SymbolPnL,
    pub symbol_pnl_7: SymbolPnL,
    pub symbol_pnl_8: SymbolPnL,
    pub symbol_pnl_9: SymbolPnL,
    /// Number of symbols with PnL data
    pub symbol_count: u32,
    /// Total trades processed
    pub trade_count: u32,
    /// Commitment to the trade data
    pub commitment: felt252,
}

#[generate_trait]
pub impl TradeResultImpl of TradeResultTrait {
    /// Get symbol PnL at index
    fn get_symbol_pnl(self: @TradeResult, index: u32) -> SymbolPnL {
        match index {
            0 => *self.symbol_pnl_0,
            1 => *self.symbol_pnl_1,
            2 => *self.symbol_pnl_2,
            3 => *self.symbol_pnl_3,
            4 => *self.symbol_pnl_4,
            5 => *self.symbol_pnl_5,
            6 => *self.symbol_pnl_6,
            7 => *self.symbol_pnl_7,
            8 => *self.symbol_pnl_8,
            9 => *self.symbol_pnl_9,
            _ => Default::default(),
        }
    }

    /// Calculate total PnL across all symbols
    fn total_pnl(self: @TradeResult) -> I128 {
        let mut total = I128Trait::zero();
        let mut i: u32 = 0;
        loop {
            if i >= *self.symbol_count {
                break;
            }
            let symbol_pnl = self.get_symbol_pnl(i);
            total = total.add(symbol_pnl.pnl);
            i += 1;
        };
        total
    }
}

// =============================================================================
// Stored Report (On-Chain)
// =============================================================================

/// On-chain storage structure for verified reports
#[derive(Copy, Drop, Serde, starknet::Store)]
pub struct StoredReport {
    /// Trader's address
    pub trader: ContractAddress,
    /// Report period start
    pub timestamp_start: u64,
    /// Report period end
    pub timestamp_end: u64,
    /// Number of trades
    pub trade_count: u32,
    /// Total PnL (absolute value)
    pub total_pnl_value: u128,
    /// Whether total PnL is negative
    pub total_pnl_negative: bool,
    /// Report hash
    pub report_hash: felt252,
    /// Commitment
    pub commitment: felt252,
    /// Block number when verified
    pub verified_at_block: u64,
    /// Whether the report has been verified
    pub is_verified: bool,
}
