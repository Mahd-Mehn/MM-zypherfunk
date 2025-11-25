/**
 * Proof Generation Service
 * 
 * Handles the off-chain computation of trading performance
 * and preparation of data for Starknet submission.
 */

import { 
  processRawTrade, 
  createTradeCommitment, 
  createReportHash,
  stringToFelt,
  type RawTrade,
  type ProcessedTrade,
  type SymbolPnL
} from '../utils/trade-processor.ts';
import { logger } from '../utils/logger.ts';

// Scale factor (1e18)
const SCALE_FACTOR = BigInt('1000000000000000000');

/**
 * Position for FIFO cost-basis tracking
 */
interface Position {
  queue: Array<{ quantity: bigint; price: bigint }>;
  realizedPnl: { value: bigint; isNegative: boolean };
}

/**
 * Proof generation request
 */
export interface ProofRequest {
  trades: RawTrade[];
  traderId: string;
  timestampStart: number;
  timestampEnd: number;
}

/**
 * Proof generation result
 */
export interface ProofResult {
  commitment: bigint;
  reportHash: bigint;
  symbolPnls: SymbolPnL[];
  totalPnl: { value: bigint; isNegative: boolean };
  tradeCount: number;
  symbolCount: number;
  processedTrades: ProcessedTrade[];
}

/**
 * Calculate PnL for a single trade using FIFO
 */
function calculateTradePnl(
  position: Position,
  trade: ProcessedTrade
): { value: bigint; isNegative: boolean } {
  const isBuy = trade.side === 0;

  if (isBuy) {
    // Add to queue
    position.queue.push({ quantity: trade.quantity, price: trade.price });
    return { value: 0n, isNegative: false };
  }

  // Sell: match against FIFO queue
  let remainingSellQty = trade.quantity;
  let realizedPnl = { value: 0n, isNegative: false };

  while (remainingSellQty > 0n && position.queue.length > 0) {
    const lot = position.queue[0];

    if (lot.quantity === 0n) {
      position.queue.shift();
      continue;
    }

    const sellFromLot = lot.quantity < remainingSellQty ? lot.quantity : remainingSellQty;
    
    // Calculate PnL
    let pnlMagnitude: bigint;
    let isProfit: boolean;

    if (trade.price >= lot.price) {
      pnlMagnitude = (trade.price - lot.price) * sellFromLot / SCALE_FACTOR;
      isProfit = true;
    } else {
      pnlMagnitude = (lot.price - trade.price) * sellFromLot / SCALE_FACTOR;
      isProfit = false;
    }

    // Add to realized PnL
    if (realizedPnl.isNegative === !isProfit) {
      realizedPnl.value += pnlMagnitude;
    } else if (realizedPnl.value >= pnlMagnitude) {
      realizedPnl.value -= pnlMagnitude;
    } else {
      realizedPnl.value = pnlMagnitude - realizedPnl.value;
      realizedPnl.isNegative = !isProfit;
    }

    lot.quantity -= sellFromLot;
    remainingSellQty -= sellFromLot;

    if (lot.quantity === 0n) {
      position.queue.shift();
    }
  }

  // Deduct fee
  if (trade.fee > 0n) {
    if (realizedPnl.isNegative) {
      realizedPnl.value += trade.fee;
    } else if (realizedPnl.value >= trade.fee) {
      realizedPnl.value -= trade.fee;
    } else {
      realizedPnl.value = trade.fee - realizedPnl.value;
      realizedPnl.isNegative = true;
    }
  }

  return realizedPnl;
}

/**
 * Add two signed values
 */
function addSigned(
  a: { value: bigint; isNegative: boolean },
  b: { value: bigint; isNegative: boolean }
): { value: bigint; isNegative: boolean } {
  if (a.isNegative === b.isNegative) {
    return { value: a.value + b.value, isNegative: a.isNegative };
  }
  if (a.value >= b.value) {
    return { value: a.value - b.value, isNegative: a.isNegative };
  }
  return { value: b.value - a.value, isNegative: b.isNegative };
}

/**
 * Generate proof data for a batch of trades
 */
export async function generateProof(request: ProofRequest): Promise<ProofResult> {
  logger.info({ tradeCount: request.trades.length }, 'Generating proof');

  // Process raw trades
  const processedTrades = request.trades.map(processRawTrade);
  const tradeCount = processedTrades.length;

  // Track positions per symbol
  const symbolPositions = new Map<bigint, Position>();

  // Process each trade
  for (const trade of processedTrades) {
    let position = symbolPositions.get(trade.symbol);
    if (!position) {
      position = {
        queue: [],
        realizedPnl: { value: 0n, isNegative: false },
      };
      symbolPositions.set(trade.symbol, position);
    }

    const tradePnl = calculateTradePnl(position, trade);
    position.realizedPnl = addSigned(position.realizedPnl, tradePnl);
  }

  // Build symbol PnL results
  const symbolPnls: SymbolPnL[] = [];
  let totalPnl = { value: 0n, isNegative: false };

  for (const [symbol, position] of symbolPositions) {
    symbolPnls.push({
      symbol,
      pnl_value: position.realizedPnl.value,
      pnl_negative: position.realizedPnl.isNegative,
      is_profitable: !position.realizedPnl.isNegative && position.realizedPnl.value > 0n,
    });
    totalPnl = addSigned(totalPnl, position.realizedPnl);
  }

  // Create commitment
  const traderFelt = stringToFelt(request.traderId);
  const commitment = createTradeCommitment(
    processedTrades,
    tradeCount,
    traderFelt,
    BigInt(request.timestampStart),
    BigInt(request.timestampEnd)
  );

  // Create report hash
  const reportHash = createReportHash(
    traderFelt,
    BigInt(request.timestampStart),
    BigInt(request.timestampEnd),
    symbolPnls,
    symbolPnls.length,
    tradeCount
  );

  logger.info({
    commitment: commitment.toString(16),
    reportHash: reportHash.toString(16),
    symbolCount: symbolPnls.length,
    totalPnl: `${totalPnl.isNegative ? '-' : ''}${totalPnl.value.toString()}`,
  }, 'Proof generated');

  return {
    commitment,
    reportHash,
    symbolPnls,
    totalPnl,
    tradeCount,
    symbolCount: symbolPnls.length,
    processedTrades,
  };
}
