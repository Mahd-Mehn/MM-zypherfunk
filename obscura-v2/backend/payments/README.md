# Obscura V2 - Zcash Payments Module

Privacy-preserving subscription payments using Zcash shielded transactions.

## 🔒 Overview

This module enables:
- **Shielded Payments**: Accept ZEC payments with full transaction privacy
- **Unified Addresses**: Support for all Zcash address types (UA, Sapling, Orchard)
- **Subscription Management**: Tier-based access with automatic verification
- **Encrypted Memos**: Attach metadata to payments without exposing content

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Payments API   │────▶│  lightwalletd    │────▶│   zcashd    │
│  (FastAPI)      │     │  (gRPC server)   │     │  (full node)│
└─────────────────┘     └──────────────────┘     └─────────────┘
        │                        │
        │                        │
        ▼                        ▼
┌─────────────────┐     ┌──────────────────┐
│  zecwallet-cli  │     │  Block Cache     │
│  (light client) │     │  (compact blocks)│
└─────────────────┘     └──────────────────┘
```

## 🚀 Quick Start

### Option 1: Standalone Mode (Recommended for Development)

Uses public lightwalletd servers - no need to run your own zcashd.

```bash
# Build and run payments service only
docker-compose -f docker-compose.zcash.yml --profile standalone up -d payments-standalone

# Check health
curl http://localhost:8005/health
```

### Option 2: Full Node Mode

Run your own zcashd + lightwalletd for maximum privacy and reliability.

```bash
# Start full stack (takes several hours for initial sync)
docker-compose -f docker-compose.zcash.yml --profile full-node up -d

# Monitor sync progress
docker logs -f obscura-zcashd
```

### Option 3: Direct Python

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export LIGHTWALLETD_URL=https://testnet.lightwalletd.com:9067
export ZCASH_NETWORK=testnet

# Run service
uvicorn payments.main:app --reload --port 8005
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| POST | `/subscribe` | Create subscription payment request |
| POST | `/check` | Check payment status |
| POST | `/simulate` | (Dev) Simulate payment receipt |

### Example: Create Subscription

```bash
curl -X POST http://localhost:8005/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "tier": "pro"
  }'
```

Response:
```json
{
  "payment_address": "u1abc...",
  "amount_zec": 0.1,
  "status": "pending_payment"
}
```

### Example: Check Payment

```bash
curl -X POST http://localhost:8005/check \
  -H "Content-Type: application/json" \
  -d '{
    "payment_address": "u1abc..."
  }'
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LIGHTWALLETD_URL` | lightwalletd gRPC endpoint | `https://mainnet.lightwalletd.com:9067` |
| `ZCASH_NETWORK` | Network: `mainnet` or `testnet` | `testnet` |
| `ZECWALLET_CLI_PATH` | Path to zecwallet-cli binary | `/usr/local/bin/zecwallet-cli` |
| `WALLET_DATA_DIR` | Directory for wallet data | `/app/data/wallet` |
| `ZECWALLET_DECRYPTION_KEY` | Wallet encryption password | (none) |

### Public Lightwalletd Servers

For development/testing, use public servers:

| Network | Server | Port |
|---------|--------|------|
| Mainnet | `mainnet.lightwalletd.com` | 9067 |
| Testnet | `testnet.lightwalletd.com` | 9067 |

## 🔧 Running Your Own Infrastructure

### Prerequisites

1. **Disk Space**: ~100GB for zcashd blockchain data
2. **Memory**: 4GB+ RAM recommended
3. **Time**: Initial sync takes 6-24 hours

### Setup zcashd

1. Edit `config/zcash.conf`:
```conf
experimentalfeatures=1
lightwalletd=1
txindex=1
rpcuser=zcashrpc
rpcpassword=YOUR_STRONG_PASSWORD
```

2. Start zcashd and wait for sync:
```bash
docker-compose -f docker-compose.zcash.yml --profile full-node up -d zcashd
docker logs -f obscura-zcashd
```

### Setup lightwalletd

Once zcashd is synced:
```bash
docker-compose -f docker-compose.zcash.yml --profile full-node up -d lightwalletd
```

Test connectivity:
```bash
grpcurl -plaintext localhost:9067 cash.z.wallet.sdk.rpc.CompactTxStreamer/GetLightdInfo
```

## 🔐 Security Considerations

### Production Checklist

- [ ] Use TLS for lightwalletd (generate certs via Let's Encrypt)
- [ ] Change default RPC passwords in `zcash.conf`
- [ ] Restrict RPC access to lightwalletd container only
- [ ] Enable wallet encryption in zecwallet-cli
- [ ] Regular wallet backups
- [ ] Monitor for incoming payments with proper confirmation depth

### TLS Certificate Setup

```bash
# Generate self-signed for testing
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 365 -subj "/CN=lightwalletd.local"

# For production, use certbot:
certbot certonly --standalone -d your-domain.com
```

## 💰 Subscription Tiers

| Tier | Price (ZEC) | Features |
|------|-------------|----------|
| Basic | 0.01 | Basic copy trading |
| Pro | 0.10 | Advanced analytics, priority execution |

## 🧪 Testing

### Get Testnet ZEC

1. Generate a testnet address:
```bash
curl -X POST http://localhost:8005/subscribe \
  -d '{"user_id": "test", "tier": "basic"}'
```

2. Get testnet ZEC from faucet: https://faucet.testnet.z.cash/

3. Send ZEC to the address and verify:
```bash
curl -X POST http://localhost:8005/check \
  -d '{"payment_address": "YOUR_ADDRESS"}'
```

### Mock Mode

For testing without real ZEC:
```bash
# Simulate payment
curl -X POST http://localhost:8005/simulate \
  -d '{"payment_address": "YOUR_ADDRESS"}'
```

## 📚 Resources

- [Zcash Documentation](https://zcash.readthedocs.io/)
- [lightwalletd GitHub](https://github.com/zcash/lightwalletd)
- [zecwallet-cli](https://github.com/adityapk00/zecwallet-light-cli)
- [Unified Addresses](https://z.cash/learn/what-are-zcash-unified-addresses/)
- [Zcash Protocol](https://zips.z.cash/)

## 🐛 Troubleshooting

### lightwalletd won't connect to zcashd

```bash
# Check zcashd is running and synced
docker exec obscura-zcashd zcash-cli getblockchaininfo

# Check RPC credentials match
grep rpc config/zcash.conf
```

### Wallet not syncing

```bash
# Check lightwalletd logs
docker logs obscura-lightwalletd

# Verify gRPC is accessible
grpcurl -plaintext localhost:9067 list
```

### Payment not detected

1. Verify minimum confirmations (default: 1)
2. Check wallet sync status
3. Ensure correct network (testnet vs mainnet)
