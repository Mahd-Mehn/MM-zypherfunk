# Ztarknet Integration Guide

## Overview
Ztarknet is a validity rollup (ZK-Rollup) on top of Zcash, leveraging the Starknet stack (Cairo, Madara, STARKs). This integration allows Obscura to verify trading performance using ZK-STARKs while settling proofs on the Zcash network, maintaining the privacy-first ethos of the platform.

## Architecture
- **L2 (Execution)**: Madara Sequencer (running Cairo VM).
- **L1 (Settlement)**: Zcash (via custom validity proof verification logic).
- **DA (Data Availability)**: Zcash Shielded Pool (or specific DA layer).

## Deployment Configuration

To deploy the Obscura Verification contracts to a Ztarknet instance:

### 1. Prerequisites
- `scarb` (Cairo package manager)
- `starkli` (Starknet CLI)
- Ztarknet RPC Endpoint: `https://rpc.regtest.ztarknet.cash`
- Chain ID: `ZFuture`

### 2. Build Contracts
```bash
cd verification/cairo
scarb build
```

### 3. Account Setup
Generate a keystore for the Ztarknet sequencer:
```bash
starkli signer keystore from-key ~/.starkli-wallets/deployer.json
starkli account oz init ~/.starkli-wallets/deployer_account.json --rpc http://localhost:9944
starkli account deploy ~/.starkli-wallets/deployer_account.json --rpc http://localhost:9944
```

### 4. Deploy Verifier
```bash
starkli declare target/dev/obscura_verification_Verifier.contract_class.json --rpc http://localhost:9944
starkli deploy <CLASS_HASH> --rpc http://localhost:9944
```

## Compatibility Notes
- **Cairo Version**: The contracts are written in Cairo 1.0, which is fully compatible with the Madara sequencer used by Ztarknet.
- **Proof Submission**: The `submitter.ts` service needs to be configured with the Ztarknet RPC URL instead of the Starknet Mainnet/Sepolia URL.

## Future Work
- **Native ZEC Interop**: Allow paying for verification gas fees directly in ZEC.
- **L3 Privacy**: Explore deploying a private app-chain on top of Ztarknet for even greater trade privacy.
