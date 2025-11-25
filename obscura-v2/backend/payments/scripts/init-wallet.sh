#!/bin/bash
# =============================================================================
# Obscura V2 - Initialize Zecwallet CLI
# =============================================================================
# Run this script to create a new wallet or restore from seed
# =============================================================================

set -e

WALLET_DATA_DIR="${WALLET_DATA_DIR:-/app/data/wallet}"
LIGHTWALLETD_URL="${LIGHTWALLETD_URL:-https://testnet.lightwalletd.com:9067}"
ZECWALLET_CLI="${ZECWALLET_CLI_PATH:-/usr/local/bin/zecwallet-cli}"

echo "=========================================="
echo "  Zecwallet CLI Initialization"
echo "=========================================="
echo ""
echo "Lightwalletd: $LIGHTWALLETD_URL"
echo "Wallet Dir: $WALLET_DATA_DIR"
echo ""

# Check if wallet already exists
if [ -f "$WALLET_DATA_DIR/zecwallet-light-wallet.dat" ]; then
    echo "Wallet already exists at $WALLET_DATA_DIR"
    echo ""
    read -p "Do you want to (S)ync, (B)ackup seed, or (R)estore from seed? [S/B/R]: " action
    
    case $action in
        [Bb])
            echo ""
            echo "Showing wallet seed phrase (KEEP THIS SAFE!):"
            echo "=========================================="
            $ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" seed
            echo "=========================================="
            ;;
        [Rr])
            echo ""
            echo "WARNING: This will delete the existing wallet!"
            read -p "Are you sure? [y/N]: " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                rm -f "$WALLET_DATA_DIR/zecwallet-light-wallet.dat"
                echo ""
                read -p "Enter seed phrase: " seed_phrase
                echo "Restoring wallet..."
                $ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" restore "$seed_phrase"
            fi
            ;;
        *)
            echo ""
            echo "Syncing wallet..."
            $ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" sync
            ;;
    esac
else
    echo "No wallet found. Creating new wallet..."
    echo ""
    
    # Create new wallet
    $ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" new
    
    echo ""
    echo "=========================================="
    echo "  IMPORTANT: Save your seed phrase!"
    echo "=========================================="
    $ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" seed
    echo "=========================================="
    echo ""
    echo "Your wallet has been created. Back up the seed phrase above!"
fi

echo ""
echo "Wallet Info:"
echo "=========================================="
$ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" info
echo ""

echo "Addresses:"
echo "=========================================="
$ZECWALLET_CLI --server "$LIGHTWALLETD_URL" --data-dir "$WALLET_DATA_DIR" addresses

echo ""
echo "Done!"
