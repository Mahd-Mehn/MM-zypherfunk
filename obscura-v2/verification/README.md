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

## Deployed Contract (Starknet Sepolia)

| Property | Value |
|----------|-------|
| **Contract Address** | `0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f` |
| **Class Hash** | `0x191aad8debf4ed4e2b25a8864c4ad6f22aab004e2e4164349ea4dcc488c3f37` |
| **Network** | Starknet Sepolia Testnet |
| **Owner** | `0x0442b94543f5f4a79161c0c661741407f931492e01a067fdd7337d2f135cd29d` |

View on explorer: [Starkscan](https://sepolia.starkscan.co/contract/0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f)

## Quick Start

### Prerequisites
- [Scarb 2.8.4](https://docs.swmansion.com/scarb/) (Cairo package manager)
- [Starknet Foundry (sncast)](https://foundry-rs.github.io/starknet-foundry/) (Deployment tool)
- Node.js 18+ / Bun

### 1. Build Cairo Contracts

```bash
cd cairo
scarb build
```

### 2. Run Tests

```bash
scarb test
```

### 3. Start Service

```bash
cd service
bun install
bun dev
```

---

## Full Setup Guide (macOS)

This section documents the complete setup process for the Cairo development environment and contract deployment.

### Step 1: Install Scarb (Cairo Package Manager)

```bash
# Install specific version (2.8.4 recommended for Starknet Sepolia compatibility)
curl --proto '=https' --tlsv1.2 -sSf https://docs.swmansion.com/scarb/install.sh | sh -s -- -v 2.8.4

# Verify installation
scarb --version
# Expected: scarb 2.8.4

# Check Cairo version
scarb cairo-run --version
# Expected: cairo-run 2.8.4
```

> **Note**: Version compatibility is critical. Starknet Sepolia expects specific CASM compiler versions. Using Scarb 2.8.4 with `starknet = "2.8.4"` in Scarb.toml ensures compatibility.

### Step 2: Install Starknet Foundry (sncast)

We recommend `sncast` over `starkli` for deployment due to better RPC compatibility:

```bash
# Install Starknet Foundry
curl -L https://raw.githubusercontent.com/foundry-rs/starknet-foundry/master/scripts/install.sh | sh

# Run the installer
snfoundryup

# Verify installation
sncast --version
# Expected: sncast 0.53.0 or later
```

### Step 3: Create Starknet Wallet & Account

```bash
# Create wallet directory
mkdir -p ~/.starkli-wallets/deployer

# Generate keystore (saves encrypted private key)
starkli signer keystore new ~/.starkli-wallets/deployer/keystore.json
# Enter a password when prompted - SAVE THIS PASSWORD!
# This outputs your public key

# Fund your wallet on Sepolia
# 1. Go to https://starknet-faucet.vercel.app/
# 2. Use the public key address to receive test ETH

# Initialize account (Argent X or Braavos style)
starkli account oz init \
  --keystore ~/.starkli-wallets/deployer/keystore.json \
  ~/.starkli-wallets/deployer/account.json

# Deploy the account contract (requires funded wallet)
starkli account deploy \
  --keystore ~/.starkli-wallets/deployer/keystore.json \
  ~/.starkli-wallets/deployer/account.json
```

### Step 4: Configure Starknet Foundry

Create `snfoundry.toml` in your Cairo project root:

```toml
[sncast.deployer]
account = "deployer"
accounts-file = "/Users/<YOUR_USER>/.starkli-wallets/deployer/account.json"
keystore = "/Users/<YOUR_USER>/.starkli-wallets/deployer/keystore.json"
```

### Step 5: Build the Contract

```bash
cd obscura-v2/verification/cairo

# Build Sierra and CASM artifacts
scarb build

# Verify build outputs
ls target/dev/
# Should show: obscura_ObscuraVerifier.contract_class.json (Sierra)
#              obscura_ObscuraVerifier.compiled_contract_class.json (CASM)
```

### Step 6: Declare the Contract Class

```bash
# Declare using sncast (recommended)
sncast declare \
  --contract-name ObscuraVerifier \
  --network sepolia

# This outputs:
# - class_hash: The unique identifier for your contract class
# - transaction_hash: The declaration transaction

# Example output:
# class_hash: 0x191aad8debf4ed4e2b25a8864c4ad6f22aab004e2e4164349ea4dcc488c3f37
```

### Step 7: Deploy the Contract Instance

```bash
# Deploy with constructor arguments
# The ObscuraVerifier constructor takes an owner address (felt252)
sncast --account deployer deploy \
  --class-hash 0x191aad8debf4ed4e2b25a8864c4ad6f22aab004e2e4164349ea4dcc488c3f37 \
  --arguments '0x0442b94543f5f4a79161c0c661741407f931492e01a067fdd7337d2f135cd29d' \
  --network sepolia

# Example output:
# contract_address: 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f
# transaction_hash: 0x07bf28165bf8fe9e38b6f77abdbb87d3914249999a3cfc49940584c1f157b605
```

### Step 8: Verify Deployment

```bash
# Call a read function to verify the contract is working
sncast call \
  --contract-address 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f \
  --function get_report_count \
  --network sepolia

# Expected output: response: [0x0] (no reports submitted yet)
```

---

## Interacting with the Contract

### Read Functions (Free)

```bash
# Get total report count
sncast call \
  --contract-address 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f \
  --function get_report_count \
  --network sepolia

# Get trader stats
sncast call \
  --contract-address 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f \
  --function get_trader_stats \
  --calldata 0x<TRADER_ADDRESS> \
  --network sepolia
```

### Write Functions (Requires Gas)

```bash
# Register as a trader
sncast --account deployer invoke \
  --contract-address 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f \
  --function register_trader \
  --network sepolia

# Submit a verified report (typically called by the orchestration service)
sncast --account deployer invoke \
  --contract-address 0x0100dc8bce9ff7f15f481a9350e90744c31b4112613efa06adabf0341e08993f \
  --function submit_report \
  --calldata <report_hash> <trader_address> <timestamp_start> <timestamp_end> <total_pnl_mag> <total_pnl_sign> <trade_count> <win_count> <total_volume_mag> <total_volume_sign> \
  --network sepolia
```

---

## Troubleshooting

### CASM Compiler Version Mismatch

If you see errors like `contract class hash mismatch` or `compiled_class_hash did not match`:

1. Check Scarb version matches `starknet` version in `Scarb.toml`
2. Use `--network sepolia` flag instead of explicit RPC URLs
3. Rebuild with `scarb clean && scarb build`

### RPC Version Incompatibility

Some RPC providers (like Alchemy) may use older spec versions. Solutions:
- Use `--network sepolia` flag which uses sncast's built-in RPC
- Or use a compatible RPC like `https://starknet-sepolia.public.blastapi.io`

### Account Not Found

If sncast can't find your account:
1. Verify paths in `snfoundry.toml` are absolute
2. Check account file exists: `cat ~/.starkli-wallets/deployer/account.json`
3. Ensure account is deployed on Sepolia (not just initialized)

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
