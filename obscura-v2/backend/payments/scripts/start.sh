#!/bin/bash
# =============================================================================
# Obscura V2 - Zcash Payments Startup Script
# =============================================================================
# This script initializes the zecwallet-cli and starts the payments service
# =============================================================================

set -e

echo "=========================================="
echo "  Obscura Payments - Startup Script"
echo "=========================================="

# Configuration
LIGHTWALLETD_URL="${LIGHTWALLETD_URL:-https://testnet.lightwalletd.com:9067}"
WALLET_DATA_DIR="${WALLET_DATA_DIR:-/app/data/wallet}"
ZCASH_NETWORK="${ZCASH_NETWORK:-testnet}"

# Parse lightwalletd URL
LIGHTWALLETD_HOST=$(echo $LIGHTWALLETD_URL | sed -E 's|https?://||' | cut -d: -f1)
LIGHTWALLETD_PORT=$(echo $LIGHTWALLETD_URL | sed -E 's|https?://||' | cut -d: -f2)

echo "Configuration:"
echo "  Network: $ZCASH_NETWORK"
echo "  Lightwalletd: $LIGHTWALLETD_HOST:$LIGHTWALLETD_PORT"
echo "  Wallet Dir: $WALLET_DATA_DIR"
echo ""

# Create wallet directory if it doesn't exist
mkdir -p "$WALLET_DATA_DIR"

# Check if zecwallet-cli is available
if ! command -v zecwallet-cli &> /dev/null; then
    echo "Warning: zecwallet-cli not found, running in mock mode"
else
    echo "✓ zecwallet-cli found at $(which zecwallet-cli)"
    
    # Test lightwalletd connection
    echo "Testing lightwalletd connection..."
    if grpcurl -plaintext "$LIGHTWALLETD_HOST:$LIGHTWALLETD_PORT" cash.z.wallet.sdk.rpc.CompactTxStreamer/GetLightdInfo 2>/dev/null; then
        echo "✓ Lightwalletd connection successful"
    else
        echo "Warning: Could not connect to lightwalletd at $LIGHTWALLETD_HOST:$LIGHTWALLETD_PORT"
        echo "  The service will start but may operate in limited mode"
    fi
fi

echo ""
echo "Starting Payments Service..."
echo "=========================================="

# Start the FastAPI service
exec uvicorn payments.main:app --host 0.0.0.0 --port 8000
