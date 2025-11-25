# Obscura v2 Backend

Production-grade decentralized copy-trading infrastructure powered by **Nillion**, **NEAR Chain Signatures**, and **Zcash**.

## 🏗️ Architecture Overview

This backend implements the "Grand Slam" feature lineup for maximum hackathon impact:

1. **Citadel (Nillion)** - Decentralized secret storage using Nillion's `nilDB` and blind computation (`nilCC`)
2. **Conductor (NEAR MPC)** - Cross-chain transaction signing via NEAR's Multi-Party Computation network
3. **Payments (Zcash)** - Shielded subscription payments for privacy-preserving monetization

### Key Features

- ✅ **No centralized key storage** - API keys secured in Nillion's distributed network
- ✅ **Cross-chain execution** - Sign transactions for EVM chains (Base, Ethereum, etc.) from NEAR
- ✅ **Shielded payments** - Accept ZEC subscriptions with full privacy guarantees
- ✅ **Zero-Knowledge proofs** - Trading reputation verified without revealing strategies

## 📋 Prerequisites

### 1. Nillion Setup (Citadel)

**Option A: Use Nillion Testnet (Recommended)**
```bash
# Install the secretvaults SDK
pip install git+https://github.com/NillionNetwork/secretvaults-py.git

# Set environment variables
export NILLION_NETWORK_URL="https://testnet.nillion.network"
export NILLION_API_KEY="your-api-key"  # Get from Nillion dashboard
```

**Option B: Local Development (Mock Mode)**
```bash
# Leave NILLION_NETWORK_URL unset - the client will run in mock mode
# This is fine for initial development and testing
```

### 2. NEAR Chain Signatures Setup (Conductor)

**Option A: Use a Relayer (Easiest for Dev)**
```bash
# Clone the NEAR chainsig example
git clone https://github.com/near-examples/chainsig-script.git
cd chainsig-script

# Install dependencies
yarn install

# Set up your .env file
cp .env-sample .env
# Edit .env with your NEAR testnet account details

# The example repo provides ready-to-use signing functions
# You can wrap these in a simple HTTP server for your relayer
```

**Minimal Relayer Server (Python)**
```python
# Save as relayer.py and run alongside your backend
from fastapi import FastAPI
import subprocess
import json

app = FastAPI()

@app.post("/sign")
async def sign_transaction(request: dict):
    # Call the NEAR chainsig script
    result = subprocess.check_output([
        "node", "path/to/chainsig-script/index.js",
        "--payload", request["payload"],
        "--path", request["path"]
    ])
    return json.loads(result)

# Run: uvicorn relayer:app --port 8080
```

**Set environment variable:**
```bash
export NEAR_CHAINSIG_RELAYER_URL="http://localhost:8080/sign"
```

**Option B: Direct RPC Mode**
```bash
# For production, call the MPC contract directly
export NEAR_MPC_CONTRACT_ID="v1.signer-prod.testnet"
export NEAR_MPC_PUBLIC_KEY="secp256k1:4NfTiv3UsGahebgTaHyD9vF8KYKMBnfd6kh94mK6xv8fGBiJB8TBtFMP5WWXz6B89Ac1fbpzPwAvoyQebemHFwx3"
export NEAR_RPC_URL="https://rpc.testnet.near.org"
export NEAR_ACCOUNT_ID="your-account.testnet"
export NEAR_PRIVATE_KEY="ed25519:your-private-key"
```

### 3. Zcash Setup (Payments)

**Download Zecwallet CLI:**
```bash
# Linux/macOS
wget https://github.com/adityapk00/zecwallet-light-cli/releases/download/v1.7.7/linux-zecwallet-cli-v1.7.7.zip
unzip linux-zecwallet-cli-v1.7.7.zip
chmod +x zecwallet-cli

# Set environment variable
export ZECWALLET_CLI_PATH="/path/to/zecwallet-cli"
```

**Optional: Set wallet password**
```bash
export ZECWALLET_DECRYPTION_KEY="your-wallet-password"
```

## 🚀 Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install optional packages (if not on PyPI)
pip install git+https://github.com/NillionNetwork/secretvaults-py.git
```

## ⚙️ Configuration

Create a `.env` file in the `backend/` directory:

```bash
# Nillion Configuration
NILLION_NETWORK_URL=https://testnet.nillion.network
NILLION_API_KEY=your-nillion-api-key

# NEAR Chain Signatures
NEAR_CHAINSIG_RELAYER_URL=http://localhost:8080/sign
# OR for direct mode:
# NEAR_MPC_CONTRACT_ID=v1.signer-prod.testnet
# NEAR_ACCOUNT_ID=yourname.testnet
# NEAR_PRIVATE_KEY=ed25519:...

# Zcash Payments
ZECWALLET_CLI_PATH=/path/to/zecwallet-cli
ZECWALLET_DECRYPTION_KEY=optional-wallet-password

# Application Settings
DATABASE_URL=postgresql://user:pass@localhost/obscura
SECRET_KEY=your-secret-key-for-jwt
```

## 🧪 Testing the Integrations

### Test Nillion Client

```python
import asyncio
from citadel.nillion_client import nillion

async def test_nillion():
    # Store a secret
    store_id = await nillion.store_secret("my-api-key-secret", "binance-key-1")
    print(f"Stored secret: {store_id}")
    
    # Compute a signature using the secret
    signature = await nillion.compute_signature(store_id, b"transaction-payload")
    print(f"Signature: {signature}")

asyncio.run(test_nillion())
```

### Test NEAR MPC Client

```python
import asyncio
from conductor.near_client import near_mpc

async def test_near():
    # Derive an Ethereum address
    eth_address = near_mpc.derive_eth_address("yourname.testnet", "ethereum-1")
    print(f"Derived ETH address: {eth_address}")
    
    # Request a signature (requires relayer or full setup)
    payload = b"x00" * 32  # 32-byte transaction hash
    signature = await near_mpc.request_signature(payload, "ethereum-1", "yourname.testnet")
    print(f"Signature: {signature}")

asyncio.run(test_near())
```

### Test Zcash Client

```python
from payments.zcash_client import zcash

# Generate a new unified address
address = zcash.get_new_unified_address()
print(f"New UA: {address}")

# Watch for payment
zcash.watch_address(address, 0.01)  # Expect 0.01 ZEC

# Check payment status
import asyncio
paid = asyncio.run(zcash.check_payment(address))
print(f"Payment received: {paid}")

# For demo/testing: simulate payment
zcash.simulate_payment(address)
```

## 🎯 Usage Examples

### Store Exchange API Keys Securely

```python
from citadel.nillion_client import nillion

async def store_user_keys(user_id: str, api_key: str, api_secret: str):
    """Store user's exchange API credentials in Nillion."""
    key_store_id = await nillion.store_secret(api_key, f"user-{user_id}-key")
    secret_store_id = await nillion.store_secret(api_secret, f"user-{user_id}-secret")
    
    # Save store_ids to your database
    return {"key_id": key_store_id, "secret_id": secret_store_id}
```

### Execute Cross-Chain Trade

```python
from conductor.near_client import near_mpc
from eth_account import Account
from web3 import Web3

async def execute_trade_on_base(user_near_account: str, swap_data: bytes):
    """Sign and execute a trade on Base using NEAR MPC."""
    
    # Derive the user's controlled address on Base
    base_address = near_mpc.derive_eth_address(user_near_account, "base-trading-1")
    
    # Build transaction
    tx = {
        "to": "0x...",  # DEX router address
        "data": swap_data,
        "gas": 200000,
        "nonce": ...,
    }
    
    # Get transaction hash
    w3 = Web3()
    tx_hash = w3.keccak(...)  # Serialize and hash the transaction
    
    # Request signature from NEAR MPC
    signature = await near_mpc.request_signature(tx_hash, "base-trading-1", user_near_account)
    
    # Combine transaction + signature and broadcast
    # ...
    
    return tx_hash.hex()
```

### Process Shielded Subscription Payment

```python
from payments.zcash_client import zcash

async def create_subscription(trader_id: str, plan: str) -> str:
    """Generate a payment address for trader subscription."""
    
    # Generate unique address for this subscription
    payment_address = zcash.get_new_unified_address()
    
    # Define subscription tiers
    tiers = {"basic": 0.1, "pro": 0.5, "enterprise": 2.0}
    amount_zec = tiers[plan]
    
    # Watch for payment
    zcash.watch_address(payment_address, amount_zec)
    
    return payment_address

async def verify_subscription_payment(payment_address: str) -> bool:
    """Check if subscription payment was received."""
    return await zcash.check_payment(payment_address, min_confirmations=2)
```

## 🎪 Demo Mode

All three clients support mock mode for development without external dependencies:

```bash
# Run without any environment variables
python -m citadel.nillion_client  # Mock Nillion
python -m conductor.near_client   # Mock NEAR MPC
python -m payments.zcash_client   # Mock Zcash
```

The clients will automatically detect missing SDKs and run in demonstration mode while maintaining compatible interfaces.

## 🔐 Security Best Practices

1. **Never commit `.env` files** - Add to `.gitignore`
2. **Rotate NEAR keys regularly** - Use separate keys for dev/prod
3. **Encrypt Zecwallet** - Always use wallet encryption in production
4. **Validate derivation paths** - Sanitize user-provided paths to prevent path traversal
5. **Rate limit signature requests** - Prevent abuse of MPC signing service
6. **Monitor Nillion quotas** - Track API usage to avoid service interruptions

## 📚 Additional Resources

### Nillion
- [Nillion Docs](https://docs.nillion.com)
- [SecretVaults Python Examples](https://github.com/NillionNetwork/secretvaults-py/tree/main/examples)
- [Blind Computation Guide](https://docs.nillion.com/build/compute/overview)

### NEAR Chain Signatures
- [Official Documentation](https://docs.near.org/chain-abstraction/chain-signatures)
- [Example Scripts](https://github.com/near-examples/chainsig-script)
- [MPC Contract Source](https://github.com/near/mpc)

### Zcash
- [Unified Addresses Explained](https://z.cash/learn/what-are-zcash-unified-addresses/)
- [Zecwallet Python Wrapper](https://github.com/P5vc/zecwallet-python)
- [Zcash Developer Docs](https://z.cash/learn/)

## 🏆 Hackathon Bounty Alignment

This implementation targets:

- **NEAR Cross-Chain** ($20k) - Chain signatures for Base/EVM execution
- **Nillion** ($25k NIL) - Decentralized secret storage for API keys
- **Zcash Community** ($5k) - Shielded payment integration
- **Project Tachyon** ($35k pool) - Privacy infrastructure
- **General Cross-Chain** ($55k pool) - Multi-chain architecture

**Total Potential:** $100k+

## 🤝 Contributing

This is a hackathon project. For production use:
- Implement comprehensive error handling
- Add transaction retry logic
- Set up monitoring/alerting
- Perform security audits
- Add comprehensive test coverage

## 📄 License

MIT License - See LICENSE file for details
