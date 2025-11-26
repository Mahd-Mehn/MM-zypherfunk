#!/bin/bash

# Ztarknet Deployment Script
# Deploys Obscura Verification Contracts to Ztarknet Regtest

RPC_URL="https://rpc.regtest.ztarknet.cash"
ACCOUNT_FILE="~/.starkli-wallets/deployer_account.json"
KEYSTORE_FILE="~/.starkli-wallets/deployer.json"

echo "🚀 Deploying to Ztarknet ($RPC_URL)..."

# 1. Check for Starkli
if ! command -v starkli &> /dev/null; then
    echo "❌ Starkli not found. Please install it first."
    exit 1
fi

# 2. Build Contracts
echo "🔨 Building Cairo contracts..."
cd verification/cairo
scarb build

# 3. Declare Contract
echo "📜 Declaring Verifier Contract..."
CLASS_HASH=$(starkli declare target/dev/obscura_verification_Verifier.contract_class.json \
    --rpc $RPC_URL \
    --account $ACCOUNT_FILE \
    --keystore $KEYSTORE_FILE \
    --watch)

echo "✅ Class Hash: $CLASS_HASH"

# 4. Deploy Contract
echo "🚀 Deploying Contract Instance..."
CONTRACT_ADDRESS=$(starkli deploy $CLASS_HASH \
    --rpc $RPC_URL \
    --account $ACCOUNT_FILE \
    --keystore $KEYSTORE_FILE \
    --watch)

echo "🎉 Deployment Complete!"
echo "Contract Address: $CONTRACT_ADDRESS"

# 5. Save Address
echo $CONTRACT_ADDRESS > ../deployed_address.txt
