/**
 * Trade Processing Utilities for Starknet
 * 
 * Handles conversion of trade data to Cairo-compatible format,
 * including Poseidon hashing and field element scaling.
 */

import { poseidon1 as poseidon } from 'poseidon-lite';

// Scale factor for circuit (1e18)
const SCALE_FACTOR = BigInt('1000000000000000000');

// Field prime for Starknet (Cairo uses a different field than BN254)
const STARK_PRIME = BigInt('0x800000000000011000000000000000000000000000000000000000000000001');

/**
 * Order type mappings (matching Cairo enum)
 */
const ORDER_TYPE_MAP: Record<string, number> = {
  market: 0,
  limit: 1,
  stop_loss: 2,
  stop_loss_limit: 3,
  take_profit: 4,
  take_profit_limit: 5,
};

/**
 * Side mappings
 */
const SIDE_MAP: Record<string, number> = {
  buy: 0,
  sell: 1,
};

/**
 * Convert a string to a felt252 using Poseidon hash
 */
export function stringToFelt(value: string): bigint {
  const bytes = Buffer.from(value, 'utf8');
  // Convert to bigint, ensuring it fits in felt252
  const asBigInt = BigInt('0x' + bytes.toString('hex')) % STARK_PRIME;
  return asBigInt;
}

/**
 * Hash a string using Poseidon (Starknet's native hash)
 */
export function poseidonHash(...inputs: bigint[]): bigint {
  return poseidon(inputs);
}

/**
 * Scale a decimal number string to circuit format (multiply by 1e18)
 */
export function scaleDecimal(value: string): bigint {
  const parts = value.split('.');
  const integerPart = parts[0] || '0';
  const decimalPart = parts[1] || '';

  // Pad or truncate to 18 decimal places
  const paddedDecimal = decimalPart.padEnd(18, '0').substring(0, 18);

  // Combine and convert to BigInt
  return BigInt(integerPart + paddedDecimal);
}

/**
 * Get numeric value for order type
 */
export function getOrderTypeValue(orderType: string): number {
  const normalized = orderType.toLowerCase().replace(/[_-]/g, '_');
  return ORDER_TYPE_MAP[normalized] ?? 0;
}

/**
 * Get numeric value for side
 */
export function getSideValue(side: string): number {
  return SIDE_MAP[side.toLowerCase()] ?? 0;
}

/**
 * Trade input from the backend/Sentinel
 */
export interface RawTrade {
  trade_id: string;
  trader_user_id: string;
  symbol: string;
  exchange: string;
  side: string;
  order_type: string;
  quantity: string;
  price: string;
  fee: string;
  timestamp: number;
}

/**
 * Processed trade ready for Cairo circuit
 */
export interface ProcessedTrade {
  side: number;
  quantity: bigint;
  price: bigint;
  fee: bigint;
  trade_id: bigint;
  trader_user_id: bigint;
  symbol: bigint;
  order_type: number;
  order_updated_at: bigint;
  exchange: bigint;
}

/**
 * Process a raw trade from the backend into Cairo format
 */
export function processRawTrade(raw: RawTrade): ProcessedTrade {
  return {
    side: getSideValue(raw.side),
    quantity: scaleDecimal(raw.quantity),
    price: scaleDecimal(raw.price),
    fee: scaleDecimal(raw.fee),
    trade_id: stringToFelt(raw.trade_id),
    trader_user_id: stringToFelt(raw.trader_user_id),
    symbol: stringToFelt(raw.symbol),
    order_type: getOrderTypeValue(raw.order_type),
    order_updated_at: BigInt(raw.timestamp),
    exchange: stringToFelt(raw.exchange),
  };
}

/**
 * Create a trade commitment (matches Cairo implementation)
 */
export function createTradeCommitment(
  trades: ProcessedTrade[],
  tradeCount: number,
  trader: bigint,
  timestampStart: bigint,
  timestampEnd: bigint
): bigint {
  // Hash context
  let hash = poseidonHash(trader, timestampStart, timestampEnd, BigInt(tradeCount));

  // Hash each trade
  for (let i = 0; i < tradeCount; i++) {
    const trade = trades[i];
    const tradeHash = poseidonHash(
      trade.trade_id,
      trade.trader_user_id,
      trade.symbol,
      BigInt(trade.side),
      BigInt(trade.order_type),
      trade.quantity,
      trade.price,
      trade.fee,
      trade.order_updated_at,
      trade.exchange
    );
    hash = poseidonHash(hash, tradeHash);
  }

  return hash;
}

/**
 * Symbol PnL result
 */
export interface SymbolPnL {
  symbol: bigint;
  pnl_value: bigint;
  pnl_negative: boolean;
  is_profitable: boolean;
}

/**
 * Create a report hash (matches Cairo implementation)
 */
export function createReportHash(
  trader: bigint,
  timestampStart: bigint,
  timestampEnd: bigint,
  symbolPnls: SymbolPnL[],
  symbolCount: number,
  tradeCount: number
): bigint {
  // Hash basic info
  let hash = poseidonHash(
    trader,
    timestampStart,
    timestampEnd,
    BigInt(tradeCount),
    BigInt(symbolCount)
  );

  // Hash each symbol's PnL
  for (let i = 0; i < symbolCount; i++) {
    const pnl = symbolPnls[i];
    const symbolHash = poseidonHash(
      pnl.symbol,
      pnl.pnl_value,
      pnl.pnl_negative ? 1n : 0n,
      pnl.is_profitable ? 1n : 0n
    );
    hash = poseidonHash(hash, symbolHash);
  }

  return hash;
}
