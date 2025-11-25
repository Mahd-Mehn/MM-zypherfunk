# Obscura Verification - Starknet ZK-STARK Trading Proofs

Zero-Knowledge trading performance verification system using **Cairo** and **Starknet's native STARK proofs**.

## Overview

This module enables traders to cryptographically prove their trading performance (PnL, win rate, trade count) without revealing individual trade details. Unlike the legacy `alchemist` (Noir/SNARK-based), this implementation leverages Starknet's native STARK proof system for:

- **No trusted setup** (unlike SNARKs)
- **Post-quantum security**
- **Native L2 integration** with Starknet
- **Lower verification costs** on-chain

## Architecture

```
verification/
├── cairo/                    # Cairo 1.0 contracts & programs
│   ├── src/
│   │   ├── lib.cairo         # Module root
│   │   ├── types.cairo       # Data structures
│   │   ├── verifier.cairo    # On-chain verifier contract
│   │   └── prover.cairo      # Off-chain proof generation logic
│   ├── tests/
│   │   └── test_verifier.cairo
│   └── Scarb.toml            # Cairo package manifest
│
├── service/                  # TypeScript orchestration service
│   ├── src/
│   │   ├── index.ts
│   │   ├── prover.ts         # Proof generation client
│   │   ├── submitter.ts      # Starknet transaction submission
│   │   └── utils/
│   ├── package.json
│   └── tsconfig.json
│
└── README.md
```

## Key Concepts

### 1. Trading Performance Report
A trader submits a batch of trades (private) and claims a performance summary (public):
- **Private Inputs**: Individual trades (side, price, quantity, symbol, fee)
- **Public Inputs**: Trader address, time range, report hash, claimed PnL

### 2. STARK Proof Generation
The Cairo program:
1. Validates trade data integrity
2. Computes PnL using FIFO cost-basis accounting
3. Generates a commitment to the trade batch
4. Outputs a verifiable hash matching the claimed performance

### 3. On-Chain Verification
The Starknet contract:
1. Receives the proof and public inputs
2. Verifies the STARK proof (native to Starknet)
3. Stores verified performance reports
4. Emits events for off-chain indexing

## Quick Start

### Prerequisites
- [Scarb](https://docs.swmansion.com/scarb/) (Cairo package manager)
- [Starkli](https://book.starkli.rs/) (Starknet CLI)
- Node.js 18+

### 1. Build Cairo Contracts

```bash
cd cairo
scarb build
```

### 2. Run Tests

```bash
scarb test
```

### 3. Deploy to Starknet (Testnet)

```bash
# Set up account
starkli account fetch <YOUR_ADDRESS> --output account.json

# Declare contract class
starkli declare target/dev/obscura_verifier.contract_class.json

# Deploy contract
starkli deploy <CLASS_HASH> --account account.json
```

### 4. Start Service

```bash
cd service
pnpm install
pnpm dev
```

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Trading Data   │────▶│  Cairo Prover   │────▶│ STARK Proof +   │
│  (from Sentinel)│     │  (off-chain)    │     │ Public Outputs  │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Verified       │◀────│ Starknet        │◀────│ Submit Tx       │
│  Report Event   │     │ Verifier        │     │ (service)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Why Starknet/STARK over Noir/SNARK?

| Feature | SNARK (Noir/Barretenberg) | STARK (Cairo/Starknet) |
|---------|---------------------------|------------------------|
| Trusted Setup | Required | **Not Required** |
| Proof Size | ~300 bytes | ~50-100 KB |
| Verification Cost | Lower gas (EVM) | **Native on Starknet** |
| Post-Quantum | ❌ | ✅ |
| Ecosystem | EVM chains | **Starknet L2** |

For Obscura V2, we chose STARK because:
1. Native integration with Starknet's growing DeFi ecosystem
2. No ceremony/trusted setup risk
3. Future-proof cryptography

## Integration with Backend

The `verification/service` exposes REST endpoints consumed by `backend/modules/analytics`:

```
POST /api/v1/proof/generate   # Generate proof from trade batch
POST /api/v1/proof/submit     # Submit proof to Starknet
GET  /api/v1/report/:id       # Fetch verified report status
```

## License

MIT
