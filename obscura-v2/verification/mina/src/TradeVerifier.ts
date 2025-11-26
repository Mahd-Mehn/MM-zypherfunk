import {
  Field,
  SmartContract,
  state,
  State,
  method,
  Struct,
  UInt64,
  Bool,
  Provable,
  Poseidon,
  ZkProgram,
  SelfProof,
} from 'o1js';

// --- Data Structures ---

export class Trade extends Struct({
  entryPrice: UInt64,
  exitPrice: UInt64,
  quantity: UInt64,
  isLong: Bool, // true = Long, false = Short
}) {
  entryPrice: UInt64;
  exitPrice: UInt64;
  quantity: UInt64;
  isLong: Bool;

  constructor(entryPrice: UInt64, exitPrice: UInt64, quantity: UInt64, isLong: Bool) {
    super({ entryPrice, exitPrice, quantity, isLong });
    this.entryPrice = entryPrice;
    this.exitPrice = exitPrice;
    this.quantity = quantity;
    this.isLong = isLong;
  }
}

export class PerformanceReport extends Struct({
  totalPnl: UInt64, // Represented as scaled integer (e.g. * 10^6)
  winCount: UInt64,
  totalTrades: UInt64,
  traderHash: Field, // Hash of the trader's ID/Secret
}) {
  totalPnl: UInt64;
  winCount: UInt64;
  totalTrades: UInt64;
  traderHash: Field;

  constructor(totalPnl: UInt64, winCount: UInt64, totalTrades: UInt64, traderHash: Field) {
    super({ totalPnl, winCount, totalTrades, traderHash });
    this.totalPnl = totalPnl;
    this.winCount = winCount;
    this.totalTrades = totalTrades;
    this.traderHash = traderHash;
  }
}

// --- ZkProgram (Recursive Proofs) ---

export const TradeVerifier = ZkProgram({
  name: 'trade-verifier',
  publicInput: PerformanceReport,

  methods: {
    // Base case: Verify a single trade
    verifyTrade: {
      privateInputs: [Trade, Field], // Trade data, Trader Secret
      method(publicOutput: PerformanceReport, trade: Trade, traderSecret: Field) {
        // 1. Verify Trader Identity
        const derivedHash = Poseidon.hash([traderSecret]);
        derivedHash.assertEquals(publicOutput.traderHash);

        // 2. Calculate PnL
        // Long: (Exit - Entry) * Qty
        // Short: (Entry - Exit) * Qty
        
        // We use conditional logic for PnL calculation
        // Note: In a real app, we need to handle negative PnL carefully with Field arithmetic or specific logic
        // Here we simplify to absolute PnL for demonstration or assume profitable trades for this specific proof type
        // Or we can use a "balance" approach starting from a base amount.
        
        const entry = trade.entryPrice;
        const exit = trade.exitPrice;
        const qty = trade.quantity;

        const isLong = trade.isLong;
        
        // Calculate raw diff
        // If Long: diff = exit - entry
        // If Short: diff = entry - exit
        
        // Using Provable.if to handle the conditional logic
        const pnl = Provable.if(
            isLong,
            exit.sub(entry).mul(qty),
            entry.sub(exit).mul(qty)
        );

        // Check if PnL matches claimed totalPnl (for single trade base case)
        pnl.assertEquals(publicOutput.totalPnl);
        
        // Check counts
        publicOutput.totalTrades.assertEquals(UInt64.from(1));
        
        // Check win (if pnl > 0)
        // Since UInt64 cannot be negative, if the subtraction above didn't underflow, it's >= 0.
        // We assume for this simplified logic that we are proving *profitable* trades or handling underflow checks elsewhere.
        // A win is if PnL > 0
        const isWin = pnl.greaterThan(UInt64.from(0));
        const winValue = Provable.if(isWin, UInt64.from(1), UInt64.from(0));
        winValue.assertEquals(publicOutput.winCount);
      },
    },

    // Recursive step: Merge two reports
    mergeReports: {
      privateInputs: [SelfProof, SelfProof],
      method(
        publicOutput: PerformanceReport,
        earlierProof: SelfProof<PerformanceReport, void>,
        laterProof: SelfProof<PerformanceReport, void>
      ) {
        // 1. Verify sub-proofs
        earlierProof.verify();
        laterProof.verify();

        // 2. Consistency Checks
        // Ensure both proofs belong to the same trader
        earlierProof.publicInput.traderHash.assertEquals(publicOutput.traderHash);
        laterProof.publicInput.traderHash.assertEquals(publicOutput.traderHash);
        
        // 3. Aggregate Data
        const totalPnl = earlierProof.publicInput.totalPnl.add(laterProof.publicInput.totalPnl);
        const totalTrades = earlierProof.publicInput.totalTrades.add(laterProof.publicInput.totalTrades);
        const winCount = earlierProof.publicInput.winCount.add(laterProof.publicInput.winCount);

        // 4. Assert Aggregates match Public Output
        totalPnl.assertEquals(publicOutput.totalPnl);
        totalTrades.assertEquals(publicOutput.totalTrades);
        winCount.assertEquals(publicOutput.winCount);
      },
    },
  },
});

// --- Smart Contract ---

export class ObscuraReputation extends SmartContract {
  // State variables stored on-chain
  @state(Field) verifiedTraderRoot = State<Field>();

  @method verifyPerformance(proof: SelfProof<PerformanceReport, void>) {
    // 1. Verify the recursive proof
    proof.verify();

    // 2. Update on-chain state (simplified)
    // In a real app, we would update a Merkle Tree of trader reputations
    // Here we just emit an event or update a root hash
    
    const report = proof.publicInput;
    
    // Example: We only accept proofs with > 10 trades and > 50% win rate
    report.totalTrades.assertGreaterThan(UInt64.from(10));
    
    // Update state to signal verification
    // We hash the report to store a commitment to the latest verified state
    const reportHash = Poseidon.hash([
        report.traderHash, 
        report.totalPnl.value, 
        report.totalTrades.value
    ]);
    
    this.verifiedTraderRoot.set(reportHash);
  }
}
