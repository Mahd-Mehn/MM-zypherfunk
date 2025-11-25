# Obscura V2 - Privacy-Preserving Social Trading Protocol

![Obscura Banner](https://via.placeholder.com/1200x400?text=Obscura+V2+-+Trade+With+Proof,+Not+Trust)

> **Hackathon Submission**: A modular, privacy-first social trading platform leveraging Zero-Knowledge Proofs (ZK), Trusted Execution Environments (TEE), and Shielded Payments.

## 🚀 Project Overview

Obscura V2 revolutionizes social trading by solving the "transparency vs. privacy" dilemma. Traditional platforms require traders to expose their full history and strategies. Obscura allows traders to **prove** their performance without **revealing** their sensitive trade data.

- **For Traders**: Monetize your skills without leaking your alpha. Use ZK proofs (DEX) and TEE attestations (CEX) to verify performance.
- **For Followers**: Copy trade with confidence, knowing performance metrics are cryptographically verified.
- **Privacy First**: Subscription payments are shielded via Zcash, and API keys are secured using Nillion's blind compute network.

## 🏗️ Architecture

The project follows a **Modular Monolith** architecture for the backend, **Starknet-native STARK proofs** for verification, and a modern **Next.js** frontend.

```
.
├── obscura-v2/
│   ├── backend/                # Modular Monolith (Python/FastAPI)
│   │   ├── modules/            # Domain-bounded services
│   │   │   ├── api_gateway/    # Unified entry point
│   │   │   ├── trading/        # Multi-exchange execution (CCXT)
│   │   │   ├── citadel/        # Secure storage (Nillion)
│   │   │   ├── subscriptions/  # Private payments (Zcash)
│   │   │   ├── copy_trading/   # Copy engine
│   │   │   └── analytics/      # Performance metrics
│   │   ├── payments/           # Zcash payment engine
│   │   └── shared/             # Shared kernel (DB, Config)
│   │
│   ├── verification/           # 🆕 Starknet ZK-STARK Proofs
│   │   ├── cairo/              # Cairo 1.0 contracts & circuits
│   │   │   ├── src/types.cairo     # Trade, Position, Report types
│   │   │   ├── src/prover.cairo    # Off-chain proof logic
│   │   │   └── src/verifier.cairo  # On-chain verification contract
│   │   └── service/            # TypeScript orchestration
│   │
│   └── frontend/               # Next.js 14 App Router
│       ├── app/                # Pages & Layouts
│       ├── components/         # Shadcn/UI Components
│       └── lib/                # Utilities & API Clients
│
└── documentation/              # Architecture & Protocol Specs
```

## ✨ Key Features

### 🛡️ Privacy & Security

- **Starknet ZK-STARK Proofs**: Prove win rates and PnL using Cairo circuits with **no trusted setup** and **post-quantum security**.
- **Nillion SecretVault**: API keys for exchanges (Binance, Coinbase) are stored and used via blind compute—never exposed to the backend in plaintext.
- **Zcash Shielded Payments**: Subscriptions are paid in ZEC using Unified Addresses, preserving financial privacy for followers.

### ⚡ Trading Engine

- **Universal Connector**: Support for 100+ exchanges via CCXT.
- **Real-time Copying**: Low-latency trade replication engine.
- **Smart Routing**: Optimizes execution across liquidity sources.

### 📊 Analytics

- **Verifiable Leaderboard**: Rankings based on cryptographically proven metrics.
- **Performance Attribution**: Detailed breakdown of PnL sources.

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy (Async), PostgreSQL, Redis
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/UI
- **Infrastructure**: Docker, Docker Compose
- **ZK Verification (Starknet)**:
  - **Cairo 1.0**: Smart contracts and proof circuits
  - **Scarb**: Cairo package manager
  - **Starknet.js**: TypeScript SDK for Starknet
- **Web3/Privacy**:
  - **Nillion**: Secure Multi-Party Computation (MPC) for secrets.
  - **Zcash**: Shielded transactions for payments.
  - **Starknet L2**: Native STARK proof verification.

## 🏁 Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ & pnpm
- Python 3.11+

### 1. Backend Setup

The backend is containerized. You can run the full stack with one command.

```bash
cd obscura-v2/backend

# Configure environment
cp .env.example .env
# (Edit .env with your credentials)

# Start services
docker-compose up -d
```

Services will be available at:

- **API Gateway**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`

### 2. Verification Module (Starknet)

```bash
cd obscura-v2/verification/cairo

# Build Cairo contracts
scarb build

# Run tests
scarb test

# Start the orchestration service
cd ../service
pnpm install
pnpm dev
```

### 3. Frontend Setup

```bash
cd obscura-v2/frontend

# Install dependencies
pnpm install

# Configure environment
cp .env.example .env.local

# Start development server
pnpm dev
```

Visit `http://localhost:3000` to view the application.

## 🧪 Testing

**Backend**:

```bash
cd obscura-v2/backend
pytest
```

**Cairo Contracts**:

```bash
cd obscura-v2/verification/cairo
scarb test
```

**Frontend**:

```bash
cd obscura-v2/frontend
pnpm test
```

## 📚 Documentation

Detailed documentation is available in the `documentation/` folder:
- [System Architecture](documentation/04_SYSTEM_ARCHITECTURE.md)
- [Privacy Architecture](documentation/01_PRIVACY_ARCHITECTURE_OVERVIEW.md)
- [ZK Implementation](documentation/03_ZK_IMPLEMENTATION.md)
- [Security Model](documentation/05_SECURITY_MODEL.md)

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
