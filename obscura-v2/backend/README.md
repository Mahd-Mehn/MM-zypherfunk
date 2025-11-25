# Obscura V2 Backend - Modular Monolith Architecture

Privacy-preserving copy trading platform with secure credential storage and shielded payments.

## 🏗️ Architecture Overview

This backend follows a **Modular Monolith** architecture, allowing both unified deployment and standalone microservices deployment.

```
backend/
├── shared/                     # Cross-cutting concerns
│   ├── config.py              # Centralized configuration
│   ├── database/              # Database models & connections
│   │   ├── connection.py      # AsyncPG connection pool
│   │   └── models.py          # SQLAlchemy models
│   └── services/              # Shared services
│       └── redis_service.py   # Redis caching & pub/sub
│
├── modules/                    # Domain-bounded modules
│   ├── api_gateway/           # Unified entry point
│   ├── trading/               # Multi-exchange trading
│   ├── subscriptions/         # Zcash billing
│   ├── copy_trading/          # Trade monitoring & copying
│   ├── analytics/             # Performance metrics
│   └── citadel/               # Nillion secure storage
│
├── alembic/                   # Database migrations
├── docker-compose.yml         # Full stack orchestration
└── requirements.txt           # Unified dependencies
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### 1. Clone & Configure

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Start with Docker (Recommended)

```bash
# Start full stack (API Gateway + Infrastructure)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api-gateway
```

### 3. Run Migrations

```bash
# Run database migrations
docker-compose --profile migrations up migrations
```

## 📦 Module Deployment Options

### Option A: Modular Monolith (Default)

All modules run within the API Gateway:

```bash
docker-compose up -d api-gateway postgres redis
```

**Ports:**
- API Gateway: `http://localhost:8000`

### Option B: Standalone Services

Deploy individual modules as microservices:

```bash
# Start infrastructure
docker-compose up -d postgres redis

# Start specific services
docker-compose --profile standalone up -d trading
docker-compose --profile standalone up -d subscriptions
docker-compose --profile standalone up -d analytics
docker-compose --profile standalone up -d citadel
docker-compose --profile standalone up -d copy-trading
```

**Ports:**
- Trading: `http://localhost:8001`
- Subscriptions: `http://localhost:8002`
- Copy Trading: `http://localhost:8003`
- Analytics: `http://localhost:8004`
- Citadel: `http://localhost:8005`

### Option C: Full Microservices

Deploy all services separately:

```bash
docker-compose --profile full up -d
```

## 🔧 Local Development

### Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Individual Modules

```bash
# Start API Gateway
cd modules/api_gateway
uvicorn gateway:app --reload --port 8000

# Start Trading Service
cd modules/trading
uvicorn service:app --reload --port 8001

# Start Analytics Service
cd modules/analytics
uvicorn service:app --reload --port 8004
```

## 📚 API Documentation

Once running, access the OpenAPI docs:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

### Key Endpoints

| Module | Endpoint | Description |
|--------|----------|-------------|
| Auth | `POST /api/v1/auth/register` | User registration |
| Auth | `POST /api/v1/auth/login` | User login |
| Trading | `POST /api/v1/trading/execute` | Execute trade |
| Trading | `GET /api/v1/trading/balances` | Get balances |
| Subscriptions | `POST /api/v1/subscriptions/subscribe` | Create subscription |
| Copy Trading | `POST /api/v1/copy/follow` | Follow a trader |
| Analytics | `GET /api/v1/analytics/leaderboard` | Get leaderboard |
| Citadel | `POST /api/v1/keys/store` | Store API keys |

## 🔐 Security Features

### Nillion SecretVault (Citadel)
- Secure credential storage using blind compute
- API keys never exposed in plaintext
- MPC-based key management

### Zcash Shielded Transactions (Subscriptions)
- Private subscription payments
- No transaction graph exposure
- Automatic payment verification

### Zero-Knowledge Proofs
- Trade execution without exposing strategy
- Privacy-preserving portfolio analytics
- Verifiable trade copying

## 📊 Module Details

### Trading Module
- **100+ Exchange Support** via CCXT
- CEX: Binance, Coinbase, Kraken, etc.
- DEX: Uniswap, SushiSwap, PancakeSwap
- Smart order routing
- Rate limiting & retry logic

### Copy Trading Module
- Real-time trade monitoring
- Proportional position sizing
- Configurable risk limits
- Automatic trade execution

### Analytics Module
- Performance metrics (ROI, Sharpe, etc.)
- Leaderboard rankings
- Trade history analysis
- Portfolio tracking

### Subscriptions Module
- Zcash payment processing
- Tier-based access control
- Automatic renewal
- Usage tracking

### Citadel Module
- Nillion integration
- Secure key storage
- Blind compute operations
- Encrypted data handling

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules --cov-report=html

# Run specific module tests
pytest modules/trading/tests/
pytest modules/analytics/tests/
```

## 🐳 Docker Build

### Build Individual Modules

```bash
# Build trading module
docker build -f modules/trading/Dockerfile -t obscura-trading .

# Build citadel module
docker build -f modules/citadel/Dockerfile -t obscura-citadel .
```

### Build All Modules

```bash
docker-compose build
```

## 📝 Environment Variables

See `.env.example` for all configuration options. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection | Yes |
| `REDIS_URL` | Redis connection | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `NILLION_ORG_SECRET_KEY` | Nillion auth | For Citadel |
| `ZCASH_NODE_URL` | Zcash node | For Subscriptions |

## 🔄 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## 📈 Monitoring

### Health Checks

Each module exposes a health endpoint:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
# etc.
```

### Prometheus Metrics

Metrics available at `/metrics` endpoint (when enabled).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
