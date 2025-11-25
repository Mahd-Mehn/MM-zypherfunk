use super::types::{Trade, I128, I128Trait, SymbolPnL};
use super::prover::{verify_trades, create_report_hash, create_trade_commitment};

#[test]
fn test_i128_addition_same_sign() {
    let a = I128Trait::new(100, false);
    let b = I128Trait::new(50, false);
    let result = a.add(b);
    assert(result.value == 150, 'Wrong sum value');
    assert(!result.is_negative, 'Should be positive');
}

#[test]
fn test_i128_addition_different_sign() {
    let a = I128Trait::new(100, false);
    let b = I128Trait::new(30, true);
    let result = a.add(b);
    assert(result.value == 70, 'Wrong difference');
    assert(!result.is_negative, 'Should be positive');
}

#[test]
fn test_i128_subtraction() {
    let a = I128Trait::new(50, false);
    let b = I128Trait::new(100, false);
    let result = a.sub(b);
    assert(result.value == 50, 'Wrong value');
    assert(result.is_negative, 'Should be negative');
}

#[test]
fn test_i128_multiplication() {
    let a = I128Trait::new(10, false);
    let b = I128Trait::new(5, true);
    let result = a.mul(b);
    assert(result.value == 50, 'Wrong product');
    assert(result.is_negative, 'Should be negative');
}

#[test]
fn test_trade_commitment_consistency() {
    // Create sample trades
    let trade1 = Trade {
        side: 0, // buy
        quantity: 1000000000000000000, // 1.0 scaled
        price: 50000000000000000000000, // 50000.0 scaled
        fee: 100000000000000000, // 0.1 scaled
        trade_id: 'trade1',
        trader_user_id: 'trader1',
        symbol: 'BTCUSD',
        order_type: 0,
        order_updated_at: 1700000000,
        exchange: 'binance',
    };

    let trades: Array<Trade> = array![trade1];
    
    // Generate commitment
    let commitment1 = create_trade_commitment(
        trades.span(),
        1,
        'trader1',
        1699900000,
        1700100000,
    );

    // Same inputs should produce same commitment
    let commitment2 = create_trade_commitment(
        trades.span(),
        1,
        'trader1',
        1699900000,
        1700100000,
    );

    assert(commitment1 == commitment2, 'Commitments should match');
}

#[test]
fn test_report_hash_consistency() {
    let symbol_pnl = SymbolPnL {
        symbol: 'BTCUSD',
        pnl: I128Trait::new(1000000000000000000, false), // 1.0 profit
        is_profitable: true,
    };

    let pnls: Array<SymbolPnL> = array![symbol_pnl];

    let hash1 = create_report_hash(
        'trader1',
        1699900000,
        1700100000,
        pnls.span(),
        1,
        5,
    );

    let hash2 = create_report_hash(
        'trader1',
        1699900000,
        1700100000,
        pnls.span(),
        1,
        5,
    );

    assert(hash1 == hash2, 'Hashes should match');
}

#[test]
fn test_i128_zero() {
    let zero = I128Trait::zero();
    assert(zero.is_zero(), 'Should be zero');
    assert(zero.is_positive(), 'Zero is positive');
}
